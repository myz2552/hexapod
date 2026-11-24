# Katkı Rehberi

Bu repo, TouchSight Hexapod projesinin mekanik, elektronik, yazılım ve deney belgelerini bir arada tutar.

## Çalışma Düzeni

- Değişiklikleri küçük ve açıklanabilir adımlarla yapın.
- Deney sonuçlarını tarih, donanım durumu ve kullanılan yazılım sürümüyle birlikte kaydedin.
- Mekanik veya elektronik değişikliklerin yazılım etkisini not edin.
- Kararları `docs/decisions.md` dosyasına kısa kayıtlar olarak ekleyin.
- `firmware/` ve `controller/` alt modüllerinde değişiklik yapmayın. Robota özel ayarlar `config/hexapod.yml` içine gider; `hardware.direction`, `hardware.trim` veya `safety` değerlerini değiştirirseniz satıra yorum ekleyin.
- Commit öncesi testler: `python -m unittest discover -s software -t . -v` ve `bash controller/tests/run.sh`.

## Belge Dili

Ana proje belgeleri Türkçe tutulacaktır. Kod içi yorumlar ve dosya adları gerektiğinde İngilizce olabilir.

## Dosya Düzeni

Önerilen ilerleyen repo yapısı:

```text
firmware/      Alt modül: upstream Servo 2040 firmware'i (değiştirilmez)
controller/    Alt modül: upstream Pi istemcisi (değiştirilmez)
cad/           Projeye göre değiştirilmiş CAD parçaları (upstream CAD kopyalanmaz, bkz. docs/cad-reference.md)
config/        hexapod.yml: robota özel yapılandırma ve kalibrasyon
docs/          Proje belgeleri
experiments/   Deney kayıtları (single_leg, walking, vision, pushability)
software/      Kendi Pi yazılımımız (bringup; Faz 2'de vision, decision, sensors)
```

## Deney Kaydı

Faz 1'de her mekanik, elektronik, servo kalibrasyonu, tek bacak IK veya yürüyüş testi için şu bilgiler kaydedilmelidir:

- Tarih
- Robot mekanik durumu
- Pil veya güç durumu
- Kullanılan güç ayarları (UBEC voltajları, batarya voltajı) ve `config/hexapod.yml` commit'i
- Test edilen hareket (yürüyüş tipi, hız) ve varsa telemetri CSV dosyası (`software.bringup --log`)
- Gözlenen sorunlar
- Başarılı / başarısız sonucu

Faz 2'de kamera ve YOLO deneyleri ile PUSH/AVOID denemeleri kaydedilmelidir. Ortak deneme kimliği, nesne sınıfı, YOLO algılama güveni, görsel itilebilirlik tahmini, kontrollü gövde teması yapıldıysa servo güç hattı akımı, IMU ve ilerleme ölçümleri, karar (FORWARD / PUSH / AVOID / STOP/BACK) ve gerçek hareket sonucu kaydedilmelidir.

## Terminoloji

Belgelerde şu terimler kullanılmalıdır: Raspberry Pi 5, Servo 2040, UBEC, MG996R 180°, Coxa, Femur, Tibia, inverse kinematics / IK, tripod gait, wave gait, firmware, controller, provisioning, YOLO, PUSH, AVOID, STOP/BACK. Servo 2040 servolara güç üretmez; servo gücü 6 V UBEC'ten klemenslere gelir ve kart yalnızca dağıtır, ölçer ve PWM üretir.

Kesinleşmemiş donanım ve parametreler (kamera, IMU, harici akım sensörü ihtiyacı, batarya kapasitesi, YOLO model sürümü, eşikler) TBD veya "deneylerden sonra belirlenecek" olarak yazılmalıdır.
