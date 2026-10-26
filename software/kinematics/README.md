# software/kinematics

Tek bacak ileri/ters kinematik (FK/IK) ve gövde ↔ bacak çerçeve dönüşümleri. Saf matematik:
donanım, servo komut açısı veya kalibrasyon içermez. Eklem limitleri burada değil,
kalibrasyon katmanında ([software/hardware](../hardware/README.md)) uygulanır.

- `leg.py`: `forward_kinematics`, `inverse_kinematics` (diz-yukarı çözüm), `UnreachableError`
- `geometry.py`: `config/robot_geometry.yaml` yükleme, `body_to_leg` / `leg_to_body`, `foot_ik` / `foot_fk`

Birimler: mm ve derece.

## Geometri

Ölçüler [config/robot_geometry.yaml](../../config/robot_geometry.yaml) dosyasındadır ve
upstream [ggldnl/Hexapod-Hardware](https://github.com/ggldnl/Hexapod-Hardware) URDF'inden
hesaplanmıştır (mekanik parçalar aynıdır):

| Segment | Uzunluk | Not |
| --- | --- | --- |
| Coxa (coxa ekseni → femur ekseni) | 68.0 mm | URDF |
| Femur (femur ekseni → tibia ekseni) | 76.7 mm | URDF |
| Tibia (tibia ekseni → ayak ucu) | ≈100 mm | Mesh tahmini; montajdan sonra kumpasla ölçün |

## Çerçeveler

- **Gövde:** x ileri, y sol, z yukarı; orijin gövde merkezi.
- **Bacak:** orijin coxa ekseni üzerinde, femur ekseni yüksekliğinde; x coxa 0° iken bacağın
  dışa doğru yönü, z yukarı. Tek bacak test standında XYZ hedefleri bu çerçevededir.

## Eklem açı konvansiyonu (sıfır pozu)

Bu açılar **kinematik eklem açısıdır**, servo PWM komut açısı değildir. Kalibrasyondaki
`zero_cmd_deg` tam olarak aşağıdaki sıfır pozunda okunur.

| Eklem | 0° (sıfır pozu) | Pozitif yön |
| --- | --- | --- |
| Coxa | Bacak montaj yönünde (gövdeden dışarı, heading doğrultusunda) | Üstten bakınca saat yönünün tersi |
| Femur | Femur yatay (su terazisi) | Femur ucu yukarı |
| Tibia | Femur yatayken ayak ucu tibia ekseninin tam altında (çekül) | Ayak dışarı/yukarı açılır |

```text
yandan görünüş, sıfır pozu
      coxa ekseni
          │      femur (yatay)
          ●══════○══════════○   ← tibia ekseni
                            │
                            │ tibia (dikey, çekül)
                            ▼ ayak ucu
```

Sıfır pozunda ayak, bacak çerçevesinde `(144.7, 0, −100)` mm noktasındadır.
Referans pozu için (ör. +45°) basit bir 3B baskı açı şablonu veya telefon eğim ölçer kullanın.

## Kullanım

```python
from software.kinematics import load_geometry, inverse_kinematics

geometry = load_geometry()
angles = inverse_kinematics(geometry.segments, 140.0, 0.0, -90.0)  # bacak çerçevesi
angles = geometry.foot_ik("front_left", (180.0, 140.0, -90.0))    # gövde çerçevesi
```

Fiziksel bacakla deneme için [software/single_leg](../single_leg/README.md).
