# Yazılım Kurulumu ve Devreye Alma

Robotun kontrol döngüsü (durum makinesi, yürüyüş üreteci, inverse kinematics) Servo 2040 üzerinde, [firmware/](../firmware/README.md) klasöründeki kodla çalışır. Raspberry Pi 5, [controller/](../controller/README.md) klasöründeki istemciyle karta yüksek seviyeli komutlar gönderir (hız, yürüyüş tipi, gövde pozu) ve telemetri okur.

| Klasör | Kaynak | Lisans |
| --- | --- | --- |
| `firmware/` | ggldnl/H-0996-Firmware, `163eb03` | GPL-3.0 |
| `controller/` | ggldnl/H-0996-Controller, `103f3c3` | GPL-3.0 |
| `hardware/` | ggldnl/H-0996-Hardware, `5d695c1` | CERN-OHL-W-2.0 |

Kod satırları upstream ile aynıdır; yorumlar ve README'ler Türkçeye çevrilmiştir. Robotumuza özel ayarlar (bacak ölçüleri, kanal ataması, servo kalibrasyonu, güvenlik sınırları) `controller/hexapod/config/config.yml` dosyasındadır.

## 1. Repoyu klonlama

```bash
git clone https://github.com/myz2552/hexapod.git
cd hexapod
```

## 2. Raspberry Pi 5 ayarları

UART'ı açın ve seri konsolu kapatın:

```bash
sudo raspi-config
# Interface Options > Serial Port
#   Login shell over serial?   → No
#   Serial port hardware?      → Yes
```

`/boot/firmware/config.txt` dosyasının sonuna ekleyin:

```ini
# GPIO14/15 üzerindeki UART0 (/dev/ttyAMA0). Pi 5'te varsayılan seri port hata ayıklama soketindedir.
dtparam=uart0=on
# Pi GPIO 5 V pinlerinden UBEC ile beslendiği için
usb_max_current_enable=1
```

Kullanıcıyı `dialout` grubuna ekleyip yeniden başlatın:

```bash
sudo usermod -aG dialout $USER
sudo reboot
```

Açıldıktan sonra `ls -l /dev/ttyAMA0` portu göstermelidir.

## 3. Python ortamı

Repo kökünden:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Bu komut `controller/` klasöründeki istemciyi (`hexapod` paketi) düzenlenebilir modda, ayrıca `pyserial`, `ruamel.yaml` ve kalibrasyon aracının klavye kütüphanesini kurar. Düzenlenebilir kurulum sayesinde robot config'i repodaki dosyadır; kalibrasyon aracı sonuçları doğrudan oraya yazar.

## 4. Firmware'i derleme ve yükleme

Derleme Raspberry Pi üzerinde ya da bir Linux bilgisayarda yapılabilir. Pico SDK ve Pimoroni kütüphaneleri repo dışında, yan yana durur:

```bash
sudo apt update
sudo apt install cmake gcc-arm-none-eabi build-essential

mkdir -p ~/pico && cd ~/pico
git clone https://github.com/raspberrypi/pico-sdk
(cd pico-sdk && git submodule update --init)
git clone https://github.com/pimoroni/pimoroni-pico
export PICO_SDK_PATH=~/pico/pico-sdk

cd <repo>/firmware
mkdir -p build && cd build
cmake ..
make
```

Sonuç `firmware/build/hexapod_firmware.uf2` dosyasıdır. Yüklemek için:

1. Servo 2040'ı USB-C ile bilgisayara veya Pi'ye bağlayın.
2. `BOOT/USER` düğmesini basılı tutarken `RESET`'e basın, ikisini bırakın. Kart `RPI-RP2` adlı bir sürücü olarak görünür.
3. `hexapod_firmware.uf2` dosyasını bu sürücüye kopyalayın. Kart yeniden başlar ve firmware çalışır.

USB kablosu yalnızca firmware yüklemek içindir. Çalışma sırasında kart Pi'ye UART ile bağlanır (bkz. [wiring.md](wiring.md)).

## 5. Bağlantı testi (servolar enerjilenmez)

```bash
python -m software.bringup telemetry
```

Beklenen çıktı: durum `OFF`, servo hattının voltajı ve akımı. `no reply` / zaman aşımı hatası alınırsa:

- TX ve RX kabloları ters olabilir.
- `/dev/ttyAMA0` yoktur veya seri konsol açıktır (2. adım).
- Kartta firmware yoktur (4. adım).

Firmware'in salt okunur test betiği de kullanılabilir: `python firmware/protocol_test.py`.

## 6. Servo kalibrasyonu

Her servonun -90° ve +90° konumlarını veren darbe genişlikleri tek tek ölçülür. Kalibrasyonu servolar bacaklara takılmadan, boştayken yapın.

```bash
python controller/calibrate.py               # 18 servo
python controller/calibrate.py --channels 0 1 2   # yalnızca front_right
```

| Tuş | İşlev |
| --- | --- |
| ↑ / w, ↓ / s | ince ayar ± |
| → / d, ← / a | kaba ayar ± |
| Enter | mevcut darbeyi kaydet (önce -90°, sonra +90°) |
| u / Backspace | son kaydı geri al |
| q / Esc | kaydet ve çık |

Araç sonuçları `controller/hexapod/config/config.yml` içindeki `hardware.pulses` alanına yazar. Dosyayı commit edin.

## 7. Montaj ve ilk ayağa kalkma

1. Servoları montaj videosundaki ([hardware/README.md](../hardware/README.md#-montaj-talimatları), `leg_assembly`) pozlara göre bacaklara takın. Kanal ataması: [wiring.md](wiring.md#servo-kanal-ataması).
2. Robotu bacakları havada kalacak şekilde bir desteğe koyun.
3. Ayağa kalkma komutunu verin:

   ```bash
   python -m software.bringup stand --seconds 5 --log runs/ilk_kalkis.csv
   ```

4. Bir eklem ters dönüyor ya da yanlış açıda duruyorsa `hardware.direction` ve `hardware.trim` değerlerini düzeltin. Değişikliği dosyada yorumla belirtin.
5. Robotu yere koyup tekrar deneyin. Komut bitince ekrana yazılan en yüksek akımı not edin; 10 A'e yakınsa [wiring.md](wiring.md) uyarılarına bakın.

## 8. Yürüyüş

```bash
python -m software.bringup walk --gait tripod --vx 60 --seconds 8 --log runs/tripod_60.csv
python -m software.bringup walk --gait wave   --vx 40 --seconds 8 --log runs/wave_40.csv
```

Firmware üç yürüyüş tipini destekler: `tripod`, `wave`, `ripple`. Hız sınırları ve adım parametreleri `controller/hexapod/config/config.yml` içindeki `gaits` ve `safety` bölümlerindedir. CSV kayıtları (`runs/` git'e girmez) deney sonuçlarıyla birlikte `experiments/walking/` altına özetlenir.

Controller'ın zamanlı demo betiği de çalışır: `python controller/demo.py`.

## Güvenlik davranışları (firmware)

- Kart 500 ms boyunca komut veya heartbeat almazsa robotu oturtur ve servoların gücünü keser.
- Toplam servo akımı `safety.current_max` (12 A) üstüne çıkarsa ya da servo hattı voltajı `safety.voltage_min` (5 V) altına düşerse kart `FAULT` durumuna geçer ve servoları keser.
- `software.bringup` Ctrl-C ile durdurulduğunda robotu oturtur.

## Upstream'den güncelleme almak

Upstream depolarda yeni bir sürüm çıkarsa değişiklikler elle aktarılır: upstream'deki farkı (`git diff <eski>..<yeni>`) inceleyin, kod değişikliklerini ilgili klasöre uygulayın, yeni yorumları Türkçeye çevirin ve README'deki kaynak commit'i güncelleyin. Firmware ve controller aynı protokol sürümünde olmalıdır; ikisini birlikte güncelleyin.

Aldığımız sürümde firmware'in kendi host testlerinin bir kısmı (`firmware/test/run.sh`, `test_robot`) upstream'de de başarısızdır; bu yüzden CI yalnızca controller testlerini ve bizim testlerimizi çalıştırır.
