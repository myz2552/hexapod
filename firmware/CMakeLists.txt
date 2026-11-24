cmake_minimum_required(VERSION 3.12)

set(NAME hexapod_firmware)

# pico_sdk_import.cmake ve pimoroni_pico_import.cmake dosyalarını bu klasöre kopyalayın
# (Pico SDK / Pimoroni Pico kütüphaneleriyle gelirler; eski firmware'in kullandıklarıyla
# aynıdır). PICO_SDK_PATH ve PIMORONI_PICO_PATH ortam değişkenleri tanımlı olmalıdır.
include(pico_sdk_import.cmake)
include(pimoroni_pico_import.cmake)

project(${NAME} C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# src/ tek include köküdür; her #include oradan başlar, böylece klasör yolda görünür
# (ör. #include "core/config.hpp", "communication/protocol.hpp").
include_directories(src)

add_executable(${NAME} src/main.cpp)

# servo2040_hal.hpp'nin kullandığı Pimoroni sürücüleri.
include(libraries/servo2040/servo2040)
include(drivers/analogmux/analogmux)
include(drivers/analog/analog)

target_link_libraries(${NAME}
    hardware_uart
    pico_stdlib
    servo2040
    analogmux
    analog
)

# UART1 Pi bağlantısıdır; başka hiçbir şey onu sürmesin diye iki stdio arka ucu da kapalı tutulur.
pico_enable_stdio_usb(${NAME} 0)
pico_enable_stdio_uart(${NAME} 0)

pico_add_extra_outputs(${NAME})
