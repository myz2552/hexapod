# software/single_leg

Faz 1A tek bacak (Coxa/Femur/Tibia) XYZ ayak pozisyonlama aracı. Donanım üzerinde henüz doğrulanmamıştır.

## Önkoşul

1. [servo_test](../servo_test/README.md) bring-up adımları tamamlanmış olmalı.
2. Üç eklem `calibrate_servo.py` ile şema v2'ye göre kalibre edilmiş olmalı (`config/servo_calibration.yaml`).
3. `config/robot_geometry.yaml` içindeki `tibia_mm` gerçek bacakta ölçülmüş olmalı.

## Kullanım

Repo kökünden. Hedefler **bacak çerçevesinde** mm'dir (bkz. [kinematics](../kinematics/README.md#çerçeveler)).

```bash
# Kuru çalıştırma (varsayılan): IK, eklem açıları ve servo komutları yazdırılır, servo oynamaz.
python -m software.single_leg.move_foot 144.7 0 -100

# Gerçek hareket: başlangıç pozuna gider, ardından interaktif hedefler hız sınırlı uygulanır.
python -m software.single_leg.move_foot 144.7 0 -100 --execute --speed 30
```

İnteraktif modda `x y z` girilir; `q` PWM'i bırakıp çıkar. Erişilemeyen veya kalibre limit dışı
hedefler hareket öncesinde reddedilir. Kuru çalıştırmada kalibrasyon yoksa yalnızca eklem açıları gösterilir.

İlk deneme önerisi: sıfır pozu `(144.7, 0, −100)` ile başlayın, sonra küçük adımlarla (±10 mm)
hedefleri değiştirip ayak ucunun konumunu cetvelle ölçün. Sonuçları `experiments/single_leg/` altına kaydedin.

Faz 1A geçiş ölçütü: tek bacak seçilen XYZ koordinatlarına güvenli ve tekrarlanabilir şekilde ulaşabilmelidir.
