#pragma once
#include "esp_err.h"

esp_err_t c5_capture_init(int rx_gpio, int baud);
void c5_capture_run(void);
