# Sistem Mimarisi

## Genel Bakış

TouchSight Hexapod mimarisi önce yürüyebilen kameralı robot platformunu oluşturacak şekilde katmanlandırılır. Gelişmiş algı ve karar özellikleri, temel hareket platformu kararlı hale geldikten sonra eklenecek ayrı bir katman olarak düşünülür.

Ana katmanlar:

- Mekanik platform
- Güç ve servo elektronik altyapısı
- Hareket kontrolü
- Kamera altyapısı
- İleri aşama algı ve karar modülleri

## Öncelikli Sistem Akışı

```text
Servo komutları
  -> Servo sürücü
  -> Bacak hareketleri
  -> Duruş / yürüme / dönüş

Kamera
  -> Görüntü alma
  -> Kayıt veya canlı izleme
```

İlk sürümde hedef, bu iki hattın güvenilir çalışmasıdır: robot yürürken kamera sisteminin de temel görüntü akışını sağlayabilmesi.

## İleri Aşama Sistem Akışı

```text
Kamera
  -> YOLO algılama
  -> Engel sınıfı, konumu, güven skoru
  -> İtilebilirlik ön tahmini

Belirsizlik varsa
  -> Kontrollü kısa itme hareketi
  -> Servo hattı akımı
  -> İvmeölçer verisi
  -> İt / dolaş / dur kararı
```

Bu akış, platform yürüyebilir hale geldikten sonra eklenecek deneysel karar katmanıdır.

## Ana Modüller

### Mechanical Platform

Robotun 3B yazıcıyla üretilecek gövde, bacak ve bağlantı parçalarını kapsar.

Sorumluluklar:

- Servo yerleşimi
- Bacak geometrisi
- Gövde rijitliği
- Kamera montaj noktası
- Elektronik yerleşim alanları

### Power and Servo Electronics

Servo motorların güvenilir çalışması için güç dağıtımı ve sürücü altyapısını kapsar.

Sorumluluklar:

- Servo güç hattı
- Servo sürücü kartı
- Raspberry Pi bağlantıları
- Kablo düzeni
- Güvenli açma / kapama yaklaşımı

### Locomotion

Hexapod yürüyüşünü ve gövde hareketlerini yönetir.

Sorumluluklar:

- Servo kalibrasyonu
- Temel duruş
- İleri yürüyüş
- Sağ / sol dönüş
- Güvenli duruş ve durdurma

### Camera

Robot üzerindeki kameradan görüntü alınmasını sağlar.

Sorumluluklar:

- Kamera başlatma
- Görüntü alma
- Görüntü kaydetme
- İleri aşama algı modüllerine görüntü sağlama

### Vision and Decision

İkinci aşamada eklenecek algı ve karar katmanıdır.

Sorumluluklar:

- YOLO ile nesne algılama
- Engel konumu ve sınıfı tahmini
- İtilebilirlik ön tahmini
- Gerekirse fiziksel yoklama kararı

### Touch Probe

İleri aşamada belirsiz engeller için kontrollü temas deneyi yapar.

Sorumluluklar:

- Kısa itme hareketi
- Akım ve ivme verisi toplama
- Basit eşiklerle itilebilirlik yorumu
- Güvenli geri çekilme

## İlk Teknik Varsayımlar

- Ana bilgisayar Raspberry Pi olacaktır.
- Servo kontrolü ayrı bir servo sürücü kartı veya mikrodenetleyici üzerinden yapılabilir.
- İlk hedef, gerçek zamanlı karmaşık algı değil kararlı hareket kontrolüdür.
- Kamera ilk aşamada görüntü alma ve kayıt amacıyla kullanılacaktır.
- IMU ve akım ölçümü ileri aşama özellikleri için eklenecektir.

## Tasarım İlkeleri

- Önce yürüyen platform, sonra gelişmiş algı.
- Mekanik ve güç altyapısı yazılım özelliklerinden önce doğrulanmalıdır.
- Servo kalibrasyonu tekrar edilebilir olmalıdır.
- Kamera entegrasyonu platformu ağırlaştırmayacak ve dengeyi bozmayacak şekilde yapılmalıdır.
- İleri aşama deneyleri, temel yürüyüş başarısını riske atmadan eklenmelidir.
