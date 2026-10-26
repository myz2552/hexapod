"""Manually collect measured servo calibration (schema v2); never search for endpoints."""

import argparse
import copy
from pathlib import Path
import sys
import tempfile
from typing import Any

if __package__:
    from .cli_common import confirm, finite_float, run_cli
    from .pca9685_controller import ServoRig, ServoSettings, validate_angle
else:
    from cli_common import confirm, finite_float, run_cli
    from pca9685_controller import ServoRig, ServoSettings, validate_angle

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # script-style invocation
    sys.path.insert(0, str(REPO_ROOT))

from software.hardware.calibration import (  # noqa: E402
    DEFAULT_CALIBRATION, EXAMPLE_CALIBRATION, JOINTS, MEASURED_FIELDS, JointCalibration,
    read_document)

DEFAULT_OUTPUT = DEFAULT_CALIBRATION
MARKS = {"z": "zero_cmd_deg", "r": "ref_cmd_deg", "l": "min_cmd_deg", "u": "max_cmd_deg"}
HELP = """+ / -: move one step; g 95: goto command angle
z: mark current command as kinematic ZERO pose (see software/kinematics/README.md)
r: mark current command as REFERENCE pose (joint at --ref-deg, measured with a jig)
l / u: mark current command as safe lower / upper limit
p: show marks and derived direction/scale; s: save; h: help; q: release and quit
Never seek a stop by stalling or buzzing. Cut servo power if binding occurs."""


def load_document(path: Path) -> dict[str, Any]:
    """Read existing calibration or the null-valued example without guessing."""
    return read_document(path if path.exists() else EXAMPLE_CALIBRATION)


def build_joint(document: dict[str, Any], leg: str, joint: str,
                marks: dict[str, Any], ref_deg: float | None) -> JointCalibration:
    """Validate marks against the document's board/channel; raises ValueError."""
    if leg not in document["legs"]:
        raise ValueError(f"Leg {leg!r} not in calibration file")
    if joint not in JOINTS:
        raise ValueError("Unknown joint")
    values = dict(marks, ref_joint_deg=ref_deg)
    missing = [k for k in MEASURED_FIELDS if values.get(k) is None]
    if missing:
        raise ValueError(f"Mark {', '.join(missing)} before saving")
    entry = document["legs"][leg][joint]
    return JointCalibration(board=entry["board"], channel=entry["channel"],
                            **{k: values[k] for k in MEASURED_FIELDS})


def save_calibration(path: Path, leg: str, joint: str, marks: dict[str, Any],
                     ref_deg: float | None) -> JointCalibration:
    """Validate and atomically replace YAML, preserving all other joint data."""
    import yaml

    data = copy.deepcopy(load_document(path))
    calibration = build_joint(data, leg, joint, marks, ref_deg)
    data["legs"][leg][joint].update({k: getattr(calibration, k) for k in MEASURED_FIELDS})
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            yaml.safe_dump(data, stream, sort_keys=False, allow_unicode=True)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return calibration


def describe(marks: dict[str, Any], ref_deg: float) -> str:
    text = ", ".join(f"{k}={v}" for k, v in marks.items())
    zero, ref = marks.get("zero_cmd_deg"), marks.get("ref_cmd_deg")
    if zero is not None and ref is not None and ref != zero:
        scale = (ref - zero) / ref_deg
        text += f"; direction={'+1' if scale > 0 else '-1'}, scale={scale:.3f} cmd/joint deg"
    return text


def interact(rig: Any, args: argparse.Namespace, settings: ServoSettings,
             document: dict[str, Any]) -> None:
    """Collect marks from this session; only explicit s writes a file."""
    marks: dict[str, Any] = dict.fromkeys(MARKS.values())
    angle = args.start
    channel = document["legs"][args.leg][args.joint]["channel"]
    rig.set_angle(channel, angle)
    print(HELP)
    while True:
        try:
            tokens = input(f"{args.leg}.{args.joint} {angle:g} cmd > ").split()
        except EOFError:
            return
        if not tokens:
            continue
        command = tokens[0]
        try:
            if command == "q" and len(tokens) == 1:
                return
            if command in ("+", "-") and len(tokens) == 1:
                target = angle + (args.step if command == "+" else -args.step)
            elif command == "g" and len(tokens) == 2:
                target = float(tokens[1])
            else:
                target = None
            if target is not None:
                validate_angle(target, settings)
                rig.set_angle(channel, target)
                angle = target
            elif command in MARKS and len(tokens) == 1:
                marks[MARKS[command]] = angle
            elif command == "p" and len(tokens) == 1:
                print(describe(marks, args.ref_deg))
            elif command == "s" and len(tokens) == 1:
                saved = save_calibration(args.output, args.leg, args.joint, marks, args.ref_deg)
                low, high = saved.joint_limits_deg
                print(f"Saved {args.leg}.{args.joint} to {args.output}; direction "
                      f"{saved.direction:+d}, joint range {low:.1f}..{high:.1f} deg")
            elif command == "h" and len(tokens) == 1:
                print(HELP)
            else:
                print("Unknown command; h for help")
        except ValueError as exc:
            print(f"Rejected: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("joint", choices=JOINTS)
    parser.add_argument("--leg", default="test_leg")
    parser.add_argument("--ref-deg", type=finite_float, default=45.0,
                        help="Measured joint angle of the reference pose (default +45)")
    parser.add_argument("--start", type=finite_float, default=90.0)
    parser.add_argument("--step", type=finite_float, default=2.0)
    parser.add_argument("--lower", type=finite_float, default=60.0)
    parser.add_argument("--upper", type=finite_float, default=120.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        settings = ServoSettings(min_deg=args.lower, max_deg=args.upper)
        if args.lower >= args.upper or args.step <= 0 or args.step > args.upper - args.lower:
            raise ValueError("Require lower < upper and 0 < step <= upper - lower")
        if args.ref_deg == 0 or abs(args.ref_deg) > 180:
            raise ValueError("--ref-deg must be non-zero and within +/-180")
        validate_angle(args.start, settings)
    except ValueError as exc:
        parser.error(str(exc))
    if args.output.resolve() == EXAMPLE_CALIBRATION.resolve():
        parser.error("Do not overwrite the null-valued calibration example")
    document = load_document(args.output)  # Validate existing data before any motion.
    if args.leg not in document["legs"]:
        parser.error(f"Leg {args.leg!r} not in {args.output}")
    entry = document["legs"][args.leg][args.joint]
    print(f"{args.leg}.{args.joint}: board 0x{entry['board']:02x} CH{entry['channel']}, "
          f"start {args.start:g}; command bounds {args.lower:g}..{args.upper:g}; "
          f"step {args.step:g}; reference pose {args.ref_deg:+g} joint deg")
    confirm()
    with ServoRig(address=entry["board"], settings=settings) as rig:
        interact(rig, args, settings, document)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
