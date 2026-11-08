#include "capture.h"
#include "frame.h"

#include <stdint.h>

#include "driver/gpio.h"
#include "driver/uart.h"
#include "driver/usb_serial_jtag.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "sdkconfig.h"

#if !CONFIG_IDF_TARGET_ESP32C5 || !CONFIG_ESPTOOLPY_FLASHSIZE_32MB
#error "Waveshare NXRX 32R8U profile requires ESP32-C5 and 32 MB flash"
#endif
#if !CONFIG_ESP_CONSOLE_NONE || !CONFIG_ESP_CONSOLE_SECONDARY_NONE
#error "Capture owns native USB Serial/JTAG; disable competing console writers"
#endif

#define CAPTURE_UART UART_NUM_1
#define CAPTURE_RX_BUFFER 4096
#define EVENT_QUEUE_SIZE 64

static QueueHandle_t events;

esp_err_t c5_capture_init(int rx_gpio, int baud) {
    if (rx_gpio != 4) return ESP_ERR_INVALID_ARG;
    // UART1 is exclusively owned here from reset. NO_CHANGE leaves all output
    // routes untouched; it does not detach a previously configured TX route.
    // No other component may configure UART1 or write to native USB.
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
    err = gpio_set_direction(rx_gpio, GPIO_MODE_INPUT);
    if (err != ESP_OK) return err;
    err = gpio_set_pull_mode(rx_gpio, GPIO_FLOATING);
    if (err != ESP_OK) return err;
    err = uart_driver_install(CAPTURE_UART, CAPTURE_RX_BUFFER, 0,
                              EVENT_QUEUE_SIZE, &events, 0);
    if (err != ESP_OK) return err;
    usb_serial_jtag_driver_config_t usb = {
        .tx_buffer_size = 1024,
        .rx_buffer_size = 256,
    };
    return usb_serial_jtag_driver_install(&usb);
}

static void send_frame(const uint8_t *frame, size_t size, uint32_t *failures) {
    // v6.1 enqueues a complete ring-buffer item or returns zero. A successful
    // enqueue is NOT acknowledgement by the host. No unbounded stdout writes.
    int sent = usb_serial_jtag_write_bytes(frame, size, pdMS_TO_TICKS(20));
    if (sent != (int)size) ++*failures;
}

void c5_capture_run(void) {
    uint8_t input[C5_FRAME_MAX_PAYLOAD];
    uint8_t frame[C5_FRAME_MAX_PAYLOAD + C5_FRAME_OVERHEAD];
    uint32_t sequence = 0;
    uint32_t counters[C5_STATUS_COUNTERS] = {0};
    int64_t next_status = 0;
    for (;;) {
        // Poll data independently of events: a full event queue must not stall RX.
        // Reading frees the driver's stashed RX data; do not flush buffered bytes.
        int n = uart_read_bytes(CAPTURE_UART, input, sizeof(input), pdMS_TO_TICKS(20));
        uart_event_t event;
        for (unsigned i = 0; i < EVENT_QUEUE_SIZE &&
             xQueueReceive(events, &event, 0) == pdTRUE; ++i) {
            switch (event.type) {
                case UART_FIFO_OVF: ++counters[0]; break;
                case UART_BUFFER_FULL: ++counters[1]; break;
                case UART_PARITY_ERR: ++counters[2]; break;
                case UART_FRAME_ERR: ++counters[3]; break;
                default: break;
            }
        }
        int64_t now = esp_timer_get_time() / 1000;
        if (now >= next_status) {
            size_t size = c5_status_encode(frame, sizeof(frame), counters,
                                           sequence++, (uint32_t)now);
            send_frame(frame, size, &counters[4]);
            next_status = now + 1000;
        }
        if (n > 0) {
            size_t size = c5_frame_encode(frame, sizeof(frame), input, (size_t)n,
                                          sequence++, (uint32_t)now);
            send_frame(frame, size, &counters[4]);
        }
    }
}
