# Proje Tanımı

## Amaç

Önce ayakta durabilen ve yürüyebilen bir hexapod oluşturmak; ardından görüntü ve tek bacakla fiziksel test verilerini birleştirerek engeli gövdeyle itme veya etrafından dolaşma kararı vermektir.

## Aşama 1: Mekanik Tasarım ve Yürüyüş

Kapsam:

- Gövde, bacak ve bağlantı parçalarının tasarımı ve 3B üretimi
- Bacak geometrisi, eklem konumları, servo yerleşimleri ve motor açı sınırları
- Mekanik montaj, güç dağıtımı ve servo kontrolü
- Her eklemin nötr açısı, dönüş yönü ve güvenli açı aralığının kalibrasyonu
- Ters kinematik, ayak yörüngeleri ve yürüyüş düzenleri
- Ayakta durma, ileri yürüyüş, dönüş ve durma deneyleri

Başarı ölçütleri:

- Robot monte edilmiş, servo açı ayarları belgelenmiş olmalıdır.
- Robot temel duruşunu koruyabilmelidir.
- Yürüme, dönüş ve durma hareketleri tekrarlanabilir olmalıdır.
- Mesafe, süre, sapma, güç durumu ve mekanik sorunlar kaydedilmelidir.

Kamera, YOLO ve nesneye itme testi ikinci aşamada ele alınacaktır.

## Aşama 2: Görsel ve Fiziksel Algıyla Engel Yönetimi

Kapsam:

- Kamera yerleşimi, görüntü alma ve kayıt
- YOLO ile nesne sınıfı ve görüntüde konumunun tespiti
- Görsel itilebilirlik ön tahmini
- Nesneye yaklaşma ve destek duruşu oluşturma
- Tek bacakla kısa itme testi, ölçüm ve bacağı geri alma
- Görsel bilgi ile fiziksel test verilerinin birleştirilmesi
- İtilebilir nesneyi gövdeyle iterek ilerleme veya itilemez nesnenin etrafından dolaşma

Güvenle değerlendirilebilen her nesne için bacak testi standart adımdır. Güvenli temas kurulamazsa test zorlanmaz; robot durur veya geri çekilir. YOLO algılama güveni, nesnenin itilebilirlik olasılığından ayrı ele alınacaktır.

Servo akımı ve IMU verilerinin kullanılması planlanmaktadır. Test bacağı ölçümlerinin destek bacaklarının yükünden nasıl ayrıştırılacağı deneylerle değerlendirilecektir. Kalibrasyon, bacakla ölçülen direncin gövdeyle itme başarısını ne kadar iyi öngördüğünü sınayacaktır.

Başarı ölçütleri:

- Kamera ve YOLO ile nesne tespiti çalışmalıdır.
- Robot destek duruşunda tek bacakla test yapıp bacağını yürüyüş konumuna alabilmelidir.
- Görsel ve fiziksel veriler aynı denemeyle ilişkilendirilmelidir.
- Birleşik karara göre gövdeyle itme ve dolaşma davranışları gösterilmelidir.
- Karar doğruluğu, gövdeyle itme başarısı, geçiş süresi ve başarısızlıklar raporlanmalıdır.

## Kapsam Dışı

- Dış mekanda tam otonom navigasyon
- Endüstriyel güvenlik sertifikasyonu
- Çok robotlu koordinasyon
- Yüksek hız veya yüksek yük taşıma hedefleri

## Ana Riskler

- Mekanik esneme ve servo kalibrasyon hataları
- Güç hattında gerilim düşümü ve aşırı yük
- Bacak testi sırasında destek duruşunun bozulması
- Destek servolarının akımının test ölçümünü etkilemesi
- Bacak testinin gövdeyle itme başarısını yeterince açıklayamaması
- Algı hataları, ölçüm gürültüsü ve dolaşma alanının yetersizliği
