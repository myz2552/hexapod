"""Manually collect measured servo calibration; never search for endpoints."""

import argparse
import copy
from pathlib import Path
import tempfile
from typing import Any

if __package__:
    from .cli_common import add_address, confirm, finite_float, run_cli
    from .pca9685_controller import JOINT_CHANNELS, ServoRig, ServoSettings, validate_angle
else:
    from cli_common import add_address, confirm, finite_float, run_cli
    from pca9685_controller import JOINT_CHANNELS, ServoRig, ServoSettings, validate_angle

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "config" / "servo_calibration.yaml"
FIELDS = ("min_deg", "neutral_deg", "max_deg", "direction")
HELP = """+ / -: move one step; g 95: goto command angle
l / n / u: mark current angle as minimum / neutral / maximum
d 1 / d -1: mark direction; p: show marks; s: save; h: help; q: release and quit
Never seek a stop by stalling or buzzing. Cut servo power if binding occurs."""


def load_document(path: Path) -> dict[str, Any]:
    """Read existing calibration or the null-valued example without guessing."""
    import yaml

    source = path if path.exists() else REPO_ROOT / "config" / "servo_calibration.example.yaml"
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("leg") != "test_leg":
        raise ValueError("Calibration must be a mapping with leg: test_leg")
    if data.get("channels") != JOINT_CHANNELS:
        raise ValueError("Calibration channels must be coxa: 0, femur: 1, tibia: 2")
    servos = data.get("servos")
    if not isinstance(servos, dict):
        raise ValueError("Calibration requires a servos mapping")
    for joint in JOINT_CHANNELS:
        if not isinstance(servos.get(joint), dict) or not all(k in servos[joint] for k in FIELDS):
            raise ValueError(f"Missing calibration fields for {joint}")
    return data


def save_calibration(path: Path, joint: str, marks: dict[str, Any],
                     settings: ServoSettings) -> None:
    """Validate and atomically replace YAML, preserving all other joint data."""
    import yaml

    if joint not in JOINT_CHANNELS:
        raise ValueError("Unknown joint")
    for field in FIELDS:
        if marks.get(field) is None:
            raise ValueError(f"Mark {field} before saving")
    for field in FIELDS[:3]:
        value = marks[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be numeric")
        validate_angle(value, settings)
    if type(marks["direction"]) is not int or marks["direction"] not in (-1, 1):
        raise ValueError("Direction must be +1 or -1")
    if not marks["min_deg"] <= marks["neutral_deg"] <= marks["max_deg"]:
        raise ValueError("Require min_deg <= neutral_deg <= max_deg")
    data = copy.deepcopy(load_document(path))
    data["servos"][joint].update({field: marks[field] for field in FIELDS})
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


def interact(rig: ServoRig, args: argparse.Namespace, settings: ServoSettings) -> None:
    """Collect marks from this session; only explicit s writes a file."""
    marks: dict[str, Any] = dict.fromkeys(FIELDS)
    angle = args.start
    channel = JOINT_CHANNELS[args.joint]
    rig.set_angle(channel, angle)
    print(HELP)
    while True:
        try:
            tokens = input(f"{args.joint} {angle:g} deg > ").split()
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
            elif command in ("l", "n", "u") and len(tokens) == 1:
                marks[{"l": "min_deg", "n": "neutral_deg", "u": "max_deg"}[command]] = angle
            elif command == "d" and len(tokens) == 2 and tokens[1] in ("1", "+1", "-1"):
                marks["direction"] = int(tokens[1])
            elif command == "p" and len(tokens) == 1:
                print(marks)
            elif command == "s" and len(tokens) == 1:
                save_calibration(args.output, args.joint, marks, settings)
                print(f"Saved {args.joint} to {args.output}")
            elif command == "h" and len(tokens) == 1:
                print(HELP)
            else:
                print("Unknown command; h for help")
        except ValueError as exc:
            print(f"Rejected: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("joint", choices=JOINT_CHANNELS)
    parser.add_argument("--start", type=finite_float, default=90.0)
    parser.add_argument("--step", type=finite_float, default=2.0)
    parser.add_argument("--lower", type=finite_float, default=60.0)
    parser.add_argument("--upper", type=finite_float, default=120.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    add_address(parser)
    args = parser.parse_args()
    try:
        settings = ServoSettings(min_deg=args.lower, max_deg=args.upper)
        if args.lower >= args.upper or args.step <= 0 or args.step > args.upper - args.lower:
            raise ValueError("Require lower < upper and 0 < step <= upper - lower")
        validate_angle(args.start, settings)
    except ValueError as exc:
        parser.error(str(exc))
    if args.output.resolve() == (REPO_ROOT / "config" / "servo_calibration.example.yaml").resolve():
        parser.error("Do not overwrite the null-valued calibration example")
    load_document(args.output)  # Validate existing data before any motion.
    print(f"{args.joint}: CH{JOINT_CHANNELS[args.joint]}, start {args.start:g} deg; "
          f"command bounds {args.lower:g}..{args.upper:g}; step {args.step:g}")
    confirm()
    with ServoRig(address=args.address, settings=settings) as rig:
        interact(rig, args, settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
