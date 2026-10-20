# TouchSight Hexapod

TouchSight Hexapod, Raspberry Pi 5 ile kontrol edilen, 3B baskılı, 18 serbestlik dereceli (18-DOF) bir hexapod robot projesidir. Proje iki mekatronik mühendisliği öğrencisi tarafından geliştirilmektedir.

Robotun 6 bacağı vardır. Her bacakta 3 adet MG996R 180° positional servo bulunur: Coxa, Femur ve Tibia. Servolar, Raspberry Pi 5'e I2C ile bağlı PCA9685 PWM kontrol kartı üzerinden sürülür. İlk sürümde ESP32 ve Servo2040 kullanılmayacaktır.

Proje iki ana fazdan oluşacaktır.

## Faz 1 – Mekanik Platform ve Yürüyüş

Önce tek bacak prototipi oluşturulacaktır.

```text
3 × MG996R
    ↓
Coxa / Femur / Tibia
    ↓
PCA9685
    ↓
Raspberry Pi 5
```

Bu aşamada:

- servo kontrolü
- servo nötr açı kalibrasyonu
- servo hareket limitleri
- tek bacak inverse kinematics (IK)
- XYZ ayak pozisyonlama

doğrulanacaktır.

Ardından sistem 6 bacak ve 18 servoya genişletilecektir (Raspberry Pi 5 → 2 × PCA9685 → 18 × MG996R).

Tam robotta:

- ayakta durma
- ileri yürüme
- sağa/sola dönme
- durma
- tripod gait

geliştirilecektir.

## Faz 2 – Kamera, YOLO ve Engel Kararı

Robot yürürken kameradan aldığı görüntü YOLO ile analiz edilecektir.

Temel akış:

```text
Kamera
  ↓
YOLO
  ↓
Nesne tespiti
  ↓
Nesne sınıfı + konumu
  ↓
Görsel itilebilirlik tahmini
  ↓
PUSH / AVOID
```

- Robot nesneyi itilebilir olarak değerlendirirse ön gövdesi/tamponuyla nesneyi iterek yoluna devam edecektir (PUSH).
- Robot nesneyi itilemez olarak değerlendirirse nesnenin etrafından dolaşacaktır (AVOID).
- Görsel tahmin belirsizse robot düşük hızlı kontrollü gövde teması uygulayacak ve servo güç hattı akımı + IMU + robotun ilerleme bilgisi kullanılarak karar doğrulanacaktır.
- Güvenli hareket mümkün değilse robot duracak veya geri çekilecektir (STOP/BACK).

Robot kolu kullanılmayacaktır. Tek bacak prototipi yalnızca Faz 1'deki mekanik ve IK doğrulaması için kullanılır; Faz 2'de standart bir tek bacakla itme testi yoktur.

PUSH/AVOID eşikleri, akım ve IMU ölçüm düzeni deneylerden sonra belirlenecektir.

## Güç

Servolar Raspberry Pi üzerinden beslenmez. Servo sistemi ayrı 6 V yüksek akım hattından beslenir; Raspberry Pi 5 ve servo güç sisteminin GND referansı ortaktır. İlk tek bacak testlerinde laboratuvar güç kaynağı kullanılacaktır. Ayrıntılar için [bağlantı belgesine](docs/wiring.md) bakın.

## Repo Yapısı

- [Proje tanımı](docs/project-brief.md): kapsam ve başarı ölçütleri
- [Sistem mimarisi](docs/architecture.md): modüller ve davranış akışı
- [Yol haritası](docs/roadmap.md): Faz 1A–2D geliştirme planı
- [Donanım](docs/hardware.md): kesinleşmiş ve TBD donanım listesi
- [Bağlantılar](docs/wiring.md): tek bacak prototipi bağlantı şeması
- [CAD referansı](docs/cad-reference.md): mekanik referans platform ve lisans notları
- [Teknik kararlar](docs/decisions.md): karar geçmişi

```text
cad/           Projeye göre değiştirilmiş CAD parçaları (upstream CAD kopyalanmaz)
config/        Örnek kalibrasyon ve yapılandırma dosyaları
docs/          Proje belgeleri
experiments/   Deney kayıtları
software/      Raspberry Pi 5 yazılımı
```

## Durum

Proje başlangıç aşamasındadır. Belgeler hedeflenen tasarımı anlatır; yürüyüş, YOLO ve PUSH/AVOID davranışlarının uygulanmış veya doğrulanmış olduğunu ifade etmez.
