# experiments/walking

Faz 1B-1C deneyleri: ayakta durma akımı, tripod ve wave yürüyüşü, hız, yanal sapma, dönüş, durma, akım ve enerji karşılaştırması.

Telemetri `python -m software.bringup walk --gait <tripod|wave> --vx <mm/s> --log runs/<ad>.csv` ile kaydedilir. Her deneme için yürüyüş tipi, hız komutu, ölçülen mesafe/süre, yanal sapma ve CSV dosyasının özeti (ortalama/tepe akım, en düşük voltaj) buraya yazılır.

Kayıt formatı için bkz. [CONTRIBUTING.md](../../CONTRIBUTING.md#deney-kaydı).
