# software/hardware

Kinematik eklem açısı ile servo arasındaki katman. IK ve gait yalnızca eklem açısı üretir;
bu katman açıları kalibrasyonla PCA9685 komutlarına çevirir. İleride sürücü değişirse
(ör. Servo2040) veya simülasyon eklenirse yalnızca bu katman değişir.

```text
IK / gait (eklem açısı)
  ↓
calibration.py   eklem açısı → komut açısı, ölçülmüş limit kontrolü
  ↓
motion.py        hız sınırlı doğrusal interpolasyon
  ↓
pca9685_bank.py  kart adresi + kanal → PWM (tek I2C hattı, birden çok PCA9685)
```

| Modül | Görev |
| --- | --- |
| `calibration.py` | Şema v2 doğrulama, `JointCalibration` (`to_command`, `to_joint`, `joint_limits_deg`, türetilmiş `direction`/`scale`) |
| `pca9685_bank.py` | `PCA9685Bank`: ortak I2C hattında birden çok kart; açılış/kapanışta tüm çıkışları bırakır. `RecordingOutput`: donanımsız kuru çalıştırma/test |
| `motion.py` | `JointMotion`: `initialize` (başlangıç pozu, eklem eklem), `move_to` (maks. hız sınırlı), `release` |

## Kalibrasyon şeması v2

Örnek: [config/servo_calibration.example.yaml](../../config/servo_calibration.example.yaml).
Her eklem kart adresi, kanal ve **ham fiziksel ölçümler** tutar: sıfır pozu komutu, bilinen
bir referans açıdaki komut ve güvenli min/max komut. Yön ve ölçek bu iki pozdan türetilir:

```text
komut = zero_cmd_deg + scale × eklem_açısı
scale = (ref_cmd_deg − zero_cmd_deg) / ref_joint_deg     (işaret = yön)
```

Böylece MG996R'nin 750..2250 µs eşlemesinin gerçek 180°'ye oturmaması da düzeltilir.
Sıfır pozu tanımı: [software/kinematics/README.md](../kinematics/README.md#eklem-açı-konvansiyonu-sıfır-pozu).

Doğrulamalar: ölçüm alanı null ise kullanılmaz; aynı kart+kanal iki ekleme atanamaz;
sıfır ve referans pozu limitler içinde ve en az 5 komut derecesi ayrık olmalıdır; v1 şeması reddedilir.

## Güvenlik notları

- `move_to` hedefi yazmadan önce tüm pozu limitlere karşı doğrular; reddedilen hareket hiçbir servoyu oynatmaz.
- `initialize` hız sınırlı **değildir**: başlangıç konumu bilinmediği için servolar kendi hızlarıyla atlar. Bacak yüksüz olmalıdır.
- Komut açısı, kalibrasyon sırasında kullanılan bring-up araçlarıyla aynı pulse eşlemesini kullanır (`software/servo_test/pca9685_controller.py`); kalibrasyon kartla birlikte geçerlidir. PCA9685 osilatörleri kartan karta farklı olabileceğinden kart veya kablo değişirse yeniden kalibre edin.
- PWM bırakma güç kesme değildir; servo PSU'su erişilebilir olmalıdır. Donanımsal acil durdurma için PCA9685 OE pininin bir GPIO'ya bağlanması önerilir (henüz uygulanmadı).

Kod donanım üzerinde henüz doğrulanmamıştır; testler sahte I2C/PWM nesneleri kullanır.
