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

Durum: Değiştirildi

> Bu karar 2026-11-23 tarihli "Servo 2040 ve batarya güç sistemi" kararıyla değiştirilmiştir. Raspberry Pi 5'in ana bilgisayar olması ve servoların ayrı 6 V hattan beslenmesi korunmuştur; PCA9685 yerine Servo 2040 kullanılır. Kayıt karar geçmişi olarak korunur.

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

> 2026-11-24 güncellemesi: Lisans (CERN-OHL-W-2.0) incelendi; CAD dosyaları kaynak ve lisans korunarak `hardware/` klasörüne kopyalandı.

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

## 2026-10-26: Kalibrasyon şeması v2, eklem konvansiyonu ve yazılım katmanları

Durum: İptal edildi

> 2026-11-24 tarihli "Upstream H-0996 elektronik ve yazılım mimarisi" kararıyla geçersiz kalmıştır. Kalibrasyon ve kinematik artık `firmware/` ve `controller/hexapod/config/config.yml` ile yapılır. İlgili kod (`software/kinematics`, `software/hardware`, `software/servo_test`, `software/single_leg`) repodan kaldırılmıştır; `ef46a24` commit'inde incelenebilir.

Bağlam:
v1 kalibrasyon şeması (`neutral_deg`, `min_deg`, `max_deg`, `direction`) servo komut açısını gerçek eklem açısına çevirmeye yetmiyordu: "nötr" anlamsal olarak tanımsızdı, yönün neye göre olduğu belirtilmemişti ve 750..2250 µs eşlemesinin MG996R'nin gerçek açısına oturmaması (ölçek) hesaba katılmıyordu. Şema ayrıca tek kart ve sabit CH0..CH2 varsayıyordu; tam robotta 2 × PCA9685 kullanılacaktır.

Karar:
- Eklem açı konvansiyonu ve kinematik sıfır pozu tanımlandı (coxa montaj yönünde, femur yatay, tibia ayak ucu tibia ekseninin altında; bkz. `software/kinematics/README.md`).
- Kalibrasyon şeması v2: her eklem için kart adresi, kanal, sıfır pozu komutu, bilinen bir referans açıdaki komut ve güvenli min/max komut saklanır. Yön ve ölçek iki pozdan türetilir; ayrı alan olarak tutulmaz.
- Bacak ölçüleri (coxa 68.0 mm, femur 76.7 mm, tibia ≈100 mm) upstream URDF'ten hesaplanıp `config/robot_geometry.yaml` dosyasına kaynağıyla yazıldı; tibia montajdan sonra ölçülecektir.
- Yazılım katmanlara ayrıldı: kinematik yalnızca eklem açısı üretir; `software/hardware` kalibrasyon, hız sınırlı hareket ve çoklu PCA9685 çıkışını yönetir.

Sonuç:
Faz 1A'da IK ve XYZ testi kalibrasyon tamamlanır tamamlanmaz yapılabilir. Sürücü değişikliği (ör. Servo2040) veya simülasyon yalnızca çıkış katmanını etkiler. v1 formatındaki yerel kalibrasyon dosyaları geçersizdir; eklemler yeniden kalibre edilmelidir. Konvansiyon ekipçe onaylanınca durum "Kabul edildi" yapılmalıdır.

## 2026-11-23: Servo 2040 ve batarya güç sistemi

Durum: Değiştirildi

> 2026-11-24 tarihli "Upstream H-0996 elektronik ve yazılım mimarisi" kararıyla değiştirilmiştir. Servo 2040 ve 2S LiPo korunmuştur. USB bağlantısı, kendi MicroPython firmware'imiz, Pi üzerinde IK/gait ve "aynı modelden iki 10 A UBEC" planı yerine upstream'in UART bağlantısı, C++ firmware'i ve iki farklı Hobbywing UBEC kullanılır. Kayıt karar geçmişi olarak korunur.

Bağlam:
Tam robot için planlanan 2 × PCA9685, ayrı voltaj düşürücüler ve güç dağıtımı hem gövdede fazla yer kaplıyordu hem de kablolaması karmaşıktı. Batarya ve final güç dönüştürücü de henüz belirlenmemişti (TBD). 2026-10-26 kararında yazılımın çıkış katmanı, sürücü değişikliği yalnızca bu katmanı etkileyecek şekilde ayrılmıştı.

Karar:
- Servo PWM kontrolü için 2 × PCA9685 yerine tek bir Pimoroni Servo 2040 kullanılır. Kart 18 servo çıkışına, servo güç hattında akım/voltaj ölçümüne, 6 analog sensör girişine ve Qw/ST konnektörüne sahiptir.
- Raspberry Pi 5 ana bilgisayar olarak kalır; Servo 2040'a USB ile bağlanır. USB hem seri haberleşmeyi hem kartın lojik beslemesini sağlar. PWM zamanlaması RP2040'ta üretilir.
- Güç: 2S LiPo → 25 A sigorta → anahtar → XT60 Y-ayırıcı → aynı modelden iki UBEC (10 A sürekli / 20 A tepe, 2S–6S giriş). UBEC #1 6,0 V'ta servoları (Servo 2040 klemensi), UBEC #2 5,0 V'ta Raspberry Pi 5'i (USB-C güç kablosu) besler.
- 6 V servo hattı nedeniyle Servo 2040'ın "Separate USB and Ext. Power" izi kesilir.
- Kanal ataması ve bağlantılar [wiring.md](wiring.md) dosyasındadır.
- ESP32 kullanılmaz.

Sonuç:
- Elektronik tek kart + iki UBEC'e iner; I2C kablolaması ve kart adresleri ortadan kalkar.
- Servo 2040 klemensleri sürekli 10 A için tasarlanmıştır; yürüyüş akımı bunu aşarsa servo gücü ikinci bir 6 V UBEC ile bölünecektir. Akım ilk testlerde ölçülmelidir.
- Servo 2040 için MicroPython firmware'i (seri komut protokolü) ve Raspberry Pi tarafında yeni bir çıkış sürücüsü yazılmalıdır. `software/servo_test` araçları ve kalibrasyon şemasındaki `board` alanı (PCA9685 I2C adresi) bu geçişte güncellenecektir. Bu iş tamamlanana kadar mevcut PCA9685 kodu referans olarak korunur.
- PCA9685 osilatör farkı nedeniyle alınmış kalibrasyonlar Servo 2040'a taşınmaz; eklemler yeniden kalibre edilmelidir.
- Kart üstü akım ölçümü Faz 2C'deki servo güç hattı akımı ihtiyacını karşılayabilir; yeterliliği deneyle belirlenecektir.
- Batarya kapasitesi yürüyüş akımı ölçüldükten sonra kesinleşecektir.

## 2026-11-24: Upstream H-0996 elektronik ve yazılım mimarisi

Durum: Kabul edildi

Bağlam:
Mekanik tasarım zaten upstream H-0996 projesinden alınmıştı. 2026-11-23 kararıyla Servo 2040'a geçilmişti, ancak kart için kendi firmware'imizi ve Pi tarafında kendi IK/yürüyüş kodumuzu yazmamız gerekiyordu. Upstream'in aynı mekanik ve aynı kart için çalışan, test edilmiş firmware'i (durum makinesi, tripod/wave/ripple yürüyüşü, IK, akım/voltaj koruması, watchdog) ve Pi tarafı istemcisi vardır. Ekibin önceliği robotu kısa sürede güvenle ayakta durdurup yürütmek ve proje katkısını Faz 2'ye (kamera, YOLO, itilebilirlik) ayırmaktır.

Karar:
- Elektronik ve hareket kontrolü upstream ile birebir aynıdır: Servo 2040 üzerinde [H-0996-Firmware](https://github.com/ggldnl/H-0996-Firmware), Raspberry Pi 5 üzerinde [H-0996-Controller](https://github.com/ggldnl/H-0996-Controller). Upstream depolar (mekanik için [H-0996-Hardware](https://github.com/ggldnl/H-0996-Hardware) de dahil) bu repoya `firmware/`, `controller/` ve `hardware/` klasörleri olarak kopyalanmıştır. Kod satırları aynıdır; kod içi yorumlar ve README'ler Türkçeye çevrilmiştir. Her klasörün README'sinde kaynak commit ve lisans yazar.
- Pi ↔ Servo 2040 bağlantısı UART'tır (921600 baud, Pi GPIO14/15 ↔ GP21/GP20). Servo 2040'ın lojik beslemesi Pi'nin 5 V pininden gelir.
- Upstream'in özel PCB'si kullanılmaz; `electronics_mount` ve elle kablolama kullanılır.
- Güç: 2S LiPo → 25 A sigorta (upstream'de yok, ekledik) → Hobbywing UBEC 10A V2-Car (6,0 V, servolar, Servo 2040 klemensi) ve Hobbywing UBEC 5A V2-Air (5,0 V, Raspberry Pi 5 GPIO 5 V). Upstream iki adet iki kanallı 8 A UBEC kullanır; 10A V2-Car 5 V veremediği için Pi hattına ayrı bir model seçilmiştir.
- Servo 2040'ın "Separate USB and Ext. Power" izi kesilir.
- Robota özel tüm ayarlar `controller/hexapod/config/config.yml` dosyasındadır. Kalibrasyon `controller/calibrate.py` ile yapılır ve sonucu bu dosyaya yazar.
- Pi tarafında devreye alma, ayakta durma ve yürüyüş kaydı için `software/bringup.py` yazıldı; upstream istemcisini kullanır.
- Önceki PCA9685 tabanlı Python kodu (kinematik, kalibrasyon v2, çıkış katmanı, bring-up araçları) kaldırıldı.

Sonuç:
- Faz 1'de firmware veya IK yazmak gerekmez; iş kurulum, kalibrasyon, ölçüm ve tripod/wave karşılaştırmasına iner.
- Yürüyüş Servo 2040'ta gerçek zamanlı çalıştığı için Faz 2'de YOLO'nun Pi'deki yükü yürüyüşü bozmaz.
- Yürüyüş algoritmasını değiştirmek C++ firmware'de değişiklik gerektirir. Böyle bir ihtiyaç doğarsa ayrı karar kaydı açılır ve değişiklik kodda yorumla işaretlenir.
- Kilitli upstream firmware sürümünde bazı host testleri başarısızdır; donanımda doğrulanana kadar bu not edilmiştir. CI controller testlerini ve config testlerini çalıştırır.
- Upstream firmware'in akım kesmesi 12 A'dir; Servo 2040 klemensleri 10 A sürekli için tasarlanmıştır. İlk ayağa kalkma ve yürüyüşte akım ölçülerek gerekirse `safety.current_max` düşürülür.
- Lisans: firmware ve controller GPL-3.0, mekanik tasarım CERN-OHL-W-2.0'dır. Lisans metinleri ilgili klasörlerde korunur; yorumların çevrilmesi gibi değişiklikler klasör README'lerinde belirtilmiştir.
- Upstream'deki yeni sürümler otomatik gelmez; elle incelenip aktarılır (bkz. [setup.md](setup.md#upstreamden-güncelleme-almak)).

