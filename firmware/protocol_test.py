"""
Servo2040 firmware'i için bağımsız seri bağlantı duman testi.

src/communication/protocol.hpp içindeki hat protokolünü elle kopyalar ve bağlı
karta yalnızca okuma sorguları gönderir. Böylece pyserial dışında hiçbir şey
kurmadan "kart çalışıyor ve protokolü konuşuyor mu?" sorusunu UART üzerinden
kontrol edebilirsiniz.

Yalnızca okuma yapar (telemetri/voltaj/akım); robotu asla etkinleştirmez ve
servo oynatmaz. Tam üst seviye istemci (enable, yürüyüşler, hızlar,
yapılandırma) için controller/ klasöründeki `hexapod` paketini kullanın.

    python3 protocol_test.py            # /dev/ttyAMA0 üzerinden telemetri sorgula

Çerçeve düzeni (kesin tanım için protocol.hpp'ye bakın):

    SOF | LEN | opcode | yük[LEN] | CRC düşük | CRC yüksek
    0xAA  1B     1B      LEN bayt   2 bayt (CRC16-CCITT)

  - LEN yalnızca yükü sayar; opcode DAHİL DEĞİLDİR.
  - CRC16-CCITT (polinom 0x1021, başlangıç 0xFFFF), LEN + opcode + yük üzerinden,
    little-endian. Çerçeve sonu baytı yoktur: çerçeveyi LEN sınırlar.
  - Çok baytlı tüm alanlar little-endian'dır; float'lar IEEE-754'tür.
"""
import struct
import time

import serial

# UART (src/core/config.hpp içindeki cfg::BAUD ile aynı olmalı)
PORT = "/dev/ttyAMA0"
BAUD_RATE = 921600

# Çerçeveleme
SOF = 0xAA
MAX_PAYLOAD = 128

# Bu testin sorgulama hızı (kartın 50 Hz kontrol döngüsünden bağımsız)
HZ = 5.0
PERIOD = 1.0 / HZ

# Opcode'lar (alt küme; salt okuma sorguları + hata yanıtı)
GET_TELEMETRY = 0x40  # () -> TelemetryReply  "<Bfffff"
GET_VOLTAGE = 0x41    # () -> VoltageReply    "<f"
GET_CURRENT = 0x42    # () -> CurrentReply    "<f"
ERROR = 0xEE          # kartın kendisinin gönderdiği ErrorReply "<B"

# proto::State, telemetriyi okunur yazdırmak için
STATE_NAMES = {
    0: "SETUP",
    1: "IDLE",
    2: "WALK",
    3: "SHUTDOWN",
    4: "FAULT",
    5: "OFF",
}


class Protocol:

    def __init__(self, port: str, baud: int, timeout=0.1):
        self.ser = serial.Serial(port, baud, timeout=timeout)

    def close(self):
        self.ser.close()

    @staticmethod
    def crc16(data: bytes) -> int:
        crc = 0xFFFF
        for b in data:
            crc ^= b << 8
            for _ in range(8):
                crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
                crc &= 0xFFFF
        return crc

    def send(self, opcode: int, data: bytes = b""):
        length = len(data)  # yük uzunluğu; opcode sayılmaz

        frame = bytearray()
        frame.append(SOF)
        frame.append(length)
        frame.append(opcode)
        frame.extend(data)

        crc = self.crc16(bytes([length, opcode]) + data)
        frame.append(crc & 0xFF)         # CRC düşük bayt
        frame.append((crc >> 8) & 0xFF)  # CRC yüksek bayt

        self.ser.write(frame)

    def read_frame(self):
        """Geçerli tek bir çerçeve için bekleyen alıcı. (opcode, yük) ya da None döndürür."""
        # Çerçeve başlangıcına senkronize ol
        while True:
            b = self.ser.read(1)
            if not b:
                return None
            if b[0] == SOF:
                break

        length = self.ser.read(1)
        if not length:
            return None
        length = length[0]
        if length > MAX_PAYLOAD:  # olanaksız uzunluk -> vazgeç, çağıran tekrar dener
            return None

        opcode = self.ser.read(1)
        if not opcode:
            return None
        opcode = opcode[0]

        payload = self.ser.read(length)
        if len(payload) != length:
            return None

        crc_bytes = self.ser.read(2)
        if len(crc_bytes) != 2:
            return None

        rx_crc = crc_bytes[0] | (crc_bytes[1] << 8)
        calc_crc = self.crc16(bytes([length, opcode]) + payload)
        if rx_crc != calc_crc:
            return None

        return opcode, payload


def describe(opcode: int, data: bytes) -> str:
    """Bir yanıt çerçevesi için okunabilir tek satırlık özet."""
    if opcode == GET_TELEMETRY and len(data) == 21:
        state, ox, oy, oyaw, volts, amps = struct.unpack("<Bfffff", data)
        name = STATE_NAMES.get(state, f"?{state}")
        return (f"[{name:8}] odom=({ox:7.1f}, {oy:7.1f}) mm  "
                f"yaw={oyaw:6.1f} deg  {volts:5.2f} V  {amps:5.2f} A")
    if opcode in (GET_VOLTAGE, GET_CURRENT) and len(data) == 4:
        (value,) = struct.unpack("<f", data)
        unit = "V" if opcode == GET_VOLTAGE else "A"
        return f"{value:.2f} {unit}"
    if opcode == ERROR and len(data) == 1:
        return f"ERROR status=0x{data[0]:02X}"
    return f"opcode=0x{opcode:02X} data={data.hex()}"


if __name__ == "__main__":

    proto = Protocol(PORT, BAUD_RATE)
    print(f"Polling telemetry on {PORT} @ {BAUD_RATE} baud (Ctrl-C to stop)...")

    try:
        next_tick = time.monotonic()

        while True:

            proto.send(GET_TELEMETRY)
            frame = proto.read_frame()
            if frame is not None:
                print(describe(*frame))
            else:
                print("(no reply)")

            next_tick += PERIOD
            sleep_time = next_tick - time.monotonic()
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        proto.close()
