"""Command Coxa/CH0, Femur/CH1 and Tibia/CH2 sequentially, then release."""

import argparse
import time

if __package__:
    from .cli_common import (add_motion_options, confirm, finite_float, motion_settings,
                             nonnegative_float, run_cli)
    from .pca9685_controller import JOINT_CHANNELS, ServoRig, validate_angle
else:
    from cli_common import (add_motion_options, confirm, finite_float, motion_settings,
                            nonnegative_float, run_cli)
    from pca9685_controller import JOINT_CHANNELS, ServoRig, validate_angle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--angles", nargs=3, type=finite_float, default=[90.0] * 3,
                        metavar=("COXA", "FEMUR", "TIBIA"))
    parser.add_argument("--step-delay", type=nonnegative_float, default=1.0)
    add_motion_options(parser)
    args = parser.parse_args()
    settings = motion_settings(args.allow_wide_range)
    try:
        for angle in args.angles:
            validate_angle(angle, settings)
    except ValueError as exc:
        parser.error(str(exc))
    plan = list(zip(JOINT_CHANNELS.items(), args.angles))
    for (joint, channel), angle in plan:
        print(f"{joint}: CH{channel} -> {angle:g} deg PWM command")
    print(f"Step delay {args.step_delay:g} s; final hold {args.hold:g} s")
    confirm(args.yes)
    with ServoRig(address=args.address, settings=settings) as rig:
        for index, ((joint, channel), angle) in enumerate(plan):
            rig.set_angle(channel, angle)
            if index < len(plan) - 1:
                time.sleep(args.step_delay)
        time.sleep(args.hold)
        rig.release_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
