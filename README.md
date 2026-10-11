# TouchSight Hexapod

TouchSight Hexapod, iki mekatronik mühendisliği öğrencisinin geliştirdiği, 3B yazıcıyla üretilecek ve Raspberry Pi ile kontrol edilecek düşük maliyetli bir altı bacaklı robot projesidir. Proje iki ana aşamada geliştirilecektir.

## Aşama 1: Mekanik Platform ve Yürüyüş

İlk aşamanın hedefi mekanik ve elektronik altyapısı tamamlanmış, ayakta durabilen ve yürüyebilen bir robot oluşturmaktır.

- Gövde, bacak, eklem ve servo yerleşimlerinin tasarlanması
- Bacak boyları, motor açıları ve eklem hareket sınırlarının belirlenmesi
- 3B üretim, montaj, güç dağıtımı ve servo kontrol altyapısı
- Her servonun yönünün, nötr açısının ve güvenli hareket aralığının kalibrasyonu
- Ters kinematik, temel duruş ve yürüyüş kontrolü
- Ayakta durma, ileri yürüme, dönme ve durma testleri

Bu aşama robotun tekrarlanabilir biçimde ayakta durması ve temel yürüyüş testlerini tamamlamasıyla sonuçlanacaktır.

## Aşama 2: Kamera, YOLO ve Tek Bacakla İtme Testi

Yürüyüş doğrulandıktan sonra kamera ve görüntü işleme eklenecektir. Robot YOLO ile nesneyi tespit edip görsel bir itilebilirlik ön tahmini oluşturacak, ardından tek bacağıyla kısa ve kontrollü bir itme testi yapacaktır. Diğer bacaklar destek duruşunu koruyacaktır.

Görsel bilgi ve fiziksel test verileri birleştirilerek karar verilecektir:

- İtilebilir nesnede test bacağı yürüyüş konumuna alınacak; robot gövdesiyle nesneyi iterek yoluna devam edecektir.
- İtilemez nesnede robot nesnenin etrafından dolaşacaktır.
- Güvenli test veya hareket mümkün değilse robot duracak veya geri çekilecektir.

Bacakla test nesnenin direncini değerlendirmek, gövdeyle itme ise yolu açmak içindir. Test yalnızca görsel tahmin belirsiz olduğunda değil, güvenle değerlendirilebilen nesneler için standart akışta yapılacaktır. Fiziksel değerlendirmede servo akımı ve IMU verilerinin kullanılması planlanmaktadır; ölçüm düzeni ve karar eşikleri deneylerle belirlenecektir.

```text
Kamera -> YOLO ile nesne tespiti -> Görsel ön tahmin
       -> Tek bacakla kontrollü itme testi
       -> Görsel ve fiziksel verilerin birleştirilmesi
       -> Gövdeyle iterek ilerle / Etrafından dolaş
```

## Repo Yapısı

- [Proje tanımı](docs/project-brief.md): kapsam ve başarı ölçütleri
- [Sistem mimarisi](docs/architecture.md): modüller ve davranış akışı
- [Yol haritası](docs/roadmap.md): iki aşamalı geliştirme planı
- [Teknik kararlar](docs/decisions.md): karar geçmişi

Kod, CAD dosyaları, deney kayıtları ve model dosyaları geliştirme ilerledikçe eklenecektir.

## Durum

Proje başlangıç aşamasındadır. Belgeler hedeflenen tasarımı anlatır; yürüyüş, YOLO ve itme davranışlarının uygulanmış veya doğrulanmış olduğunu ifade etmez.
