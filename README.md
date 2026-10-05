# TouchSight Hexapod

TouchSight Hexapod, iki mekatronik mühendisliği öğrencisinin geliştirdiği, 3B yazıcıyla üretilecek ve Raspberry Pi ile çalışacak düşük maliyetli kameralı bir altı bacaklı robot projesidir.

Projenin ana hedefi, kameraya sahip bir hexapod robot platformu oluşturmak ve bu robotun kararlı biçimde yürüyebilmesini sağlamaktır. Görüntü işleme, engel algılama, YOLO ile sınıflandırma ve fiziksel itme deneyi gibi özellikler ikinci aşama geliştirme hedefleri olarak ele alınacaktır.

## Öncelikler

1. Üretilebilir bir altı bacaklı mekanik platform tasarlamak.
2. Servo motorları güvenilir biçimde sürebilen elektronik altyapıyı kurmak.
3. Raspberry Pi tabanlı kontrol yazılımını başlatmak.
4. Robotun temel duruş, ileri yürüme ve dönme hareketlerini gerçekleştirmesini sağlamak.
5. Kamera görüntüsünü alıp kaydedebilen temel algı altyapısını eklemek.
6. Daha sonraki aşamalarda engel algılama ve itilebilirlik deneylerini geliştirmek.

## İlk Sürüm Hedefi

İlk çalışan sürümde robotun şu yeteneklere sahip olması beklenir:

- 3B yazıcıyla üretilmiş gövde ve bacak yapısı
- Raspberry Pi üzerinden çalışan temel kontrol yazılımı
- Servo kalibrasyonu
- Kararlı ayakta durma
- Düz zeminde ileri yürüme
- Basit sağ / sol dönüş
- Kamera görüntüsü alma ve kayıt

## İleri Aşama Fikri

Platform yürüyebilir hale geldikten sonra TouchSight yaklaşımı devreye alınacaktır. Bu aşamada robot, önündeki engelin itilebilir olup olmadığını önce kamerayla ve YOLO tabanlı algıyla tahmin eder. Tahmin belirsizse küçük ve kontrollü bir itme denemesi yaparak servo hattı akımı ve ivmeölçer verisini değerlendirir. Sonrasında engeli itmeye ya da etrafından dolaşmaya karar verir.

Bu özellik ana platform tamamlandıktan sonra geliştirilecek deneysel bir katmandır.

## Donanım Bileşenleri

- Raspberry Pi tabanlı kontrol bilgisayarı
- Kamera modülü
- Servo motorlarla çalışan altı bacaklı mekanizma
- Servo sürücü kartı
- 3B yazıcıyla üretilecek gövde ve bacak parçaları
- İleri aşamalar için IMU ve akım ölçüm devresi

## Yazılım Bileşenleri

- Servo kalibrasyon ve hareket kontrolü
- Yürüyüş paterni üretimi
- Kamera görüntüsü alma
- Robot durum kaydı
- İleri aşamalar için görüntü işleme, YOLO algılama ve karar mantığı

## Repo Yapısı

```text
docs/
  architecture.md      Sistem mimarisi ve geliştirme katmanları
  project-brief.md     Proje tanımı, kapsam ve başarı ölçütleri
  roadmap.md           Aşamalı geliştirme planı
  decisions.md         Teknik karar kayıtları
```

Kod, CAD dosyaları, deney kayıtları ve model dosyaları geliştirme ilerledikçe bu yapıya eklenecektir.

## Durum

Proje başlangıç aşamasındadır. İlk odak, yürüyebilen kameralı hexapod platformunun mekanik, elektronik ve temel yazılım altyapısını oluşturmaktır.
