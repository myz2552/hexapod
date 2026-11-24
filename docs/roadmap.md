# Yol Haritası

```text
Faz 1A  Elektronik devreye alma ve tek bacak
  ↓
Faz 1B  Tam platform ve ayakta durma
  ↓
Faz 1C  Yürüyüş ve tripod / wave karşılaştırması
  ↓
Faz 2A  Kamera + YOLO
  ↓
Faz 2B  PUSH / AVOID
  ↓
Faz 2C  Belirsiz durumda fiziksel doğrulama
  ↓
Faz 2D  Deneysel karşılaştırma
```

Faz 1'de firmware, yürüyüş ve IK upstream'den hazır gelir (bkz. [architecture.md](architecture.md)). Faz 1'in işi doğru kurulum, kalibrasyon, ölçüm ve karşılaştırmadır.

## Faz 1A – Elektronik Devreye Alma ve Tek Bacak

Donanım: Raspberry Pi 5, Servo 2040, 3 × MG996R, 3 × F686ZZ, 6 V laboratuvar güç kaynağı. Adımlar: [setup.md](setup.md), bağlantılar: [wiring.md](wiring.md).

- Servo 2040'ın "Separate USB and Ext. Power" izini kes.
- Firmware'i derle ve Servo 2040'a yükle.
- Pi'de UART'ı aç, Pi ↔ Servo 2040 UART kablolamasını yap.
- `python -m software.bringup telemetry` ile bağlantıyı doğrula.
- 18 servoyu bacaklara takmadan `controller/calibrate.py` ile kalibre et; `controller/hexapod/config/config.yml` dosyasını commit et.
- front_right bacağını monte et (kanal 0–2), F686ZZ yataklamasını test et.
- Bacağın hareket yönlerini ve trim değerlerini laboratuvar güç kaynağıyla kontrol et.

Geçiş ölçütü: Kart telemetri veriyor, 18 servonun darbe kalibrasyonu `controller/hexapod/config/config.yml` içinde kayıtlı, test bacağı doğru yönlerde hareket ediyor.

## Faz 1B – Tam Platform ve Ayakta Durma

- 6 bacağı ve 18 servoyu monte et; kanal atamasını [wiring.md](wiring.md#servo-kanal-ataması) tablosuna göre yap.
- `battery_mount` yuvalarını Hobbywing UBEC'lere göre uyarla (`hardware/CAD/modified/`).
- Güç sistemini kur: 2S LiPo, 25 A sigorta, UBEC S (6,0 V), UBEC P (5,0 V).
- Robot destek üzerindeyken ayağa kalkmayı dene, `hardware.direction` ve `hardware.trim` değerlerini düzelt.
- Yerde ayağa kalk, en yüksek akımı ve voltaj düşümünü kaydet (`software.bringup stand --log`).
- Kamera yuvasını ve ön itme tamponunu tasarla.

Geçiş ölçütü: Robot bataryayla ayağa kalkıp kararlı şekilde ayakta durabiliyor ve oturabiliyor; akım ve voltaj kaydı var.

## Faz 1C – Yürüyüş ve Karşılaştırma

- Tripod ve wave yürüyüşünü düz zeminde dene.
- İleri yürüme, dönüş ve durma.
- Aynı mesafe için hız, yanal sapma, ortalama/tepe akım ve enerji tüketimi ölçümü (`software.bringup walk --log`).
- Tripod ve wave karşılaştırma raporu (`experiments/walking/`).
- Ripple yürüyüşü firmware'de hazırdır; ek karşılaştırma olarak eklenebilir.

Geçiş ölçütü: Robot iki yürüyüş tipiyle tekrarlanabilir şekilde yürüyor, dönüyor ve duruyor; karşılaştırma verisi kayıtlı.

## Faz 2A – Kamera + YOLO

- Kamerayı yerleştir ve görüntü akışını çalıştır.
- Veri setini hazırla ve YOLO modelini eğit (model sürümü ve veri seti boyutu TBD).
- YOLO'nun Pi 5 üzerinde yürüyüşle birlikte çalışırken hızını ölç. Yürüyüş Servo 2040'ta çalıştığı için YOLO yükü yürüyüşün zamanlamasını etkilemez; yalnızca heartbeat'lerin 500 ms içinde gitmesi gerekir.

Veri setinde yalnızca `obstacle` şeklinde tek sınıf kullanılmamalıdır. En azından nesne sınıfları ayrı tutulmalıdır, örneğin:

```text
cardboard_box
plastic_bottle
sponge
brick
books
fixed_structure
```

## Faz 2B – PUSH / AVOID

Robot şu davranışları gerçekleştirmelidir:

| Durum | Davranış | Controller komutu |
| --- | --- | --- |
| Engel yok | FORWARD | `set_velocity(vx, 0, 0)` |
| İtilebilir | PUSH (ön gövde/tamponla iterek ilerleme) | düşük `vx` |
| İtilemez | AVOID (etrafından dolaşma) | dönüş ve yanal hız |
| Güvenli hareket mümkün değil | STOP/BACK | `stop()` veya negatif `vx` |

## Faz 2C – Belirsiz Durumda Fiziksel Doğrulama

```text
Düşük hızlı gövde teması
  ↓
Servo 2040 akımı + IMU + odometri
  ↓
PUSH / AVOID
```

Servo 2040 akım ölçümünün yeterliliği (gerekirse harici INA226 / INA260), IMU modeli ve PUSH/AVOID eşikleri deneylerden sonra belirlenecektir.

## Faz 2D – Deneysel Karşılaştırma

Şunlar raporlanacaktır:

- Detection accuracy
- Decision accuracy
- Push success
- Avoidance success
- Traversal time
- False push decision
