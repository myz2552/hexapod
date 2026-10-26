"""Servo calibration schema v2: kinematic joint angle <-> servo command angle.

Each joint stores raw physical measurements in servo *command* degrees:

* ``zero_cmd_deg``: command at which the joint is in its kinematic zero pose
  (see software/kinematics/README.md).
* ``ref_cmd_deg`` / ``ref_joint_deg``: command at which the joint sits at a
  known, physically measured joint angle (e.g. +45 deg with an angle jig).
* ``min_cmd_deg`` / ``max_cmd_deg``: safe command limits observed without
  stalling against a mechanical stop.

Direction and scale are derived from the two poses, so they cannot disagree
with the measurements. Values must come from physical calibration; never guess.
"""

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
JOINTS = ("coxa", "femur", "tibia")
MEASURED_FIELDS = ("zero_cmd_deg", "ref_cmd_deg", "ref_joint_deg", "min_cmd_deg", "max_cmd_deg")
FIELDS = ("board", "channel") + MEASURED_FIELDS
MIN_REF_SPAN_CMD_DEG = 5.0  # shorter spans make the derived scale too noisy
COMMAND_RANGE_DEG = (0.0, 180.0)
_EPS = 1e-9

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALIBRATION = REPO_ROOT / "config" / "servo_calibration.yaml"
EXAMPLE_CALIBRATION = REPO_ROOT / "config" / "servo_calibration.example.yaml"


class JointLimitError(ValueError):
    """Raised when a joint angle maps outside the calibrated command limits."""


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def validate_board(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0x08 <= value <= 0x77:
        raise ValueError("board must be an I2C address integer in 0x08..0x77")
    return value


def validate_channel(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 15:
        raise ValueError("channel must be an integer in 0..15")
    return value


@dataclass(frozen=True)
class JointCalibration:
    board: int
    channel: int
    zero_cmd_deg: float
    ref_cmd_deg: float
    ref_joint_deg: float
    min_cmd_deg: float
    max_cmd_deg: float

    def __post_init__(self) -> None:
        validate_board(self.board)
        validate_channel(self.channel)
        for name in MEASURED_FIELDS:
            _finite(getattr(self, name), name)
        low, high = COMMAND_RANGE_DEG
        if not low <= self.min_cmd_deg <= self.max_cmd_deg <= high:
            raise ValueError(f"Require {low:g} <= min_cmd_deg <= max_cmd_deg <= {high:g}")
        for name in ("zero_cmd_deg", "ref_cmd_deg"):
            if not self.min_cmd_deg <= getattr(self, name) <= self.max_cmd_deg:
                raise ValueError(f"{name} must lie within min_cmd_deg..max_cmd_deg")
        if self.ref_joint_deg == 0 or abs(self.ref_joint_deg) > 180:
            raise ValueError("ref_joint_deg must be non-zero and within +/-180")
        if abs(self.ref_cmd_deg - self.zero_cmd_deg) < MIN_REF_SPAN_CMD_DEG:
            raise ValueError(f"Reference and zero poses must differ by >= "
                             f"{MIN_REF_SPAN_CMD_DEG:g} command deg")

    @property
    def scale(self) -> float:
        """Signed command degrees per joint degree."""
        return (self.ref_cmd_deg - self.zero_cmd_deg) / self.ref_joint_deg

    @property
    def direction(self) -> int:
        return 1 if self.scale > 0 else -1

    @property
    def joint_limits_deg(self) -> tuple[float, float]:
        ends = sorted((self.to_joint(self.min_cmd_deg), self.to_joint(self.max_cmd_deg)))
        return ends[0], ends[1]

    def to_command(self, joint_deg: float) -> float:
        _finite(joint_deg, "joint_deg")
        command = self.zero_cmd_deg + self.scale * joint_deg
        if not self.min_cmd_deg - _EPS <= command <= self.max_cmd_deg + _EPS:
            low, high = self.joint_limits_deg
            raise JointLimitError(f"Joint angle {joint_deg:.2f} deg outside calibrated "
                                  f"{low:.2f}..{high:.2f} deg")
        return min(max(command, self.min_cmd_deg), self.max_cmd_deg)

    def to_joint(self, command_deg: float) -> float:
        return (_finite(command_deg, "command_deg") - self.zero_cmd_deg) / self.scale


LegCalibration = dict[str, JointCalibration]


def validate_document(data: Any) -> dict[str, Any]:
    """Check schema structure; measured values may still be null."""
    if not isinstance(data, dict):
        raise ValueError("Calibration must be a mapping")
    if "servos" in data or "channels" in data:
        raise ValueError("Calibration uses the old v1 schema; recalibrate with schema_version: 2")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Calibration requires schema_version: {SCHEMA_VERSION}")
    legs = data.get("legs")
    if not isinstance(legs, dict) or not legs:
        raise ValueError("Calibration requires a non-empty legs mapping")
    outputs: dict[tuple[int, int], str] = {}
    for leg, joints in legs.items():
        if not isinstance(leg, str) or not isinstance(joints, dict) or set(joints) != set(JOINTS):
            raise ValueError(f"Leg {leg!r} must map exactly coxa, femur, tibia")
        for joint in JOINTS:
            entry = joints[joint]
            where = f"{leg}.{joint}"
            if not isinstance(entry, dict) or not all(k in entry for k in FIELDS):
                raise ValueError(f"{where} must contain {', '.join(FIELDS)}")
            try:
                output = (validate_board(entry["board"]), validate_channel(entry["channel"]))
            except ValueError as exc:
                raise ValueError(f"{where}: {exc}") from exc
            if output in outputs:
                raise ValueError(f"{where} and {outputs[output]} share board 0x{output[0]:02x} "
                                 f"channel {output[1]}")
            outputs[output] = where
            for name in MEASURED_FIELDS:
                if entry[name] is not None:
                    try:
                        _finite(entry[name], name)
                    except ValueError as exc:
                        raise ValueError(f"{where}: {exc}") from exc
    return data


def parse_calibration(data: Any) -> dict[str, LegCalibration]:
    """Build complete calibrations; any null measurement is an error."""
    validate_document(data)
    result: dict[str, LegCalibration] = {}
    for leg, joints in data["legs"].items():
        result[leg] = {}
        for joint in JOINTS:
            entry = joints[joint]
            missing = [k for k in MEASURED_FIELDS if entry[k] is None]
            if missing:
                raise ValueError(f"{leg}.{joint} is not calibrated (null: {', '.join(missing)}); "
                                 "run calibrate_servo.py first")
            try:
                result[leg][joint] = JointCalibration(**{k: entry[k] for k in FIELDS})
            except ValueError as exc:
                raise ValueError(f"{leg}.{joint}: {exc}") from exc
    return result


def read_document(path: Path) -> dict[str, Any]:
    import yaml

    return validate_document(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def load_calibration(path: Path = DEFAULT_CALIBRATION) -> dict[str, LegCalibration]:
    import yaml

    return parse_calibration(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
