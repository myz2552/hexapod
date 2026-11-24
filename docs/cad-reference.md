# CAD Referansı

## Kaynak

Mekanik tasarım [ggldnl/H-0996-Hardware](https://github.com/ggldnl/H-0996-Hardware) deposundan alınmıştır (commit `5d695c1`). STL, STEP, URDF ve montaj medyası bu repoda [hardware/](../hardware/README.md) klasöründedir; dosyalar değiştirilmeden kopyalanmış, README Türkçeye çevrilmiştir.

| Klasör | İçerik |
| --- | --- |
| `hardware/CAD/stl/parts/` | Basılacak parçalar |
| `hardware/CAD/step/parts/` | Düzenlemek için STEP dosyaları |
| `hardware/CAD/stl/hardware/` | Simülasyon/URDF modelleri (servo, batarya, elektronik); basılmaz |
| `hardware/hexapod.urdf` | Robotun URDF modeli |
| `hardware/media/` | Montaj videoları ve fotoğrafları |
| `hardware/CAD/modified/` | Projeye göre değiştirdiğimiz parçalar |

## Basılacak parçalar (tam robot, PCB'siz)

| Parça | Adet |
| --- | --- |
| base | 1 |
| top_stiffeners | 1 |
| bottom_stiffeners | 1 |
| femur | 6 |
| tibia | 6 |
| bracket_A | 18 |
| bracket_B | 18 |
| servo_mod | 18 |
| battery_mount | 1 (Hobbywing UBEC'ler için uyarlanacak) |
| electronics_mount | 1 |

Tek bacak testi için: femur 1, tibia 1, bracket_A 3, bracket_B 3, servo_mod 3.

## Projeye göre değiştirilecek parçalar

- `battery_mount` UBEC yuvaları: upstream'in iki kanallı 8 A UBEC'ine göre tasarlanmıştır. Kullandığımız Hobbywing 10A V2-Car (45 × 20 × 16,2 mm) ve 5A V2-Air (50 × 17 × 10 mm) için yuvalar uyarlanacak ya da UBEC'ler cırt bant/kelepçeyle sabitlenecek.
- Kamera yuvası (kamera modeli TBD).
- Ön itme tamponu (Faz 2 PUSH ve kontrollü gövde teması için).
- Sigorta yuvası (isteğe bağlı).

Değiştirilen her parça `hardware/CAD/modified/` altına, hangi upstream parçadan türetildiği ve neyin değiştiği yazılarak konur.

## Lisans

Tasarım **CERN-OHL-W-2.0** (CERN Open Hardware Licence v2 – Weakly Reciprocal) lisanslıdır ([hardware/LICENSE.md](../hardware/LICENSE.md)). Bu repoda uyulması gerekenler:

- Kaynak (ggldnl/H-0996-Hardware) ve lisans metni korunur.
- Değiştirilen parçalar aynı lisansla paylaşılır ve değişiklikler belirtilir (`hardware/CAD/modified/` içindeki notlar).
- Sunum ve raporlarda mekanik tasarımın kaynağı belirtilir.
