# Yol Haritası

```text
Faz 1A  Tek Bacak Prototipi
  ↓
Faz 1B  Tam Mekanik Platform
  ↓
Faz 1C  Yürüyüş Kontrolü
  ↓
Faz 2A  Kamera + YOLO
  ↓
Faz 2B  PUSH / AVOID
  ↓
Faz 2C  Belirsiz durumda fiziksel doğrulama
  ↓
Faz 2D  Deneysel karşılaştırma
```

## Faz 1A – Tek Bacak Prototipi

Donanım: 1 × Raspberry Pi 5, 1 × Servo 2040, 3 × MG996R 180°, 3 × F686ZZ. Servolar laboratuvar güç kaynağından (6 V) beslenir. Bağlantılar: [wiring.md](wiring.md).

- [ggldnl/Hexapod-Hardware](https://github.com/ggldnl/Hexapod-Hardware) mekanik tasarımını referans al ([cad-reference.md](cad-reference.md)).
- Tek bacak parçalarını üret.
- 3 MG996R monte et.
- F686ZZ rulmanlı servo yataklamasını test et.
- Servo 2040'ın "Separate USB and Ext. Power" izini kes ve Raspberry Pi 5'e USB ile bağla.
- Servo 2040 için MicroPython firmware'i ve seri komut protokolünü yaz.
- `software/hardware` altına Servo 2040 çıkış sürücüsünü ekle; `software/servo_test` araçlarını ve kalibrasyon şemasındaki `board` alanını Servo 2040'a uyarla.
- Servoları çıkış 1 (Coxa) / 2 (Femur) / 3 (Tibia) olarak ata.
- Servo yönlerini belirle.
- Nötr açıları belirle.
- Güvenli min/max açıları belirle.
- Değerleri `config/servo_calibration.example.yaml` formatında kaydet.
- Tek bacak inverse kinematics (IK) geliştir.
- XYZ hedeflerini fiziksel olarak doğrula.

Faz 1A geçiş ölçütü: Tek bacak seçilen XYZ koordinatlarına güvenli ve tekrarlanabilir şekilde ulaşabilmelidir.

## Faz 1B – Tam Mekanik Platform

- 6 bacak üret.
- 18 servo monte et.
- Kanal atamasını [wiring.md](wiring.md) tablosuna göre yap.
- Raspberry Pi 5 + Servo 2040 montaj plakasını oluştur.
- Kamera yuvasını oluştur (kamera modeli TBD).
- Güç sistemini kur: 2S LiPo, sigorta, anahtar, 2 × UBEC (6 V servo, 5 V Pi).
- İlk ayağa kalkmada Servo 2040 akım ölçümünü kaydet; 10 A sınırına göre güç bölme gereğini değerlendir.
- Yürüyüş akımına göre batarya kapasitesini kesinleştir.
- Ön itme tamponunu tasarla.

## Faz 1C – Yürüyüş Kontrolü

- 18 servo calibration
- 6-leg IK
- Tripod gait
- İleri yürüme
- Dönüş
- Durma
- Hız ve yanal sapma ölçümü

Ripple gait zorunlu değildir; ek karşılaştırma olarak tutulabilir.

## Faz 2A – Kamera + YOLO

- Kamerayı yerleştir ve görüntü akışını çalıştır.
- Veri setini hazırla ve YOLO modelini eğit (model sürümü ve veri seti boyutu TBD).

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

| Durum | Davranış |
| --- | --- |
| Engel yok | FORWARD |
| İtilebilir | PUSH (ön gövde/tamponla iterek ilerleme) |
| İtilemez | AVOID (etrafından dolaşma) |
| Güvenli hareket mümkün değil | STOP/BACK |

## Faz 2C – Belirsiz Durumda Fiziksel Doğrulama

```text
Düşük hızlı gövde teması
  ↓
Servo akımı + IMU + ilerleme
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
