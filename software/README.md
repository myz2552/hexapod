# software

Raspberry Pi 5 üzerinde çalışan yazılım. Servo PWM sinyalleri I2C üzerinden PCA9685 ile üretilir.

```text
software/
├── servo_test/   PCA9685 bring-up ve manuel servo kalibrasyonu (şema v2)
├── hardware/     kalibrasyon (eklem açısı ↔ komut), çoklu PCA9685, hız sınırlı hareket
├── kinematics/   bacak FK/IK, gövde ↔ bacak çerçeveleri
├── single_leg/   Faz 1A XYZ ayak pozisyonlama aracı
├── gait/         tripod gait (henüz yok)
├── vision/       kamera + YOLO (henüz yok)
├── decision/     FORWARD / PUSH / AVOID / STOP/BACK (henüz yok)
└── sensors/      akım sensörü ve IMU (henüz yok)
```

Katmanlar:

```text
gait / single_leg   →  ayak hedefi (mm)
kinematics          →  kinematik eklem açısı (°)
hardware            →  kalibrasyon + hız sınırı → PCA9685 komutu
```

Yapılandırma `config/` altındadır: `robot_geometry.yaml` (bacak ölçüleri, git'te) ve
`servo_calibration.yaml` (fiziksel kalibrasyon, gitignore; örnek: `servo_calibration.example.yaml`).

## Geliştirme

Repo kökünden:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .              # testler ve kuru çalıştırma için (yalnızca PyYAML)
pip install -e ".[hardware]"  # Raspberry Pi üzerinde, PCA9685 erişimi için
python -m unittest discover -s software -t . -v
```

Testler donanım gerektirmez; GitHub Actions her push/PR'da aynı testleri Python 3.11 ve 3.13 ile çalıştırır.
Paket kurmadan da araçlar `python -m software.<paket>.<modül>` ile repo kökünden çalışır.
