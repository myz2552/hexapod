"""
İstemci için bayt taşıyıcıları. İstemcinin yalnızca write() ve elinden geldiğince
çalışan bir read() fonksiyonuna ihtiyacı vardır; bu soyutlama sayesinde aynı istemci
gerçek bir seri porta ya da simülasyonda süreç içi bir firmware köprüsüne bağlanabilir.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Transport(ABC):

    @abstractmethod
    def write(self, data: bytes) -> None:
        ...

    @abstractmethod
    def read(self, n: int) -> bytes:
        """En fazla n bayt döndürür; zaman aşımında daha azını (veya b'') döndürebilir."""
        ...

    def close(self) -> None:
        pass


class SerialTransport(Transport):
    """pyserial üzerinden Servo2040'a gerçek UART bağlantısı."""

    def __init__(self, port: str, baud: int, timeout: float = 0.02) -> None:
        import serial  # paket pyserial olmadan da çalışsın diye geç içe aktarılır
        self._ser = serial.Serial(port, baud, timeout=timeout)

    def write(self, data: bytes) -> None:
        self._ser.write(data)

    def read(self, n: int) -> bytes:
        # pyserial'in read(n) fonksiyonu ancak tam n bayt geldiğinde erken döner; kartın
        # gönderdiğinden fazlasını istemek, hiç gelmeyecek baytları beklerken tüm zaman
        # aşımını harcar. Bunun yerine tamponda olanı al; yalnızca tampon boşken tek bir
        # bayt için bekle
        waiting = self._ser.in_waiting
        if waiting:
            return self._ser.read(min(n, waiting))
        return self._ser.read(1)

    def close(self) -> None:
        self._ser.close()
