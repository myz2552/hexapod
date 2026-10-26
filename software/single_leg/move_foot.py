"""Move one leg's foot to XYZ targets in the leg frame (mm) via IK.

Dry run by default: prints joint and command angles without touching hardware.
--execute moves the leg; further targets are entered interactively and are
speed limited. Not hardware validated.
"""

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # script-style invocation
    sys.path.insert(0, str(REPO_ROOT))

from software.hardware.calibration import DEFAULT_CALIBRATION, JOINTS, load_calibration  # noqa: E402
from software.kinematics.geometry import DEFAULT_GEOMETRY, load_geometry  # noqa: E402
from software.kinematics.leg import JointAngles, inverse_kinematics  # noqa: E402
from software.servo_test.cli_common import confirm, finite_float, run_cli  # noqa: E402

HELP = "Enter: x y z (mm, leg frame) to move; h: help; q: release and quit"


def solve(segments, target: tuple[float, float, float], leg: str) -> dict[tuple[str, str], float]:
    angles: JointAngles = inverse_kinematics(segments, *target)
    return {(leg, joint): angle for joint, angle in angles.as_dict().items()}


def report(pose: dict[tuple[str, str], float], calibration) -> None:
    for (leg, joint), angle in pose.items():
        line = f"  {joint:5s} joint {angle:8.2f} deg"
        if calibration is not None:
            cal = calibration[leg][joint]
            line += (f"  -> board 0x{cal.board:02x} CH{cal.channel} "
                     f"command {cal.to_command(angle):7.2f}")
        print(line)


def interactive(motion, segments, leg: str) -> None:
    print(HELP)
    while True:
        try:
            tokens = input(f"{leg} foot > ").split()
        except EOFError:
            return
        if not tokens:
            continue
        if tokens == ["q"]:
            return
        if tokens == ["h"]:
            print(HELP)
            continue
        try:
            if len(tokens) != 3:
                raise ValueError("Expected three numbers: x y z")
            target = tuple(finite_float(t) for t in tokens)
            pose = solve(segments, target, leg)
            motion.commands_for(pose)  # limit check before printing as accepted
            report(pose, motion.calibration)
            steps = motion.move_to(pose)
            print(f"Moved in {steps} steps")
        except (ValueError, argparse.ArgumentTypeError) as exc:
            print(f"Rejected: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for axis in ("x", "y", "z"):
        parser.add_argument(axis, type=finite_float, help=f"{axis.upper()} in mm, leg frame")
    parser.add_argument("--leg", default="test_leg")
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--execute", action="store_true", help="Actually move the servos")
    parser.add_argument("--speed", type=finite_float, default=30.0,
                        help="Max joint speed in deg/s for interactive moves (default 30)")
    parser.add_argument("-y", "--yes", action="store_true")
    args = parser.parse_args()
    if not 0 < args.speed <= 180:
        parser.error("--speed must be in (0, 180] deg/s")
    segments = load_geometry(args.geometry).segments
    pose = solve(segments, (args.x, args.y, args.z), args.leg)

    calibration = None
    try:
        calibration = load_calibration(args.calibration)
        if args.leg not in calibration:
            raise ValueError(f"Leg {args.leg!r} not in {args.calibration}")
    except (OSError, ValueError) as exc:
        if args.execute:
            raise
        print(f"Calibration unavailable ({exc}); showing joint angles only.")
        calibration = None
    print(f"IK for {args.leg} foot at ({args.x:g}, {args.y:g}, {args.z:g}) mm:")
    report(pose, calibration)
    if not args.execute:
        print("Dry run: no servo was moved. Add --execute to move.")
        return 0

    from software.hardware.motion import JointMotion
    from software.hardware.pca9685_bank import PCA9685Bank

    boards = tuple(sorted({calibration[args.leg][j].board for j in JOINTS}))
    print("Start pose is sent joint by joint WITHOUT speed limiting (start position unknown).")
    confirm(args.yes)
    with PCA9685Bank(boards) as bank:
        motion = JointMotion(bank, {args.leg: calibration[args.leg]},
                             max_speed_deg_s=args.speed)
        motion.initialize(pose)
        interactive(motion, segments, args.leg)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
