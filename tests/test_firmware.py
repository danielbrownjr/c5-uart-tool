"""Run the real capture loop against bounded host driver doubles."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STUBS = r'''
#include <stddef.h>
#include <stdint.h>
typedef int esp_err_t;
typedef void *QueueHandle_t;
typedef struct { int type; } uart_event_t;
typedef struct { int baud_rate, data_bits, parity, stop_bits, flow_ctrl, source_clk; } uart_config_t;
typedef struct { unsigned tx_buffer_size, rx_buffer_size; } usb_serial_jtag_driver_config_t;
#define CONFIG_IDF_TARGET_ESP32C5 1
#define CONFIG_ESPTOOLPY_FLASHSIZE_32MB 1
#define CONFIG_ESP_CONSOLE_NONE 1
#define CONFIG_ESP_CONSOLE_SECONDARY_NONE 1
#define ESP_OK 0
#define ESP_ERR_INVALID_ARG 1
#define UART_NUM_1 1
#define UART_DATA_8_BITS 8
#define UART_PARITY_DISABLE 0
#define UART_STOP_BITS_1 1
#define UART_HW_FLOWCTRL_DISABLE 0
#define UART_SCLK_DEFAULT 0
#define UART_PIN_NO_CHANGE -1
#define GPIO_MODE_INPUT 1
#define GPIO_FLOATING 0
#define UART_FIFO_OVF 1
#define UART_BUFFER_FULL 2
#define UART_PARITY_ERR 3
#define UART_FRAME_ERR 4
#define pdTRUE 1
#define pdMS_TO_TICKS(ms) (ms)
esp_err_t uart_param_config(int, const uart_config_t *);
esp_err_t uart_set_pin(int, int, int, int, int, int, int);
esp_err_t gpio_set_direction(int, int);
esp_err_t gpio_set_pull_mode(int, int);
esp_err_t uart_driver_install(int, int, int, int, QueueHandle_t *, int);
esp_err_t usb_serial_jtag_driver_install(usb_serial_jtag_driver_config_t *);
int uart_read_bytes(int, void *, size_t, unsigned);
int xQueueReceive(QueueHandle_t, uart_event_t *, unsigned);
int64_t esp_timer_get_time(void);
int usb_serial_jtag_write_bytes(const void *, size_t, unsigned);
'''


class FirmwareFlowTests(unittest.TestCase):
    def test_rx_only_overflow_and_usb_failure_reporting(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'stubs.h').write_text(STUBS)
            for header in ('esp_err.h', 'sdkconfig.h', 'esp_timer.h',
                           'driver/uart.h', 'driver/gpio.h', 'driver/usb_serial_jtag.h',
                           'freertos/FreeRTOS.h', 'freertos/queue.h'):
                path = root / header
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            binary = root / 'flow'
            subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=undefined', '-include', str(root / 'stubs.h'),
                '-I', folder, '-I', str(ROOT / 'main/include'),
                str(ROOT / 'tests/firmware_harness.c'), str(ROOT / 'main/capture.c'),
                str(ROOT / 'main/frame.c'), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=5)
