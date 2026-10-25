"""Shared CLI validation and operator confirmation, without hardware imports."""

import argparse
import math
import sys
from collections.abc import Callable

if __package__:
    from .pca9685_controller import DEFAULT_I2C_ADDRESS, ServoSettings
else:
    from pca9685_controller import DEFAULT_I2C_ADDRESS, ServoSettings


def address_value(value: str) -> int:
    """Accept decimal or 0x-prefixed seven-bit device addresses."""
    try:
        address = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use an integer address, e.g. 0x40") from exc
    if not 0x08 <= address <= 0x77:
        raise argparse.ArgumentTypeError("Address must be in 0x08..0x77")
    return address


def finite_float(value: str) -> float:
    """Reject NaN/infinity at the CLI boundary."""
    try:
        result = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected a number") from exc
    if not math.isfinite(result):
        raise argparse.ArgumentTypeError("Expected a finite number")
    return result


def nonnegative_float(value: str) -> float:
    result = finite_float(value)
    if result < 0:
        raise argparse.ArgumentTypeError("Value must be >= 0")
    return result


def add_address(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--address", type=address_value, default=DEFAULT_I2C_ADDRESS)


def add_motion_options(parser: argparse.ArgumentParser) -> None:
    add_address(parser)
    parser.add_argument("--hold", type=nonnegative_float, default=1.0)
    parser.add_argument("--allow-wide-range", action="store_true",
                        help="Allow 0..180 commands ONLY after physical limits are verified")
    parser.add_argument("-y", "--yes", action="store_true")


def motion_settings(wide: bool) -> ServoSettings:
    return ServoSettings(min_deg=0, max_deg=180) if wide else ServoSettings()


def confirm(yes: bool = False) -> None:
    """Print the warning even when confirmation has been supplied by flag."""
    print("WARNING: External 6.0 V servo PSU and common GND required. "
          "Keep the leg unloaded and clear; even 90 deg can hit a mechanical stop. "
          "Cut servo power immediately on binding/stall. PWM release is not power isolation.")
    if not yes and input("Press Enter to move; type anything to cancel: ").strip():
        raise ValueError("Movement cancelled")


def run_cli(action: Callable[[], int]) -> int:
    """Return useful exit codes after context managers have cleaned up."""
    try:
        return action()
    except KeyboardInterrupt:
        print("Interrupted; PWM cleanup attempted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
