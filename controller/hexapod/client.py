"""
Kart üzerindeki kontrolcü için Pi tarafı istemci.

Kart tüm kontrol döngüsünü (yürüyüş, IK, durum makinesi) çalıştırır; Pi yüksek
seviyeli hedef değerler gönderir, telemetri okur ve bağlanırken robota özel config'i
karta yükler. Firmware'deki üç mesaj türünün aynısı vardır:
  yanıtsız: hedef değerler, yaşam döngüsü, LED, heartbeat; yanıt yoktur. Her biri
    kartın komut watchdog'unu besler.
  istek/yanıt: telemetri sorguları; kart tek bir çerçeveyle yanıtlar ve biz onu
    bekleriz (en fazla `timeout` kadar).
  onaylı: jog ve yapılandırma; kart tek bir Status baytıyla yanıtlar.

Tipik kullanım:

    from hexapod.client import connect
    bot = connect()          # bağlantıyı açar ve config.yml'den yapılandırır
    bot.enable()

Standart sıralar firmware tarafından sabitlenmiştir ve değiştirilmemelidir.
"""

from __future__ import annotations

import struct
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

import yaml

from . import protocol as P
from .framing import FrameParser, encode_frame
from .protocol import BodyPose, GaitId, LedMode, Opcode, Telemetry
from .transport import Transport

# Hattaki cfg::Leg / cfg::Joint / proto::GaitId sırası (bacak öncelikli düzleştirme)
LEGS = (
    "front_right",
    "middle_right",
    "rear_right",
    "rear_left",
    "middle_left",
    "front_left",
)
JOINTS = ("coxa", "femur", "tibia")
GAITS = ("tripod", "wave", "ripple")

# config.yml paketin içinde gelir (hexapod/config/config.yml); böylece paket ister
# depodan çalıştırılsın ister pip ile kurulsun dosya mevcuttur
DEFAULT_CONFIG = Path(__file__).resolve().parent / "config" / "config.yml"

ConfigLike = Union[Mapping, str, Path, None]


@dataclass
class Velocity:
    vx: float  # mm/s, gövde +x (ileri)
    vy: float  # mm/s, gövde +y (sol)
    wz: float  # derece/s, yaw (+ saat yönünün tersi)


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


class HexapodError(RuntimeError):
    """Kart bir Error çerçevesiyle yanıt verdi."""


class ConfigError(ValueError):
    """Config, provision()'ın beklediği yapıya uymuyor. Mesaj sorunlu yolu
    belirtir, böylece elle düzenlenmiş bir config.yml kolayca düzeltilir."""


class HexapodClient:

    def __init__(self, transport: Transport, timeout: float = 0.2) -> None:
        self._t = transport
        self._timeout = timeout
        self._parser = FrameParser()
        # Taşıyıcıdan çekilmiş ama henüz ayrıştırılmamış baytlar. Porttan okumak veriyi
        # tüketir; bu yüzden bir isteğin fazladan okuduğu her şey bir sonraki istek onu
        # kullanana kadar burada durmalıdır, yoksa arkasındaki çerçeve kaybolur
        self._rx = bytearray()
        # Kartın komut verildiği gibi benimsediği açık döngü durum için Pi tarafı tamponlar;
        # böylece get_velocity()/get_gait() gidiş-dönüş gerektirmez. Hız sınırları
        # provision() sırasında öğrenilir, böylece tampon kartın kendi kırpmasını yansıtır.
        self._vx = self._vy = self._wz = 0.0
        self._gait = GaitId.TRIPOD  # firmware varsayılanı (gait::GaitId TRIPOD)
        self._lin_vel_max: Optional[float] = None
        self._ang_vel_max: Optional[float] = None

    def close(self) -> None:
        self._t.close()

    # Yapılandırma (provisioning)

    def provision(self, config: ConfigLike = None) -> None:
        """Bir config'in tamamını doğrular ve her kart bölümünü hat sırasıyla gönderir.

        `config` önceden ayrıştırılmış bir eşleme, bir YAML dosyasının yolu
        (str/Path) ya da paketle gelen varsayılan için None olabilir. Config önce
        tümüyle doğrulanır: eksik anahtar veya yanlış yapı, yolu belirten bir
        ConfigError fırlatır ve hiçbir şey gönderilmez; böylece kart asla yarım
        yapılandırılmış kalmaz. `pins` ve `pulses` isteğe bağlıdır; bölüm yoksa
        kart derlenmiş varsayılanını korur, varsa doğrulanıp gönderilir. Bölümler
        yalnızca kart enerjisizken uygulanır ve kart her birini onaylar.
        """
        if isinstance(config, Mapping):
            cfg = config
        else:
            path = Path(config) if config is not None else DEFAULT_CONFIG
            with open(path) as f:
                cfg = yaml.safe_load(f)
        if not isinstance(cfg, Mapping):
            raise ConfigError(f"config root must be a mapping, got {type(cfg).__name__}")

        # Herhangi bir uyumsuzlukta noktalı yolla ConfigError fırlatan erişimciler
        def node(dotted: str):
            cur = cfg
            for key in dotted.split("."):
                if not isinstance(cur, Mapping) or key not in cur:
                    raise ConfigError(f"missing '{dotted}'")
                cur = cur[key]
            return cur

        def numbers(value, n: int, where: str) -> List[float]:
            if not isinstance(value, (list, tuple)) or len(value) != n:
                raise ConfigError(f"'{where}' must be {n} numbers, got {value!r}")
            out = []
            for i, x in enumerate(value):
                if isinstance(x, bool) or not isinstance(x, (int, float)):
                    raise ConfigError(f"'{where}[{i}]' must be a number, got {x!r}")
                out.append(float(x))
            return out

        def number(dotted: str) -> float:
            x = node(dotted)
            if isinstance(x, bool) or not isinstance(x, (int, float)):
                raise ConfigError(f"'{dotted}' must be a number, got {x!r}")
            return float(x)

        def vec(dotted: str, n: int) -> List[float]:
            return numbers(node(dotted), n, dotted)

        def per_leg(dotted: str, n: int) -> List[float]:
            return [v for leg in LEGS for v in vec(f"{dotted}.{leg}", n)]

        # Tek bir bayt gönderilmeden önce her bölümü oluştur ve doğrula
        body = [
            number("kinematics.legs.coxa"),
            number("kinematics.legs.femur"),
            number("kinematics.legs.tibia"),
            number("kinematics.legs.coxa_offset"),
            number("kinematics.standing_height"),
            number("kinematics.stance_radius"),
            number("gaits.cycle_time"),
        ]

        mounts: List[float] = []
        for leg in LEGS:
            pos = vec(f"kinematics.mounts.{leg}.position", 3)
            ori = vec(f"kinematics.mounts.{leg}.orientation", 3)
            # Yalnızca yaw gönderilir: coxa ekseni dikeydir, bu yüzden bir bacak roll veya
            # pitch ile monte edilemez. z, coxa-femur ekleminin yüksekliğidir
            mounts += [pos[0], pos[1], pos[2], ori[2]]

        direction = per_leg("hardware.direction", 3)
        trim = per_leg("hardware.trim", 3)

        ranges = [v for j in JOINTS for v in vec(f"safety.{j}_range", 2)]

        gaits: List[float] = []
        for name in GAITS:
            gaits += [
                number(f"gaits.{name}.duty_factor"),
                number(f"gaits.{name}.step_height"),
                number(f"gaits.{name}.max_stride"),
                number(f"gaits.{name}.overlap"),
            ]

        limits = [
            number("safety.lin_vel_max"),
            number("safety.ang_vel_max"),
            number("safety.vel_smooth_tau"),
            number("safety.body_lin_vel_max"),
            number("safety.body_ang_vel_max"),
            number("safety.joint_vel_max"),
            number("safety.current_max"),
            number("safety.voltage_min"),
        ]
        # Hız sınırlarını sakla; set_velocity komut verilen değeri tamponlarken kartın
        # kırpmasını yansıtabilsin (bkz. get_velocity)
        self._lin_vel_max = limits[0]
        self._ang_vel_max = limits[1]

        body_pose = [
            v
            for axis in ("x", "y", "z", "roll", "pitch", "yaw")
            for v in vec(f"safety.{axis}_range", 2)
        ]

        hw = node("hardware")
        pins = None
        if "pins" in hw:
            pins = [int(v) for leg in LEGS for v in vec(f"hardware.pins.{leg}", 3)]
        pulses = None
        if "pulses" in hw:
            pulses = []
            for leg in LEGS:
                triples = node(f"hardware.pulses.{leg}")
                if not isinstance(triples, (list, tuple)) or len(triples) != len(JOINTS):
                    raise ConfigError(
                        f"'hardware.pulses.{leg}' must be {len(JOINTS)} triples, "
                        f"got {triples!r}"
                    )
                for j, triple in enumerate(triples):
                    pulses += [
                        int(x) for x in numbers(triple, 3, f"hardware.pulses.{leg}[{j}]")
                    ]

        # Her şey doğrulandı, şimdi gönder. Pinler kalibrasyondan önce gider; böylece
        # darbeler uygulanırken HAL'in mantıksal-fiziksel eşlemesi hazır olur
        self._ack(Opcode.PROVISION_BODY, struct.pack(P.FMT_PROVISION_BODY, *body))
        self._ack(Opcode.PROVISION_MOUNTS, struct.pack(P.FMT_PROVISION_MOUNTS, *mounts))
        self._ack(Opcode.PROVISION_DIRECTION, struct.pack(P.FMT_PROVISION_DIRECTION, *direction))
        self._ack(Opcode.PROVISION_TRIM, struct.pack(P.FMT_PROVISION_TRIM, *trim))
        self._ack(Opcode.PROVISION_RANGES, struct.pack(P.FMT_PROVISION_RANGES, *ranges))
        self._ack(Opcode.PROVISION_GAITS, struct.pack(P.FMT_PROVISION_GAITS, *gaits))
        self._ack(Opcode.PROVISION_LIMITS, struct.pack(P.FMT_PROVISION_LIMITS, *limits))
        self._ack(Opcode.PROVISION_BODY_POSE, struct.pack(P.FMT_PROVISION_BODY_POSE, *body_pose))
        if pins is not None:
            self._ack(Opcode.PROVISION_PINS, struct.pack(P.FMT_PROVISION_PINS, *pins))
        if pulses is not None:
            self._ack(Opcode.PROVISION_SERVO_CAL, struct.pack(P.FMT_PROVISION_SERVO_CAL, *pulses))

    # Düşük seviye temel işlemler; ayrı çalışan kalibrasyon aracı da kullanır

    def set_pins(self, pins) -> None:
        """18 fiziksel çıkışı tam yapılandırma yapmadan, bacak öncelikli bir listeden
        doğrudan ayarlar. calibrate.py tarafından jog'dan önce kullanılır"""
        self._ack(Opcode.PROVISION_PINS,
                  struct.pack(P.FMT_PROVISION_PINS, *[int(p) for p in pins]))

    def jog_servo(self, channel: int, pulse_us: int) -> None:
        """Bir servoyu (mantıksal kanal) mikrosaniye cinsinden ham bir darbeye sürer; 0
        servoyu bırakır. Ayrı çalışan kalibrasyon aracı kullanır. Yalnızca OFF durumunda çalışır"""
        self._ack(Opcode.JOG_SERVO,
                  struct.pack(P.FMT_JOG_SERVO, channel, pulse_us))

    # Yanıtsız komutlar

    def enable(self) -> None:
        self._vx = self._vy = self._wz = 0.0  # kart enable'da hareketi sıfırlar
        self._send(Opcode.ENABLE)

    def shutdown(self) -> None:
        self._vx = self._vy = self._wz = 0.0  # kart otururken hızı sıfırlar
        self._send(Opcode.SHUTDOWN)

    def stop(self) -> None:
        self._vx = self._vy = self._wz = 0.0
        self._send(Opcode.STOP)

    def heartbeat(self) -> None:
        self._send(Opcode.HEARTBEAT)

    def set_velocity(self, vx: float, vy: float, wz: float) -> None:
        """vx, vy mm/s (gövde çerçevesi, +x ileri / +y sol); wz derece/s (+ saat yönünün tersi).
        Yapılandırılan sınırlara kırpılır ve tamponlanır; böylece get_velocity()
        gidiş-dönüş olmadan geri okur (açık döngü: komut, hedef değerin kendisidir)."""
        if self._lin_vel_max is not None:
            vx = _clamp(vx, -self._lin_vel_max, self._lin_vel_max)
            vy = _clamp(vy, -self._lin_vel_max, self._lin_vel_max)
        if self._ang_vel_max is not None:
            wz = _clamp(wz, -self._ang_vel_max, self._ang_vel_max)
        self._vx, self._vy, self._wz = vx, vy, wz
        self._send(Opcode.SET_VELOCITY, struct.pack(P.FMT_SET_VELOCITY, vx, vy, wz))

    def set_body_pose(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
    ) -> None:
        """Ayakta duruşa göre gövde pozu ofsetleri: x/y/z mm (z ayakta duruş
        yüksekliğine göre), roll/pitch/yaw derece"""
        self._send(
            Opcode.SET_BODY_POSE,
            struct.pack(P.FMT_SET_BODY_POSE, x, y, z, roll, pitch, yaw),
        )

    def set_gait(self, gait: GaitId) -> None:
        self._gait = GaitId(gait)  # tamponlanır; kart komut verildiği gibi benimser
        self._send(Opcode.SET_GAIT, struct.pack(P.FMT_SET_GAIT, int(gait)))

    def set_led(
        self, mode: LedMode, r: int, g: int, b: int, freq_hz: float = 0.0
    ) -> None:
        self._send(
            Opcode.SET_LED, struct.pack(P.FMT_SET_LED, int(mode), r, g, b, freq_hz)
        )

    # İstek/yanıt

    def get_telemetry(self) -> Telemetry:
        return P.unpack_telemetry(self._request(Opcode.GET_TELEMETRY))

    def get_voltage(self) -> float:
        return struct.unpack(P.FMT_VOLTAGE, self._request(Opcode.GET_VOLTAGE))[0]

    def get_current(self) -> float:
        return struct.unpack(P.FMT_CURRENT, self._request(Opcode.GET_CURRENT))[0]

    def get_joints(self) -> List[float]:
        return list(struct.unpack(P.FMT_JOINTS, self._request(Opcode.GET_JOINTS)))

    def get_body_pose(self) -> BodyPose:
        """Kartın CANLI gövde pozunu sorgular: hedefin kendisini değil, son set_body_pose
        hedefine doğru ilerlerken ara değeri. set_body_pose ile aynı birim ve referans
        (x/y/z mm, z ayakta duruş yüksekliğine göre; roll/pitch/yaw derece). z ofseti
        için .height okunur."""
        return P.unpack_body_pose(self._request(Opcode.GET_BODY_POSE))

    # Pi'de tamponlanan durum (gidiş-dönüş yok). Kart bu komutlara anında ve açık
    # döngüde uyar, yani son komut mevcut hedef değerin KENDİSİDİR.

    def get_velocity(self) -> Velocity:
        """Son komut verilen hız (mm/s, mm/s, derece/s), yapılandırılan sınırlara kırpılmış.
        Kartın kendiliğinden durmasını (haberleşme watchdog'u veya bir hata) YANSITMAZ;
        kartın hâlâ enerjili ve yürüyor olduğunu doğrulamak gerekiyorsa
        get_telemetry().state okunmalıdır."""
        return Velocity(self._vx, self._vy, self._wz)

    def get_gait(self) -> GaitId:
        """Son komut verilen yürüyüş tipi (Pi'de tamponlanır)."""
        return self._gait

    # İç işleyiş

    def _ack(self, opcode: Opcode, payload: bytes = b"") -> None:
        status = self._request(opcode, payload)  # Error gelirse HexapodError fırlatır
        code = status[0] if status else int(P.Status.REJECTED)
        if code != int(P.Status.OK):
            raise HexapodError(f"{Opcode(opcode).name} rejected: {P.Status(code).name}")

    def _send(self, opcode: Opcode, payload: bytes = b"") -> None:
        self._t.write(encode_frame(int(opcode), payload))

    def _request(self, opcode: Opcode, payload: bytes = b"") -> bytes:
        self._t.write(encode_frame(int(opcode), payload))
        deadline = time.monotonic() + self._timeout
        want = int(opcode)

        while True:
            # Porta geri dönmeden önce tamponda olanı ayrıştır; böylece önceki bir yanıtla
            # aynı okumada gelen bir çerçeve de görülür
            i = 0
            try:
                while i < len(self._rx):
                    b = self._rx[i]
                    i += 1
                    if not self._parser.feed(b):
                        continue
                    op, data = self._parser.opcode, self._parser.payload
                    if op == int(Opcode.ERROR):
                        status = P.Status(data[0]) if data else P.Status.REJECTED
                        raise HexapodError(f"board error: {status.name}")
                    if op == want:
                        return data
                    # İstemediğimiz bir çerçeve, genellikle önceki bir sorguya geç gelen yanıt:
                    # at ve ayrıştırmaya devam et
            finally:
                # Her çıkışta çalışır; böylece döndürülen ya da başarısız olan çerçevenin
                # arkasındaki baytlar yığın çerçevesiyle birlikte atılmak yerine saklanır
                del self._rx[:i]

            if time.monotonic() >= deadline:
                raise TimeoutError(f"no reply to {Opcode(opcode).name}")
            # 256, azami boyutta iki çerçeveyi karşılar; böylece toplu gelen veri tek çağrıda okunur
            self._rx += self._t.read(256)


def connect(
    config: ConfigLike = None, port: Optional[str] = None, baud: int = 921600,
    provision: bool = True, timeout: float = 0.2
) -> HexapodClient:
    """Seri bağlantıyı açar ve kartı config'ten yapılandırır.

    config bir eşleme, config.yml yolu ya da paketle gelen varsayılan için None
    olabilir; port, serial.port'u geçersiz kılar. `serial` yalnızca Pi tarafındadır,
    karta gönderilmez. timeout yanıt başına bekleme süresidir (s): kaybolan bir yanıt
    sorgu vazgeçmeden önce bu kadar süre harcar, bu yüzden sorgulama periyoduna göre
    küçük tutun.
    """
    from .transport import SerialTransport

    if isinstance(config, Mapping):
        cfg = config
    else:
        path = Path(config) if config is not None else DEFAULT_CONFIG
        with open(path) as f:
            cfg = yaml.safe_load(f)
    serial = cfg.get("serial", {}) if isinstance(cfg, Mapping) else {}
    port = port or serial.get("port")
    baud = baud or int(serial.get("baud", 921600))
    client = HexapodClient(SerialTransport(port, baud, timeout=timeout), timeout=timeout)
    if provision:
        client.provision(cfg)
    return client
