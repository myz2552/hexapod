"""Several PCA9685 boards on one I2C bus, addressed by (board, channel).

Uses exactly the same pulse mapping as the bring-up/calibration tools
(software.servo_test.pca9685_controller), so calibrated command angles mean
the same pulse widths here. Command limits are enforced by the calibration
layer; this layer only rejects values outside the 0..180 command range.
"""

import math
from typing import Any, Protocol

from software.servo_test.pca9685_controller import DEFAULT_FREQUENCY_HZ, ServoSettings
from .calibration import validate_board, validate_channel

FULL_RANGE = ServoSettings(min_deg=0.0, max_deg=180.0)


class ServoOutput(Protocol):
    """Anything that can receive servo command angles."""

    def write(self, board: int, channel: int, command_deg: float) -> None: ...

    def release_all(self) -> None: ...


def _check_command(command_deg: float) -> None:
    if isinstance(command_deg, bool) or not isinstance(command_deg, (int, float)) \
            or not math.isfinite(command_deg) or not 0.0 <= command_deg <= 180.0:
        raise ValueError("Command angle must be finite and within 0..180")


class RecordingOutput:
    """Hardware-free output for dry runs and tests; records every write."""

    def __init__(self, boards: tuple[int, ...] = (0x40,)) -> None:
        self.boards = tuple(validate_board(b) for b in boards)
        self.writes: list[tuple[int, int, float]] = []
        self.releases = 0

    def write(self, board: int, channel: int, command_deg: float) -> None:
        if board not in self.boards:
            raise ValueError(f"Board 0x{board:02x} is not open")
        validate_channel(channel)
        _check_command(command_deg)
        self.writes.append((board, channel, float(command_deg)))

    def release_all(self) -> None:
        self.releases += 1


class PCA9685Bank:
    """Open all boards on a shared bus, release every output on open and close."""

    def __init__(self, boards: tuple[int, ...], frequency: int = DEFAULT_FREQUENCY_HZ,
                 settings: ServoSettings = FULL_RANGE) -> None:
        if not boards or len(set(boards)) != len(boards):
            raise ValueError("Give one or more distinct board addresses")
        for board in boards:
            validate_board(board)
        if not 24 <= frequency <= 1526:
            raise ValueError("PCA9685 frequency must be in 24..1526 Hz")
        self.settings = settings
        self._bus: Any = None
        self._pcas: dict[int, Any] = {}
        self._servos: dict[tuple[int, int], Any] = {}
        import board as board_module
        from adafruit_pca9685 import PCA9685

        try:
            self._bus = board_module.I2C()
            for address in boards:
                pca = PCA9685(self._bus, address=address)
                self._pcas[address] = pca
                pca.frequency = frequency
            self.release_all()
        except BaseException:
            self.close()
            raise

    @property
    def boards(self) -> tuple[int, ...]:
        return tuple(self._pcas)

    def write(self, board: int, channel: int, command_deg: float) -> None:
        validate_channel(channel)
        _check_command(command_deg)
        if board not in self._pcas:
            raise ValueError(f"Board 0x{board:02x} is not open")
        key = (board, channel)
        if key not in self._servos:
            from adafruit_motor.servo import Servo

            self._servos[key] = Servo(
                self._pcas[board].channels[channel], min_pulse=self.settings.min_pulse,
                max_pulse=self.settings.max_pulse, actuation_range=self.settings.actuation_range)
        self._servos[key].angle = command_deg

    def release_all(self) -> None:
        """Attempt every output on every board even if one write fails."""
        first_error: Exception | None = None
        for pca in self._pcas.values():
            for channel in range(16):
                try:
                    pca.channels[channel].duty_cycle = 0
                except Exception as exc:
                    if first_error is None:
                        first_error = exc
        if first_error is not None:
            raise first_error

    def close(self) -> None:
        """Release all PWM, then deinitialize boards and bus; idempotent."""
        try:
            try:
                self.release_all()
            finally:
                for pca in self._pcas.values():
                    try:
                        pca.deinit()
                    except Exception:
                        pass
        finally:
            self._pcas.clear()
            self._servos.clear()
            if self._bus is not None:
                try:
                    self._bus.deinit()
                finally:
                    self._bus = None

    def __enter__(self) -> "PCA9685Bank":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
