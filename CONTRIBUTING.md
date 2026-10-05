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

İlk aşamada her mekanik, elektronik, yürüyüş veya kamera testi için şu bilgiler kaydedilmelidir:

- Tarih
- Robot mekanik durumu
- Pil veya güç durumu
- Kullanılan servo ve güç ayarları
- Test edilen hareket veya kamera işlevi
- Gözlenen sorunlar
- Başarılı / başarısız sonucu

İleri aşama algı deneylerinde ayrıca engel tipi, görsel tahmin sonucu, itme denemesi sonucu, akım ve ivme gözlemleri kaydedilebilir.
