"""H-0996 firmware'i için Pi tarafı controller.

Firmware'deki (firmware/src/communication/protocol.hpp) hat protokolünün aynısını
uygular ve tüm kontrol döngüsünü çalıştıran karta yüksek seviyeli hedef değerler gönderir.
"""
from .client import ConfigError, HexapodClient, HexapodError, Velocity, connect
from .framing import FrameParser, crc16, encode_frame
from .protocol import (
    BodyPose,
    GaitId,
    LedMode,
    Opcode,
    State,
    Status,
    Telemetry,
)
from .transport import SerialTransport, Transport

__all__ = [
    "HexapodClient",
    "HexapodError",
    "ConfigError",
    "connect",
    "Transport",
    "SerialTransport",
    "FrameParser",
    "encode_frame",
    "crc16",
    "Opcode",
    "State",
    "GaitId",
    "LedMode",
    "Status",
    "Telemetry",
    "BodyPose",
    "Velocity",
]
