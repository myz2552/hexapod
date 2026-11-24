#pragma once
//
// robot::Robot her şeyi bu soyut arayüz üzerinden sürer; böylece tüm davranış
// katmanı host üzerinde sahte bir uygulamayla derlenir ve test edilir. Gerçek
// Servo2040 uygulaması (Pico SDK / Pimoroni) platform katmanındadır ve SDK'yı
// içeren tek yer orasıdır

#include <cstdint>

#include "core/config.hpp"

namespace hw {

struct Interface {
  virtual ~Interface() = default;

  // 18 servoyu sürer. Açılar kalibre edilmiş servo uzayı dereceleridir, bacak öncelikli
  // (indis == cfg::servo_channel(leg, joint))
  virtual void write_servos(const float (&deg)[cfg::N_SERVOS]) = 0;

  // Kartın o anda tuttuğu 18 servo açısını geri okur (write_servos ile aynı birim ve
  // sıra). Ayağa kalkmayı bir poz varsaymak yerine bacakların gerçekte bulunduğu
  // yerden başlatmak için kullanılır.
  virtual void read_servos(float (&deg)[cfg::N_SERVOS]) = 0;

  // Servo güç hattını açar/kapatır (cfg::POWER_CUTOFF_PIN)
  virtual void set_power(bool on) = 0;

  // Hat telemetrisi
  virtual float read_voltage() = 0; // volt
  virtual float read_current() = 0; // amper

  // Durum LED'i/LED'leri
  virtual void set_led(uint8_t mode, uint8_t r, uint8_t g, uint8_t b,
                       float freq_hz) = 0;

  // Zamana bağlı LED animasyonunu (ör. yanıp sönme) ilerletir. Robot bunu her
  // kontrol döngüsünde çağırır; SOLID modlarda hiçbir şey yapmaz
  virtual void update_leds() = 0;

  // Yapılandırılan fiziksel kalibrasyon. Saf çekirdek mantıksal kanallar ve servo
  // uzayı dereceleriyle çalışır ve bunlara hiç ihtiyaç duymaz; yalnızca gerçek sürücü
  // duyar, bu yüzden varsayılan olarak hiçbir şey yapmazlar. Host'taki sahte uygulama
  // bunları yok sayar ve mantıksal kanalları doğrudan çizer.
  //   set_servo_calibration: bir servo için ölçülmüş darbe genişlikleri. Servo uzayı
  //     sınırlarını [min_deg, max_deg] aralığını [min_us, max_us] aralığına eşler, sıfır mid_us'tadır.
  //   set_servo_pin: mantıksal bir kanalı hangi fiziksel çıkışın sürdüğü (yeniden kablolama).
  virtual void set_servo_calibration(uint8_t /*channel*/, uint16_t /*min_us*/,
                                     uint16_t /*mid_us*/, uint16_t /*max_us*/) {}
  virtual void set_servo_pin(uint8_t /*channel*/, uint8_t /*pin*/) {}

  // Düşük seviye kalibrasyon jog'u: tek bir servoyu ham bir darbeye sürer, gerekirse
  // güç hattını açar, durum makinesinden bağımsızdır. pulse_us == 0 o kanalı bırakır
  // (devre dışı bırakır); son aktif kanal bırakılınca güç hattı kesilir. Sahte uygulamada etkisizdir.
  virtual void jog_servo(uint8_t /*channel*/, uint16_t /*pulse_us*/) {}
};

struct Proxy : hw::Interface {

  // Durum
  float servos[cfg::N_SERVOS] = {};
  bool wrote = false;
  bool powered = false;
  float volts = 7.4f;
  float amps = 0.5f;
  int led_calls = 0;
  int led_updates = 0;

  void write_servos(const float (&deg)[cfg::N_SERVOS]) override {
    for (int i = 0; i < cfg::N_SERVOS; ++i)
      servos[i] = deg[i];
    wrote = true;
  }

  void read_servos(float (&deg)[cfg::N_SERVOS]) override {
    for (int i = 0; i < cfg::N_SERVOS; ++i)
      deg[i] = servos[i];
  }

  void set_power(bool on) override { powered = on; }
  
  float read_voltage() override { return volts; }
  
  float read_current() override { return amps; }
  
  void set_led(uint8_t, uint8_t, uint8_t, uint8_t, float) override {
    ++led_calls;
  }

  void update_leds() override { ++led_updates; }
};

} // namespace hw