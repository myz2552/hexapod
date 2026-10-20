# Bağlantılar

## Uyarı

> **MG996R servolar Raspberry Pi'nin 5 V pininden beslenmemelidir.**
>
> Servolar ayrı 6 V yüksek akım hattından beslenir. Raspberry Pi 5'in 5 V pini servo akımını karşılayamaz; Pi kararsız çalışabilir veya zarar görebilir.

PCA9685 bir PWM kontrol kartıdır ("servo driver" olarak anılsa da servolara güç üretmez). Kartın VCC girişi yalnızca lojik beslemesidir; servo gücü harici kaynaktan gelir.

## Tek Bacak Prototipi

### Raspberry Pi 5 → PCA9685 (I2C ve lojik besleme)

| Raspberry Pi 5 | PCA9685 |
| --- | --- |
| Pin 1 – 3.3V | VCC |
| Pin 3 – SDA (GPIO2) | SDA |
| Pin 5 – SCL (GPIO3) | SCL |
| Pin 6 – GND | GND |

### PCA9685 → Servo Kanalları

| PCA9685 kanalı | Eklem |
| --- | --- |
| CH0 | Coxa |
| CH1 | Femur |
| CH2 | Tibia |

### Güç

| Bağlantı | Kaynak |
| --- | --- |
| Servo + | Harici 6 V |
| Servo GND | Harici PSU GND |

İlk tek bacak testlerinde harici 6 V kaynak olarak laboratuvar güç kaynağı kullanılacaktır.

### Ortak GND

Aşağıdaki GND'ler birbirine bağlı olmalıdır:

- Raspberry Pi 5 GND
- PCA9685 GND
- Servo PSU GND

Ortak GND olmadan PWM sinyalinin referansı tanımsız kalır ve servolar düzensiz hareket edebilir.

```text
Raspberry Pi 5 ──I2C (SDA/SCL, 3.3V)──► PCA9685 ──PWM CH0/CH1/CH2──► MG996R × 3
      │                                    │                             ▲
      └──────────────GND───────────────────┴──────GND──── 6 V PSU ──+────┘
```

## Tam Robot

Tam robotta 2 × PCA9685 aynı I2C hattını paylaşır ve 18 × MG996R'yi sürer. Kart adresleri, kanal ataması, güç dağıtımı, batarya ve final güç dönüştürücü Faz 1B'de belirlenecek ve bu belgeye eklenecektir (TBD).
