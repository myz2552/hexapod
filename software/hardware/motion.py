"""Speed-limited joint motion on top of calibration and a servo output.

Poses are kinematic joint angles keyed by (leg, joint). Every target is
mapped through the calibration (which enforces measured limits) before any
output is written, so a rejected move never moves a servo partially.
"""

import math
import time
from collections.abc import Callable, Mapping

from .calibration import JointCalibration, LegCalibration
from .pca9685_bank import ServoOutput

JointKey = tuple[str, str]
Pose = Mapping[JointKey, float]


class MotionError(RuntimeError):
    """Raised when motion is requested in an invalid controller state."""


class JointMotion:
    def __init__(self, output: ServoOutput, calibration: Mapping[str, LegCalibration],
                 max_speed_deg_s: float = 60.0, rate_hz: float = 50.0,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        if not (math.isfinite(max_speed_deg_s) and max_speed_deg_s > 0):
            raise ValueError("max_speed_deg_s must be positive")
        if not (math.isfinite(rate_hz) and 0 < rate_hz <= 200):
            raise ValueError("rate_hz must be in (0, 200]")
        self.output = output
        self.calibration = calibration
        self.max_speed_deg_s = float(max_speed_deg_s)
        self.rate_hz = float(rate_hz)
        self._sleep = sleep
        self.current: dict[JointKey, float] | None = None

    def _joint(self, key: JointKey) -> JointCalibration:
        leg, joint = key
        try:
            return self.calibration[leg][joint]
        except KeyError as exc:
            raise ValueError(f"No calibration for {leg}.{joint}") from exc

    def commands_for(self, pose: Pose) -> dict[JointKey, float]:
        """Map a full pose to command angles or raise before anything moves."""
        if not pose:
            raise ValueError("Pose is empty")
        return {key: self._joint(key).to_command(angle) for key, angle in pose.items()}

    def _write(self, commands: Mapping[JointKey, float]) -> None:
        for key, command in commands.items():
            cal = self._joint(key)
            self.output.write(cal.board, cal.channel, command)

    def initialize(self, pose: Pose, joint_delay_s: float = 0.5) -> None:
        """Send a start pose one joint at a time.

        The real start position is unknown, so this step cannot be speed
        limited: each servo jumps at its own maximum speed. Keep the leg
        unloaded and choose a pose close to where the leg already rests.
        """
        commands = self.commands_for(pose)
        for index, (key, command) in enumerate(commands.items()):
            self._write({key: command})
            if index < len(commands) - 1:
                self._sleep(joint_delay_s)
        self.current = dict(pose)

    def move_to(self, pose: Pose) -> int:
        """Linearly interpolate in joint space at <= max speed; returns steps."""
        if self.current is None:
            raise MotionError("Call initialize() before move_to()")
        unknown = set(pose) - set(self.current)
        if unknown:
            raise MotionError(f"Joints not initialized: {sorted(unknown)}")
        targets = dict(pose)
        self.commands_for(targets)  # validate end pose before moving
        start = {key: self.current[key] for key in targets}
        largest = max(abs(targets[k] - start[k]) for k in targets)
        steps = max(1, math.ceil(largest / (self.max_speed_deg_s / self.rate_hz) - 1e-9))
        for step in range(1, steps + 1):
            fraction = step / steps
            intermediate = {k: start[k] + (targets[k] - start[k]) * fraction for k in targets}
            self._write(self.commands_for(intermediate))
            self.current.update(intermediate)
            if step < steps:
                self._sleep(1.0 / self.rate_hz)
        return steps

    def release(self) -> None:
        """Stop holding position; joints may drop. Not power isolation."""
        self.current = None
        self.output.release_all()
