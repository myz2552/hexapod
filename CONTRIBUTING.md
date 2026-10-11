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
cad/          3B model ve üretim dosyaları
docs/         Proje belgeleri
firmware/     Mikrodenetleyici veya servo kontrol kodları
hardware/     Bağlantı şemaları ve parça listeleri
software/     Raspberry Pi uygulama kodları
tests/        Test ve deney araçları
models/       İleri aşama YOLO ve algı modeli notları
```

## Deney Kaydı

İlk aşamada her mekanik, elektronik, servo kalibrasyonu veya yürüyüş testi için şu bilgiler kaydedilmelidir:

- Tarih
- Robot mekanik durumu
- Pil veya güç durumu
- Kullanılan servo ve güç ayarları
- Test edilen hareket ve servo açı ayarları
- Gözlenen sorunlar
- Başarılı / başarısız sonucu

İkinci aşamada kamera ve YOLO deneyleri ile tek bacakla itme testi kayıtları tutulmalıdır. Ortak deneme kimliği, nesne tipi, görsel ön tahmin, test bacağı, destek duruşu, akım ve IMU ölçümleri, birleşik karar ve gövdeyle itme veya dolaşma sonucu kaydedilmelidir.
