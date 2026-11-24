# Donanım

Donanım upstream [H-0996-Hardware](https://github.com/ggldnl/H-0996-Hardware) malzeme listesiyle aynıdır; upstream'in özel PCB'si kullanılmaz. Farklar tablolarda "Upstream'den farkı" sütununda belirtilmiştir.

## Elektronik

| Bileşen | Adet | Görev | Upstream'den farkı |
| --- | --- | --- | --- |
| Raspberry Pi 5 | 1 | Ana bilgisayar: controller istemcisi, Faz 2'de kamera, YOLO, karar | — |
| Pimoroni Servo 2040 | 1 | RP2040 tabanlı 18 kanallı servo kartı. Upstream firmware ile durum makinesi, yürüyüş, IK, PWM, akım/voltaj ölçümü ve watchdog | — |
| MG996R 180° | 18 | Eklem servosu (Coxa / Femur / Tibia) | — |
| 2S LiPo (7,4 V), XT60 | 1 | Batarya | — |
| Hobbywing UBEC 10A V2-Car (HW30603003) | 1 | Servo hattı, **6,0 V**. Giriş 2–6S, 10 A sürekli / 15 A tepe, çıkış 6,0 / 7,4 / 8,4 V seçilebilir, açma/kapama anahtarı | Upstream: iki kanallı 8 A UBEC |
| Hobbywing UBEC 5A V2-Air (HW30607000) | 1 | Raspberry Pi 5 + Servo 2040 lojik, **5,0 V**. Giriş 2–8S, 5 A sürekli / 15 A tepe, çıkış 5,0 / 6,0 / 7,4 V seçilebilir | Upstream: iki kanallı 8 A UBEC |
| 25 A bıçak sigorta + kablolu yuva | 1 | Batarya ile UBEC girişleri arası koruma | Upstream'de yok; önerilir |

## Kablolama (PCB'siz kurulum)

| Parça | Not |
| --- | --- |
| XT60 erkek soket | Bataryayı UBEC girişlerine bağlar |
| 14 AWG ve 18–20 AWG silikon kablo, makaron | Güç hatları |
| Servo uzatma kabloları | Arka bacaklar Servo 2040'a yetişmez |
| Qw/ST (STEMMA QT) → dişi jumper kablo, dişi-dişi jumper kablolar | Pi ↔ Servo 2040 UART ve 5 V |
| USB-C veri kablosu | Yalnızca firmware yüklemek için |
| LiPo şarj cihazı (balanslı), 2S voltaj alarmı | Batarya bakımı |
| Multimetre | UBEC çıkışlarını bağlamadan önce ölçmek için |

## Mekanik

| Bileşen | Adet | Not |
| --- | --- | --- |
| 3B baskı parçalar | base 1, top_stiffeners 1, bottom_stiffeners 1, femur 6, tibia 6, bracket_A 18, bracket_B 18, servo_mod 18, battery_mount 1, electronics_mount 1 | PCB'siz kurulum için `electronics_mount` gerekir |
| F686ZZ rulman | 18 | Servo karşı tarafında eksen desteği |
| M3 vida | ~92 | |
| M3 heat-set insert | ~92 | Baskı delikleri Ø4,5 mm olduğu için OD 5 mm, L 4 mm kullanılır |
| M2 vida + M2 heat-set insert | birkaç adet | Servo 2040'ı `electronics_mount`'a sabitlemek için (montaj delikleri 2,7 mm) |

## Tek bacak testi

| Bileşen | Adet |
| --- | --- |
| Raspberry Pi 5 (kendi adaptörüyle) | 1 |
| Servo 2040 | 1 |
| MG996R + F686ZZ | 3 |
| Laboratuvar güç kaynağı, 6,0 V, ≥3 A | 1 |

## TBD (Henüz Kesinleşmemiş)

| Bileşen | Durum |
| --- | --- |
| Kamera modeli | TBD (Faz 2A) |
| IMU modeli | TBD — Servo 2040'ın Qw/ST soketi UART için kullanıldığından IMU Pi'nin I2C hattına bağlanır |
| Akım ölçümü | Servo 2040'ın kart üstü toplam akım ölçümü kullanılacak. Faz 2C kontrollü temas için yetmezse harici sensör (INA226 / INA260) eklenecek; deneylerden sonra belirlenecek |
| Batarya kapasitesi | İlk yürüyüş akımı ölçüldükten sonra değerlendirilecek |

Bu parçalar deneylerden sonra belirlenecek ve [decisions.md](decisions.md) dosyasına kaydedilecektir.
