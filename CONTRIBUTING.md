# Katkı Rehberi

Bu repo, TouchSight Hexapod projesinin mekanik, elektronik, yazılım ve deney belgelerini bir arada tutar.

## Çalışma Düzeni

- Değişiklikleri küçük ve açıklanabilir adımlarla yapın.
- Deney sonuçlarını tarih, donanım durumu ve kullanılan yazılım sürümüyle birlikte kaydedin.
- Mekanik veya elektronik değişikliklerin yazılım etkisini not edin.
- Kararları `docs/decisions.md` dosyasına kısa kayıtlar olarak ekleyin.

## Belge Dili

Ana proje belgeleri Türkçe tutulacaktır. Kod içi yorumlar ve dosya adları gerektiğinde İngilizce olabilir.

## Dosya Düzeni

Önerilen ilerleyen repo yapısı:

```text
cad/           Projeye göre değiştirilmiş CAD parçaları (upstream CAD kopyalanmaz, bkz. docs/cad-reference.md)
config/        Örnek kalibrasyon ve yapılandırma dosyaları
docs/          Proje belgeleri
experiments/   Deney kayıtları (single_leg, walking, vision, pushability)
software/      Raspberry Pi 5 yazılımı (servo_test, single_leg, kinematics, gait, vision, decision, sensors)
```

## Deney Kaydı

Faz 1'de her mekanik, elektronik, servo kalibrasyonu, tek bacak IK veya yürüyüş testi için şu bilgiler kaydedilmelidir:

- Tarih
- Robot mekanik durumu
- Pil veya güç durumu
- Kullanılan servo ve güç ayarları
- Test edilen hareket ve servo açı ayarları
- Gözlenen sorunlar
- Başarılı / başarısız sonucu

Faz 2'de kamera ve YOLO deneyleri ile PUSH/AVOID denemeleri kaydedilmelidir. Ortak deneme kimliği, nesne sınıfı, YOLO algılama güveni, görsel itilebilirlik tahmini, kontrollü gövde teması yapıldıysa servo güç hattı akımı, IMU ve ilerleme ölçümleri, karar (FORWARD / PUSH / AVOID / STOP/BACK) ve gerçek hareket sonucu kaydedilmelidir.

## Terminoloji

Belgelerde şu terimler kullanılmalıdır: Raspberry Pi 5, PCA9685, MG996R 180°, Coxa, Femur, Tibia, inverse kinematics / IK, tripod gait, YOLO, PUSH, AVOID, STOP/BACK. PCA9685 "servo driver" olarak anıldığında aslında bir PWM kontrol kartı olduğu ve servolara güç sağlamadığı belirtilmelidir.

Kesinleşmemiş donanım ve parametreler (kamera, IMU, akım sensörü, batarya, güç dönüştürücü, YOLO model sürümü, eşikler) TBD veya "deneylerden sonra belirlenecek" olarak yazılmalıdır.
