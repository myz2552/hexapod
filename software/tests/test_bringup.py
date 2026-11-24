"""software/bringup.py akışlarını sahte bir istemciyle test eder (donanım gerekmez)."""
import csv
import tempfile
import unittest
from pathlib import Path

from software import bringup
from software.bringup import GaitId, State


class FakeTelemetry:
    def __init__(self, state, voltage=6.0, current=1.0):
        self.state, self.voltage, self.current = state, voltage, current
        self.odom_x = self.odom_y = self.odom_yaw = 0.0


class FakeClient:
    def __init__(self, fault_after=None):
        self.calls = []
        self.heartbeats = 0
        self.samples = 0
        self.fault_after = fault_after

    def enable(self): self.calls.append("enable")
    def shutdown(self): self.calls.append("shutdown")
    def set_gait(self, g): self.calls.append(("gait", g))
    def set_velocity(self, *v): self.calls.append(("vel", v))
    def heartbeat(self): self.heartbeats += 1

    def get_telemetry(self):
        self.samples += 1
        if self.fault_after is not None and self.samples > self.fault_after:
            return FakeTelemetry(State.FAULT, current=13.0)
        return FakeTelemetry(State.IDLE, current=0.5 * self.samples)


def no_sleep(_):
    pass


class BringupTest(unittest.TestCase):
    def test_stand_enables_and_feeds_watchdog(self):
        c = FakeClient()
        rec = bringup.Recorder(c, out=lambda *_: None)
        bringup.run_stand(c, rec, seconds=2, rate_hz=10, sleep=no_sleep)
        self.assertEqual(c.calls, ["enable"])
        self.assertEqual(c.heartbeats, 30 + 20)  # 3 s kalkış + 2 s ayakta, 10 Hz

    def test_walk_sets_gait_before_enable_and_stops(self):
        c = FakeClient()
        rec = bringup.Recorder(c, out=lambda *_: None)
        bringup.run_walk(c, rec, 1, 10, "wave", 40, 0, 0, sleep=no_sleep)
        self.assertEqual(c.calls, [("gait", GaitId.WAVE), "enable",
                                   ("vel", (40, 0, 0)), ("vel", (0.0, 0.0, 0.0))])

    def test_fault_aborts(self):
        c = FakeClient(fault_after=2)
        rec = bringup.Recorder(c, out=lambda *_: None)
        with self.assertRaises(RuntimeError):
            bringup.run_stand(c, rec, seconds=10, rate_hz=10, sleep=no_sleep)

    def test_csv_log_and_peaks(self):
        c = FakeClient()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runs" / "stand.csv"
            rec = bringup.Recorder(c, path, out=lambda *_: None)
            bringup.run_stand(c, rec, seconds=2, rate_hz=10, sleep=no_sleep)
            rec.close()
            rows = list(csv.reader(open(path)))
        self.assertEqual(tuple(rows[0]), bringup.LOG_FIELDS)
        self.assertEqual(len(rows) - 1, c.samples)
        self.assertAlmostEqual(rec.peak_current, 0.5 * c.samples)

    def test_parser(self):
        a = bringup.build_parser().parse_args(["walk", "--gait", "tripod", "--vx", "80"])
        self.assertEqual((a.command, a.gait, a.vx), ("walk", "tripod", 80.0))


if __name__ == "__main__":
    unittest.main()
