"""Three-joint leg forward/inverse kinematics in the leg frame (mm, degrees).

Leg frame: origin on the coxa axis at femur-axis height, +x points outward along
the leg heading when coxa = 0, +z up. Joint convention (see README):

* coxa:  0 = leg along its heading; positive = counter-clockwise seen from above.
* femur: 0 = femur horizontal; positive = femur end goes up.
* tibia: 0 = foot tip directly below the tibia axis while the femur is
  horizontal (tibia perpendicular to femur); positive = rotation in the same
  sense as femur, so the foot swings outward/up.

These are kinematic joint angles, not servo command angles; the calibration
layer converts between the two.
"""

from dataclasses import dataclass
import math


class UnreachableError(ValueError):
    """Raised when a foot target cannot be reached by the leg geometry."""


@dataclass(frozen=True)
class LegSegments:
    coxa_mm: float
    femur_mm: float
    tibia_mm: float

    def __post_init__(self) -> None:
        for name in ("coxa_mm", "femur_mm", "tibia_mm"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")


@dataclass(frozen=True)
class JointAngles:
    coxa_deg: float
    femur_deg: float
    tibia_deg: float

    def as_dict(self) -> dict[str, float]:
        return {"coxa": self.coxa_deg, "femur": self.femur_deg, "tibia": self.tibia_deg}


def forward_kinematics(seg: LegSegments, angles: JointAngles) -> tuple[float, float, float]:
    """Return the foot tip (x, y, z) in the leg frame."""
    t1 = math.radians(angles.coxa_deg)
    t2 = math.radians(angles.femur_deg)
    t23 = math.radians(angles.femur_deg + angles.tibia_deg)
    radial = seg.coxa_mm + seg.femur_mm * math.cos(t2) + seg.tibia_mm * math.sin(t23)
    z = seg.femur_mm * math.sin(t2) - seg.tibia_mm * math.cos(t23)
    return radial * math.cos(t1), radial * math.sin(t1), z


def inverse_kinematics(seg: LegSegments, x: float, y: float, z: float,
                       min_horizontal_mm: float = 1.0) -> JointAngles:
    """Solve the knee-up solution for a foot target in the leg frame.

    Joint limits are not checked here; the calibration layer owns them.
    """
    if not all(math.isfinite(v) for v in (x, y, z)):
        raise ValueError("Foot target must be finite")
    horizontal = math.hypot(x, y)
    if horizontal < min_horizontal_mm:
        raise UnreachableError("Foot target is on the coxa axis; coxa angle undefined")
    coxa = math.atan2(y, x)
    radial = horizontal - seg.coxa_mm
    reach = math.hypot(radial, z)
    l2, l3 = seg.femur_mm, seg.tibia_mm
    if reach > l2 + l3 or reach < abs(l2 - l3) or reach == 0:
        raise UnreachableError(
            f"Femur-to-foot distance {reach:.1f} mm outside {abs(l2 - l3):.1f}..{l2 + l3:.1f} mm")
    cos_beta = (l2 * l2 + reach * reach - l3 * l3) / (2 * l2 * reach)
    femur = math.atan2(z, radial) + math.acos(max(-1.0, min(1.0, cos_beta)))
    knee_r = radial - l2 * math.cos(femur)
    knee_z = z - l2 * math.sin(femur)
    tibia_abs = math.atan2(knee_z, knee_r)  # tibia direction from horizontal
    tibia = tibia_abs - femur + math.pi / 2
    tibia = math.atan2(math.sin(tibia), math.cos(tibia))  # wrap to (-pi, pi]
    return JointAngles(math.degrees(coxa), math.degrees(femur), math.degrees(tibia))
