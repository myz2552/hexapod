# Yol Haritası

## Faz 0: Tanım ve Planlama

- Proje hedeflerini yazılı hale getir.
- İlk sürüm kapsamını yürüyebilen kameralı hexapod olarak netleştir.
- Donanım bileşen listesini çıkar.
- Temel repo belgelerini oluştur.

Çıktı:

- README
- Proje tanımı
- Mimari belge
- Yol haritası

## Faz 1: Mekanik Platform

- İlk hexapod gövde ve bacak tasarımını oluştur.
- Servo yerleşimini belirle.
- Kamera montaj konumunu planla.
- Elektronik yerleşim alanlarını ayır.
- 3B baskı ve montaj toleranslarını değerlendir.

Çıktı:

- CAD taslakları
- Montaj notları
- İlk parça listesi

## Faz 2: Elektronik ve Güç Altyapısı

- Raspberry Pi, servo sürücü ve güç bağlantılarını planla.
- Servo güç hattı için uygun güç kaynağı veya pil yaklaşımını belirle.
- Kablo düzenini ve güvenli açma / kapama düzenini tasarla.
- Kamera bağlantısını test et.

Çıktı:

- Bağlantı şeması
- Güç planı
- Kamera bağlantı testi

## Faz 3: Servo Kalibrasyonu ve Temel Duruş

- Servo kalibrasyon aracını geliştir.
- Her bacak için nötr pozisyonları belirle.
- Robotun güvenli ayakta duruşunu oluştur.
- Duruş sırasında servo yüklerini ve ısınmayı gözlemle.

Çıktı:

- Servo kalibrasyon notları
- Kararlı temel duruş

## Faz 4: Temel Yürüyüş

- İlk yürüyüş paternini oluştur.
- İleri yürüme hareketini test et.
- Sağ ve sol dönüş hareketlerini ekle.
- Güvenli durdurma davranışı geliştir.

Çıktı:

- Düz zeminde temel yürüyüş
- Basit dönüş hareketleri
- Hareket test kayıtları

## Faz 5: Kamera Entegrasyonu

- Raspberry Pi üzerinde kamera akışını çalıştır.
- Görüntü alma ve kayıt komutlarını ekle.
- Robot yürürken kamera görüntüsünün kullanılabilirliğini test et.
- Kamera konumunun denge ve görüş açısına etkisini değerlendir.

Çıktı:

- Kamera görüntü kaydı
- Görüş açısı notları
- Kameralı yürüyüş testi

## Faz 6: İleri Algı ve Deneysel Karar Hattı

- YOLO modelini seç ve ilk testleri yap.
- Engel sınıfı, konumu ve güven skorlarını kaydet.
- İtilebilirlik için ilk görsel karar kuralını oluştur.
- Kontrollü itme deneyi fikrini küçük testlerle doğrula.
- Akım ve ivme ölçümünü deneysel olarak değerlendir.

Çıktı:

- Görsel algı prototipi
- Deneysel itilebilirlik notları
- İleri geliştirme kararı

## Faz 7: İyileştirme ve Sunum

- Mekanik dayanıklılığı iyileştir.
- Kablo yönetimi ve elektronik yerleşimi düzenle.
- Demo senaryosunu hazırla.
- Proje raporu ve görsellerini tamamla.

Çıktı:

- Çalışır kameralı hexapod demo
- Proje raporu
- Sunum materyali
