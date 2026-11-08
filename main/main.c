#include <stdio.h>

#include "capture.h"
#include "esp_err.h"
#include "sdkconfig.h"

void app_main(void) {
    // Avoid output buffering delaying a USB Serial/JTAG capture.
    setvbuf(stdout, NULL, _IONBF, 0);
    ESP_ERROR_CHECK(c5_capture_init(CONFIG_C5_UART_RX_GPIO, CONFIG_C5_UART_BAUD));
    // Machine-readable marker; host decoder ignores preceding ESP-IDF boot logs.
    puts("C5 UART Tool ready: framed RX only");
    c5_capture_run();
}
