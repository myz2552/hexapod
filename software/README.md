# software

Raspberry Pi 5 üzerinde çalışan yazılım. Servo PWM sinyalleri I2C üzerinden PCA9685 ile üretilir.

```text
software/
├── servo_test/   PCA9685 ile tek servo testleri
├── single_leg/   Faz 1A tek bacak kontrolü
├── kinematics/   inverse kinematics (IK)
├── gait/         tripod gait
├── vision/       kamera + YOLO
├── decision/     FORWARD / PUSH / AVOID / STOP/BACK
└── sensors/      akım sensörü ve IMU
```

Servo kalibrasyon değerleri `config/` altındaki YAML dosyalarından okunur.
