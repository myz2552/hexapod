# software/sensors

IMU (model TBD) ve gerekirse harici akım sensörü okuma (Faz 2C).

Servo hattının toplam akımı ve voltajı Servo 2040 tarafından ölçülür ve telemetride gelir (`HexapodClient.get_telemetry()`, `get_current()`, `get_voltage()`). Faz 2C kontrollü temas için çözünürlüğü veya örnekleme hızı yetmezse harici sensör (INA226 / INA260) eklenecektir; deneylerden sonra belirlenecek. Servo 2040'ın Qw/ST soketi UART için kullanıldığından IMU ve ek sensörler Raspberry Pi'nin I2C hattına bağlanır.
