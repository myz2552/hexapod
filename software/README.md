# software

Raspberry Pi 5 üzerinde çalışan kendi yazılımımız. Hareket kontrolü (durum makinesi, yürüyüş, IK) Servo 2040 üzerindeki firmware'dedir (`firmware/`); Pi ile kart arasındaki protokolü controller istemcisi (`controller/`, `hexapod` paketi) sağlar. Bu klasördeki kod o istemciyi kullanır, kendi protokolü yoktur (bkz. [docs/architecture.md](../docs/architecture.md)).

```text
software/
├── bringup.py    telemetri okuma, ayakta durma, yürüyüş + CSV telemetri kaydı
├── tests/        robot config doğrulaması ve bringup testleri (donanım gerekmez)
├── gait/         yürüyüş karşılaştırma analizleri (yürüyüşün kendisi firmware'de)
├── sensors/      IMU ve gerekirse harici akım sensörü (Faz 2C)
├── vision/       kamera + YOLO (Faz 2A)
└── decision/     FORWARD / PUSH / AVOID / STOP/BACK (Faz 2B-2C)
```

## Kullanım

Kurulum ve donanım adımları: [docs/setup.md](../docs/setup.md). Repo kökünden:

```bash
python -m software.bringup telemetry
python -m software.bringup stand --seconds 10
python -m software.bringup walk --gait wave --vx 40 --seconds 8 --log runs/wave_40.csv
python -m software.bringup --help
```

## Testler

```bash
python -m unittest discover -s software -t . -v   # config + bringup
bash controller/tests/run.sh                       # controller testleri
```

GitHub Actions her push/PR'da ikisini Python 3.11 ve 3.13 ile çalıştırır.

## Faz 2 kodu için kural

Hareket komutları yalnızca `hexapod.HexapodClient` üzerinden gönderilir (`set_velocity`, `stop`, `set_body_pose`, `heartbeat`). Kart 500 ms heartbeat almazsa oturur; YOLO döngüsü uzun sürüyorsa heartbeat ayrı bir iş parçacığından gönderilmelidir.
