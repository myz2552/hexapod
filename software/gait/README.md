# software/gait

Yürüyüşün kendisi Servo 2040 üzerindeki upstream firmware'dedir (`firmware/src/core/gait.hpp`): tripod, wave ve ripple. Parametreler `config/hexapod.yml` içindeki `gaits` bölümündedir.

Bu klasör Faz 1C karşılaştırması için analiz kodunu tutacaktır: `software.bringup walk --log` ile kaydedilen CSV dosyalarından hız, yanal sapma, ortalama/tepe akım ve enerji (V × A × süre) hesaplanması.
