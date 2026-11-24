// Firmware giriş noktası.
//
// Döngü: UART'ı olabildiğince hızlı boşalt (baytlar -> FrameParser -> router ->
// gerekirse yanıt) ve robotu cfg::CONTROL_RATE_HZ hızında bir adım ilerlet. Bu
// yalnızca basit bir zamanlayıcıdır

#include "hardware/gpio.h"
#include "hardware/uart.h"
#include "pico/stdlib.h"

#include "core/config.hpp"
#include "communication/protocol.hpp"
#include "core/robot.hpp"
#include "core/router.hpp"
#include "communication/servo2040_hal.hpp"

// GPIO 20/21, RP2040'ta UART1'dir (cfg::UART_TX_PIN / cfg::UART_RX_PIN)
static uart_inst_t *const UART_PORT = uart1;

static void uart_setup() {
  uart_init(UART_PORT, cfg::BAUD);
  gpio_set_function(cfg::UART_TX_PIN, GPIO_FUNC_UART);
  gpio_set_function(cfg::UART_RX_PIN, GPIO_FUNC_UART);
  uart_set_format(UART_PORT, 8, 1, UART_PARITY_NONE);
  uart_set_fifo_enabled(UART_PORT, true);
}

int main() {
  uart_setup();

  // Donanım arayüzünü kur ve LED'leri yak-söndür
  hal::Servo2040 hw;
  hw.init();
  hw.boot_flash();

  // Robotu oluştur ve donanıma erişim ver
  robot::Robot robot(hw);
  proto::FrameParser parser;

  const uint64_t period_us = uint64_t(1.0e6f / cfg::CONTROL_RATE_HZ);
  uint64_t last_us = time_us_64();

  while (true) {

    // Haberleşme: bekleyen her şeyi oku ve tamamlanan her çerçeveyi işle
    while (uart_is_readable(UART_PORT)) {
      if (parser.feed(uart_getc(UART_PORT))) {
        uint8_t reply[cfg::MAX_PAYLOAD];
        uint8_t reply_op = 0;
        const uint8_t n =
            router::dispatch(robot, parser.opcode(), parser.payload(),
                             parser.length(), reply, reply_op);
        if (n > 0) {
          uint8_t frame[cfg::MAX_PAYLOAD + 5];
          const size_t m = proto::encode_frame(reply_op, reply, n, frame);
          for (size_t i = 0; i < m; ++i)
            uart_putc_raw(UART_PORT, frame[i]);
        }
      }
    }

    // Kontrol: sabit frekanslı adım
    const uint64_t now = time_us_64();
    if (now - last_us >= period_us) {
      const float dt = float(now - last_us) * 1.0e-6f;
      last_us = now;
      robot.update(dt);
    }

    tight_loop_contents();
  }
}
