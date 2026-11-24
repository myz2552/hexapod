# Proje Tanımı

## Amaç

Önce yürüyebilen 18-DOF bir hexapod geliştirmek, ardından kamera ve YOLO kullanarak önüne çıkan nesneleri analiz edip nesneyi gövdesiyle iterek ilerleme veya etrafından dolaşma kararı veren otonom bir sistem geliştirmek.

## Faz 1: Mekanik Platform ve Yürüyüş

Kapsam:

- Elektronik ve hareket kontrolü upstream H-0996 ile aynıdır: Servo 2040 üzerinde upstream firmware (durum makinesi, yürüyüş, IK), Raspberry Pi 5 üzerinde upstream controller istemcisi (bkz. [architecture.md](architecture.md))
- Faz 1A: Servo 2040 devreye alma, Pi ↔ kart UART bağlantısı, 18 servonun darbe kalibrasyonu, tek bacak testi
- Faz 1B: 6 bacak, 18 × MG996R, güç sistemi (2S LiPo, sigorta, 2 × UBEC), yön/trim ayarı ve ayakta durma
- Faz 1C: tripod ve wave yürüyüşü, ileri yürüme, dönme, durma ve iki yürüyüşün karşılaştırılması

Başarı ölçütleri:

- 18 servonun kalibrasyon değerleri `config/hexapod.yml` içinde belgelenmiş olmalıdır.
- Robot temel duruşunu koruyabilmelidir.
- Yürüme, dönüş ve durma hareketleri tekrarlanabilir olmalıdır.
- Tripod ve wave için hız, yanal sapma, akım/enerji ve mekanik sorunlar kaydedilmelidir.

Kamera, YOLO ve engel kararı Faz 2'de ele alınacaktır.

## Faz 2: Kamera, YOLO ve Engel Kararı

Kapsam:

- Kamera yerleşimi, görüntü alma ve kayıt
- YOLO ile nesne sınıfı ve görüntüde konumunun tespiti
- Görsel itilebilirlik tahmini
- Engel yok → FORWARD, itilebilir → PUSH, itilemez → AVOID davranışları
- Görsel karar belirsizse ön tamponla kontrollü gövde teması
- Kontrollü temasta servo güç hattı akımı + IMU + ilerleme bilgisiyle PUSH/AVOID kararının doğrulanması
- Güvenli hareket mümkün değilse STOP/BACK

Önceki standart olan "tek bacakla kısa itme testi" kaldırılmıştır. Fiziksel doğrulama yalnızca görsel karar belirsiz olduğunda yapılır ve bacakla değil, gövde/ön tamponla uygulanır. YOLO algılama güveni, nesnenin itilebilirlik olasılığından ayrı ele alınacaktır.

PUSH/AVOID eşikleri, Servo 2040 akım ölçümünün yeterliliği (gerekirse INA226 / INA260), IMU modeli, YOLO modelinin son sürümü ve veri setinin kesin boyutu deneylerden sonra belirlenecektir.

Başarı ölçütleri:

- Kamera ve YOLO ile nesne tespiti çalışmalıdır.
- Robot FORWARD, PUSH ve AVOID davranışlarını göstermelidir.
- Belirsiz durumda kontrollü gövde teması ile karar doğrulanabilmelidir.
- Görsel ve fiziksel veriler aynı denemeyle ilişkilendirilmelidir.
- Detection accuracy, decision accuracy, push success, avoidance success, traversal time ve false push decision raporlanmalıdır.

## Kapsam Dışı

- Robot kolu
- Engebeli arazi navigasyonu
- Dış mekanda tam otonom navigasyon
- Endüstriyel güvenlik sertifikasyonu
- Çok robotlu koordinasyon
- Yüksek hız veya yüksek yük taşıma hedefleri

## Ana Riskler

- Mekanik esneme ve servo kalibrasyon hataları
- 18 MG996R servonun anlık akımı nedeniyle güç hattında gerilim düşümü ve aşırı yük
- Servo 2040 klemenslerinin 10 A sürekli akım sınırının yürüyüşte aşılması
- UBEC voltaj anahtarının yanlış konumda bırakılması (Pi veya servolar zarar görür)
- Ortak GND veya TX/RX hatalarından kaynaklanan UART sorunları
- Upstream firmware'in bu robotta donanımda doğrulanmamış olması; yürüyüş davranışını değiştirmek C++ firmware'de fork gerektirir
- Gövdeyle itme sırasında duruşun veya yönün bozulması
- Yürüyüş servolarının akımının kontrollü temas ölçümünü maskelemesi
- Algı hataları, ölçüm gürültüsü ve dolaşma alanının yetersizliği
