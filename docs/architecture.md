# Sistem Mimarisi

## Genel Sistem

```text
                   Kamera
                     │
                     ▼
             ┌────────────────┐
             │ Raspberry Pi 5 │
             │----------------│
             │ YOLO           │
             │ Decision       │
             │ IK             │
             │ Gait           │
             │ Sensor Reading │
             └───────┬────────┘
                     │ USB (seri + lojik 5 V)
                     ▼
             ┌────────────────┐
             │  Servo 2040    │──Qw/ST──► IMU (TBD)
             │----------------│
             │ PWM üretimi    │◄─ ayak sensörleri (isteğe bağlı)
             │ Akım / voltaj  │
             └───────┬────────┘
                     │ 18 kanal
                     ▼
                18 × MG996R
```

Raspberry Pi 5 tek ana bilgisayardır; YOLO, karar, inverse kinematics (IK), gait ve sensör okuma yazılımları üzerinde çalışır. Servo PWM sinyalleri, Pi'ye USB ile bağlı Servo 2040 kartının RP2040 işlemcisinde üretilir; Pi yalnızca servo komutlarını gönderir. Servo 2040 ayrıca servo güç hattının akımını ve voltajını ölçer. ESP32 kullanılmaz.

Kamera modeli ve IMU modeli henüz TBD'dir. Servo 2040'ın akım ölçümünün Faz 2C için yeterliliği deneyle belirlenecektir; yetmezse harici sensör (INA226 / INA260) eklenir. Bkz. [donanım](hardware.md).

## Faz 1A – Tek Bacak

```text
Raspberry Pi 5
  ↓ USB
Servo 2040
  ↓
3 × MG996R (çıkış 1 Coxa, 2 Femur, 3 Tibia)
  ↓
Servo calibration
  ↓
Inverse kinematics
  ↓
XYZ foot control
```

Tek bacak yalnızca Faz 1 mekanik ve IK doğrulaması için kullanılır. Bağlantılar için bkz. [wiring.md](wiring.md).

## Faz 1B – Tam Hexapod

```text
18 × MG996R
  ↓
1 × Servo 2040
  ↓
6-leg IK
  ↓
Tripod gait
  ↓
Walk / Turn / Stop
```

## Faz 2 – Algı ve Engel Kararı

```text
Kamera
  ↓
YOLO
  ↓
Nesne sınıfı + konumu
  ↓
Görsel itilebilirlik
  ↓
┌─────────────┬──────────────┐
│             │              │
PUSH        AVOID         BELİRSİZ
│             │              │
İt          Dolaş      Kontrollü temas
                           ↓
                      Akım + IMU
                           ↓
                      PUSH / AVOID
```

Belirsiz durumda robot ön tampon ile düşük hızlı kontrollü gövde teması yapar. Servo güç hattı akımı, IMU ve robotun ilerleme bilgisi birlikte değerlendirilerek PUSH veya AVOID kararı verilir. Güvenli hareket mümkün değilse robot STOP/BACK davranışı uygular.

Önceki "tek bacakla nesneye itme testi" mimarisi kaldırılmıştır (bkz. [decisions.md](decisions.md)).

## Modüller

### Mekanik Platform

Mekanik başlangıç noktası [ggldnl/Hexapod-Hardware](https://github.com/ggldnl/Hexapod-Hardware) tasarımıdır. MG996R montaj geometrisi, F686ZZ rulmanlı yataklama ve M3 vida / M3 heat-set insert yaklaşımı korunur. Raspberry Pi 5 + Servo 2040 montaj plakası, kamera yuvası, güç sistemi (batarya, iki UBEC) yerleşimi ve ön itme tamponu projeye göre yeniden tasarlanır. Bkz. [cad-reference.md](cad-reference.md).

### Güç ve Servo Elektroniği

Güç 2S LiPo'dan gelir ve aynı modelden iki UBEC ile ikiye ayrılır: 6,0 V hat Servo 2040 üzerinden 18 servoyu, 5,0 V hat Raspberry Pi 5'i besler. Servo akım darbeleri Pi'ye ulaşmaz. Servo 2040 servo güç hattının akımını ve voltajını ölçer; bu ölçüm hem aşırı akım korumasında hem de Faz 2C kontrollü temasta kullanılır. Ayrıntılar: [wiring.md](wiring.md).

### Hareket Kontrolü

Servo kalibrasyonu (yön, nötr açı, min/max), Coxa/Femur/Tibia IK, duruş ve tripod gait'i yönetir. Faz 2'de PUSH (gövdeyle itme), AVOID (dolaşma), kontrollü gövde teması ve STOP/BACK hareketleri eklenir.

### Kamera ve YOLO

Görüntü alır; nesne sınıfı, görüntüde konum ve algılama güveni üretir. YOLO algılama güveni doğrudan itilebilirlik olarak kullanılmaz; görsel itilebilirlik tahmini ayrıca oluşturulur. Veri seti tek bir `obstacle` sınıfı yerine ayrı nesne sınıfları içerir. YOLO modelinin son sürümü TBD'dir.

### Fiziksel Doğrulama

Yalnızca görsel karar belirsiz olduğunda çalışır. Ön tamponla düşük hızlı temas sırasında servo güç hattı akımı, IMU ve ilerleme verilerini kaydeder ve değerlendirir. Eşikler deneylerden sonra belirlenecektir.

### Karar

Görsel itilebilirlik tahmini yeterince güvenliyse doğrudan PUSH veya AVOID seçer; belirsizse fiziksel doğrulama sonucunu kullanır. Engel yoksa FORWARD devam edilir.

### Deney Kaydı

Servo açıları, hareket komutları, görsel tahmin, fiziksel doğrulama verileri, karar ve gerçek hareket sonucu ortak deneme kimliğiyle `experiments/` altında kaydedilir.

## Tasarım İlkeleri

- Faz 2'den önce ayakta durma ve yürüyüş doğrulanmalıdır.
- Servo yönleri, nötr açıları ve min/max limitleri fiziksel kalibrasyonla belirlenmeli ve belgelenmelidir; değerler uydurulmamalıdır.
- MG996R servolar Raspberry Pi'nin 5 V pininden beslenmemelidir.
- Görsel tahmin, fiziksel doğrulama ve hareket başarısı ayrı kaydedilmelidir.
- Gövdeyle itme başarısızsa robot durmalı; uygun alan varsa AVOID değerlendirilmelidir.
