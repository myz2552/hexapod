"""move_foot CLI checks without hardware; calibration values are synthetic."""

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from software.hardware import JointMotion, RecordingOutput, parse_calibration
from software.hardware.tests.test_hardware import document
from software.kinematics import load_geometry
from software.single_leg import move_foot

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "software" / "single_leg" / "move_foot.py"


def run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True)


class MoveFootTests(unittest.TestCase):
    def test_help_both_styles(self) -> None:
        for invocation in ([str(SCRIPT)], ["-m", "software.single_leg.move_foot"]):
            result = run(*invocation, "--help", cwd=Path(tempfile.gettempdir())
                         if invocation[0] == str(SCRIPT) else ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_dry_run_without_calibration_never_needs_hardware(self) -> None:
        result = run(str(SCRIPT), "144.7", "0", "-100", "--calibration", "/nonexistent.yaml")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dry run", result.stdout)
        self.assertRegex(result.stdout, r"femur joint\s+0\.00 deg")

    def test_dry_run_with_calibration_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cal.yaml"
            path.write_text(yaml.safe_dump(document()), encoding="utf-8")
            ok = run(str(SCRIPT), "144.7", "0", "-100", "--calibration", str(path))
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertIn("board 0x40 CH1 command   90.00", ok.stdout)
            for target in (("500", "0", "0"), ("50", "137", "-100")):  # unreachable / coxa 70 deg
                bad = run(str(SCRIPT), *target, "--calibration", str(path))
                self.assertEqual(bad.returncode, 1, bad.stdout)
            missing = run(str(SCRIPT), "144.7", "0", "-100", "--execute", "-y",
                          "--calibration", "/nonexistent.yaml")
            self.assertEqual(missing.returncode, 1)
            self.assertEqual(run(str(SCRIPT), "1", "2", "3", "--speed", "0").returncode, 2)

    def test_interactive_moves_and_rejects(self) -> None:
        out = RecordingOutput((0x40,))
        motion = JointMotion(out, parse_calibration(document()), max_speed_deg_s=30,
                             sleep=lambda _: None)
        segments = load_geometry().segments
        motion.initialize(move_foot.solve(segments, (144.7, 0, -100), "test_leg"))
        before = len(out.writes)
        text = io.StringIO()
        with patch("builtins.input", side_effect=["140 10 -90", "500 0 0", "1 2", "x y z",
                                                  "q"]):
            with contextlib.redirect_stdout(text):
                move_foot.interactive(motion, segments, "test_leg")
        self.assertGreater(len(out.writes), before)
        self.assertEqual(text.getvalue().count("Rejected"), 3)
        foot = load_geometry().segments
        angles = motion.current
        from software.kinematics import JointAngles, forward_kinematics
        reached = forward_kinematics(foot, JointAngles(*(angles[("test_leg", j)]
                                                         for j in ("coxa", "femur", "tibia"))))
        for a, e in zip(reached, (140, 10, -90)):
            self.assertAlmostEqual(a, e, places=6)


if __name__ == "__main__":
    unittest.main()
