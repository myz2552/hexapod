"""Calibration mapping, multi-board output and motion checks without hardware.

All calibration numbers here are synthetic fixtures, NOT physical values.
"""

import copy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from software.hardware import (JointCalibration, JointLimitError, JointMotion, MotionError,
                               PCA9685Bank, RecordingOutput, parse_calibration)
from software.hardware.calibration import EXAMPLE_CALIBRATION, read_document

FIXTURE = dict(board=0x40, channel=1, zero_cmd_deg=90.0, ref_cmd_deg=45.0,
               ref_joint_deg=45.0, min_cmd_deg=30.0, max_cmd_deg=150.0)


def document() -> dict:
    data = copy.deepcopy(read_document(EXAMPLE_CALIBRATION))
    for channel, joint in enumerate(("coxa", "femur", "tibia")):
        data["legs"]["test_leg"][joint].update(
            FIXTURE, channel=channel, ref_cmd_deg=135.0 if joint == "coxa" else 45.0)
    return data


class CalibrationTests(unittest.TestCase):
    def test_direction_scale_and_limits(self) -> None:
        cal = JointCalibration(**FIXTURE)
        self.assertEqual(cal.direction, -1)
        self.assertAlmostEqual(cal.scale, -1.0)
        self.assertEqual(cal.to_command(0), 90.0)
        self.assertEqual(cal.to_command(30), 60.0)
        self.assertEqual(cal.joint_limits_deg, (-60.0, 60.0))
        self.assertAlmostEqual(cal.to_joint(cal.to_command(12.5)), 12.5)
        for angle in (60.0001, -61, float("nan")):
            with self.assertRaises(ValueError):
                cal.to_command(angle)
        with self.assertRaises(JointLimitError):
            cal.to_command(70)
        # Non-unit scale: 30 cmd deg for a 45 deg reference pose.
        wide = JointCalibration(**dict(FIXTURE, ref_cmd_deg=120.0))
        self.assertAlmostEqual(wide.to_command(45), 120.0)
        self.assertEqual(wide.direction, 1)

    def test_invalid_calibrations_are_rejected(self) -> None:
        for change in (dict(board=0x80), dict(channel=16), dict(channel=True),
                       dict(min_cmd_deg=-1), dict(max_cmd_deg=181), dict(zero_cmd_deg=20),
                       dict(ref_cmd_deg=160), dict(ref_joint_deg=0), dict(ref_cmd_deg=93),
                       dict(zero_cmd_deg=float("inf"))):
            with self.assertRaises(ValueError, msg=str(change)):
                JointCalibration(**dict(FIXTURE, **change))

    def test_example_is_null_and_not_usable(self) -> None:
        with self.assertRaisesRegex(ValueError, "not calibrated"):
            parse_calibration(read_document(EXAMPLE_CALIBRATION))

    def test_document_validation(self) -> None:
        parsed = parse_calibration(document())
        self.assertEqual(parsed["test_leg"]["tibia"].channel, 2)
        duplicate = document()
        duplicate["legs"]["test_leg"]["tibia"]["channel"] = 0
        missing = document()
        del missing["legs"]["test_leg"]["femur"]["max_cmd_deg"]
        for broken in (duplicate, missing, {"schema_version": 1, "legs": {}},
                       {"leg": "test_leg", "servos": {}}, dict(document(), legs={})):
            with self.assertRaises(ValueError):
                parse_calibration(broken)


class OutputTests(unittest.TestCase):
    def test_recording_output_validates(self) -> None:
        out = RecordingOutput((0x40,))
        out.write(0x40, 3, 90)
        self.assertEqual(out.writes, [(0x40, 3, 90.0)])
        for args in ((0x41, 0, 90), (0x40, 16, 90), (0x40, 0, 181), (0x40, 0, float("nan"))):
            with self.assertRaises(ValueError):
                out.write(*args)

    def test_bank_shares_bus_and_releases_everything(self) -> None:
        bus = SimpleNamespace(closed=False)
        bus.deinit = lambda: setattr(bus, "closed", True)
        created = []

        class FakePCA:
            def __init__(self, i2c, address):
                self.bus, self.address, self.closed = i2c, address, False
                self.channels = [SimpleNamespace(duty_cycle=123) for _ in range(16)]
                created.append(self)

            def deinit(self):
                self.closed = True

        class FakeServo:
            def __init__(self, pwm, **kwargs):
                self.pwm, self.kwargs, self.angle = pwm, kwargs, None

        modules = {"board": SimpleNamespace(I2C=lambda: bus),
                   "adafruit_pca9685": SimpleNamespace(PCA9685=FakePCA),
                   "adafruit_motor": SimpleNamespace(),
                   "adafruit_motor.servo": SimpleNamespace(Servo=FakeServo)}
        with patch.dict(sys.modules, modules):
            with self.assertRaises(RuntimeError):
                with PCA9685Bank((0x40, 0x41)) as bank:
                    self.assertEqual([p.bus for p in created], [bus, bus])
                    self.assertTrue(all(c.duty_cycle == 0 for p in created for c in p.channels))
                    bank.write(0x41, 5, 100)
                    servo = bank._servos[(0x41, 5)]
                    self.assertEqual(servo.angle, 100)
                    self.assertEqual((servo.kwargs["min_pulse"], servo.kwargs["max_pulse"]),
                                     (750, 2250))
                    with self.assertRaises(ValueError):
                        bank.write(0x42, 0, 90)
                    raise RuntimeError("simulated failure")
        self.assertTrue(bus.closed and all(p.closed for p in created))
        self.assertTrue(all(c.duty_cycle == 0 for p in created for c in p.channels))
        for boards in ((), (0x40, 0x40), (0x07,)):
            with self.assertRaises(ValueError):
                PCA9685Bank(boards)


class MotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.out = RecordingOutput((0x40,))
        self.sleeps: list[float] = []
        self.motion = JointMotion(self.out, parse_calibration(document()),
                                  max_speed_deg_s=50, rate_hz=50, sleep=self.sleeps.append)
        self.zero = {("test_leg", j): 0.0 for j in ("coxa", "femur", "tibia")}

    def test_requires_initialize_and_rejects_before_moving(self) -> None:
        with self.assertRaises(MotionError):
            self.motion.move_to(self.zero)
        with self.assertRaises(JointLimitError):
            self.motion.initialize({**self.zero, ("test_leg", "femur"): 90.0})
        self.assertEqual(self.out.writes, [])
        self.motion.initialize(self.zero, joint_delay_s=0.25)
        self.assertEqual(self.out.writes, [(0x40, 0, 90.0), (0x40, 1, 90.0), (0x40, 2, 90.0)])
        self.assertEqual(self.sleeps, [0.25, 0.25])
        written = len(self.out.writes)
        with self.assertRaises(JointLimitError):
            self.motion.move_to({("test_leg", "tibia"): -61.0})
        with self.assertRaises(MotionError):
            self.motion.move_to({("front_left", "coxa"): 0.0})
        self.assertEqual(len(self.out.writes), written)

    def test_speed_limit_and_interpolation(self) -> None:
        self.motion.initialize(self.zero, joint_delay_s=0)
        self.out.writes.clear()
        self.sleeps.clear()
        # 50 deg/s at 50 Hz = 1 deg per step; 10 deg move -> 10 steps.
        steps = self.motion.move_to({("test_leg", "coxa"): 10.0, ("test_leg", "femur"): -5.0})
        self.assertEqual(steps, 10)
        self.assertEqual(self.sleeps, [0.02] * 9)
        coxa = [c for b, ch, c in self.out.writes if ch == 0]
        femur = [c for b, ch, c in self.out.writes if ch == 1]
        self.assertAlmostEqual(coxa[-1], 100.0)  # coxa scale +1
        self.assertAlmostEqual(femur[-1], 95.0)  # femur scale -1
        self.assertTrue(all(abs(b - a) <= 1.0 + 1e-9 for a, b in zip([90.0] + coxa, coxa)))
        self.assertEqual(self.motion.current[("test_leg", "tibia")], 0.0)
        self.assertEqual(self.motion.move_to({("test_leg", "coxa"): 10.0}), 1)
        self.motion.release()
        self.assertIsNone(self.motion.current)
        self.assertEqual(self.out.releases, 1)

    def test_rejects_bad_parameters(self) -> None:
        for kwargs in (dict(max_speed_deg_s=0), dict(rate_hz=0), dict(rate_hz=1000),
                       dict(max_speed_deg_s=float("nan"))):
            with self.assertRaises(ValueError):
                JointMotion(self.out, {}, **kwargs)


if __name__ == "__main__":
    unittest.main()
