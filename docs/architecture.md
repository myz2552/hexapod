# Sistem Mimarisi

## Aşama 1: Platform ve Yürüyüş

```text
Mekanik geometri ve eklem sınırları
  -> Servo yönleri ve nötr açı kalibrasyonu
  -> Ters kinematik ve ayak yörüngeleri
  -> Servo sürücüleri
  -> Ayakta durma / Yürüme / Dönme / Durma
```

Bu aşama mekanik tasarım, üretim, güç sistemi ve hareket kontrolünü kapsar.

## Aşama 2: Algı, Bacak Testi ve Karar

```text
Kamera -> YOLO -> Nesne sınıfı ve görüntüde konumu
  -> Görsel itilebilirlik ön tahmini
  -> Yaklaşma ve destek duruşu
  -> Tek bacakla kısa itme testi
  -> Akım ve IMU verilerinin kaydı
  -> Görsel ve fiziksel verilerin birleştirilmesi
  -> Test bacağının yürüyüş konumuna alınması
  -> İtilebilir: gövdeyle iterek ilerleme
     İtilemez: etrafından dolaşma
     Güvenli hareket mümkün değil: durma / geri çekilme
```

Test yalnızca belirsizlikte değil, güvenle değerlendirilebilen nesneler için standart akışta yapılır. Bacakla yoklama ve gövdeyle itme ayrı davranışlardır.

## Modüller

### Mekanik Platform

Gövde, bacak, eklem ve servo yerleşimlerini kapsar. İlk aşamada geometri, motor açı sınırları ve montaj toleransları belirlenir. İkinci aşamada test bacağının erişimi, kamera görüşü ve gövde temas yüzeyi değerlendirilir.

### Güç ve Servo Elektroniği

Güç dağıtımı, servo sürücüleri ve Raspberry Pi bağlantılarını yönetir. İkinci aşamada akım ölçümü eklenir. Test bacağının yükünü destek bacaklarından ayırt etme yöntemi deneylerle seçilir.

### Hareket Kontrolü

Servo kalibrasyonu, duruş, ters kinematik ve yürüyüşü yönetir. İkinci aşamada destek duruşu, test bacağı hareketi, geri alma, gövdeyle itme ve dolaşma eklenir. Yoklama sırasında normal yürüyüş durdurulur; diğer bacaklar destek sağlar.

### Kamera ve YOLO

Görüntü alır, nesne sınıfı, görüntüde konum ve algılama güvenini üretir. Algılama güven skoru doğrudan itilebilirlik olarak kullanılmaz; görsel ön tahmin ayrıca oluşturulur.

### Tek Bacakla İtme Testi

Tek bacakla kontrollü temas ve kısa itme uygular. Test açıları, süre, hareket sınırları ve durdurma eşikleri deneylerle belirlenir. Akım ve IMU verileri kaydedilir; test sonrası bacak yürüyüş konumuna alınır.

### Veri Birleştirme ve Karar

Aynı nesnenin görsel ön tahmini ve fiziksel test bulgularını birlikte değerlendirir. Birleştirme yöntemi ve eşikler kalibrasyonla seçilecektir. Çıktı gövdeyle itme, dolaşma veya güvenli durma kararıdır. Bacak testi ile gövdeyle itme başarısı arasındaki ilişki doğrulanacaktır.

### Deney Kaydı

Servo açıları, hareket komutları, görsel tahmin, fiziksel test, karar ve gerçek hareket sonucu ortak deneme kimliğiyle kaydedilir.

## Tasarım İlkeleri

- İkinci aşamadan önce ayakta durma ve yürüyüş doğrulanmalıdır.
- Servo açıları ve hareket sınırları belgelenmelidir.
- Görsel tahmin, test sonucu ve hareket başarısı ayrı kaydedilmelidir.
- Bacak testi sırasında destek duruşu korunmalıdır.
- Gövdeyle itme başarısızsa robot durmalı; uygun alan varsa dolaşma değerlendirilmelidir.
