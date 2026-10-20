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
                     │ I2C
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      PCA9685     Akım sensörü   IMU
         │
         ▼
      MG996R
```

Raspberry Pi 5 tek ana bilgisayardır; YOLO, karar, inverse kinematics (IK), gait ve sensör okuma yazılımları üzerinde çalışır. Servo PWM sinyalleri PCA9685 PWM kontrol kartı ile üretilir. İlk sürümde ESP32 ve Servo2040 kullanılmaz.

Kamera modeli, akım sensörü modeli (INA226 / INA260) ve IMU modeli henüz TBD'dir; bkz. [donanım](hardware.md).

## Faz 1A – Tek Bacak

```text
Raspberry Pi 5
  ↓ I2C
PCA9685
  ↓
3 × MG996R (CH0 Coxa, CH1 Femur, CH2 Tibia)
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
2 × PCA9685
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

Mekanik başlangıç noktası [ggldnl/Hexapod-Hardware](https://github.com/ggldnl/Hexapod-Hardware) tasarımıdır. MG996R montaj geometrisi, F686ZZ rulmanlı yataklama ve M3 vida / M3 heat-set insert yaklaşımı korunur. Raspberry Pi 5 yuvası, PCA9685 montajı, kamera yuvası, güç sistemi yerleşimi ve ön itme tamponu projeye göre yeniden tasarlanır. Bkz. [cad-reference.md](cad-reference.md).

### Güç ve Servo Elektroniği

PCA9685, sıkça "servo driver" olarak anılsa da aslında I2C ile kontrol edilen 16 kanallı bir PWM kontrol kartıdır; servoların gücünü sağlamaz. Servolar ayrı 6 V yüksek akım hattından beslenir; Raspberry Pi 5, PCA9685 ve servo güç kaynağının GND'leri ortaktır. Faz 2'de servo güç hattına akım sensörü eklenir.

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
