#pragma once
//
// Pimoroni SDK ile konuşan tek dosya budur:
// - PIO0 üzerinde 18 servo
// - PIO1 üzerinde 6 WS2812 LED
// - servo güç hattı (cfg::POWER_CUTOFF_PIN)
// - analog çoklayıcı (voltaj / akım)
//
// Geri kalan her şey (robot::Robot, yürüyüş, gövde, kinematik) SDK'dan bağımsızdır
// ve host üzerinde sahte bir uygulamayla test edilir

#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "servo2040.hpp" // Pimoroni sürücüsü (bu dosyadan, servo2040_hal.hpp'den farklıdır)
#include "analog.hpp"
#include "analogmux.hpp"

#include "core/config.hpp"
#include "communication/protocol.hpp" // proto::LedMode
#include "communication/hardware.hpp"

namespace hal {

using namespace plasma;
using namespace servo;

static_assert(servo2040::NUM_SERVOS == cfg::N_SERVOS,
              "Servo2040 has a different servo count than cfg::N_SERVOS");

class Servo2040 : public hw::Interface {
public:
  Servo2040()
      : servos_(pio0, 0, servo2040::SERVO_1, servo2040::NUM_SERVOS),
        leds_(servo2040::NUM_LEDS, pio1, 0, servo2040::LED_DATA),
        vol_adc_(servo2040::SHARED_ADC, servo2040::VOLTAGE_GAIN),
        cur_adc_(servo2040::SHARED_ADC, servo2040::CURRENT_GAIN,
                 servo2040::SHUNT_RESISTOR, servo2040::CURRENT_OFFSET),
        mux_(servo2040::ADC_ADDR_0, servo2040::ADC_ADDR_1, servo2040::ADC_ADDR_2,
             PIN_UNUSED, servo2040::SHARED_ADC) {}

  // Açılışta, Robot çalışmadan önce bir kez çağrılır
  void init() {
    servos_.init();
    leds_.start();
    gpio_init(cfg::POWER_CUTOFF_PIN);
    gpio_set_dir(cfg::POWER_CUTOFF_PIN, GPIO_OUT);
    gpio_put(cfg::POWER_CUTOFF_PIN, 0); // enerjisiz başla
    for (uint i = 0; i < servo2040::NUM_SERVOS; ++i)
      pin_map_[i] = static_cast<uint8_t>(i); // yapılandırılana kadar birebir eşleme
  }

  // hw::Interface

  // 18 servonun hepsini aynı anda sür: her değeri hazırla, sonra bir kez load() çağır.
  // deg MANTIKSAL kanala göre indekslenir; pin_map_ onu fiziksel çıkışa yönlendirir.
  // Servo uzayı derecesinden darbeye dönüşüm, her servonun yapılandırılmış
  // kalibrasyonunu kullanır (bkz. set_servo_calibration).
  void write_servos(const float (&deg)[cfg::N_SERVOS]) override {
    for (uint i = 0; i < servo2040::NUM_SERVOS; ++i)
      servos_.value(pin_map_[i], deg[i], /*load=*/false);
    servos_.load();
  }

  // Kartın her MANTIKSAL kanalda tuttuğu açıyı geri okur (ServoCluster her servo
  // için son değeri saklar). Eski get_servo_angle() ile aynı işi yapar.
  void read_servos(float (&deg)[cfg::N_SERVOS]) override {
    for (uint i = 0; i < servo2040::NUM_SERVOS; ++i)
      deg[i] = servos_.value(pin_map_[i]);
  }

  // Enerjilendirme = önce servo çıkışlarını aç, sonra güç hattını bağla; enerjiyi
  // kesmek için tersi (PWM'i kapatmadan önce gücü kes)
  void set_power(bool on) override {
    if (on) {
      servos_.enable_all();
      gpio_put(cfg::POWER_CUTOFF_PIN, 1);
    } else {
      gpio_put(cfg::POWER_CUTOFF_PIN, 0);
      servos_.disable_all();
    }
  }

  float read_voltage() override {
    mux_.select(servo2040::VOLTAGE_SENSE_ADDR);
    return vol_adc_.read_voltage();
  }
  float read_current() override {
    mux_.select(servo2040::CURRENT_SENSE_ADDR);
    return cur_adc_.read_current();
  }

  // Tüm şerit için tek renk; BLINK modunu update_leds() sürer
  void set_led(uint8_t mode, uint8_t r, uint8_t g, uint8_t b,
               float freq_hz) override {
    led_mode_ = mode;
    lr_ = r; lg_ = g; lb_ = b;
    led_freq_ = freq_hz;
    led_toggle_us_ = time_us_64();
    led_on_ = true;
    apply(true);
  }

  // LED yanıp sönmesini ilerletir. SOLID modda hiçbir şey yapmaz (şerit zaten ayarlı).
  // hw::Interface: robot bunu her kontrol döngüsünde çağırır
  void update_leds() override {
    if (led_mode_ != uint8_t(proto::LedMode::BLINK) || led_freq_ <= 0.0f)
      return;
    const uint64_t half_us = uint64_t(1.0e6f / (2.0f * led_freq_));
    const uint64_t now = time_us_64();
    if (now - led_toggle_us_ >= half_us) {
      led_toggle_us_ = now;
      led_on_ = !led_on_;
      apply(led_on_);
    }
  }

  // Karta özel kurulum yardımcısı (hw::Interface'in parçası değil): açılışta,
  // kart robota verilmeden önce bir kez çağrılır. Kartın açıldığı belli olsun
  // diye kısa bir animasyon gösterir
  void boot_flash() {

    // (208, 107, 51), robotumun rengine uyan güzel bir turuncu ton

    // Tüm LED'leri aynı anda bir kez yak-söndür
    // for (uint8_t i = 0; i < servo2040::NUM_LEDS; ++i) {leds_.set_rgb(i, 208, 107, 51);
    // sleep_ms(150);
    // for (uint8_t i = 0; i < servo2040::NUM_LEDS; ++i) leds_.set_rgb(i, 0, 0, 0);

    // LED'leri tek tek, sırayla yak
    for (uint8_t i = 0; i < servo2040::NUM_LEDS; ++i) {
      leds_.set_rgb(i, 208, 107, 51);
      sleep_ms(50);
      leds_.set_rgb(i, 0, 0, 0);
    }
  }

  // Yapılandırılan servo başına kalibrasyon: servonun kendi darbe<->açı aktarım
  // fonksiyonu. Montajdan önce BOŞTAKİ servoda ölçülür, bu yüzden eklemin mekanik
  // olarak nerede durduğuna dair bilgi taşımaz. Sabit kural:
  //   min_us <-> -90 derece,  mid_us <-> 0 derece,  max_us <-> +90 derece
  // (mid_us yalnızca (min_us+max_us)/2'dir). Çekirdek kinematiği zaten
  // cfg::DIRECTION/TRIM_DEG ile servo uzayı derecesine çevirmiş ve eklemin
  // cfg::RANGE aralığına kırpmıştır. Bu aralık +-90'ı aşabilir (ör. tibia -120
  // dereceye kadar iner), bu yüzden sınırlar burada devre dışıdır: kalibrasyon bu
  // aralığı -90/+90 referans noktalarından kırpmadan dışa doğru uzatmalıdır.
  void set_servo_calibration(uint8_t channel, uint16_t min_us, uint16_t mid_us,
                             uint16_t max_us) override {
    if (channel >= cfg::N_SERVOS) return;
    Calibration &cal = servos_.calibration(pin_map_[channel]);
    cal.apply_three_pairs(min_us, mid_us, max_us, -90.0f, 0.0f, 90.0f);
    cal.limit_to_calibration(false, false); // +-90'ın ötesine uzat (ör. tibia)
  }

  // Yeniden kablolama: mantıksal bir kanalı hangi fiziksel ServoCluster çıkışının sürdüğü.
  void set_servo_pin(uint8_t channel, uint8_t pin) override {
    if (channel < cfg::N_SERVOS && pin < cfg::N_SERVOS) pin_map_[channel] = pin;
  }

  // Ayrı çalışan kalibrasyon betiği için düşük seviye jog. Tutulan ilk servoda güç
  // hattını açar, hiçbir servo tutulmayınca keser; durum makinesinden bağımsızdır.
  void jog_servo(uint8_t channel, uint16_t pulse_us) override {
    if (channel >= cfg::N_SERVOS) return;
    const uint8_t phys = pin_map_[channel];
    if (pulse_us == 0) { // bırak
      servos_.disable(phys);
      if (jog_held_[channel]) { jog_held_[channel] = false; --jog_active_; }
      if (jog_active_ == 0) gpio_put(cfg::POWER_CUTOFF_PIN, 0);
      return;
    }
    if (jog_active_ == 0) gpio_put(cfg::POWER_CUTOFF_PIN, 1); // gerektiğinde enerjilendir
    servos_.enable(phys);
    servos_.pulse(phys, static_cast<float>(pulse_us)); // Pimoroni pulse() mikrosaniye cinsindendir
    if (!jog_held_[channel]) { jog_held_[channel] = true; ++jog_active_; }
  }

private:
  void apply(bool on) {
    for (uint i = 0; i < servo2040::NUM_LEDS; ++i)
      leds_.set_rgb(i, on ? lr_ : 0, on ? lg_ : 0, on ? lb_ : 0);
  }

  ServoCluster servos_;
  WS2812 leds_;
  Analog vol_adc_, cur_adc_;
  AnalogMux mux_;

  uint8_t led_mode_ = 0, lr_ = 0, lg_ = 0, lb_ = 0;
  float led_freq_ = 0.0f;
  uint64_t led_toggle_us_ = 0;
  bool led_on_ = true;

  // Yapılandırma durumu
  uint8_t pin_map_[cfg::N_SERVOS] = {};   // mantıksal kanal -> fiziksel çıkış
  uint8_t jog_active_ = 0;                // jog_servo() ile şu an tutulan servolar
  bool jog_held_[cfg::N_SERVOS] = {};
};

} // namespace hal
