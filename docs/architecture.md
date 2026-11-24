# Sistem Mimarisi

Mekanik, elektronik ve hareket kontrolü upstream [H-0996](https://github.com/ggldnl/H-0996) projesiyle aynıdır. Projenin kendi katkısı Raspberry Pi tarafındaki üst katmandır: kamera, YOLO, itilebilirlik kararı, deney kaydı ve yürüyüş karşılaştırması.

## Genel Sistem

```text
                     Kamera (Faz 2)
                        │
                        ▼
              ┌──────────────────────┐
              │   Raspberry Pi 5     │
              │----------------------│
              │ YOLO + karar (Faz 2) │
              │ software.bringup     │
              │ controller (hexapod) │──── config/hexapod.yml
              └──────────┬───────────┘
                         │ UART 921600 baud (GPIO14/15 ↔ GP21/20) + 5 V + GND
                         ▼
              ┌──────────────────────┐
              │   Servo 2040         │
              │   (H-0996-Firmware)  │
              │----------------------│
              │ Durum makinesi       │
              │ Yürüyüş üreteci      │
              │ Inverse kinematics   │
              │ PWM, akım/voltaj     │
              │ Watchdog, FAULT      │
              └──────────┬───────────┘
                         │ 18 kanal
                         ▼
                    18 × MG996R
```

| Katman | Nerede | Kaynak |
| --- | --- | --- |
| Durum makinesi (OFF → kalkış → IDLE ↔ WALK → oturma, FAULT) | Servo 2040 | `firmware/src/core/robot.hpp` |
| Yürüyüş üreteci: tripod, wave, ripple | Servo 2040 | `firmware/src/core/gait.hpp` |
| Bacak FK/IK | Servo 2040 | `firmware/src/core/kinematics.hpp` |
| PWM, servo gücü, akım/voltaj ölçümü | Servo 2040 | `firmware/src/communication/servo2040_hal.hpp` |
| Seri protokol ve istemci | Pi | `controller/hexapod/` |
| Robot yapılandırması ve kalibrasyon | Pi → karta gönderilir | `config/hexapod.yml` |
| Devreye alma, ayakta durma, yürüyüş kaydı | Pi | `software/bringup.py` |
| Kamera, YOLO, karar | Pi | `software/vision`, `software/decision` (Faz 2) |

Pi bağlanırken `config/hexapod.yml` içeriğini karta gönderir (provisioning). Ardından yalnızca yüksek seviyeli komutlar yollar: ayağa kalk / otur, yürüyüş tipi, hız (vx, vy, dönüş), gövde pozu ve heartbeat. Kart telemetri olarak durum, odometri, servo hattı voltajı ve akımını döndürür.

## Güç

```text
2S LiPo ── 25 A sigorta ─┬─► UBEC S (Hobbywing 10A V2-Car, 6,0 V) ──► Servo 2040 klemensi ──► 18 × MG996R
                         └─► UBEC P (Hobbywing 5A V2-Air, 5,0 V) ──► Raspberry Pi 5 ──► Servo 2040 lojik 5 V
```

Ayrıntılar ve uyarılar: [wiring.md](wiring.md).

## Faz 1 – Platform ve Yürüyüş

```text
Servo 2040 + firmware devreye alma
  ↓
18 servo kalibrasyonu (controller/calibrate.py → hardware.pulses)
  ↓
Montaj, yön ve trim düzeltmesi (hardware.direction / hardware.trim)
  ↓
Ayakta durma
  ↓
Tripod ve wave yürüyüşü, karşılaştırma
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
                Servo 2040 akımı + IMU + odometri
                           ↓
                      PUSH / AVOID
```

Karar katmanı hareketi controller istemcisi üzerinden uygular: PUSH yavaş ileri hız, AVOID dönüş ve yanal hız, STOP/BACK sıfır veya geri hız. Belirsiz durumda robot ön tamponla düşük hızlı gövde teması yapar; Servo 2040'ın telemetrideki akım ölçümü, IMU ve odometri birlikte değerlendirilir. Güvenli hareket mümkün değilse robot STOP/BACK uygular.

Önceki "tek bacakla nesneye itme testi" mimarisi kaldırılmıştır (bkz. [decisions.md](decisions.md)).

## Modüller

### Mekanik Platform

Upstream [Hexapod-Hardware](https://github.com/ggldnl/H-0996-Hardware) parçaları PCB'siz kurulumla kullanılır: `electronics_mount` üzerinde Pi ve Servo 2040, `battery_mount` üzerinde batarya ve iki UBEC. Projeye özel değişiklikler: Hobbywing UBEC'ler için `battery_mount` yuvaları, kamera yuvası ve ön itme tamponu. Bkz. [cad-reference.md](cad-reference.md).

### Kamera ve YOLO

Görüntü alır; nesne sınıfı, görüntüdeki konum ve algılama güveni üretir. YOLO algılama güveni doğrudan itilebilirlik olarak kullanılmaz; görsel itilebilirlik tahmini ayrıca oluşturulur. Veri seti tek bir `obstacle` sınıfı yerine ayrı nesne sınıfları içerir. YOLO modelinin son sürümü TBD'dir.

### Fiziksel Doğrulama

Yalnızca görsel karar belirsiz olduğunda çalışır. Ön tamponla düşük hızlı temas sırasında servo hattı akımı, IMU ve ilerleme verilerini kaydeder ve değerlendirir. Servo 2040'ın akım ölçümü toplam servo akımıdır; çözünürlüğünün yeterliliği ve eşikler deneylerden sonra belirlenecektir.

### Karar

Görsel itilebilirlik tahmini yeterince güvenliyse doğrudan PUSH veya AVOID seçer; belirsizse fiziksel doğrulama sonucunu kullanır. Engel yoksa FORWARD devam edilir.

### Deney Kaydı

Telemetri (`software.bringup --log`), hareket komutları, görsel tahmin, fiziksel doğrulama verileri, karar ve gerçek hareket sonucu ortak deneme kimliğiyle `experiments/` altında kaydedilir.

## Tasarım İlkeleri

- Faz 2'den önce ayakta durma ve yürüyüş doğrulanmalıdır.
- Upstream firmware ve controller değiştirilmeden kullanılır; robota özel her şey `config/hexapod.yml` içindedir. Upstream kodunda değişiklik gerekirse önce fork yapılır ve [decisions.md](decisions.md) dosyasına kaydedilir.
- Servo kalibrasyonu, yön ve trim değerleri fiziksel ölçümle belirlenmeli; değerler uydurulmamalıdır.
- MG996R servolar Raspberry Pi'den beslenmez.
- Görsel tahmin, fiziksel doğrulama ve hareket başarısı ayrı kaydedilmelidir.
- Gövdeyle itme başarısızsa robot durmalı; uygun alan varsa AVOID değerlendirilmelidir.
