"""Exercise application startup when panel initialization fails."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
#include <assert.h>
#include "capture.h"
#include "display.h"
void app_main(void);
static int capture_started;
esp_err_t c5_display_init(void) { return 7; } // Simulate LCD failure.
esp_err_t c5_display_last_error(void) { return 7; }
esp_err_t c5_capture_init(int pin, int baud) {
    assert(pin == 4 && baud == 115200);
    capture_started = 1;
    return ESP_OK;
}
void c5_capture_run(void) { assert(capture_started); }
int main(void) { app_main(); assert(capture_started); return 0; }
"""


class StartupFailureTests(unittest.TestCase):
    def test_lcd_failure_does_not_block_uart_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "esp_err.h").write_text(
                "#pragma once\ntypedef int esp_err_t;\n#define ESP_OK 0\n"
                "#define ESP_ERROR_CHECK(x) do { if ((x) != ESP_OK) __builtin_trap(); } while (0)\n"
            )
            (root / "sdkconfig.h").write_text(
                "#define CONFIG_C5_UART_RX_GPIO 4\n#define CONFIG_C5_UART_BAUD 115200\n"
            )
            (root / "harness.c").write_text(HARNESS)
            binary = root / "startup"
            subprocess.run(
                ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 "-I", str(root), "-I", str(ROOT / "main/include"),
                 str(ROOT / "main/main.c"), str(root / "harness.c"),
                 "-o", str(binary)], check=True
            )
            subprocess.run([str(binary)], check=True, timeout=5)
