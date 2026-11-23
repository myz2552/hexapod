# Donanım

## Kesinleşmiş Donanım

| Bileşen | Görev | Not |
| --- | --- | --- |
| Raspberry Pi 5 | Ana bilgisayar | YOLO, karar, IK, gait ve sensör okuma |
| Pimoroni Servo 2040 | Servo PWM kontrolü | RP2040 tabanlı 18 kanallı servo kontrol kartı. Raspberry Pi 5'e USB ile bağlanır (seri haberleşme + kartın lojik beslemesi). Servo güç hattında akım ve voltaj ölçümü, 6 analog sensör girişi ve bir Qw/ST (I2C) konnektörü vardır. 62 × 42 × 12 mm, M2.5 montaj delikleri. |
| MG996R 180° | Eklem servosu | Positional servo; Coxa / Femur / Tibia |
| UBEC 10 A (2S–6S giriş, 5/6 V seçilebilir) | Güç dönüştürücü | Aynı modelden 2 adet: biri 6,0 V (servolar), biri 5,0 V (Raspberry Pi 5). Örnek: Hobbywing UBEC 10A 2-6S (10 A sürekli / 20 A tepe). |
| 2S LiPo, XT60 | Batarya | Kapasite deneylerden sonra kesinleşecek; başlangıç önerisi 5000 mAh, ≥ 25C |
| F686ZZ | Servo yataklama rulmanı | Servo karşı tarafında eksen desteği |
| M3 vidalar | Montaj | |
| M3 heat-set insert | 3B baskı parçalara diş | |

ESP32 kullanılmayacaktır. PCA9685 tabanlı tasarımdan Servo 2040'a geçiş gerekçesi için bkz. [decisions.md](decisions.md).

## Güç Sistemi Parçaları

| Parça | Önerilen özellik | Not |
| --- | --- | --- |
| Sigorta | 25 A bıçak sigorta + hat içi yuva | Bataryadan hemen sonra |
| Ana anahtar | ≥ 30 A | Kolay erişilebilir yerde |
| Dağıtım | XT60 Y-ayırıcı kablo | Ayrı dağıtım kartı gerekmez |
| Kondansatör | 2200 µF, ≥ 16 V elektrolitik | Servo 2040 servo güç klemenslerine |
| Pi güç kablosu | Açık uç → USB-C erkek güç kablosu | 5 V UBEC'i Pi'nin USB-C girişine bağlar; ters takılamaz |
| USB kablosu | USB-A → USB-C, 15–20 cm | Raspberry Pi 5 ↔ Servo 2040 |
| LiPo voltaj alarmı | 2S | Aşırı deşarjı önler |

## Adetler

| Bileşen | Tek bacak prototipi | Tam robot |
| --- | --- | --- |
| MG996R 180° | 3 | 18 |
| Servo 2040 | 1 | 1 |
| UBEC 10 A | — (laboratuvar güç kaynağı) | 2 (+1 yedek önerilir) |
| 2S LiPo | — | 1 |
| F686ZZ | 3 | 18 |
| Raspberry Pi 5 | 1 | 1 |

İlk tek bacak testlerinde servo güç kaynağı olarak laboratuvar güç kaynağı (6 V) kullanılacaktır; Servo 2040'ın lojik beslemesi USB üzerinden Raspberry Pi 5'ten gelir.

## TBD (Henüz Kesinleşmemiş)

| Bileşen | Durum |
| --- | --- |
| Kamera modeli | TBD |
| IMU modeli | TBD — Servo 2040'ın Qw/ST konnektörüne veya Pi'nin I2C hattına bağlanabilir |
| Akım ölçümü | Servo 2040'ın kart üstü akım ölçümü öncelikli değerlendirilecek. Faz 2C kontrollü temas için çözünürlüğü ve örnekleme hızı yetmezse harici sensör (INA226 / INA260) eklenecek; deneylerden sonra belirlenecek |
| Batarya kapasitesi | TBD — yürüyüş akımı ölçüldükten sonra |
| Ayak temas sensörleri | TBD — isteğe bağlı; Servo 2040'ın 6 analog sensör girişine bağlanabilir |

Bu parçalar deneyler ve güç ihtiyacı ölçümlerinden sonra belirlenecek ve [decisions.md](decisions.md) dosyasına kaydedilecektir.
