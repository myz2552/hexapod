"""
HDLC tarzı çerçeveleme.

Çerçeve:  SOF(0xAA) | LEN | opcode | yük[LEN] | CRC16-düşük | CRC16-yüksek
  - LEN yalnızca yükü sayar (opcode ayrıdır); çerçeve sonu baytı yoktur.
  - CRC16-CCITT (polinom 0x1021, başlangıç 0xFFFF), LEN + opcode + yük üzerinden.
"""
from __future__ import annotations

from .protocol import MAX_PAYLOAD, SOF

CRC_POLY = 0x1021
CRC_INIT = 0xFFFF


def _crc_update(crc: int, byte: int) -> int:
    crc ^= byte << 8
    for _ in range(8):
        crc = ((crc << 1) ^ CRC_POLY) if (crc & 0x8000) else (crc << 1)
        crc &= 0xFFFF
    return crc


def crc16(data: bytes) -> int:
    crc = CRC_INIT
    for b in data:
        crc = _crc_update(crc, b)
    return crc


def encode_frame(opcode: int, payload: bytes = b"") -> bytes:
    """Bir opcode + yük için eksiksiz bir çerçeve oluşturur."""
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"payload {len(payload)} > MAX_PAYLOAD {MAX_PAYLOAD}")
    length = len(payload)
    body = bytes([length, opcode]) + payload
    crc = crc16(body)
    return bytes([SOF]) + body + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


class FrameParser:
    """Bayt bayt alıcı. `feed(b)` CRC'si geçerli bir çerçeveyi tamamlayan baytta True
    döndürür; `opcode`/`payload` bir sonraki feed'e kadar geçerlidir.
    Hatalı uzunluk veya CRC'de bir sonraki SOF'ta sessizce yeniden senkronize olur."""

    _SOF, _LEN, _OP, _PAYLOAD, _CRCLO, _CRCHI = range(6)

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._phase = self._SOF
        self._len = 0
        self._crc = CRC_INIT
        self._rx_crc = 0
        self.opcode = 0
        self.payload = b""
        self._buf = bytearray()

    def feed(self, b: int) -> bool:
        b &= 0xFF
        p = self._phase
        if p == self._SOF:
            if b == SOF:
                self._phase = self._LEN
            return False
        if p == self._LEN:
            if b > MAX_PAYLOAD:  # olanaksız uzunluk -> yeniden senkronize ol
                self._phase = self._LEN if b == SOF else self._SOF
                return False
            self._len = b
            self._crc = _crc_update(CRC_INIT, b)
            self._buf = bytearray()
            self._phase = self._OP
            return False
        if p == self._OP:
            self.opcode = b
            self._crc = _crc_update(self._crc, b)
            self._phase = self._CRCLO if self._len == 0 else self._PAYLOAD
            return False
        if p == self._PAYLOAD:
            self._buf.append(b)
            self._crc = _crc_update(self._crc, b)
            if len(self._buf) >= self._len:
                self._phase = self._CRCLO
            return False
        if p == self._CRCLO:
            self._rx_crc = b
            self._phase = self._CRCHI
            return False
        if p == self._CRCHI:
            self._rx_crc |= b << 8
            self._phase = self._SOF
            if self._rx_crc == self._crc:
                self.payload = bytes(self._buf)
                return True
            return False
        return False
