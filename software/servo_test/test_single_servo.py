"""Command one unloaded servo once, hold briefly, and release PWM."""

import argparse
import time

if __package__:
    from .cli_common import add_motion_options, confirm, finite_float, motion_settings, run_cli
    from .pca9685_controller import ServoRig, validate_angle, validate_channel
else:
    from cli_common import add_motion_options, confirm, finite_float, motion_settings, run_cli
    from pca9685_controller import ServoRig, validate_angle, validate_channel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--angle", type=finite_float, default=90.0)
    add_motion_options(parser)
    args = parser.parse_args()
    settings = motion_settings(args.allow_wide_range)
    try:
        validate_channel(args.channel)
        validate_angle(args.angle, settings)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"CH{args.channel}: target PWM command {args.angle:g} deg; hold {args.hold:g} s")
    confirm(args.yes)
    with ServoRig(address=args.address, settings=settings) as rig:
        rig.set_angle(args.channel, args.angle)
        time.sleep(args.hold)
        rig.release(args.channel)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
