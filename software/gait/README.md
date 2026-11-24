# software/gait

Yürüyüşün kendisi Servo 2040 üzerindeki firmware'dedir (`firmware/src/core/gait.hpp`): tripod, wave ve ripple. Parametreler `controller/hexapod/config/config.yml` içindeki `gaits` bölümündedir.

Bu klasör Faz 1C karşılaştırması için analiz kodunu tutacaktır: `software.bringup walk --log` ile kaydedilen CSV dosyalarından hız, yanal sapma, ortalama/tepe akım ve enerji (V × A × süre) hesaplanması.
