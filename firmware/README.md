# Firmware (Servo 2040)

> **Kaynak:** Bu klasör [ggldnl/H-0996-Firmware](https://github.com/ggldnl/H-0996-Firmware) deposunun `163eb03` commit'inden alınmıştır. Lisansı GPL-3.0'dır (bkz. [LICENSE.md](LICENSE.md)).
> **Yaptığımız değişiklikler:** Kod satırlarına dokunulmadı. Yalnızca kod içi yorumlar ve bu README Türkçeye çevrildi; yollar bu repoya göre düzenlendi.

Bu klasör, hexapod'u süren Servo 2040 kartının firmware'ini içerir.

Servo 2040 tüm kontrol döngüsünü çalıştırır: sonlu durum makinesi (ayağa kalk / yürü / otur), yürüyüş üreteci ve inverse kinematics. Pi yalnızca yüksek seviyeli hedef değerler (hız, yürüyüş tipi, gövde pozu) gönderir ve telemetri okur. Pi tarafı istemcisi [controller/](../controller/README.md) klasöründedir.

Aşağıda kodun nasıl derlenip yükleneceği ve iki kart arasındaki haberleşme protokolünün nasıl çalıştığı anlatılmaktadır.

## 🗂️ Klasör düzeni

Her şey yalnızca başlık dosyalarından oluşan C++17 kodudur ve `src/` kökündedir; bu yüzden her include klasörünü gösterir (ör. `#include "core/robot.hpp"`).

```
src/
  main.cpp                    # giriş noktası: UART'ı boşalt -> işle -> çalıştır
  core/
    config.hpp                # geometri, yürüyüşler, pinler, sınırlar (derlenmiş varsayılanlar + yapılandırılabilir değerler)
    robot.hpp                 # durum makinesi ve robotun niyet API'si (enable/walk/pose ...)
    gait.hpp                  # ayak yörüngesi üreteci (sabit tempo, hıza göre ölçeklenen adım)
    kinematics.hpp            # bacak başına ileri/ters kinematik
    router.hpp                # çözülen çerçeveleri robot çağrısına çevirir, yanıtı oluşturur
  communication/
    protocol.hpp              # hat protokolü: opcode'lar, yük struct'ları, çerçeveleme (CRC + ayrıştırıcı)
    hardware.hpp              # robotun sürdüğü soyut donanım arayüzü (çekirdek test edilebilsin diye)
    servo2040_hal.hpp         # Pimoroni SDK'ya dokunan tek dosya (servolar, LED'ler, güç, ADC)
  utils/
    math.hpp                  # küçük geometri yardımcıları (Vec3, derece/radyan, kırpma, açı sarma)
test/                         # host tarafı testleri, saf C++ (kart yok, SDK yok) -> ./test/run.sh
protocol_test.py              # seri bağlantı testi (yalnızca pyserial)
```

`core/` altındaki her şey (ve `communication/protocol.hpp` ile `utils/`) SDK'dan bağımsızdır ve bilgisayarda sahte bir donanım arayüzüne karşı derlenir; host testleri bunu kullanır. Pico SDK/Pimoroni kütüphanelerini yalnızca `servo2040_hal.hpp` içerir.

## 🛠️ Derleme ve yükleme

Başlamadan önce Pimoroni'nin [şablon deposuna](https://github.com/pimoroni/pico-boilerplate?tab=readme-ov-file#before-you-start) göz atın; firmware bu şablondan başlatılmıştır.

En kolayı, SDK'yı ve Pimoroni kütüphanelerini tutan bir `pico` klasörü oluşturmaktır:

```
pico
├── pico-sdk
└── pimoroni-pico
```

Bu repo `pico` klasörünün dışında, istediğiniz yerde durabilir; derleme `PICO_SDK_PATH` üzerinden SDK'yı bulur.

### Derleme ortamını hazırlama

Gerekli paketleri kurun:

```bash
sudo apt update
sudo apt install cmake gcc-arm-none-eabi build-essential
```

### Pico SDK'yı indirme

Pico SDK'yı `pico` klasörüne indirin:

```bash
mkdir -p ~/pico && cd ~/pico
git clone https://github.com/raspberrypi/pico-sdk
cd pico-sdk
git submodule update --init
export PICO_SDK_PATH=`pwd`
cd ../
```

Bu şekilde tanımlanan `PICO_SDK_PATH` yalnızca o oturum boyunca geçerlidir. Kalıcı olması için `.bashrc` dosyanıza ekleyin:

```bash
echo 'export PICO_SDK_PATH="/path/to/pico-sdk"' >> ~/.bashrc
```

### Pimoroni kütüphanelerini indirme

Pimoroni kütüphanelerini `pico` klasörüne indirin:

```bash
git clone https://github.com/pimoroni/pimoroni-pico
```

`CMakeLists.txt`, bu klasörde bulunan `pico_sdk_import.cmake` ve `pimoroni_pico_import.cmake` dosyalarını içerir. Bunlar SDK'yı ve Pimoroni kütüphanelerini `PICO_SDK_PATH` ile bulur; varsayılan olarak `pimoroni-pico` klasörünün `pico-sdk` ile yan yana olmasını bekler. `PICO_SDK_PATH` tanımlamak istemiyorsanız ve VS Code kullanıyorsanız yolu `.vscode/settings.json` üzerinden CMake'e verebilirsiniz.

### Derleme

Repo içinde bu klasöre geçip bir derleme klasörü oluşturun ve derleyin:

```bash
cd <repo>/firmware
mkdir build
cd build
cmake ..
make
```

Bu işlem `build` klasöründe **`hexapod_firmware.uf2`** dosyasını üretir.

### Yükleme

- Servo 2040'ı USB-C ile bilgisayara bağlayın.
- `boot/user` düğmesini basılı tutarken `reset`'e basın, sonra ikisini de bırakın. Servo 2040 bir USB sürücüsü olarak görünür.
- `hexapod_firmware.uf2` dosyasını bu sürücüye sürükleyip bırakın. Kart yeniden başlar ve firmware'i çalıştırır.

Raspberry Pi üzerinde SSH ile derlediyseniz:

- Servo 2040'ı USB ile Pi'ye bağlayın.
- Yukarıdaki gibi boot moduna alın (`boot/user` + `reset`). Bir blok aygıt olarak görünür (`lsblk`).
- Yeni sürücüyü bulun (ör. `/dev/sda1`, `/media/<kullanıcı>/RPI-RP2` altına bağlanmış).
- `build` klasöründen `mv hexapod_firmware.uf2 /media/<kullanıcı>/RPI-RP2` komutunu çalıştırın. Kart yeniden başlar ve firmware'i çalıştırır.

## 🧪 Host testleri

Davranış katmanı SDK'dan bağımsız olduğu için bilgisayarda düz `g++` ile derlenip çalıştırılabilir (kart ve Pico SDK gerekmez):

```bash
./test/run.sh          # veya  CXX=clang++ ./test/run.sh
```

Bu komut her `test/test_*.cpp` dosyasını sahte bir donanım arayüzüne karşı derler ve kinematiği, yürüyüşü, durum makinesini ve protokol çerçevelemesini test eder.

> **Not:** Aldığımız sürümde `test_robot` testlerinin bir kısmı upstream'de de başarısızdır. Bu yüzden repomuzun CI'ı bu testleri çalıştırmaz.

Gerçek kart Raspberry Pi'ye bağlıysa, kartın çalışıp doğru yanıt verdiğini kontrol etmek için `protocol_test.py` betiğini çalıştırabilirsiniz. Betik yalnızca okuma yapar (telemetri/voltaj/akım); robotu asla etkinleştirmez ve servo oynatmaz.

Kartı bağlayın (bkz. [Bağlantı](#-bağlantı)), sonra Pi üzerinde:

```bash
pip install pyserial
python3 protocol_test.py
```

Saniyede birkaç kez `GetTelemetry` sorgusu gönderir ve çözülen yanıtı yazdırır:

```
Polling telemetry on /dev/ttyAMA0 @ 921600 baud (Ctrl-C to stop)...
[OFF     ] odom=(    0.0,     0.0) mm  yaw=   0.0 deg   7.42 V   0.03 A
[OFF     ] odom=(    0.0,     0.0) mm  yaw=   0.0 deg   7.41 V   0.03 A
...
```

`(no reply)` hiçbir yanıt gelmediği anlamına gelir. Genellikle sebebi TX/RX'in ters bağlanması, yanlış baud hızı ya da Pi'de seri portun açık olmamasıdır. Port ve baud dosyanın başındaki sabitlerdir (varsayılan config'e göre `PORT = "/dev/ttyAMA0"`, `BAUD_RATE = 921600`); farklıysa düzenleyin.

## 🔌 Bağlantı

Kart Pi ile UART üzerinden konuşur. Firmware **GP20 (TX) / GP21 (RX) üzerindeki UART1**'i kullanır (`cfg::UART_TX_PIN` / `cfg::UART_RX_PIN`); bu pinler Servo 2040'ın SDA/SCL (Qwiic) soketine çıkarılmıştır. Çapraz bağlayın (her tarafın TX'i diğerinin RX'ine gider) ve GND'yi ortak yapın:

| Raspberry Pi   | Servo2040        |
|----------------|------------------|
| 5V             | 5V               |
| GND            | GND              |
| GPIO14 (TXD)   | GP21 / SCL (RX)  |
| GPIO15 (RXD)   | GP20 / SDA (TX)  |

> TX/RX'i kartın üzerindeki baskıyla tekrar kontrol edin: firmware GP20'den gönderir, GP21'den alır. Yanıt gelmiyorsa en olası sebep TX/RX'in ters olmasıdır.

Bağlantı **921600 baud** hızında çalışır (`cfg::BAUD`).

Pi'de donanım UART'ını açın:

- `sudo raspi-config` > `Interface Options` > `Serial Port`
- Would you like a login shell over serial? > **No**
- Would you like the serial port hardware enabled? > **Yes**
- Kaydedip yeniden başlatın.

Robotumuza özel kablolama, güç bağlantıları ve Pi 5 ayarları için bkz. [docs/wiring.md](../docs/wiring.md) ve [docs/setup.md](../docs/setup.md).

## 📡 Haberleşme protokolü

### Çerçeve düzeni

Sıkı, HDLC tarzı bir çerçeve:

| SOF  | LEN | opcode | yük      | CRC lo | CRC hi |
|------|-----|--------|----------|--------|--------|
| 1B   | 1B  | 1B     | LEN B    | 1B     | 1B     |


| Alan    | Boyut | Açıklama                                                          |
|---------|-------|-------------------------------------------------------------------|
| SOF     | 1     | Çerçeve başlangıç işareti (`0xAA`)                                 |
| LEN     | 1     | Yalnızca yük uzunluğu. Opcode **sayılmaz** (`0..128`)             |
| opcode  | 1     | Komut tanımlayıcısı                                               |
| yük     | n     | Argümanlar (ikili, little-endian)                                 |
| CRC     | 2     | `LEN + opcode + yük` üzerinden CRC16-CCITT (polinom `0x1021`, başlangıç `0xFFFF`), little-endian |

Toplam çerçeve boyutu `LEN + 5`'tir. **Çerçeve sonu baytı yoktur**: çerçeveyi `LEN` sınırlar, CRC doğrular. CRC hatalıysa (veya `LEN` 128'den büyükse) alıcı çerçeveyi atar ve bir sonraki SOF'u arar. Çok baytlı tüm alanlar little-endian'dır; float'lar IEEE-754'tür.

### Mesaj türleri

Her opcode iki türden biridir:

- **Yanıtsız (fire-and-forget)**: yanıt yok. Hedef değerler ve yaşam döngüsü komutları. Her biri ayrıca bir komut watchdog'unu besler: kart hareket halindeyken `cfg::WATCHDOG_TIMEOUT_MS` (500 ms) boyunca hiçbir şey duymazsa kendiliğinden durur.
- **İstek/yanıt**: istekle **aynı opcode**'u taşıyan tam olarak bir yanıt çerçevesi (sorgular) ya da istek reddedildiyse veya hatalıysa bir `Error` çerçevesi (`0xEE`).

### Komut seti

Opcode'un üst dört biti onu amacına göre gruplar.

**Düşük seviye hata ayıklama (`0x0x`)**: istek/yanıt, `AckReply` (`<B` durum) ile onaylanır.

| İşlem | OpCode | Yük (`struct` formatı) | Yanıt |
|-----------|--------|--------------------------------|-----------|
| Jog Servo | `0x01` | `<BH` kanal, pulse_us (0=bırak) | AckReply |

**Yapılandırma (`0x1x`)**: istek/yanıt, onaylı. Pi bağlanırken tüm çalışma zamanı config'ini her mesajda bir bölüm olarak gönderir; hareket sırasında hiçbir şey yeniden yapılandırılmasın diye bunlar yalnızca enerji yokken (OFF/FAULT) kabul edilir.

| İşlem | OpCode | Yük (`struct` formatı) |
|-----------|--------|------------------------|
| Provision Body       | `0x10` | `<fffffff` uzuv uzunlukları, coxa ofseti, ayakta yükseklik, duruş yarıçapı, döngü süresi |
| Provision Mounts     | `0x11` | `<24f` bacak başına: x, y, z, yaw |
| Provision Direction  | `0x12` | `<18f` servo başına: +/-1       |
| Provision Trim       | `0x13` | `<18f` servo başına: trim derece   |
| Provision Ranges     | `0x14` | `<6f` eklem tipi başına: min, max derece |
| Provision Gaits      | `0x15` | `<12f` yürüyüş başına: duty, adım yüksekliği, max adım, örtüşme |
| Provision Limits     | `0x16` | `<ffffffff` hız sınırları, aşırı akım, düşük voltaj |
| Provision Body Pose  | `0x17` | `<12f` eksen başına: min, max    |
| Provision Servo Cal  | `0x18` | `<54H` servo başına: min, orta, max µs |
| Provision Pins       | `0x19` | `<18B` mantıksal kanal başına fiziksel pin |

**Hedef değerler ve yaşam döngüsü (`0x3x`)**: yanıtsız.

| İşlem | OpCode | Yük (`struct` formatı) |
|-----------|--------|------------------------|
| Set Velocity  | `0x30` | `<fff` vx, vy (mm/s), wz (derece/s) |
| Set Body Pose | `0x31` | `<ffffff` x, y, z (mm), roll, pitch, yaw (derece) |
| Set Gait      | `0x32` | `<B` yürüyüş kimliği (0 tripod, 1 wave, 2 ripple) |
| Enable        | `0x33` | yok; ayağa kalkar, IDLE'da biter |
| Shutdown      | `0x34` | yok; oturur, OFF'ta biter  |
| Stop          | `0x35` | yok; hızı sıfırlar (yumuşak durma) |
| Set LED       | `0x36` | `<BBBBf` mod, r, g, b, yanıp sönme frekansı |
| Heartbeat     | `0x37` | yok; canlı tutma, watchdog'u besler |

**Sorgular (`0x4x`)**: istek/yanıt; kart aynı opcode ile yanıtlar.

| İşlem | OpCode | Yanıt (`struct` formatı) |
|-----------|--------|----------------------|
| Get Telemetry | `0x40` | `<Bfffff` durum, odom x, odom y, odom yaw, voltaj, akım |
| Get Voltage   | `0x41` | `<f` volt   |
| Get Current   | `0x42` | `<f` amper    |
| Get Joints    | `0x43` | `<18f` servo uzayı açıları (derece), bacak öncelikli |

**Kartın başlattığı**

| İşlem | OpCode | Yük (`struct` formatı) |
|-----------|--------|------------------------|
| Error | `0xEE` | `<B` durum kodu |

Durum kodları: `0x00` reddedildi (yanlış durum), `0x01` OK, `0x02` erişilemez (IK erişim dışında), `0x03` hatalı opcode, `0x04` hatalı uzunluk.

### Durumlar

Telemetri durum makinesini (`proto::State`) bildirir:

| Değer | Durum    | Anlamı |
|-------|----------|---------|
| 0 | `SETUP`    | kalkış: ayağa kalkma animasyonu çalışıyor |
| 1 | `IDLE`     | ayakta, sıfır hız |
| 2 | `WALK`     | yürüyüş uyguluyor |
| 3 | `SHUTDOWN` | alçalma: oturma animasyonu çalışıyor |
| 4 | `FAULT`    | acil durdurulmuş (aşırı akım / düşük voltaj); toparlanmak için Enable gerekir |
| 5 | `OFF`      | enerjisiz bekleme, Enable bekliyor |

Ayağa kalkma ve oturma animasyonları kesilemez; yalnızca bir hata araya girebilir.

## 🧩 Mimari

`main.cpp`, sürekli iki iş yapan küçük bir zamanlayıcıdır:

1. **Haberleşme**: UART'ı boşaltır ve her baytı bir `proto::FrameParser`'a verir. CRC'si geçerli eksiksiz bir çerçeve geldiğinde `router::dispatch` onu `robot::Robot` niyet API'sine bir çağrıya çevirir (`enable()`, `set_velocity()`, `set_gait()`, ...) ve sorgularda bir yanıt çerçevesi geri yazar.
2. **Kontrol**: sabit `cfg::CONTROL_RATE_HZ` (50 Hz) adımında `robot.update(dt)` çağırır; bu fonksiyon durum makinesini ilerletir, yürüyüşü çalıştırır, IK'yi çözer ve 18 servo açısını donanım arayüzü üzerinden yazar.

Robot temiz bir kinematik çerçevede çalışır ve servo uzayına (yön/trim/kırpma, derece) yalnızca en sonda eşler. Bu davranış katmanının tamamı donanımla soyut `hw::Interface` üzerinden konuştuğu için bilgisayarda sahte bir uygulamayla derlenir ve test edilir. Kart gerektiren tek parça `servo2040_hal.hpp`'dir.

`config.hpp`'nin çoğu, kartı tek başına da tam çalışır hâle getiren derlenmiş varsayılanlardır; Pi'nin bağlanırken değiştirmesine izin verilen değerler (geometri, kinematik eşleme, yürüyüşler, sınırlar) yapılandırma opcode'larının atama yaptığı değiştirilebilir global değişkenlerdir.

### Yeni bir opcode ekleme

1. `protocol.hpp` içindeki `enum class Opcode`'a bir değer ekleyin (dört bitlik gruplara dikkat edin).
2. Veri taşıyorsa `#pragma pack` ile sıkıştırılmış bir yük `struct`'ı ve boyutunu sabitleyen bir `static_assert` ekleyin; Python `struct` formatını `// py:` yorumuna yazın.
3. Yanıt almıyorsa `kind_of()` içinde yanıtsız olarak listeleyin.
4. `router::dispatch` içinde işleyin (`len`'i doğrulayın, yükü çözün, robotu çağırın, yanıtı/onayı oluşturun).
5. İki uç birebir uyumlu kalsın diye opcode'u ve yük formatını Pi tarafındaki `hexapod` istemcisine ([controller/](../controller/README.md)) de ekleyin.

## 🤝 Kaynak

Firmware'in yazarı ggldnl'dir. Proje hakkında daha fazla bilgi için [ana H-0996 deposuna](https://github.com/ggldnl/H-0996) bakın.
