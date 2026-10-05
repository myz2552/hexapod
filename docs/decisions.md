# Teknik Karar Kayıtları

Bu dosya, proje ilerledikçe alınan önemli teknik kararları kısa biçimde kaydetmek için kullanılır.

## Karar Formatı

Her karar için şu yapı kullanılacaktır:

```text
## YYYY-AA-GG: Karar başlığı

Durum: Önerildi | Kabul edildi | Değiştirildi | İptal edildi

Bağlam:
Kararın neden gerektiği.

Karar:
Seçilen yaklaşım.

Sonuç:
Bu kararın etkileri, artıları ve riskleri.
```

## 2026-10-05: İlk odak yürüyebilen kameralı hexapod platformu olacak

Durum: Kabul edildi

Bağlam:
Projenin uzun vadeli fikri kamerayla çevresini algılayan ve gerektiğinde fiziksel temasla kararını doğrulayan bir hexapod robottur. Ancak bu özelliklerin sağlıklı geliştirilebilmesi için önce mekanik olarak yürüyebilen, elektronik olarak kararlı ve kamera taşıyabilen bir platform gereklidir.

Karar:
İlk sürümün ana hedefi, 3B yazıcıyla üretilmiş, Raspberry Pi ile kontrol edilen, kameradan görüntü alabilen ve temel yürüme / dönme hareketlerini yapabilen bir hexapod robot oluşturmaktır. YOLO, itilebilirlik tahmini, servo akımı ve ivmeölçerle doğrulama gibi özellikler ikinci aşama hedefleri olarak ele alınacaktır.

Sonuç:
Proje daha uygulanabilir bir sırayla ilerler. Önce mekanik, güç, servo kontrolü ve yürüyüş problemleri çözülür. Gelişmiş algı ve karar özellikleri, kararlı bir platform üzerinde daha sonra test edilir.
