"""Hardware-independent safety, CLI and calibration regression checks."""

import contextlib
import copy
import importlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml

from software.servo_test import calibrate_servo as calibration
from software.servo_test import pca9685_controller as controller


class FakeBus:
    def __init__(self) -> None:
        self.unlocked = False
        self.closed = False

    def try_lock(self) -> bool:
        return True

    def scan(self) -> list[int]:
        return [0x40]

    def unlock(self) -> None:
        self.unlocked = True

    def deinit(self) -> None:
        self.closed = True


class FakePCA:
    def __init__(self, bus: FakeBus, address: int) -> None:
        self.channels = [SimpleNamespace(duty_cycle=123) for _ in range(16)]
        self.closed = False

    def deinit(self) -> None:
        self.closed = True


class FakeServo:
    def __init__(self, pwm: object, **kwargs: object) -> None:
        self.angle = None


class BringupTests(unittest.TestCase):
    def test_lazy_servo_and_cleanup_on_interrupt_and_exception(self) -> None:
        for failure in (KeyboardInterrupt, RuntimeError):
            bus = FakeBus()
            modules = {
                "board": SimpleNamespace(I2C=lambda: bus),
                "adafruit_pca9685": SimpleNamespace(PCA9685=FakePCA),
                "adafruit_motor": SimpleNamespace(),
                "adafruit_motor.servo": SimpleNamespace(Servo=FakeServo),
            }
            with patch.dict(sys.modules, modules):
                with self.assertRaises(failure):
                    with controller.ServoRig() as rig:
                        pca = rig._pca
                        self.assertFalse(rig._servos)
                        for channel, angle in ((-1, 90), (16, 90), (0, 59),
                                               (0, 121), (0, float("nan"))):
                            with self.assertRaises(ValueError):
                                rig.set_angle(channel, angle)
                        rig.set_angle(0, 90)
                        self.assertEqual(rig._servos[0].angle, 90)
                        raise failure()
                self.assertTrue(pca.closed)
                self.assertTrue(bus.closed)
                self.assertTrue(all(c.duty_cycle == 0 for c in pca.channels))
                rig.close()

    def test_scan_unlocks_and_closes_on_failure(self) -> None:
        bus = FakeBus()
        with patch.dict(sys.modules, {"board": SimpleNamespace(I2C=lambda: bus)}):
            self.assertEqual(controller.scan_i2c_addresses(), [0x40])
            self.assertTrue(bus.unlocked and bus.closed)
            with patch.object(bus, "scan", side_effect=OSError("bus error")):
                with self.assertRaises(OSError):
                    controller.scan_i2c_addresses()
                self.assertTrue(bus.unlocked and bus.closed)

    def test_release_continues_after_channel_failure(self) -> None:
        rig = controller.ServoRig.__new__(controller.ServoRig)
        rig._pca = object()
        visited = []

        def release(channel: int) -> None:
            visited.append(channel)
            if channel == 0:
                raise OSError("failed write")

        rig.release = release
        with self.assertRaises(OSError):
            rig.release_all()
        self.assertEqual(visited, list(range(16)))

    def test_yaml_preserves_other_joints_and_rejects_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calibration.yaml"
            original = calibration.load_document(path)
            original["legs"]["test_leg"]["femur"]["note"] = "preserve me"
            path.write_text(yaml.safe_dump(original), encoding="utf-8")
            before = path.read_bytes()
            # Synthetic fixtures only; these are NOT physical calibration values.
            good = dict(zero_cmd_deg=89, ref_cmd_deg=110, min_cmd_deg=61, max_cmd_deg=119)
            invalid = [(dict.fromkeys(calibration.MARKS.values()), 45.0),
                       (good, None),
                       (dict(good, min_cmd_deg=100), 45.0),
                       (dict(good, ref_cmd_deg=91), 45.0),
                       (dict(good, ref_cmd_deg=130), 45.0),
                       (dict(good, zero_cmd_deg=float("nan")), 45.0)]
            for marks, ref_deg in invalid:
                with self.assertRaises(ValueError):
                    calibration.save_calibration(path, "test_leg", "coxa", marks, ref_deg)
                self.assertEqual(path.read_bytes(), before)
            with self.assertRaises(ValueError):
                calibration.save_calibration(path, "front_left", "coxa", good, 45.0)
            saved = calibration.save_calibration(path, "test_leg", "coxa", good, 45.0)
            self.assertEqual(saved.direction, 1)
            updated = calibration.load_document(path)
            expected = copy.deepcopy(original)
            expected["legs"]["test_leg"]["coxa"].update(good, ref_joint_deg=45.0)
            self.assertEqual(updated, expected)

    def test_old_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calibration.yaml"
            path.write_text(yaml.safe_dump({"leg": "test_leg", "channels": {}, "servos": {}}),
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "v1"):
                calibration.load_document(path)

    def test_interactive_bounds_marks_and_channel_from_file(self) -> None:
        rig = SimpleNamespace(set_angle=unittest.mock.Mock())
        document = calibration.load_document(Path("/nonexistent/calibration.yaml"))
        args = SimpleNamespace(start=90, leg="test_leg", joint="femur", step=2, ref_deg=45.0,
                               output=Path("/nonexistent/calibration.yaml"))
        out = io.StringIO()
        with patch("builtins.input", side_effect=["g 121", "g nan", "g 59", "+", "z", "-",
                                                  "-", "-", "r", "p", "s", "q"]):
            with contextlib.redirect_stdout(out):
                calibration.interact(rig, args, controller.ServoSettings(), document)
        self.assertEqual([c.args for c in rig.set_angle.call_args_list],
                         [(1, 90), (1, 92), (1, 90), (1, 88), (1, 86)])
        self.assertIn("direction=-1", out.getvalue())
        self.assertIn("Rejected: Mark min_cmd_deg, max_cmd_deg", out.getvalue())

    def test_check_never_sends_angle(self) -> None:
        module = importlib.import_module("software.servo_test.check_pca9685")
        rig = unittest.mock.MagicMock()
        with patch.object(module, "scan_i2c_addresses", return_value=[0x40]), \
                patch.object(module, "ServoRig", return_value=rig), \
                patch.object(sys, "argv", ["check"]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(module.main(), 0)
        rig.__enter__.return_value.set_angle.assert_not_called()

    def test_cli_help_both_entry_styles_and_invalid_arguments(self) -> None:
        root = calibration.REPO_ROOT
        names = ("check_pca9685", "test_single_servo", "test_three_servos", "calibrate_servo")
        for name in names:
            for invocation in ([str(root / "software" / "servo_test" / f"{name}.py")],
                               ["-m", f"software.servo_test.{name}"]):
                result = subprocess.run([sys.executable, *invocation, "--help"],
                                        cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
        for name, arguments in (
            ("test_single_servo", ["--angle", "nan"]),
            ("test_single_servo", ["--channel", "16", "-y"]),
            ("test_single_servo", ["--angle", "180", "-y"]),
            ("test_three_servos", ["--angles", "90", "121", "90", "-y"]),
            ("test_three_servos", ["--hold", "-1"]),
            ("calibrate_servo", ["coxa", "--step", "0"]),
            ("calibrate_servo", ["coxa", "--start", "121"]),
            ("calibrate_servo", ["coxa", "--ref-deg", "0"]),
        ):
            result = subprocess.run([sys.executable, "-m", f"software.servo_test.{name}", *arguments],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)


if __name__ == "__main__":
    unittest.main()
