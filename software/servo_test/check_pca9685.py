"""Scan and open a PCA9685 without issuing servo movement commands."""

import argparse

if __package__:
    from .cli_common import add_address, run_cli
    from .pca9685_controller import DEFAULT_FREQUENCY_HZ, ServoRig, scan_i2c_addresses
else:
    from cli_common import add_address, run_cli
    from pca9685_controller import DEFAULT_FREQUENCY_HZ, ServoRig, scan_i2c_addresses


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_address(parser)
    parser.add_argument("--frequency", type=int, default=DEFAULT_FREQUENCY_HZ)
    args = parser.parse_args()
    if not 24 <= args.frequency <= 1526:
        parser.error("--frequency must be in 24..1526 Hz (use 50 for servos)")
    addresses = scan_i2c_addresses()
    print("I2C addresses: " + (", ".join(f"0x{a:02x}" for a in addresses) or "none"))
    if args.address not in addresses:
        raise RuntimeError(f"PCA9685 address 0x{args.address:02x} not found; check I2C and wiring")
    with ServoRig(address=args.address, frequency=args.frequency):
        print(f"OK: PCA9685 opened at 0x{args.address:02x}; PWM frequency = {args.frequency} Hz.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
