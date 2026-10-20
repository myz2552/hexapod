# Teknik Karar Kayıtları

Bu dosya, proje ilerledikçe alınan önemli teknik kararları kısa biçimde kaydetmek için kullanılır.

## Karar Formatı

Her karar için şu yapı kullanılacaktır:

```text
## YYYY-AA-GG: Karar başlığı

Durum: Önerildi | Kabul edildi | Değiştirildi | İptal edildi

Bağlam:
Kararın neden gerektiği.

Karar:
Seçilen yaklaşım.

Sonuç:
Bu kararın etkileri, artıları ve riskleri.
```

## 2026-10-05: İlk odak yürüyebilen kameralı hexapod platformu olacak

Durum: Kabul edildi

Bağlam:
Projenin uzun vadeli fikri kamerayla çevresini algılayan ve gerektiğinde fiziksel temasla kararını doğrulayan bir hexapod robottur. Ancak bu özelliklerin sağlıklı geliştirilebilmesi için önce mekanik olarak yürüyebilen, elektronik olarak kararlı ve kamera taşıyabilen bir platform gereklidir.

Karar:
İlk sürümün ana hedefi, 3B yazıcıyla üretilmiş, Raspberry Pi ile kontrol edilen, kameradan görüntü alabilen ve temel yürüme / dönme hareketlerini yapabilen bir hexapod robot oluşturmaktır. YOLO, itilebilirlik tahmini, servo akımı ve ivmeölçerle doğrulama gibi özellikler ikinci aşama hedefleri olarak ele alınacaktır.

Sonuç:
Proje daha uygulanabilir bir sırayla ilerler. Önce mekanik, güç, servo kontrolü ve yürüyüş problemleri çözülür. Gelişmiş algı ve karar özellikleri, kararlı bir platform üzerinde daha sonra test edilir.

## 2026-10-11: İki aşamalı geliştirme ve tek bacakla itme testi

Durum: Değiştirildi

> Bu karar 2026-10-20 tarihli "Faz 2 engel davranışı" kararıyla değiştirilmiştir. İki fazlı geliştirme yaklaşımı korunmuş; tek bacakla standart itme testi kaldırılmıştır. Kayıt karar geçmişi olarak korunur.

Bağlam:
Güncel tasarımda mekanik platform ve yürüyüş ilk aşamada, kamera ve fiziksel testle engel yönetimi ikinci aşamada tamamlanacaktır. Önceki akış testi yalnızca belirsizlikte tanımlıyor; test bacağı ve gövdeyle itme ayrımını belirtmiyordu.

Karar:
İlk aşama mekanik tasarım, motor açıları, servo kalibrasyonu, ayakta durma ve yürüyüş testlerini kapsar. İkinci aşama kamera ve YOLO, tek bacakla kontrollü itme testi, görsel ve fiziksel verilerin birleştirilmesi ve hareket kararını kapsar. Güvenle değerlendirilebilen nesnelerde test standart adımdır. İtilebilir nesne gövdeyle itilerek ilerlenir; itilemez nesnenin etrafından dolaşılır.

Sonuç:
İlk platform odağı korunur; kamera çalışmaları ikinci aşamaya alınır. Yalnızca belirsizlikte test yaklaşımı değiştirilmiştir. Destek duruşu ve bacak testi ile gövdeyle itme başarısının ilişkisi doğrulanacaktır. Bu kayıt güncel yaklaşımı belirler; önceki kayıt karar geçmişi olarak korunur.

## 2026-10-20: Servo kontrol mimarisi

Durum: Kabul edildi

Bağlam:
Servo kontrolü için ana bilgisayar ve PWM üretim yöntemi kesinleştirilmeliydi. ESP32 ve Servo2040 gibi ara denetleyiciler değerlendirilmişti.

Karar:
Raspberry Pi 5 ana bilgisayar olacaktır. PCA9685, I2C üzerinden servo PWM kontrolü için kullanılacaktır.

- Tek bacak: 1 PCA9685 + 3 MG996R (CH0 Coxa, CH1 Femur, CH2 Tibia)
- Tam robot: 2 PCA9685 + 18 MG996R

ESP32 ve Servo2040 ilk sürümde kullanılmayacaktır. Servolar Raspberry Pi üzerinden beslenmeyecek; ayrı 6 V yüksek akım hattından beslenecek ve GND referansı Raspberry Pi 5 ile ortak olacaktır. İlk tek bacak testlerinde laboratuvar güç kaynağı kullanılacaktır.

Sonuç:
Tek bir yazılım platformu (Raspberry Pi 5) üzerinde IK, gait, YOLO ve karar birlikte geliştirilir. Ara denetleyici firmware'i gerekmez. Servo güç sistemi, batarya ve final güç dönüştürücü ayrıca belirlenecektir (TBD).

## 2026-10-20: Mekanik referans platform

Durum: Kabul edildi

Bağlam:
Bacak ve gövde mekaniğini sıfırdan tasarlamak yerine MG996R ile çalışan, açık kaynaklı bir hexapod tasarımı başlangıç noktası olarak seçilmek istendi.

Karar:
Mekanik başlangıç noktası olarak https://github.com/ggldnl/Hexapod-Hardware kullanılacaktır.

MG996R montaj geometrisi, F686ZZ rulmanlı yataklama, M3 vida ve M3 heat-set insert yaklaşımı korunacaktır.

Raspberry Pi 5, PCA9685, kamera, güç sistemi ve ön tampon projeye göre yeniden tasarlanacaktır.

Sonuç:
Faz 1A'da tek bacak hızlıca üretilebilir. Upstream CAD dosyaları lisans/izin teyit edilene kadar bu repoya kopyalanmaz; yalnızca kaynak ve kullanılan parçalar belgelenir (bkz. docs/cad-reference.md).

## 2026-10-20: Faz 2 engel davranışı

Durum: Kabul edildi

Bağlam:
2026-10-11 kararındaki tek bacakla standart itme testi, destek duruşunun korunması ve bacak ölçümünün gövdeyle itme başarısını öngörmesi açısından riskliydi.

Karar:
Tek bacakla standart nesne yoklama kaldırılmıştır.

YOLO sonucu yeterince güvenliyse robot doğrudan PUSH veya AVOID davranışı uygulayacaktır.

Görsel karar belirsizse ön tampon ile kontrollü gövde teması yapılacak ve servo güç hattı akımı + IMU + ilerleme bilgisi kullanılarak karar doğrulanacaktır. Güvenli hareket mümkün değilse robot STOP/BACK uygular.

Sonuç:
Tek bacak prototipi yalnızca Faz 1 mekanik ve IK doğrulaması için kullanılır. Fiziksel ölçüm, itme işini yapacak olan gövde/ön tampon ile yapılır. Güven eşikleri ve PUSH/AVOID eşikleri deneylerden sonra belirlenecektir.
