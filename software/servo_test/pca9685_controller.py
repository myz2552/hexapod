"""PCA9685 access; command angles are not measured robot joint angles."""

from dataclasses import dataclass
import math
import time
from typing import Any

DEFAULT_I2C_ADDRESS = 0x40
DEFAULT_FREQUENCY_HZ = 50
JOINT_CHANNELS = {"coxa": 0, "femur": 1, "tibia": 2}
# Bring-up command guard only: these are NOT measured mechanical limits.
FIRST_TEST_MIN_DEG = 60.0
FIRST_TEST_MAX_DEG = 120.0
# Common Servo helper mapping, NOT guaranteed MG996R physical endpoints.
# Calibrate for the actual manufacturer/model variant before wider movement.
DEFAULT_MIN_PULSE_US = 750
DEFAULT_MAX_PULSE_US = 2250
DEFAULT_ACTUATION_RANGE = 180.0


@dataclass(frozen=True)
class ServoSettings:
    """PWM mapping and allowed command interval, not physical calibration."""

    min_deg: float = FIRST_TEST_MIN_DEG
    max_deg: float = FIRST_TEST_MAX_DEG
    min_pulse: int = DEFAULT_MIN_PULSE_US
    max_pulse: int = DEFAULT_MAX_PULSE_US
    actuation_range: float = DEFAULT_ACTUATION_RANGE

    def __post_init__(self) -> None:
        values = (self.min_deg, self.max_deg, self.actuation_range,
                  self.min_pulse, self.max_pulse)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Servo settings must be finite")
        if not 0 <= self.min_deg <= self.max_deg <= self.actuation_range:
            raise ValueError("Require 0 <= min_deg <= max_deg <= actuation_range")
        if not 0 < self.min_pulse < self.max_pulse or self.actuation_range <= 0:
            raise ValueError("Invalid pulse mapping or actuation range")


def validate_channel(channel: int) -> None:
    """Reject invalid PCA9685 channels before touching hardware."""
    if isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel <= 15:
        raise ValueError("Channel must be an integer in 0..15")


def validate_angle(angle: float, settings: ServoSettings) -> None:
    """Reject nonfinite or out-of-range command angles."""
    if not math.isfinite(angle) or not settings.min_deg <= angle <= settings.max_deg:
        raise ValueError(f"Angle must be finite and in {settings.min_deg}..{settings.max_deg} deg")


def scan_i2c_addresses() -> list[int]:
    """Scan board.I2C with a bounded lock wait; release the bus on exit."""
    import board

    bus = board.I2C()
    locked = False
    try:
        deadline = time.monotonic() + 2.0
        while not locked:
            locked = bus.try_lock()
            if not locked:
                if time.monotonic() >= deadline:
                    raise TimeoutError("I2C bus remained locked")
                time.sleep(0.01)
        return list(bus.scan())
    finally:
        try:
            if locked:
                bus.unlock()
        finally:
            bus.deinit()


class ServoRig:
    """Own the bus and PCA9685; lazily construct Servo helpers without movement."""

    def __init__(self, address: int = DEFAULT_I2C_ADDRESS,
                 frequency: int = DEFAULT_FREQUENCY_HZ,
                 settings: ServoSettings | None = None) -> None:
        if not 0x08 <= address <= 0x77:
            raise ValueError("I2C address must be in 0x08..0x77")
        if not 24 <= frequency <= 1526:
            raise ValueError("PCA9685 frequency must be in 24..1526 Hz")
        self.settings = settings or ServoSettings()
        self._bus: Any = None
        self._pca: Any = None
        self._servos: dict[int, Any] = {}
        import board
        from adafruit_pca9685 import PCA9685

        try:
            self._bus = board.I2C()
            self._pca = PCA9685(self._bus, address=address)
            self._pca.frequency = frequency
            self.release_all()
        except BaseException:
            self.close()
            raise

    def _require_open(self) -> None:
        if self._pca is None:
            raise RuntimeError("ServoRig is closed")

    def set_angle(self, channel: int, angle_deg: float) -> None:
        """Send one validated PWM command; no ramp or endpoint search."""
        validate_channel(channel)
        validate_angle(angle_deg, self.settings)
        self._require_open()
        if channel not in self._servos:
            from adafruit_motor.servo import Servo

            self._servos[channel] = Servo(
                self._pca.channels[channel], min_pulse=self.settings.min_pulse,
                max_pulse=self.settings.max_pulse,
                actuation_range=self.settings.actuation_range)
        self._servos[channel].angle = angle_deg

    def release(self, channel: int) -> None:
        """Disable PWM without constructing a Servo helper."""
        validate_channel(channel)
        self._require_open()
        self._pca.channels[channel].duty_cycle = 0

    def release_all(self) -> None:
        """Attempt every output even if a channel write fails."""
        self._require_open()
        first_error: Exception | None = None
        for channel in range(16):
            try:
                self.release(channel)
            except Exception as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error

    def close(self) -> None:
        """Release all PWM, then deinitialize controller and bus; idempotent."""
        try:
            if self._pca is not None:
                try:
                    self.release_all()
                finally:
                    self._pca.deinit()
        finally:
            self._pca = None
            self._servos.clear()
            if self._bus is not None:
                try:
                    self._bus.deinit()
                finally:
                    self._bus = None

    def __enter__(self) -> "ServoRig":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
