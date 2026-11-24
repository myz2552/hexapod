# Controller (Raspberry Pi tarafı)

> **Kaynak:** Bu klasör [ggldnl/H-0996-Controller](https://github.com/ggldnl/H-0996-Controller) deposunun `103f3c3` commit'inden alınmıştır. Lisansı GPL-3.0'dır (bkz. [LICENSE.md](LICENSE.md)).
> **Yaptığımız değişiklikler:** Kod satırlarına dokunulmadı. Kod içi yorumlar, docstring'ler, `hexapod/config/config.yml` açıklamaları ve bu README Türkçeye çevrildi; yollar bu repoya göre düzenlendi. Robotumuza özel değerler `hexapod/config/config.yml` içinde tutulur.

Bu klasör, robotun Raspberry Pi tarafındaki Python controller'ını içerir.

Servo 2040 kartı tüm kontrol döngüsünü (sonlu durum makinesi, yürüyüş üreteci ve inverse kinematics) çalıştırır. Bu controller seri bağlantıyı açar, bağlanırken kartı robotun yapılandırmasıyla ayarlar (provisioning), ardından yüksek seviyeli hedef değerler (hız, yürüyüş tipi, gövde pozu) gönderir ve telemetri okur. Böylece çerçeveleme ve taşıma katmanıyla hiç uğraşmamız gerekmez. Hat protokolü, firmware'deki `firmware/src/communication/protocol.hpp` dosyasının elle yapılmış bir kopyasıdır; iki tarafın uyumlu kaldığı testlerde C++ kodlayıcısına karşı bayt bayt kontrol edilir.

## 🗂️ Klasör düzeni

```
hexapod/
  protocol.py       # opcode'lar, enum'lar, struct yük formatları (firmware'in kopyası)
  framing.py        # CRC-16/CCITT, encode_frame, FrameParser
  transport.py      # Transport arayüzü + SerialTransport (pyserial)
  client.py         # HexapodClient, üst seviye API
  config/
    config.yml      # bağlanırken karta gönderilen robot tanımı (bizim robotumuzun ayarları)
calibrate.py        # ayrı çalışan, servo başına darbe genişliği kalibrasyon aracı
demo.py             # zamanlanmış donanım demosu
tests/              # saf Python testleri (donanım ve pyserial gerekmez)
```

## 🛠️ Kurulum

Başlamadan önce [Servo 2040 kurulumunu](../firmware/README.md) tamamlayın.

### Seri arayüzü açma

Pi'nin Servo 2040 ile konuşabilmesi için seri arayüzü açmamız gerekir. Aşağıdakiler işletim sistemine ve sürümüne göre değişebilir.

- Raspberry Pi OS'ta:
    ```bash
    sudo raspi-config
    ```
    `Interface Options` > `Serial` menüsüne gidin, seri konsolu (login shell) kapatın, donanım portunu açın ve yeniden başlatın. Pi 5 için ek ayarlar: [docs/setup.md](../docs/setup.md).
- Ubuntu 24.04'te işlem daha uzundur:
  - `/boot/firmware/config.txt` dosyasını düzenleyin:
    ```bash
    # UART'ı aç
    enable_uart=1
    ```
    Pi 5'te Bluetooth artık ana UART'ı paylaşmaz (Pi 4'ün aksine), bu yüzden Bluetooth'u kapatmak genellikle gerekmez.
  - Ubuntu varsayılan olarak seri portu konsol olarak kullanır. Kapatın:
    ```bash
    sudo systemctl disable serial-getty@ttyAMA0.service
    sudo systemctl stop serial-getty@ttyAMA0.service
    ```
  - Çekirdek komut satırından konsol tanımlarını kaldırın:
    ```bash
    sudo cp /boot/firmware/cmdline.txt /boot/firmware/cmdline.txt.bak
    sudo sed -i -E 's/\bconsole=(serial[0-9]+|ttyAMA[0-9]+|ttyS[0-9]+)[^[:space:]]*[[:space:]]*//g' /boot/firmware/cmdline.txt
    # veya elle düzenleyin: sudo nano /boot/firmware/cmdline.txt
    ```
  - Kullanıcınızı `dialout` grubuna ekleyin:
    ```bash
    sudo usermod -aG dialout $USER
    ```
  - Yeniden başlatın:
    ```bash
    sudo reboot
    ```

### Paket kurulumu

Controller standart bir Python paketidir. İki isteğe bağlı ek vardır: `serial` gerçek donanımla konuşmak için pyserial'i, `calibrate` kalibrasyon aracı için ruamel.yaml'ı kurar. Kalibrasyon aracı ayrıca klavye için `sshkeyboard` kullanır. Repo kökünden hepsini kurmak için:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` paketi düzenlenebilir modda kurar (`pip install -e ./controller[serial,calibrate]`). Böylece `hexapod/config/config.yml` dosyası repodaki dosyadır; kalibrasyon aracının yazdığı değerler doğrudan repoya kaydedilir.

İstemcinin kendisi bu eklerin hiçbirine ihtiyaç duymaz: kullandığınız taşıyıcı gerçek seri port olmadığı sürece `hexapod`'u içe aktarıp kartı sürmek için `pip install -e ./controller` yeterlidir.

## 🚀 Kullanım

Bağlantıyı açın ve kartı config'ten yapılandırın, sonra sürün:

```python
from hexapod import connect, GaitId

bot = connect()                 # seri portu açar ve config.yml'den yapılandırır
bot.enable()                    # ayağa kalk
bot.set_gait(GaitId.TRIPOD)
bot.set_velocity(120, 0, 0)     # vx, vy mm/s, yaw derece/s
print(bot.get_telemetry())      # durum, odometri, voltaj, akım
bot.shutdown()                  # otur
```

Kart 500 ms boyunca komut veya heartbeat almazsa kendiliğinden oturur; uzun süren döngülerde `bot.heartbeat()` çağırmayı unutmayın.

`connect()` seri portu ve baud hızını config'ten okur, her bölümü hat sırasıyla gönderir ve kullanıma hazır bir istemci döndürür. Gerektiğinde farklı bir config dosyası veya port verin; kart zaten yapılandırılmışsa yapılandırmayı atlayın:

```python
bot = connect(config="baska_robot.yml", port="/dev/ttyAMA0", baud=921600)
bot = connect(provision=False)
```

Config mekanizması olmadan yalnızca taşıyıcıyı istiyorsanız istemciyi doğrudan oluşturun:

```python
from hexapod import HexapodClient, SerialTransport

bot = HexapodClient(SerialTransport("/dev/ttyAMA0", 921600))
```

Hazır komut satırı araçları için repo kökündeki [software/bringup.py](../software/README.md) dosyasına bakın (`telemetry`, `stand`, `walk`).

## 🎛️ Kalibrasyon

`calibrate.py`, her servonun min, orta ve max darbe genişliklerini bulmak için servoları tek tek oynatan ayrı bir araçtır ve sonucu `config.yml` içinde `hardware.pulses` altına yazar. Dosyanın yorumlarını ve düzenini korumak için ruamel.yaml ile yazar; bu yüzden `serial` ve `calibrate` eklerinin kurulu olması gerekir. Kart bağlıyken ve robot enerjisizken (OFF durumunda) çalıştırın:

```bash
python controller/calibrate.py                     # paketteki config.yml'yi kullanır
python controller/calibrate.py --channels 0 1 2    # yalnızca front_right bacağı
python controller/calibrate.py --config baska_robot.yml --port /dev/ttyAMA0
```

Tuşlar ve adımlar için bkz. [docs/setup.md](../docs/setup.md#6-servo-kalibrasyonu).

## 🧪 Testler

```bash
./tests/run.sh        # saf Python, donanım ve pyserial gerekmez
```

Testler çerçevelemeyi (CRC ve firmware kodlayıcısından alınmış referans çerçeveler) ve istemciyi (yanıtsız komutlar, sorgular, hata yönetimi) gerçek hat protokolünü konuşan sahte bir karta karşı çalıştırır.

## 🤝 Kaynak

Controller'ın yazarı ggldnl'dir. Proje hakkında daha fazla bilgi için [ana H-0996 deposuna](https://github.com/ggldnl/H-0996) bakın.
