# Donanım

## Kesinleşmiş Donanım

| Bileşen | Görev | Not |
| --- | --- | --- |
| Raspberry Pi 5 | Ana bilgisayar | YOLO, karar, IK, gait ve sensör okuma |
| MG996R 180° | Eklem servosu | Positional servo; Coxa / Femur / Tibia |
| PCA9685 | Servo PWM kontrolü | I2C ile kontrol edilen 16 kanallı PWM kontrol kartı. "Servo driver" olarak anılsa da servolara güç sağlamaz, yalnızca PWM sinyali üretir. |
| F686ZZ | Servo yataklama rulmanı | Servo karşı tarafında eksen desteği |
| M3 vidalar | Montaj | |
| M3 heat-set insert | 3B baskı parçalara diş | |
| Harici 6 V servo güç sistemi | Servo beslemesi | Ayrı yüksek akım hattı; GND Raspberry Pi 5 ile ortak |

İlk sürümde ESP32 ve Servo2040 kullanılmayacaktır.

## Adetler

| Bileşen | Tek bacak prototipi | Tam robot |
| --- | --- | --- |
| MG996R 180° | 3 | 18 |
| PCA9685 | 1 | 2 |
| F686ZZ | 3 | 18 |
| Raspberry Pi 5 | 1 | 1 |

İlk tek bacak testlerinde servo güç kaynağı olarak laboratuvar güç kaynağı kullanılacaktır.

## TBD (Henüz Kesinleşmemiş)

| Bileşen | Durum |
| --- | --- |
| Kamera modeli | TBD |
| IMU modeli | TBD |
| Akım sensörü modeli | TBD — INA226 ve INA260 değerlendiriliyor, kesin karar verilmedi |
| Batarya (tip ve kapasite) | TBD |
| Final güç dönüştürücü | TBD |

Bu parçalar deneyler ve güç ihtiyacı ölçümlerinden sonra belirlenecek ve [decisions.md](decisions.md) dosyasına kaydedilecektir.
