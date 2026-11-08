#include "capture.h"
#include "esp_err.h"
#include "sdkconfig.h"

void app_main(void) {
    ESP_ERROR_CHECK(c5_capture_init(CONFIG_C5_UART_RX_GPIO, CONFIG_C5_UART_BAUD));
    c5_capture_run();
}
