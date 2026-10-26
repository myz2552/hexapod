# software/servo_test

PCA9685 üzerinden tek servo hareket testleri (CH0/CH1/CH2).

Faz 1A araçları Raspberry Pi 5 + PCA9685 + üç MG996R 180° içindir.
ESP32/Servo2040 kullanılmaz. Kod donanım üzerinde henüz doğrulanmamıştır.
IK/XYZ hareketleri bu klasörün kapsamında değildir; bkz. [single_leg](../single_leg/README.md).

## Safety

- Servolar Pi 5'in 5 V pininden **beslenmez**; harici **6.0 V yüksek akım** kaynağı gerekir.
- Pi GND, PCA9685 GND ve servo PSU GND ortak olmalıdır.
- İlk test bacak havada/yüksüz, çevresi boşken yapılmalıdır. Gerekirse bağlantıyı
  ayırın; 90° komutu bile bilinmeyen montajda mekanik stopa çarpabilir.
- Mekanik stop, sıkışma veya zorlanma/vızıltı varsa servo gücünü hemen kesin.
  Stall/buzz ile limit aramayın. Otomatik full-range sweep yapmayın.
- Varsayılan 60..120° yalnızca uç noktalardan uzak bir **komut korumasıdır**;
  ölçülmüş güvenli mekanik aralık değildir. İlk komut mevcut pozisyondan ani
  hareket yaratabilir; ardışık komutlar hız sınırlaması sağlamaz.
- `--allow-wide-range` 0..180° komutlarına izin verir; yalnızca fiziksel mekanik
  limitler doğrulandıktan sonra kullanın. İzin verilen her açı güvenli olmayabilir.
- PWM kapatıldığında aktif pozisyon tutma komutu bırakılır; bacak düşebilir.
  PWM release elektriksel güç kesme değildir. I2C arızası, zorla process sonlandırma
  veya güç kaybında yazılım cleanup garanti edilemez; PSU kapatma erişilebilir olsun.
- Bu araçlar PCA9685'in tüm çıkışlarını açılışta/çıkışta kapatır; kartı başka bir
  kontrol programıyla aynı anda kullanmayın. Kontrol testinde servo gücü kapalı olsun.

## Raspberry Pi setup

```bash
sudo raspi-config
```

Interface Options -> I2C -> Enable. Gerekirse yeniden başlatın.

```bash
sudo apt update
sudo apt install -y python3-venv i2c-tools
```

Repo kökünde:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
i2cdetect -y 1
```

Çoğu PCA9685 için varsayılan adres `0x40` olur; kart üzerindeki adres jumper'larını
kontrol edin. Adres değişmişse araçlara `--address 0x41` gibi aktarın.
[Adafruit Raspberry Pi kurulum rehberi](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi)
ve [PCA9685 API](https://docs.circuitpython.org/projects/pca9685/en/latest/api.html)
temel alınmıştır. Donanım bağımlılıkları yalnızca donanıma erişirken yüklenir;
`--help` için board/Adafruit kurulu olması gerekmez.

## Test order

Sanal ortam aktifken repo kökünden aşağıdaki klasöre geçin. Her komuttan sonra
sonucu gözlemleyip sonraki komutu ayrı çalıştırın; bu liste otomatik hareket dizisi değildir.
İlk kontrol sırasında servo PSU kapalı olsun. Hareket testlerinden önce PSU ve
mekanik kontrolünü tamamlayın. Her yeni bağlantıyı güç kapalıyken yapın.

```bash
cd software/servo_test
python check_pca9685.py
python test_single_servo.py --channel 0 --angle 90
python test_single_servo.py --channel 1 --angle 90
python test_single_servo.py --channel 2 --angle 90
python test_three_servos.py
python calibrate_servo.py coxa
python calibrate_servo.py femur
python calibrate_servo.py tibia
```

Repo kökünden alternatif paket çalıştırma: `python -m software.servo_test.check_pca9685`.
Kontrol aracı yalnızca tarama, başlatma ve PWM kapatma işlemleri yapar; servo açı
komutu göndermez. `--frequency` varsayılan 50 Hz'dir; servo testleri 50 Hz kullanır.
Tek servo `--hold` varsayılan 1 s; üç servo `--angles COXA FEMUR TIBIA`,
`--step-delay` (varsayılan 1 s), `--hold` (varsayılan 1 s) kabul eder.
Hareketten önce plan gösterilir ve Enter onayı istenir; `-y`/`--yes` onayı atlar.
Ctrl+C normal çıkışta olduğu gibi PWM cleanup çalıştırır. Başarı 0, hata 1,
argüman hatası 2, Ctrl+C 130 dönüş kodudur.

## Manual calibration

Kalibrasyon şema v2 kullanır (bkz. [software/hardware](../hardware/README.md#kalibrasyon-şeması-v2)).
Kart adresi ve kanal dosyadan okunur (`--leg`, varsayılan `test_leg`); çıktı dosyası yoksa
null değerli örnekten başlanır. Eklemi önce kinematik **sıfır pozuna**, sonra bilinen bir
**referans açıya** (`--ref-deg`, varsayılan +45) getirip işaretleyin; yön ve ölçek bu iki
pozdan hesaplanır. Sıfır pozu ve pozitif yön tanımı:
[kinematics README](../kinematics/README.md#eklem-açı-konvansiyonu-sıfır-pozu).

`--start 90 --step 2 --lower 60 --upper 120` varsayılandır. Başlangıç komutu
onaydan sonra gönderilir. Script sınırlar dışında hareket etmez, otomatik endpoint
aramaz. Daha geniş `--lower/--upper` ancak fiziksel gözlemle doğrulandığında seçilmelidir;
gerçek min/max limitlerini işaretlemek için genellikle gerekecektir.

```bash
python calibrate_servo.py femur --ref-deg 45 --lower 30 --upper 150
```

| Komut | Görev |
| --- | --- |
| `+`, `-` | Bir step artır/azalt |
| `g 95` | Belirtilen PWM komut açısına git |
| `z` | Mevcut komutu kinematik sıfır pozu olarak işaretle |
| `r` | Mevcut komutu referans pozu (`--ref-deg`) olarak işaretle |
| `l`, `u` | Mevcut komutu güvenli alt/üst limit olarak işaretle |
| `p` | İşaretleri ve türetilen yön/ölçeği göster |
| `s` | Doğrula ve YAML kaydet |
| `h` | Yardım |
| `q` | Çık ve PWM bırak |

İşaretler her oturumda boş başlar. Dört işaret tamamlanmadan, sıfır ve referans pozu
`l..u` içinde değilken veya iki poz 5 komut derecesinden yakınken kayıt yapılmaz. Varsayılan çıktı,
çalışma klasöründen bağımsız `config/servo_calibration.yaml` dosyasıdır;
`--output` ile değiştirilebilir. Diğer eklemlerin verileri korunur. YAML yeniden
yazılırken yorumlar/biçim korunmaz; veri yapısı korunur (kart adresleri ondalık yazılır: 0x40 = 64).
Aynı dosyaya eşzamanlı kalibrasyon yazmayın. `s` kullanılmadan çıkıldığında işaretler kaydedilmez.
Gerçek calibration dosyası gitignore içindedir; null değerli örnek git'te kalır.
Eski (v1: `servos`/`channels`) dosyalar reddedilir; yeniden kalibre edin.

Python scriptindeki `angle`, **servo PWM komut açısıdır**; doğrudan gerçek robot
joint angle anlamına gelmez. Adafruit Servo helper eşlemesi 750..2250 µs ve
180° actuation range kullanır. Bunlar kesin MG996R fiziksel limitleri değildir;
sıfır/referans pozu ölçümü bu farkı kalibrasyonda düzeltir.
[Servo helper API](https://docs.circuitpython.org/projects/motor/en/latest/api.html)
bu pulse eşlemesini açıklar.

Kalibrasyon sonrası XYZ denemesi: [software/single_leg](../single_leg/README.md).
Deneyleri [katkı rehberindeki](../../CONTRIBUTING.md) bilgilerle kaydedin.

## Wiring checklist

| Pi 5 fiziksel pin | PCA9685 |
| --- | --- |
| 1 (3.3V) | VCC (lojik) |
| 3 (SDA) | SDA |
| 5 (SCL) | SCL |
| 6 (GND) | GND |

CH0 Coxa, CH1 Femur, CH2 Tibia sinyalidir. Servo +/kartın servo V+ hattı
harici 6.0 V kaynaktan, servo GND harici PSU GND'den gelir. VCC ile V+ aynı
değildir; 6.0 V Pi pinlerine bağlanmaz. Kutupları, kart kanal pin sıralamasını,
ortak GND'yi ve güç kapatma erişimini enerjiden önce kontrol edin.
Ayrıntılar: [wiring](../../docs/wiring.md), [hardware](../../docs/hardware.md).

## Development validation

```bash
python -m compileall software
python -m unittest discover -s software -t . -v
```

Repo kökünden çalıştırılır; tüm yazılım testlerini kapsar (CI aynı komutu çalıştırır). Testler sahte I2C/PWM nesneleri ve geçici YAML
dosyaları kullanır; gerçek donanımı doğrulamaz.
