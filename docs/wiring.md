# Bağlantılar

Elektronik mimari upstream [H-0996](https://github.com/ggldnl/H-0996-Hardware) ile aynıdır: tek bir Pimoroni Servo 2040, 2S LiPo ve iki UBEC. Upstream'in özel PCB'si kullanılmaz; kablolama elle yapılır. Farklar yalnızca UBEC modelleri ve önerilen ana sigortadır.

## Uyarılar

> **UBEC voltaj anahtarları yanlış konumdaysa kartlar yanar.**
>
> - Servo UBEC'i (Hobbywing 10A V2-Car): yalnızca **6,0 V**. 7,4 V ve 8,4 V konumları MG996R'yi bozar.
> - Pi UBEC'i (Hobbywing 5A V2-Air): yalnızca **5,0 V**. 6,0 V ve 7,4 V konumları Raspberry Pi 5'i ve Servo 2040'ı yakar.
>
> Her UBEC'in üzerine voltajını yazın ve çıkışı bağlamadan önce multimetreyle ölçün.

> **Servo 2040'ın arkasındaki "Separate USB and Ext. Power" izi kesilmelidir.**
>
> Servo hattı 6 V'tur ve kartın lojik beslemesi Raspberry Pi'nin 5 V'undan gelir. İz kesilmezse 6 V servo hattı Pi'nin 5 V hattına bağlanır. Kestikten sonra multimetreyle kartın 5 V pini ile servo klemensi + arasında süreklilik olmadığını doğrulayın.

> **MG996R servolar Raspberry Pi'den beslenmez.** Servo gücü yalnızca Servo 2040'ın vidalı klemensinden gelir. Klemensler sürekli 10 A için tasarlanmıştır; firmware toplam akım 12 A'yı aşınca servoları keser (`safety.current_max`).

## Raspberry Pi 5 ↔ Servo 2040 (UART)

Upstream firmware UART1'i kullanır: GP20 (TX) ve GP21 (RX). Bu pinler Servo 2040'ın Qw/ST soketindeki SDA ve SCL'dir. Bağlantı çaprazdır; her tarafın TX'i diğerinin RX'ine gider.

| Raspberry Pi 5 | Servo 2040 | Not |
| --- | --- | --- |
| Pin 4 (5V) | 5V pini | Servo 2040'ın lojik beslemesi |
| Pin 6 (GND) | GND | Ortak GND |
| Pin 8 (GPIO14, TXD) | GP21 / Qw/ST SCL (RX) | |
| Pin 10 (GPIO15, RXD) | GP20 / Qw/ST SDA (TX) | |

- Hız: 921600 baud. Pi tarafında port `/dev/ttyAMA0` (bkz. [setup.md](setup.md)).
- Qw/ST soketinde 5 V yoktur; 5 V ayrı bir jumper kabloyla kartın 5V pinine gider. Pin yerini Pimoroni'nin Servo 2040 pinout'undan doğrulayın.
- Yanıt gelmiyorsa ilk şüpheli TX/RX'in ters bağlanmasıdır.

## Servo kanal ataması

Atama `controller/hexapod/config/config.yml` içindeki `hardware.pins` ile aynıdır. Yazılımdaki numaralar 0'dan başlar; kartın üzerindeki baskıda çıkışlar 1'den başlar.

| Bacak | Coxa | Femur | Tibia |
| --- | --- | --- | --- |
| front_right | 0 (kart: 1) | 1 (2) | 2 (3) |
| middle_right | 3 (4) | 4 (5) | 5 (6) |
| rear_right | 6 (7) | 7 (8) | 8 (9) |
| rear_left | 9 (10) | 10 (11) | 11 (12) |
| middle_left | 12 (13) | 13 (14) | 14 (15) |
| front_left | 15 (16) | 16 (17) | 17 (18) |

Arka bacakların servo kabloları Servo 2040'a yetişmez; servo uzatma kablosu kullanılır.

## Tek bacak testi (laboratuvar güç kaynağıyla)

```text
Raspberry Pi 5 (kendi adaptörü) ──UART + 5V + GND──► Servo 2040 ──çıkış 1/2/3──► front_right Coxa / Femur / Tibia
                                                        ▲
                         Laboratuvar güç kaynağı 6,0 V ─┘ (vidalı klemens)
```

- Güç kaynağının akım sınırını önce 1 A'e ayarlayın; tek bacak için en fazla 3–4 A yeterlidir.
- Laboratuvar kaynağının eksi ucu klemens −'ye gider; GND ortaklığı UART kablosundaki GND ile sağlanır.

## Tam robot (bataryayla)

```text
2S LiPo ── XT60 ── 25 A sigorta ──┬──► UBEC S: Hobbywing 10A V2-Car (6,0 V, kendi anahtarı) ──► Servo 2040 klemensi ──► 18 × MG996R
                   (önerilir)     │
                                  └──► UBEC P: Hobbywing 5A V2-Air (5,0 V) ──► Raspberry Pi 5 pin 2 (5V) + pin 6 (GND)
                                                                                   │
                                                                                   └── pin 4 (5V) ──► Servo 2040 5V pini (UART kablosu)
Tüm eksiler ortaktır.
```

| Hat | Parça | Kablo |
| --- | --- | --- |
| Batarya → sigorta → iki UBEC girişi | XT60 erkek, 25 A bıçak sigorta + yuvası | 14 AWG |
| UBEC S çıkışı → Servo 2040 klemensi | Hobbywing 10A V2-Car, 6,0 V | 14–16 AWG, kısa |
| UBEC P çıkışı → Pi pin 2 ve 6 | Hobbywing 5A V2-Air, 5,0 V | 18–20 AWG, kısa |
| Pi → Servo 2040 (UART) | Dişi-dişi jumper + Qw/ST jumper kablosu | 22–26 AWG |

- İki UBEC'in girişleri sigortadan sonra paralel bağlanır: + uçlar birlikte, − uçlar birlikte.
- **Sigorta upstream'de yoktur.** Upstream, Servo 2040'ın yazılımla akım kesmesine ve UBEC'lerin çıkış korumasına güvenir. Bu korumalar batarya ile UBEC girişleri arasındaki kabloyu korumaz; bu yüzden 25 A sigorta önerilir.
- Servo hattının açma/kapama anahtarı UBEC S'nin kendi anahtarıdır. Pi hattında anahtar yoktur; tüm sistemi kapatmak için önce Pi'yi kapatın (`sudo shutdown now`), sonra XT60'ı çıkarın.
- Raspberry Pi 5, GPIO 5 V pinlerinden beslendiğinde güç kaynağının 5 A verebildiğini bilemez. `/boot/firmware/config.txt` içine `usb_max_current_enable=1` eklenir. 5,0 V çıkışta kablo uzun veya inceyse Pi düşük voltaj uyarısı verebilir; kabloyu kısa tutun.
- GPIO 5 V pinlerinde ters kutup koruması yoktur. Bağlamadan önce + ve −'yi kontrol edin.

## Gövde yerleşimi

Upstream yerleşimi korunur:

- Batarya gövdenin altında, `battery_mount` üzerinde.
- UBEC'ler `battery_mount`'ın iki yuvasında. Yuvalar upstream'in UBEC modeline göredir; Hobbywing modelleri için yuvalar ekip tarafından uyarlanacaktır (`hardware/CAD/modified/`, bkz. [cad-reference.md](cad-reference.md)).
- Raspberry Pi 5 ve Servo 2040 gövdenin üstünde, `electronics_mount` üzerinde. Servo 2040 M2 vida ve M2 heat-set insert ile takılır.
- Sigorta bataryaya olabildiğince yakın, UBEC S'nin anahtarı kolay erişilebilir yerde.

## İlk açılış sırası

1. Servo 2040'ın "Separate USB and Ext. Power" izini kesin ve sürekliliği kontrol edin.
2. UBEC'lerin anahtarlarını ayarlayın: UBEC S 6,0 V, UBEC P 5,0 V. Bataryayı takıp çıkışları yüksüzken ölçün.
3. Firmware'i Servo 2040'a yükleyin ve Pi'nin UART ayarlarını yapın ([setup.md](setup.md)).
4. Servolar takılı değilken Pi'yi ve Servo 2040'ı bağlayın: `python -m software.bringup telemetry`. Durum `OFF`, voltaj ve akım okunuyor olmalı.
5. Servoları kalibre edin (`controller/calibrate.py`), sonra bacaklara monte edin.
6. Robotu bacakları havada kalacak şekilde bir desteğe koyun ve ilk ayağa kalkmayı orada deneyin: `python -m software.bringup stand`. En yüksek akımı not edin.
