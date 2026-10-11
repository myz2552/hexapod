# Yol Haritası

Proje iki ana aşamada yürütülecektir. Aşağıdaki adımlar bu aşamaların alt çalışmalarıdır.

## Aşama 1: Mekanik Platform ve Yürüyüş

### Mekanik Tasarım ve Üretim

- Gövde, bacak ve eklem geometrisini tasarla.
- Servo yerleşimleri, motor açı sınırları ve bağlantıları belirle.
- Parçaları üret, monte et ve hareket aralıklarını kontrol et.

Çıktı: CAD dosyaları, monte edilmiş platform ve geometri notları.

### Elektronik ve Servo Kalibrasyonu

- Güç dağıtımı ve servo sürücü bağlantılarını kur.
- Her servonun yönünü, nötr açısını ve güvenli açı aralığını kaydet.
- Eklem hareketlerini ve temel duruşu test et.

Çıktı: Bağlantı planı, kalibrasyon tablosu ve ayakta durma kayıtları.

### Yürüyüş Kontrolü ve Testleri

- Ters kinematik ve ayak yörüngelerini geliştir.
- İleri yürüyüş, dönüş ve durmayı uygula.
- Tekrarlı deneylerde mesafe, süre, sapma ve güç durumunu kaydet.
- Mekanik esneme, ısınma ve kalibrasyon sorunlarını gider.

Aşama geçiş ölçütü: Kararlı ayakta durma ve tekrarlanabilir yürüyüş, dönüş ve durma testlerinin tamamlanması.

## Aşama 2: Kamera, Bacak Testi ve Engel Kararı

### Kamera ve YOLO

- Kamerayı yerleştir ve görüntü akışını çalıştır.
- YOLO ile nesne tespitini kur ve görüntü verilerini hazırla.
- Nesne sınıfı, konumu ve görsel itilebilirlik ön tahminini kaydet.

Çıktı: Görsel algı prototipi ve tespit kayıtları.

### Tek Bacakla İtme Testi

- Test bacağını ve diğer bacakların destek duruşunu belirle.
- Yaklaşma, temas, kısa itme ve geri alma hareketlerini geliştir.
- Akım ve IMU ölçüm düzenini değerlendir.
- Test sınırlarını belirle ve referans deneylerle kalibre et.
- Bacak testi bulgularının gövdeyle itme başarısıyla ilişkisini ölç.

Çıktı: Bacakla test davranışı, ölçüm kayıtları ve kalibrasyon sonuçları.

### Veri Birleştirme ve Hareket Kararı

- Görsel ve fiziksel test verilerini birleştir.
- Güvenle test edilebilen nesnelerde bacak testini standart adım olarak uygula.
- Test bacağını yürüyüş konumuna geri al.
- İtilebilir nesnelerde gövdeyle iterek ilerle.
- İtilemez nesnelerde etrafından dolaş.
- Başarısızlıkta durma ve geri çekilme davranışlarını ekle.

Çıktı: Nesne tespiti, bacak testi, birleşik karar ve hareketten oluşan bütünleşik akış.

### Deneysel Doğrulama ve Sunum

- Görsel tahmin ve birleşik değerlendirme sonuçlarını karşılaştır.
- Karar doğruluğu, gövdeyle itme başarısı ve geçiş süresini raporla.
- İtme ve dolaşma senaryolarını gösteren demo hazırla.
- Tasarım, yazılım ve deney belgelerini yayıma hazırla.

Aşama tamamlanma ölçütü: Görüntü ve tek bacakla test verileriyle gövdeyle itme veya dolaşma kararının uygulanması ve sonuçların belgelenmesi.
