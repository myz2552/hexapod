# Bağlantılar

## Uyarılar

> **MG996R servolar Raspberry Pi'den veya Servo 2040'ın USB girişinden beslenmemelidir.**
>
> Servolar ayrı 6 V yüksek akım hattından, Servo 2040'ın vidalı klemenslerinden beslenir. USB-C girişi en fazla 3 A taşır.

> **Servo 2040'ın arkasındaki "Separate USB and Ext. Power" izi kesilmelidir.**
>
> Servo hattı 6 V olduğu için bu iz kesilmezse 6 V kartın lojik devresine ve Raspberry Pi 5'in USB portuna ulaşır. Kestikten sonra multimetreyle USB 5 V ile klemens + arasında süreklilik olmadığını doğrulayın. İz kesildikten sonra kartın lojik beslemesi USB'den (Raspberry Pi 5) gelir.

> **Servo 2040 klemensleri sürekli 10 A için tasarlanmıştır.** İlk testlerde kart üstü akım ölçümü izlenmelidir (bkz. [Akım sınırı](#akım-sınırı)).

## Tek Bacak Prototipi (Faz 1A)

```text
Raspberry Pi 5 ──USB (veri + lojik 5 V)──► Servo 2040 ──servo 1/2/3──► MG996R × 3
                                              ▲
                     6 V laboratuvar PSU ──+──┘ (vidalı klemens)
```

| Bağlantı | Kaynak / hedef |
| --- | --- |
| Raspberry Pi 5 USB-A | Servo 2040 USB-C (seri haberleşme + lojik besleme) |
| Servo 2040 klemens + / − | 6 V laboratuvar güç kaynağı |
| Servo 2040 çıkış 1 | Coxa |
| Servo 2040 çıkış 2 | Femur |
| Servo 2040 çıkış 3 | Tibia |

GND referansı USB kablosu üzerinden ortaktır; ayrıca GND kablosu çekmek gerekmez.

## Tam Robot (Faz 1B)

### Güç zinciri

```text
2S LiPo ── 25 A sigorta ── anahtar (≥30 A) ── XT60 Y-ayırıcı ─┬─► UBEC #1 (6,0 V) ──► Servo 2040 klemens ──► 18 × MG996R
                                                              │                        (2200 µF kondansatör)
                                                              └─► UBEC #2 (5,0 V) ──USB-C güç kablosu──► Raspberry Pi 5

Raspberry Pi 5 ──USB (veri + lojik 5 V)──► Servo 2040
```

- Servolar ve Raspberry Pi 5 ayrı UBEC'lerden beslenir; servo akım darbeleri Pi'yi yeniden başlatmaz.
- İki UBEC aynı modeldir; çıkış voltajı jumper/ayar ile seçilir. Hangisinin 6 V, hangisinin 5 V olduğu üzerlerine yazılmalıdır.
- Tüm eksiler (batarya, UBEC'ler, Servo 2040, Pi) dağıtım noktasında ve USB üzerinden ortaktır.

### Kanal ataması

Sağ bacaklar 1–9, sol bacaklar 10–18; her bacakta sıra Coxa → Femur → Tibia. Bacak adları [config/robot_geometry.yaml](../config/robot_geometry.yaml) ile aynıdır.

| Bacak | Coxa | Femur | Tibia | Ayak sensörü (isteğe bağlı) |
| --- | --- | --- | --- | --- |
| front_right | 1 | 2 | 3 | SENSOR_1 |
| middle_right | 4 | 5 | 6 | SENSOR_2 |
| rear_right | 7 | 8 | 9 | SENSOR_3 |
| rear_left | 10 | 11 | 12 | SENSOR_4 |
| middle_left | 13 | 14 | 15 | SENSOR_5 |
| front_left | 16 | 17 | 18 | SENSOR_6 |

Numaralar Servo 2040 üzerindeki servo çıkış numaralarıdır (MicroPython'da `servo2040.SERVO_1` … `servo2040.SERVO_18`). CircuitPython yalnızca 16 servoyu desteklediği için kullanılmamalıdır.

### Kablo kesitleri

| Hat | Kesit |
| --- | --- |
| Batarya → sigorta → anahtar → dağıtım | 14 AWG (2,0 mm²) |
| UBEC #1 → Servo 2040 klemensi | 14–16 AWG, kısa |
| UBEC #2 → USB-C güç kablosu | 18 AWG, kısa (voltaj düşümü) |
| Servo kabloları / uzatmalar | 22 AWG |

### Raspberry Pi 5'in UBEC ile beslenmesi

UBEC, USB-C PD ile 5 A verebildiğini bildiremez. Pi 5 açılır, ancak USB portlarının toplam akımını 600 mA ile sınırlar ve uyarı gösterebilir. Servo 2040 için bu yeterlidir. Gerekirse `/boot/firmware/config.txt` dosyasına `usb_max_current_enable=1` eklenir.

Pi'yi GPIO 5 V pinlerinden beslemek de mümkündür, ancak ters bağlantı kartı bozar; USB-C güç kablosu tercih edilmiştir.

### Akım sınırı

MG996R sınıfı servolar zorlandığında servo başına 2,5–3 A çekebilir. 18 servonun hepsi aynı anda zorlanmadıkça toplam akım bunun çok altında kalır, ancak gerçek değer ölçülmeden bilinmez. Bu nedenle:

- İlk ayağa kalkma ve yürüyüş denemelerinde Servo 2040'ın akım ölçümü kaydedilmelidir.
- Yazılımda, akım 2 saniyeden uzun süre 9 A'yı aşarsa tüm servolar bırakılmalıdır (eşik deneylerden sonra güncellenecek).
- Akım sürekli olarak 10 A'yı aşarsa servo gücü ikiye bölünür: servoların yarısının + kablosu ikinci bir 6 V UBEC'ten beslenir, sinyal ve GND Servo 2040'da kalır.

### Gövde yerleşimi

- Raspberry Pi 5 alt katta, Servo 2040 üstünde M2.5 aralık parçalarıyla.
- Batarya gövdenin altında, cırt bantla.
- UBEC'ler gövdenin iki yanında, havalanabilecekleri yerde.
- Anahtar ve sigorta kolay erişilebilir yerde.

Base parçasının orta boşluğu yaklaşık 65 × 120 mm'dir (STL'den ölçülmüştür); Pi 5 (85 × 56 mm) uzun kenarı ön-arka doğrultusunda sığar. Base içi boş çerçeve olduğundan elektronik için ince bir montaj plakası gerekir (bkz. [cad-reference.md](cad-reference.md)).

### İlk açılış sırası

1. Servo 2040'ın "Separate USB and Ext. Power" izini kesin ve sürekliliği kontrol edin.
2. UBEC #1'i 6,0 V, UBEC #2'yi 5,0 V'a ayarlayıp yüksüz ölçün (5,0–5,2 V uygun).
3. 2200 µF kondansatörü klemenslere kutbuna dikkat ederek bağlayın.
4. Servolar takılı değilken Servo 2040'ı USB ile Pi'ye bağlayın, MicroPython yükleyin, akım ve voltaj okumasını test edin.
5. Bir bacağın servolarını takın; kalibrasyon akışıyla devam edin. Mevcut bring-up ve kalibrasyon araçları ([software/servo_test](../software/servo_test/README.md)) PCA9685 için yazılmıştır ve Servo 2040'a henüz uyarlanmamıştır (bkz. [roadmap.md](roadmap.md)).
6. Tüm bacaklar takıldıktan sonra ilk açılışta robotu bacakları havada kalacak şekilde destek üzerine koyun ve akımı izleyin.
