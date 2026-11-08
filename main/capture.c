#include "capture.h"
#include "frame.h"

#include <stdint.h>
#include <stdio.h>

#include "driver/uart.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"

#define CAPTURE_UART UART_NUM_1
#define CAPTURE_RX_BUFFER 4096

esp_err_t c5_capture_init(int rx_gpio, int baud) {
    // No target TX, RTS, CTS, or power connection. UART1 is receive-only.
    const uart_config_t config = {
        .baud_rate = baud,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    esp_err_t err = uart_param_config(CAPTURE_UART, &config);
    if (err != ESP_OK) return err;
    err = uart_set_pin(CAPTURE_UART, UART_PIN_NO_CHANGE, rx_gpio,
                       UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE,
                       UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    if (err != ESP_OK) return err;
    return uart_driver_install(CAPTURE_UART, CAPTURE_RX_BUFFER, 0, 0, NULL, 0);
}

void c5_capture_run(void) {
    uint8_t input[C5_FRAME_MAX_PAYLOAD];
    uint8_t frame[C5_FRAME_MAX_PAYLOAD + C5_FRAME_OVERHEAD];
    uint32_t sequence = 0;
    for (;;) {
        int n = uart_read_bytes(CAPTURE_UART, input, sizeof(input), pdMS_TO_TICKS(20));
        if (n <= 0) continue;
        uint32_t milliseconds = (uint32_t)(esp_timer_get_time() / 1000);
        size_t size = c5_frame_encode(frame, sizeof(frame), input, (size_t)n,
                                      sequence++, milliseconds);
        if (size) {
            // USB Serial/JTAG is the only output. No uart_write_bytes() calls.
            (void)fwrite(frame, 1, size, stdout);
            (void)fflush(stdout);
        }
    }
}
