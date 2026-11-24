# TouchSight Hexapod

TouchSight Hexapod, Raspberry Pi 5 ile kontrol edilen, 3B baskılı, 18 serbestlik dereceli (18-DOF) bir hexapod robot projesidir. Proje iki mekatronik mühendisliği öğrencisi tarafından geliştirilmektedir.

Robotun 6 bacağı vardır. Her bacakta 3 adet MG996R 180° positional servo bulunur: Coxa, Femur ve Tibia. Mekanik, elektronik ve hareket kontrolü açık kaynaklı [H-0996](https://github.com/ggldnl/H-0996) hexapod projesiyle aynıdır: 18 servo bir Pimoroni Servo 2040 kartından sürülür; kart upstream firmware ile durum makinesini, yürüyüşü (tripod, wave, ripple) ve inverse kinematics'i (IK) çalıştırır. Raspberry Pi 5 karta UART üzerinden yüksek seviyeli komutlar gönderir; Faz 2'de kamera, YOLO ve karar yazılımını çalıştırır.

Proje iki ana fazdan oluşacaktır.

## Faz 1 – Platform ve Yürüyüş

```text
Raspberry Pi 5  ──UART──►  Servo 2040 (H-0996-Firmware)  ──►  18 × MG996R
controller + config         durum makinesi, yürüyüş, IK
```

- Servo 2040'a firmware yükleme ve Pi ↔ kart bağlantısı
- 18 servonun darbe kalibrasyonu, yön ve trim ayarı
- Ayakta durma
- İleri yürüme, dönme, durma
- Tripod ve wave yürüyüşlerinin karşılaştırılması (hız, sapma, akım, enerji)

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

Robot kolu kullanılmayacaktır. Faz 2'de standart bir tek bacakla itme testi yoktur.

PUSH/AVOID eşikleri, akım ve IMU ölçüm düzeni deneylerden sonra belirlenecektir.

## Güç

Robot 2S LiPo ile çalışır. Bataryadan sonra 25 A sigorta ve iki UBEC vardır: Hobbywing 10A V2-Car (6,0 V) Servo 2040 üzerinden servoları, Hobbywing 5A V2-Air (5,0 V) Raspberry Pi 5'i besler; Servo 2040'ın lojik beslemesi Pi'den gelir. Servolar Raspberry Pi üzerinden beslenmez; GND referansı ortaktır. Tek bacak testlerinde servo hattı için laboratuvar güç kaynağı kullanılır. Ayrıntılar: [bağlantılar](docs/wiring.md).

## Hızlı Başlangıç

```bash
git clone --recurse-submodules https://github.com/myz2552/hexapod.git
cd hexapod
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m software.bringup telemetry        # servoları enerjilemeden bağlantı testi
python controller/calibrate.py --config config/hexapod.yml
python -m software.bringup stand            # ayağa kalk, bekle, otur
python -m software.bringup walk --gait tripod --vx 60 --log runs/tripod.csv
```

Raspberry Pi ayarları, firmware derleme/yükleme ve kalibrasyon: [kurulum](docs/setup.md).

## Repo Yapısı

- [Proje tanımı](docs/project-brief.md): kapsam ve başarı ölçütleri
- [Sistem mimarisi](docs/architecture.md): modüller ve davranış akışı
- [Yol haritası](docs/roadmap.md): Faz 1A–2D geliştirme planı
- [Donanım](docs/hardware.md): kesinleşmiş ve TBD donanım listesi
- [Kurulum](docs/setup.md): Pi ayarları, firmware, kalibrasyon, ilk ayağa kalkma
- [Bağlantılar](docs/wiring.md): UART, güç zinciri, kanal ataması, ilk açılış sırası
- [CAD referansı](docs/cad-reference.md): mekanik referans platform ve lisans notları
- [Teknik kararlar](docs/decisions.md): karar geçmişi

```text
firmware/      Alt modül: ggldnl/H-0996-Firmware (Servo 2040, C++, GPL-3.0)
controller/    Alt modül: ggldnl/H-0996-Controller (Pi istemcisi, Python, GPL-3.0)
config/        hexapod.yml: robota özel ölçüler, kanal ataması, kalibrasyon, güvenlik sınırları
cad/           Projeye göre değiştirilmiş CAD parçaları (upstream CAD kopyalanmaz)
docs/          Proje belgeleri
experiments/   Deney kayıtları
software/      Pi tarafı kendi yazılımımız: bringup, Faz 2'de vision ve decision
```

Kendi kodumuz upstream'i değiştirmez; robota özel her şey `config/hexapod.yml` içindedir.

## Durum

Proje başlangıç aşamasındadır. Yürüyüş yazılımı upstream'den hazır gelir, ancak bu robotta henüz donanımda doğrulanmamıştır. YOLO ve PUSH/AVOID davranışları henüz uygulanmamıştır.
