"""
Ayrı çalışan, servo başına darbe genişliği kalibrasyonu.

Her servonun kendi darbe<->açı aktarım fonksiyonunu ölçer; en iyisi servo bir
bacağa vidalanmadan önce, boştayken yapılır. Böylece ölçüm eklemin mekanik
aralığı hakkında bilgi taşımaz. Her servo için yalnızca iki referans darbe
bulunur: mili -90 dereceye getiren ve +90 dereceye getiren darbe. Orta nokta
darbesi (0 derece) bu ikisinin ortalaması alınır. Kâğıt üzerinde aynı olan
servolar aynı darbeye biraz farklı tepki verir, bu yüzden 18 servonun her biri
ayrı ayrı ölçülür.

Uç noktalar servonun kendi +-90 değerleri olduğu için eklemin yapısal ofsetleri
(hardware.trim / hardware.direction) ve sınırları (safety.*_range) kendi config
bölümlerinde kalır; bu dosya yalnızca darbeleri servo derecelerine eşler.

Bu, çalışan robotun parçası olmayan ayrı bir araçtır: karta yalnızca düşük
seviye JogServo hata ayıklama komutuyla bağlanır (durum makinesi OFF kalır,
servolar ham sürülür) ve sonucu config'e `hardware.pulses` altında
[darbe@-90, darbe@0, darbe@+90] üçlüleri olarak yazar (bacak başına, coxa /
femur / tibia sırasıyla). Ana yazılım bir sonraki çalıştırıldığında connect()
bu darbeleri karta otomatik olarak gönderir.

Kontroller
----------
    [yukarı / w]   ince  +   ([aşağı / s] ince  -)
    [sağ    / d]   kaba  +   ([sol   / a] kaba  -)
    [enter]        mevcut darbeyi bu referans açı için kaydet (-90 -> +90)
    [u / bksp]     bu servodaki son kaydı geri al
    [q / esc]      o ana kadar yapılanı kaydet ve çık

Her servo için önce -90 dereceye getirip kaydedersiniz, sonra +90 dereceye
getirip kaydedersiniz; araç bu iki darbeyi (ve orta nokta olarak ortalamalarını)
saklar ve bir sonraki servoya geçer.

Çalıştırma:  python3 calibrate.py            [--port /dev/ttyAMA0] [--channels 0 1 2]
"""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq

from sshkeyboard import listen_keyboard, stop_listening

from hexapod import HexapodClient, SerialTransport
from hexapod.client import DEFAULT_CONFIG, JOINTS, LEGS

# Gidiş-dönüş YAML: config.yml'yi yorumları, anahtar sırasını ve satır içi darbe
# satırlarını koruyarak okur ve yazar; böylece kalibrasyon elle düzenlenmiş dosyayı bozmaz
yaml_rt = YAML()
yaml_rt.preserve_quotes = True


def channel_label(channel: int) -> str:
    leg, joint = divmod(channel, len(JOINTS))
    return f"{LEGS[leg]:12s} {JOINTS[joint]:5s} (ch {channel:2d})"


class ServoCalibrator:
    """Mantıksal kanal listesi üzerinde klavyeyle jog yapılan bir kalibrasyon oturumunu yürütür."""

    PHASES = ("min", "max")
    PHASE_LABEL = {"min": "-90 deg", "max": "+90 deg"}

    def __init__(
        self,
        client: HexapodClient,
        channels,
        small_step=5,
        large_step=50,
        min_pulse=500,
        max_pulse=2500,
        start_pulse=None,
    ):
        self.client = client
        self.channels = list(channels)
        self.small_step = small_step
        self.large_step = large_step
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self.start_pulse = (
            start_pulse if start_pulse is not None else (min_pulse + max_pulse) // 2
        )

        self.results = {}  # kanal -> [min, orta, max]
        self.job_idx = 0
        self.phase_idx = 0
        self.pulse = self.start_pulse
        self.captured = {}  # faz -> darbe, üzerinde çalışılan servo için
        self.finished = False

    @property
    def channel(self) -> int:
        return self.channels[self.job_idx]

    def _send(self) -> None:
        self.client.jog_servo(self.channel, int(round(self.pulse)))

    def _release(self) -> None:
        self.client.jog_servo(self.channel, 0)

    def _status(self) -> None:
        phase = self.PHASES[min(self.phase_idx, len(self.PHASES) - 1)]
        captured = "  ".join(f"{k}={int(round(v))}" for k, v in self.captured.items())
        line = (
            f"[{self.job_idx + 1:2d}/{len(self.channels)}] "
            f"{channel_label(self.channel)} | set {self.PHASE_LABEL[phase]:8s} | "
            f"pulse = {int(round(self.pulse)):4d} us"
        )
        if captured:
            line += f"   [{captured}]"
        print(f"\r{line}\033[K", end="", flush=True)

    def jog(self, step: int) -> None:
        self.pulse = min(self.max_pulse, max(self.min_pulse, self.pulse + step))
        self._send()
        self._status()
        time.sleep(0.02)

    def register(self) -> None:
        phase = self.PHASES[self.phase_idx]
        self.captured[phase] = self.pulse
        self.phase_idx += 1
        if self.phase_idx >= len(self.PHASES):
            self._finalize_servo()
        else:
            self._send()
            self._status()

    def undo(self) -> None:
        if self.phase_idx == 0:
            self._status()
            return
        self.phase_idx -= 1
        phase = self.PHASES[self.phase_idx]
        if phase in self.captured:
            self.pulse = self.captured.pop(phase)
        self._send()
        self._status()

    def _finalize_servo(self) -> None:
        # Darbeleri referans açı sırasında tutun: [-90, orta, +90]. SIRALAMAYIN;
        # darbesi açıyla birlikte azalan bir servoda darbe@-90 > darbe@+90 olması
        # normaldir ve kartın kalibrasyonu onu her iki durumda da doğru eşler.
        lo = self.captured["min"]  # -90 derecedeki darbe
        hi = self.captured["max"]  # +90 derecedeki darbe
        mid = (lo + hi) / 2.0  # 0 derecedeki darbe
        self.results[self.channel] = [int(round(lo)), int(round(mid)), int(round(hi))]
        self._release()
        print()  # bitirilen servonun satırı ekranda kalsın
        self.job_idx += 1
        if self.job_idx >= len(self.channels):
            self.finished = True
            print("\nAll servos calibrated.")
            _stop_keyboard()
            return
        self.phase_idx = 0
        self.captured = {}
        self.pulse = self.start_pulse
        self._send()
        self._status()

    def quit(self) -> None:
        print("\n\nStopping. Calibrated servos so far will be saved.")
        self._release()
        _stop_keyboard()

    def on_key(self, key: str) -> None:
        if key in ("up", "w"):
            self.jog(self.small_step)
        elif key in ("down", "s"):
            self.jog(-self.small_step)
        elif key in ("right", "d"):
            self.jog(self.large_step)
        elif key in ("left", "a"):
            self.jog(-self.large_step)
        elif key == "enter":
            self.register()
        elif key in ("u", "backspace"):
            self.undo()
        elif key in ("q", "esc"):
            self.quit()

    def run(self) -> None:

        print(__doc__)
        print(
            f"Step sizes: fine +/-{self.small_step} us, coarse +/-{self.large_step} us."
        )
        input("\nPress Enter to energize and begin (servos will move to centre)... ")
        self._send()
        self._status()
        try:
            listen_keyboard(self.on_key, delay_second_char=0.05)
        finally:
            for ch in self.channels:  # hiçbir servonun tutulu kalmadığından emin ol
                self.client.jog_servo(ch, 0)
            self.client.close()


def _stop_keyboard() -> None:
    stop_listening()


def save_results(config_path, results) -> Path:
    """Kalibrasyonu yorumları/biçimi koruyarak config.yml içinde `hardware.pulses`
    altına birleştirir. Yedek dosyanın yolunu döndürür."""
    path = Path(config_path)
    backup = path.with_name(path.name + ".bak")
    shutil.copy2(path, backup)

    with path.open() as f:
        data = yaml_rt.load(f)
    hardware = data.setdefault("hardware", {})
    pulses = hardware.get("pulses") or {}

    def flow(values):
        seq = CommentedSeq(values)
        seq.fa.set_flow_style()
        return seq

    n_joints = len(JOINTS)
    for channel, triple in results.items():
        leg, joint = divmod(channel, n_joints)
        leg_name = LEGS[leg]
        if leg_name not in pulses or not isinstance(pulses.get(leg_name), list):
            pulses[leg_name] = flow([flow([500, 1500, 2500]) for _ in JOINTS])
        pulses[leg_name][joint] = flow([int(v) for v in triple])
    hardware["pulses"] = pulses

    with path.open("w") as f:
        yaml_rt.dump(data, f)
    return backup


def _parse_channels(channels, legs):
    if channels:
        return sorted(channels)
    if legs:
        idx = {name: i for i, name in enumerate(LEGS)}
        out = []
        for leg in legs:
            base = idx[leg] * len(JOINTS)
            out += [base + j for j in range(len(JOINTS))]
        return sorted(out)
    return list(range(len(LEGS) * len(JOINTS)))  # 18'inin hepsi


def main() -> None:

    ap = argparse.ArgumentParser(description="Per-servo pulse-width calibration.")
    ap.add_argument(
        "--config",
        "-c",
        default=str(DEFAULT_CONFIG),
        help="config.yml (read for serial/pins, written with results).",
    )
    ap.add_argument("--port", "-p", default=None, help="serial port override.")
    ap.add_argument(
        "--channels",
        "-C",
        type=int,
        nargs="+",
        default=None,
        help="only calibrate these logical channels (0..17).",
    )
    ap.add_argument(
        "--legs",
        "-L",
        nargs="+",
        default=None,
        help=f"only calibrate these legs ({', '.join(LEGS)}).",
    )
    ap.add_argument("--small-step", "-s", type=int, default=5)
    ap.add_argument("--large-step", "-l", type=int, default=50)
    ap.add_argument("--min-pulse", "-u", type=int, default=500)
    ap.add_argument("--max-pulse", "-U", type=int, default=2500)
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = yaml_rt.load(f)
    serial = cfg.get("serial", {})
    port = args.port or serial.get("port")
    baud = int(serial.get("baud", 921600))
    client = HexapodClient(SerialTransport(port, baud))

    # Jog'dan önce mantıksal kanalların doğru fiziksel servolara eşlendiğinden emin ol
    hardware = cfg.get("hardware", {})
    if "pins" in hardware:
        client.set_pins([int(v) for leg in LEGS for v in hardware["pins"][leg]])

    channels = _parse_channels(args.channels, args.legs)
    cal = ServoCalibrator(
        client,
        channels,
        small_step=args.small_step,
        large_step=args.large_step,
        min_pulse=args.min_pulse,
        max_pulse=args.max_pulse,
    )
    cal.run()

    if cal.results and not args.no_save:
        backup = save_results(args.config, cal.results)
        print(f"Saved {len(cal.results)} servo(s) to {args.config} (backup: {backup}).")
    elif cal.results:
        print("--no-save set; results were not written.")
    else:
        print("No servos were fully calibrated; nothing to save.")


if __name__ == "__main__":
    main()
