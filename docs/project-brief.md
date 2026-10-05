# Proje Tanımı

## Kısa Tanım

TouchSight Hexapod, 3B yazıcıyla üretilecek, Raspberry Pi ile kontrol edilecek ve kamera taşıyacak düşük maliyetli bir altı bacaklı robot projesidir. Projenin birinci önceliği yürüyebilen, dengeli ve geliştirilebilir bir hexapod platformu oluşturmaktır.

Engel algılama, YOLO tabanlı sınıflandırma, itilebilirlik tahmini, servo akımı ve ivmeölçer verisiyle fiziksel doğrulama gibi özellikler platform çalışır hale geldikten sonra ele alınacak ikinci aşama hedefleridir.

## Ana Problem

Hexapod robotlar mekanik, elektronik ve yazılım açısından birden fazla zorluğu aynı anda içerir. Robotun ileri özellikler geliştirebilmesi için önce güvenilir bir temel platforma ihtiyacı vardır:

- Gövde ve bacakların üretilebilir olması
- Servoların doğru konumlandırılması
- Güç dağıtımının kararlı olması
- Bacak hareketlerinin kalibre edilebilmesi
- Robotun düz zeminde dengeli yürüyebilmesi
- Kameranın robot üzerine yerleştirilip görüntü verebilmesi

Bu temel kurulmadan gelişmiş algı ve karar özellikleri sağlıklı biçimde test edilemez.

## Yaklaşım

Proje kademeli olarak geliştirilecektir.

İlk aşamada mekanik platform, servo kontrolü ve temel yürüyüş davranışları kurulacaktır. Robotun ayakta durması, ileri yürümesi ve basit dönüş hareketleri önceliklidir.

İkinci aşamada kamera entegrasyonu yapılacak, Raspberry Pi üzerinde görüntü alma ve kayıt altyapısı kurulacaktır.

Üçüncü aşamada algı ve karar özellikleri eklenecektir. Bu aşamada YOLO ile engel algılama, belirsiz nesneler için kontrollü itme deneyi, servo hattı akımı ve ivmeölçer verisiyle doğrulama gibi çalışmalar yapılabilir.

## İlk Sürüm Kapsamı

- 3B yazıcıyla üretilebilir hexapod gövde ve bacak tasarımı
- Servo yerleşimi ve bağlantı planı
- Raspberry Pi üzerinde çalışan temel kontrol yazılımı
- Servo kalibrasyon aracı
- Temel duruş ve yürüyüş paternleri
- İleri yürüme ve basit yön değiştirme
- Kamera modülünden görüntü alma
- Basit test ve hata ayıklama kayıtları

## İkinci Aşama Kapsamı

- YOLO tabanlı nesne algılama
- Engel sınıfı ve konum tahmini
- Kontrollü itme deneyi
- Servo hattı akım ölçümü
- İvmeölçer / IMU verisiyle hareket yorumu
- Engel itme veya etrafından dolaşma karar mantığı

## Kapsam Dışı

- Dış mekanda tam otonom navigasyon
- Endüstriyel güvenlik sertifikasyonu
- Çok robotlu koordinasyon
- Yüksek hız veya yüksek yük taşıma hedefleri
- İlk sürümde tam otonom engel yönetimi

## Başarı Ölçütleri

İlk sürüm için:

- Robot parçaları 3B yazıcıyla üretilebilir olmalıdır.
- Servo bağlantıları kalibre edilebilir olmalıdır.
- Robot düz zeminde kararlı biçimde ayakta durabilmelidir.
- Robot düz zeminde temel yürüyüş hareketini gerçekleştirebilmelidir.
- Robot sağa ve sola basit dönüş yapabilmelidir.
- Kamera görüntüsü Raspberry Pi üzerinden alınabilmeli ve kaydedilebilmelidir.

İleri aşamalar için:

- Kamera ile temel engeller algılanabilmelidir.
- Belirsiz durumlarda kontrollü itme denemesi yapılabilmelidir.
- Akım ve ivme verisi karar mantığında kullanılabilmelidir.

## Ana Riskler

- Mekanik tasarımın servo yüklerini taşıyamaması
- Servo güç hattında gerilim düşümü veya gürültü oluşması
- Bacak geometrisinin yürüyüşü zorlaştırması
- Servo kalibrasyonunun tutarsız olması
- Raspberry Pi üzerinde kamera ve kontrol görevlerinin kaynak sınırlarına takılması
- İleri aşamada sensör verilerinin gürültülü olması
