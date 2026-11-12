#pragma once
#include "esp_err.h"
// Waveshare has no display; CYD starts with a color-bar bring-up screen.
// The display function intentionally has no UART or USB responsibilities.
esp_err_t c5_display_init(void);
// Readable from a debugger after boot; no unframed USB console output.
esp_err_t c5_display_last_error(void);
