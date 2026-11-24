"""Servo 2040 + upstream firmware için Raspberry Pi tarafı devreye alma aracı.

controller/ klasöründeki istemciyi (`hexapod` paketi) kullanır; kendi
protokolü yoktur. Üç komut:

    telemetry  Servoları hiç enerjilemeden durum, voltaj ve akımı okur.
    stand      Ayağa kalkar, belirtilen süre ayakta durur, oturur.
    walk       Ayağa kalkar, seçilen yürüyüşle (tripod / wave / ripple)
               belirtilen hızla yürür, durur ve oturur.

Her komut telemetriyi ekrana yazar; --log ile CSV olarak da kaydeder
(experiments/ altındaki deney kayıtları için).

Repo kökünden, Raspberry Pi 5 üzerinde:

    python -m software.bringup telemetry
    python -m software.bringup stand --seconds 10
    python -m software.bringup walk --gait tripod --vx 60 --seconds 8 --log runs/tripod.csv

Kart heartbeat almazsa 500 ms içinde kendiliğinden oturur ve servoları
bırakır (firmware watchdog'u); Ctrl-C de oturma komutu gönderir.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "controller" / "hexapod" / "config" / "config.yml"
CONTROLLER = ROOT / "controller"

if str(CONTROLLER) not in sys.path:
    sys.path.insert(0, str(CONTROLLER))

from hexapod import GaitId, State, connect  # noqa: E402

GAITS = {"tripod": GaitId.TRIPOD, "wave": GaitId.WAVE, "ripple": GaitId.RIPPLE}
LOG_FIELDS = ("t_s", "phase", "state", "odom_x_mm", "odom_y_mm", "odom_yaw_deg",
              "voltage_v", "current_a")


class Recorder:
    """Telemetriyi ekrana ve isteğe bağlı CSV dosyasına yazar."""

    def __init__(self, client, log_path: Optional[Path] = None, out=print):
        self.client = client
        self.out = out
        self.t0 = time.monotonic()
        self.peak_current = 0.0
        self.min_voltage = float("inf")
        self._file = None
        self._writer = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._file = open(log_path, "w", newline="")
            self._writer = csv.writer(self._file)
            self._writer.writerow(LOG_FIELDS)

    def sample(self, phase: str):
        tel = self.client.get_telemetry()
        t = time.monotonic() - self.t0
        self.peak_current = max(self.peak_current, tel.current)
        self.min_voltage = min(self.min_voltage, tel.voltage)
        self.out(f"[{t:6.2f}s] {phase:8s} {State(tel.state).name:8s} "
                 f"{tel.voltage:5.2f} V {tel.current:5.2f} A "
                 f"odom=({tel.odom_x:7.1f}, {tel.odom_y:7.1f}) mm {tel.odom_yaw:6.1f} deg")
        if self._writer:
            self._writer.writerow((f"{t:.3f}", phase, State(tel.state).name,
                                   f"{tel.odom_x:.1f}", f"{tel.odom_y:.1f}",
                                   f"{tel.odom_yaw:.1f}", f"{tel.voltage:.3f}",
                                   f"{tel.current:.3f}"))
        return tel

    def close(self):
        if self._file:
            self._file.close()


def hold(client, rec: Recorder, phase: str, seconds: float, rate_hz: float,
         sleep: Callable[[float], None] = time.sleep) -> None:
    """`seconds` boyunca watchdog'u besler, saniyede yaklaşık bir telemetri yazar."""
    dt = 1.0 / rate_hz
    steps = max(1, int(round(seconds * rate_hz)))
    every = max(1, int(round(rate_hz)))
    for i in range(steps):
        client.heartbeat()
        if i % every == 0:
            tel = rec.sample(phase)
            if tel.state == State.FAULT:
                raise RuntimeError("kart FAULT durumuna geçti (aşırı akım veya düşük voltaj)")
        sleep(dt)


def run_telemetry(client, rec: Recorder, seconds: float, rate_hz: float, sleep=time.sleep):
    for _ in range(max(1, int(round(seconds)))):
        rec.sample("read")
        sleep(1.0)


def run_stand(client, rec: Recorder, seconds: float, rate_hz: float, sleep=time.sleep):
    client.enable()
    hold(client, rec, "rise", 3.0, rate_hz, sleep)
    hold(client, rec, "stand", seconds, rate_hz, sleep)


def run_walk(client, rec: Recorder, seconds: float, rate_hz: float, gait: str,
             vx: float, vy: float, yaw: float, sleep=time.sleep):
    client.set_gait(GAITS[gait])
    client.enable()
    hold(client, rec, "rise", 3.0, rate_hz, sleep)
    client.set_velocity(vx, vy, yaw)
    hold(client, rec, "walk", seconds, rate_hz, sleep)
    client.set_velocity(0.0, 0.0, 0.0)
    hold(client, rec, "settle", 1.5, rate_hz, sleep)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--port", default=None, help="seri port (varsayılan: config'teki serial.port)")
    ap.add_argument("--no-provision", action="store_true",
                    help="kartı config ile yeniden yapılandırma")
    ap.add_argument("--rate", type=float, default=50.0, help="heartbeat frekansı, Hz")
    ap.add_argument("--log", type=Path, default=None, help="telemetriyi CSV olarak kaydet")
    sub = ap.add_subparsers(dest="command", required=True)

    t = sub.add_parser("telemetry", help="servoları enerjilemeden telemetri oku")
    t.add_argument("--seconds", type=float, default=5.0)

    s = sub.add_parser("stand", help="ayağa kalk, bekle, otur")
    s.add_argument("--seconds", type=float, default=10.0)

    w = sub.add_parser("walk", help="ayağa kalk, yürü, dur, otur")
    w.add_argument("--gait", choices=sorted(GAITS), default="tripod")
    w.add_argument("--vx", type=float, default=60.0, help="ileri hız, mm/s")
    w.add_argument("--vy", type=float, default=0.0, help="yanal hız, mm/s")
    w.add_argument("--yaw", type=float, default=0.0, help="dönüş hızı, deg/s")
    w.add_argument("--seconds", type=float, default=5.0)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    client = connect(config=str(args.config), port=args.port,
                     provision=not args.no_provision)
    rec = Recorder(client, args.log)
    moved = args.command != "telemetry"
    try:
        if args.command == "telemetry":
            run_telemetry(client, rec, args.seconds, args.rate)
        elif args.command == "stand":
            run_stand(client, rec, args.seconds, args.rate)
        else:
            run_walk(client, rec, args.seconds, args.rate, args.gait, args.vx, args.vy, args.yaw)
    except KeyboardInterrupt:
        print("\ndurduruldu, robot oturuyor")
    finally:
        if moved:
            try:
                client.shutdown()
                hold(client, rec, "sit", 3.0, args.rate)
            except Exception as exc:  # kart zaten FAULT/OFF olabilir
                print(f"oturma sırasında hata: {exc}")
        print(f"en yüksek akım {rec.peak_current:.2f} A, en düşük voltaj {rec.min_voltage:.2f} V")
        rec.close()
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
