# CAD Referansı

## Kaynak

Mekanik başlangıç noktası: [ggldnl/Hexapod-Hardware](https://github.com/ggldnl/Hexapod-Hardware)

Korunacak yaklaşımlar:

- MG996R montaj geometrisi
- F686ZZ rulmanlı servo yataklaması
- M3 vida ve M3 heat-set insert ile montaj

Projeye göre yeniden tasarlanacak parçalar:

- Raspberry Pi 5 yuvası
- PCA9685 montajı
- Kamera yuvası (kamera modeli TBD)
- Güç sistemi yerleşimi (batarya ve final güç dönüştürücü TBD)
- Ön itme tamponu (Faz 2 PUSH ve kontrollü gövde teması için)

## Tek Bacak İçin Referans Parçalar

| Parça | Adet | Not |
| --- | --- | --- |
| femur | 1 | |
| tibia | 1 | |
| bracket_A | 3 | Upstream'de STL olarak mevcut; STEP tarafında `motor_bracket.step` olarak görünüyor |
| bracket_B | 3 | Upstream'de STL olarak mevcut; STEP tarafında `motor_bracket.step` olarak görünüyor |
| servo_mod | 3 servo için gerekli adet | Adet montaj sırasında doğrulanacak |
| F686ZZ rulman | 3 | Satın alınan parça |

Değiştirilen parçalar `cad/modified/` altında tutulacak ve hangi upstream parçadan türetildikleri belirtilecektir.

## Lisans Notu

> Upstream repository'de açık bir LICENSE dosyası doğrulanmadan kaynak CAD dosyaları doğrudan bu repoya kopyalanmamalıdır.
>
> STEP dosyaları yerel CAD geliştirmesinde referans olarak kullanılabilir; kamuya açık türetilmiş CAD paylaşımı öncesi lisans/izin teyit edilmelidir.

Kontrol notu (2026-10-20): Upstream repoda bir `LICENSE.md` dosyası bulunmaktadır ve GitHub bunu **CERN-OHL-W-2.0** (CERN Open Hardware Licence v2 – Weakly Reciprocal) olarak tanımlamaktadır. Bu lisans; kaynak gösterilmesini, değiştirilen dosyaların aynı lisansla paylaşılmasını ve değişikliklerin belirtilmesini gerektirebilir. Lisans koşulları ekipçe okunup türetilmiş CAD paylaşımı için onaylanana kadar upstream STL/STEP dosyaları bu repoya commit edilmeyecektir. Bu repoda yalnızca kaynak bağlantısı, kullanılan parçalar ve değiştirilecek parçalar belgelenir.
