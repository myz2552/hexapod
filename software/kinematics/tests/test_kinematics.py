"""Pure-math kinematics checks; no hardware or calibration involved."""

import itertools
import math
import unittest

from software.kinematics import (LEG_NAMES, JointAngles, LegSegments, UnreachableError,
                                 forward_kinematics, inverse_kinematics, load_geometry,
                                 parse_geometry)

SEG = LegSegments(68.0, 76.7, 100.0)


class LegKinematicsTests(unittest.TestCase):
    def assertPoint(self, actual, expected, places=6) -> None:
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, places=places)

    def test_zero_pose_matches_convention(self) -> None:
        # Femur horizontal, tibia straight down, coxa along heading.
        self.assertPoint(forward_kinematics(SEG, JointAngles(0, 0, 0)), (144.7, 0.0, -100.0))
        # Coxa +90 deg is counter-clockwise from above: foot goes to +y.
        self.assertPoint(forward_kinematics(SEG, JointAngles(90, 0, 0)), (0.0, 144.7, -100.0))
        # Femur +90 deg lifts the femur end; tibia then points outward.
        self.assertPoint(forward_kinematics(SEG, JointAngles(0, 90, 0)), (168.0, 0.0, 76.7))
        # Tibia +90 deg swings the foot outward to femur extension.
        self.assertPoint(forward_kinematics(SEG, JointAngles(0, 0, 90)), (244.7, 0.0, 0.0))

    def test_ik_inverts_fk_over_workspace(self) -> None:
        for coxa, femur, tibia in itertools.product(range(-60, 61, 20), range(-50, 61, 10),
                                                     range(-60, 51, 10)):
            angles = JointAngles(coxa, femur, tibia)
            foot = forward_kinematics(SEG, angles)
            if math.hypot(foot[0], foot[1]) < 1.0:
                continue
            solved = inverse_kinematics(SEG, *foot)
            self.assertPoint(forward_kinematics(SEG, solved), foot, places=6)
            self.assertAlmostEqual(solved.coxa_deg, coxa, places=6)
            # -90 < tibia < 90 is the knee-up branch, which IK always returns.
            self.assertAlmostEqual(solved.femur_deg, femur, places=6)
            self.assertAlmostEqual(solved.tibia_deg, tibia, places=6)

    def test_ik_known_stance(self) -> None:
        solved = inverse_kinematics(SEG, 144.7, 0.0, -100.0)
        self.assertPoint((solved.coxa_deg, solved.femur_deg, solved.tibia_deg), (0, 0, 0))

    def test_ik_rejects_unreachable_and_invalid(self) -> None:
        for target in ((500.0, 0.0, 0.0), (68.0, 0.0, -10.0), (0.0, 0.0, -100.0)):
            with self.assertRaises(UnreachableError):
                inverse_kinematics(SEG, *target)
        with self.assertRaises(ValueError):
            inverse_kinematics(SEG, float("nan"), 0.0, 0.0)
        for bad in ((0, 76.7, 100), (68, -1, 100), (68, 76.7, float("inf")), (68, True, 100)):
            with self.assertRaises(ValueError):
                LegSegments(*bad)


class GeometryTests(unittest.TestCase):
    def test_repo_geometry_loads_and_is_symmetric(self) -> None:
        geometry = load_geometry()
        self.assertEqual(geometry.segments, SEG)
        self.assertEqual(set(geometry.legs), set(LEG_NAMES))
        for left, right in (("front_left", "front_right"), ("middle_left", "middle_right"),
                            ("rear_left", "rear_right")):
            a, b = geometry.legs[left], geometry.legs[right]
            self.assertEqual((a.x_mm, a.y_mm, a.heading_deg), (b.x_mm, -b.y_mm, -b.heading_deg))

    def test_body_leg_round_trip_and_ik(self) -> None:
        geometry = load_geometry()
        for leg in LEG_NAMES:
            point = (12.5, -40.0, -90.0)
            back = geometry.leg_to_body(leg, geometry.body_to_leg(leg, point))
            for a, e in zip(back, point):
                self.assertAlmostEqual(a, e, places=9)
            foot = geometry.foot_fk(leg, JointAngles(10, 5, -15))
            solved = geometry.foot_ik(leg, foot)
            for a, e in zip(geometry.foot_fk(leg, solved), foot):
                self.assertAlmostEqual(a, e, places=6)
        # Zero pose puts the middle-left foot straight out along +y.
        foot = geometry.foot_fk("middle_left", JointAngles(0, 0, 0))
        for a, e in zip(foot, (0.0, 70.7 + 144.7, 8.7 - 100.0)):
            self.assertAlmostEqual(a, e, places=9)

    def test_parse_rejects_bad_documents(self) -> None:
        good = {"segments": {"coxa_mm": 68, "femur_mm": 76.7, "tibia_mm": 100},
                "mount_z_mm": 8.7,
                "legs": {n: {"x_mm": 0, "y_mm": 0, "heading_deg": 0} for n in LEG_NAMES}}
        parse_geometry(good)
        broken = [None, {"segments": good["segments"]},
                  {**good, "legs": {"front_left": good["legs"]["front_left"]}},
                  {**good, "mount_z_mm": None},
                  {**good, "segments": {**good["segments"], "tibia_mm": "100"}}]
        for document in broken:
            with self.assertRaises(ValueError):
                parse_geometry(document)


if __name__ == "__main__":
    unittest.main()
