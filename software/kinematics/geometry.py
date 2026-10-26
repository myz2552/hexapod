"""Robot geometry loading and body <-> leg frame transforms (mm, degrees)."""

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

from .leg import JointAngles, LegSegments, forward_kinematics, inverse_kinematics

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GEOMETRY = REPO_ROOT / "config" / "robot_geometry.yaml"
LEG_NAMES = ("front_left", "middle_left", "rear_left",
             "rear_right", "middle_right", "front_right")


@dataclass(frozen=True)
class LegMount:
    x_mm: float
    y_mm: float
    heading_deg: float


@dataclass(frozen=True)
class RobotGeometry:
    segments: LegSegments
    mount_z_mm: float
    legs: dict[str, LegMount]

    def body_to_leg(self, leg: str, point: tuple[float, float, float]) -> tuple[float, float, float]:
        """Convert a body-frame point to the given leg's frame."""
        mount = self.legs[leg]
        dx, dy = point[0] - mount.x_mm, point[1] - mount.y_mm
        h = math.radians(mount.heading_deg)
        return (dx * math.cos(h) + dy * math.sin(h),
                -dx * math.sin(h) + dy * math.cos(h),
                point[2] - self.mount_z_mm)

    def leg_to_body(self, leg: str, point: tuple[float, float, float]) -> tuple[float, float, float]:
        """Convert a leg-frame point to the body frame."""
        mount = self.legs[leg]
        h = math.radians(mount.heading_deg)
        return (mount.x_mm + point[0] * math.cos(h) - point[1] * math.sin(h),
                mount.y_mm + point[0] * math.sin(h) + point[1] * math.cos(h),
                point[2] + self.mount_z_mm)

    def foot_ik(self, leg: str, body_point: tuple[float, float, float]) -> JointAngles:
        return inverse_kinematics(self.segments, *self.body_to_leg(leg, body_point))

    def foot_fk(self, leg: str, angles: JointAngles) -> tuple[float, float, float]:
        return self.leg_to_body(leg, forward_kinematics(self.segments, angles))


def _number(data: dict[str, Any], key: str, where: str) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{where}.{key} must be a finite number")
    return float(value)


def parse_geometry(data: Any) -> RobotGeometry:
    if not isinstance(data, dict):
        raise ValueError("Geometry must be a mapping")
    seg = data.get("segments")
    legs = data.get("legs")
    if not isinstance(seg, dict) or not isinstance(legs, dict):
        raise ValueError("Geometry requires segments and legs mappings")
    segments = LegSegments(*(_number(seg, k, "segments")
                             for k in ("coxa_mm", "femur_mm", "tibia_mm")))
    if set(legs) != set(LEG_NAMES):
        raise ValueError(f"Geometry legs must be exactly {', '.join(LEG_NAMES)}")
    mounts = {}
    for name in LEG_NAMES:
        entry = legs[name]
        if not isinstance(entry, dict):
            raise ValueError(f"legs.{name} must be a mapping")
        mounts[name] = LegMount(*(_number(entry, k, f"legs.{name}")
                                  for k in ("x_mm", "y_mm", "heading_deg")))
    return RobotGeometry(segments, _number(data, "mount_z_mm", "geometry"), mounts)


def load_geometry(path: Path = DEFAULT_GEOMETRY) -> RobotGeometry:
    import yaml

    return parse_geometry(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
