"""Robot config'ini (controller/hexapod/config/config.yml) controller'ın kendi
doğrulamasıyla kontrol eder.

Donanım ve pyserial gerekmez: yapılandırma mesajları sahte bir karta gönderilir.
"""
import struct
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "controller"
CONFIG = CONTROLLER / "hexapod" / "config" / "config.yml"

sys.path.insert(0, str(CONTROLLER))
from hexapod import HexapodClient, Opcode, Status  # noqa: E402
from hexapod import protocol as P  # noqa: E402
from hexapod.client import JOINTS, LEGS  # noqa: E402
from hexapod.framing import FrameParser, encode_frame  # noqa: E402
from hexapod.transport import Transport  # noqa: E402


class AckingBoard(Transport):
    """Her provisioning mesajını OK ile yanıtlayan sahte Servo 2040."""

    def __init__(self):
        self._rx = FrameParser()
        self._out = bytearray()
        self.received = {}

    def write(self, data):
        for b in data:
            if self._rx.feed(b):
                op, payload = self._rx.opcode, bytes(self._rx.payload)
                self.received[op] = payload
                self._out.extend(encode_frame(op, bytes([int(Status.OK)])))

    def read(self, n):
        chunk = bytes(self._out[:n])
        del self._out[:n]
        return chunk


def load():
    with open(CONFIG) as f:
        return yaml.safe_load(f)


class ConfigProvisioningTest(unittest.TestCase):
    def test_provisions_every_section(self):
        board = AckingBoard()
        HexapodClient(board, timeout=0.05).provision(load())
        expected = {
            Opcode.PROVISION_BODY, Opcode.PROVISION_MOUNTS, Opcode.PROVISION_DIRECTION,
            Opcode.PROVISION_TRIM, Opcode.PROVISION_RANGES, Opcode.PROVISION_GAITS,
            Opcode.PROVISION_LIMITS, Opcode.PROVISION_BODY_POSE, Opcode.PROVISION_PINS,
            Opcode.PROVISION_SERVO_CAL,
        }
        self.assertEqual(set(board.received), {int(op) for op in expected})

    def test_pins_use_all_18_outputs_once(self):
        pins = [p for leg in LEGS for p in load()["hardware"]["pins"][leg]]
        self.assertEqual(sorted(pins), list(range(18)))

    def test_pulses_are_monotonic_and_in_range(self):
        # [darbe@-90, darbe@0, darbe@+90]; darbesi açıyla azalan servolar ters sıralı olabilir
        pulses = load()["hardware"]["pulses"]
        for leg in LEGS:
            self.assertEqual(len(pulses[leg]), len(JOINTS), leg)
            for joint, (lo, mid, hi) in zip(JOINTS, pulses[leg]):
                where = f"{leg}.{joint}"
                self.assertTrue(all(500 <= p <= 2500 for p in (lo, mid, hi)), where)
                self.assertTrue(lo < mid < hi or lo > mid > hi, where)

    def test_safety_limits_match_hardware(self):
        cfg = load()
        # Servo 2040 klemensleri 10 A sürekli; firmware'in yazılım kesmesi 15 A tepe akımı aşmamalı
        self.assertLessEqual(cfg["safety"]["current_max"], 15.0)
        # 6 V UBEC hattı: düşük voltaj kesmesi 6 V'un altında olmalı
        self.assertLess(cfg["safety"]["voltage_min"], 6.0)
        self.assertEqual(cfg["serial"]["baud"], 921600)

    def test_body_payload_matches_config(self):
        board = AckingBoard()
        cfg = load()
        HexapodClient(board, timeout=0.05).provision(cfg)
        body = struct.unpack(P.FMT_PROVISION_BODY, board.received[int(Opcode.PROVISION_BODY)])
        legs = cfg["kinematics"]["legs"]
        self.assertAlmostEqual(body[0], legs["coxa"], places=3)
        self.assertAlmostEqual(body[1], legs["femur"], places=3)
        self.assertAlmostEqual(body[2], legs["tibia"], places=3)


if __name__ == "__main__":
    unittest.main()
