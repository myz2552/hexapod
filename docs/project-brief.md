# Proje Tanımı

## Amaç

Önce yürüyebilen 18-DOF bir hexapod geliştirmek, ardından kamera ve YOLO kullanarak önüne çıkan nesneleri analiz edip nesneyi gövdesiyle iterek ilerleme veya etrafından dolaşma kararı veren otonom bir sistem geliştirmek.

## Faz 1: Mekanik Platform ve Yürüyüş

Kapsam:

- Faz 1A: Raspberry Pi 5 + PCA9685 + 3 × MG996R ile tek bacak prototipi
- Coxa, Femur ve Tibia servolarının yön, nötr açı ve güvenli min/max açı kalibrasyonu
- Tek bacak inverse kinematics (IK) ve XYZ ayak pozisyonlama
- Faz 1B: 6 bacak, 18 × MG996R ve 2 × PCA9685 ile tam mekanik platform
- Raspberry Pi 5, PCA9685, kamera, güç sistemi ve ön tampon yerleşimi
- Faz 1C: 6 bacak IK, tripod gait, ileri yürüme, dönme ve durma

Başarı ölçütleri:

- Tek bacak seçilen XYZ koordinatlarına güvenli ve tekrarlanabilir şekilde ulaşabilmelidir.
- 18 servonun kalibrasyon değerleri belgelenmiş olmalıdır.
- Robot temel duruşunu koruyabilmelidir.
- Yürüme, dönüş ve durma hareketleri tekrarlanabilir olmalıdır.
- Hız, yanal sapma, güç durumu ve mekanik sorunlar kaydedilmelidir.

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

PUSH/AVOID eşikleri, akım sensörü modeli (INA226 / INA260), IMU modeli, YOLO modelinin son sürümü ve veri setinin kesin boyutu deneylerden sonra belirlenecektir.

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
- Ortak GND hatalarından kaynaklanan I2C/PWM sorunları
- Gövdeyle itme sırasında duruşun veya yönün bozulması
- Yürüyüş servolarının akımının kontrollü temas ölçümünü maskelemesi
- Algı hataları, ölçüm gürültüsü ve dolaşma alanının yetersizliği
