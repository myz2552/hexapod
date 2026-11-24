"""
H-0996 firmware'inin hat protokolü.

İkisini birebir uyumlu tutun: buradaki her yük, C++ struct'ının yanında `// py:`
olarak yazılmış `struct` formatının aynısını kullanır. Enum değerleri hatta
taşınır, bu yüzden onlar da aynı olmalıdır.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum

# Taşıma sabitleri (config.hpp)
SOF = 0xAA
MAX_PAYLOAD = 128


class State(IntEnum):
    SETUP = 0     # RISING: ayağa kalkma animasyonu çalışıyor
    IDLE = 1      # ayakta, sıfır hız
    WALK = 2      # yürüyüş uyguluyor
    SHUTDOWN = 3  # LOWERING: oturma animasyonu çalışıyor
    FAULT = 4     # acil durdurulmuş, enerjisiz
    OFF = 5       # enerjisiz bekleme: yeni açılmış ya da tamamen oturmuş, Enable bekliyor


class GaitId(IntEnum):
    TRIPOD = 0
    WAVE = 1
    RIPPLE = 2


class LedMode(IntEnum):
    SOLID = 0
    BLINK = 1


class Status(IntEnum):
    REJECTED = 0x00
    OK = 0x01
    UNREACHABLE = 0x02
    BAD_OPCODE = 0x03
    BAD_LENGTH = 0x04


class Opcode(IntEnum):
    # düşük seviye hata ayıklama (istek/yanıt, onay)
    JOG_SERVO = 0x01
    # yapılandırma / çalışma zamanı ayarları (istek/yanıt, onay)
    PROVISION_BODY = 0x10
    PROVISION_MOUNTS = 0x11
    PROVISION_DIRECTION = 0x12
    PROVISION_TRIM = 0x13
    PROVISION_RANGES = 0x14
    PROVISION_GAITS = 0x15
    PROVISION_LIMITS = 0x16
    PROVISION_BODY_POSE = 0x17
    PROVISION_SERVO_CAL = 0x18
    PROVISION_PINS = 0x19
    # yanıtsız (yanıt yok; watchdog'u besler)
    SET_VELOCITY = 0x30
    SET_BODY_POSE = 0x31
    SET_GAIT = 0x32
    ENABLE = 0x33
    SHUTDOWN = 0x34
    STOP = 0x35
    SET_LED = 0x36
    HEARTBEAT = 0x37
    # istek/yanıt (kart aynı opcode ile yanıtlar)
    GET_TELEMETRY = 0x40
    GET_VOLTAGE = 0x41
    GET_CURRENT = 0x42
    GET_JOINTS = 0x43
    GET_BODY_POSE = 0x44
    # kartın başlattığı
    ERROR = 0xEE


_FIRE_AND_FORGET = frozenset({
    Opcode.SET_VELOCITY, Opcode.SET_BODY_POSE, Opcode.SET_GAIT, Opcode.ENABLE,
    Opcode.SHUTDOWN, Opcode.STOP, Opcode.SET_LED, Opcode.HEARTBEAT,
})


def is_fire_and_forget(opcode: int) -> bool:
    return Opcode(opcode) in _FIRE_AND_FORGET


# Yük formatları (little-endian; `// py:` notlarının aynısı)
FMT_SET_VELOCITY = "<fff"       # vx (mm/s), vy (mm/s), wz (deg/s)
FMT_SET_BODY_POSE = "<ffffff"   # x, y, z (mm); roll, pitch, yaw (deg)
FMT_SET_GAIT = "<B"             # gait_id
FMT_SET_LED = "<BBBBf"          # mode, r, g, b, freq_hz
FMT_TELEMETRY = "<Bfffff"       # durum, odom_x, odom_y, odom_yaw(derece), voltaj, akım
FMT_VOLTAGE = "<f"
FMT_CURRENT = "<f"
FMT_JOINTS = "<18f"             # servo uzayı derecesi, bacak öncelikli (bacak*3 + eklem)
FMT_BODY_POSE = "<ffffff"       # x, y, z (mm, z ayakta duruşa göre); roll, pitch, yaw (derece)
FMT_ERROR = "<B"                # durum
FMT_ACK = "<B"                  # durum (başarıda OK) — jog / yapılandırma yanıtı

# Jog / yapılandırma (bkz. protocol.hpp). Diziler bacak öncelikli / eklem önceliklidir.
FMT_JOG_SERVO = "<BH"           # kanal, pulse_us (0 = bırak)
FMT_PROVISION_BODY = "<fffffff"  # coxa,femur,tibia uzunluğu; coxa_offset; ayakta yükseklik;
                                 # duruş yarıçapı; döngü süresi
FMT_PROVISION_MOUNTS = "<24f"   # bacak başına: x, y, z, yaw_derece
FMT_PROVISION_DIRECTION = "<18f"  # servo başına (bacak öncelikli): yön (+/-1)
FMT_PROVISION_TRIM = "<18f"     # servo başına (bacak öncelikli): trim_derece
FMT_PROVISION_RANGES = "<6f"    # eklem tipi başına: min_derece, max_derece
FMT_PROVISION_GAITS = "<12f"    # yürüyüş başına: duty, adım yüksekliği, max adım, örtüşme
FMT_PROVISION_LIMITS = "<ffffffff"  # doğrusal/açısal hız max, yumuşatma tau, gövde doğrusal/açısal, eklem hızı, current_max, voltage_min
FMT_PROVISION_BODY_POSE = "<12f"  # eksen başına min,max: x, y, z (mm); roll, pitch, yaw (derece)
FMT_PROVISION_SERVO_CAL = "<54H"  # servo başına (bacak öncelikli): min_us, mid_us, max_us
FMT_PROVISION_PINS = "<18B"     # mantıksal kanal başına fiziksel pin


@dataclass
class Telemetry:
    state: State
    odom_x: float    # mm
    odom_y: float    # mm
    odom_yaw: float  # derece
    voltage: float   # V
    current: float   # A


def unpack_telemetry(payload: bytes) -> Telemetry:
    st, ox, oy, oyaw, v, c = struct.unpack(FMT_TELEMETRY, payload)
    return Telemetry(State(st), ox, oy, oyaw, v, c)


@dataclass
class BodyPose:
    x: float      # mm, gövde kayması +x (ileri)
    y: float      # mm, gövde kayması +y (sol)
    z: float      # mm, ayakta duruş yüksekliğine göre yükseklik ofseti
    roll: float   # derece
    pitch: float  # derece
    yaw: float    # derece

    @property
    def height(self) -> float:
        """Ayakta duruşa göre gövde yüksekliği ofseti (mm). set_body_pose'un z'siyle
        aynı referans (0 == ayakta duruş yüksekliği)."""
        return self.z


def unpack_body_pose(payload: bytes) -> BodyPose:
    return BodyPose(*struct.unpack(FMT_BODY_POSE, payload))
