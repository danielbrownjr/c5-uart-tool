#include "display.h"

#include "sdkconfig.h"

#if CONFIG_C5_BOARD_CYD
#include <stdint.h>
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_vendor.h"

// Official NM-CYD-C5 pinout: shared SPI (LCD/touch/SD).
#define LCD_SPI_HOST SPI2_HOST
#define LCD_SCLK 6
#define LCD_MISO 2
#define LCD_MOSI 7
#define LCD_CS 23
#define LCD_DC 24
#define LCD_BL 25
#define TOUCH_CS 1
#define SD_CS 10
#define LCD_WIDTH 320
#define LCD_HEIGHT 240
#define STRIPE_HEIGHT 8

// Test-pattern buffer only. Live UART UI is a later change.
static uint16_t stripe[LCD_WIDTH * STRIPE_HEIGHT];

static esp_err_t panel_test_pattern(esp_lcd_panel_handle_t panel) {
    const uint16_t colors[3] = {0xF800, 0x07E0, 0x001F};
    for (int y = 0; y < LCD_HEIGHT; y += STRIPE_HEIGHT) {
        uint16_t color = colors[(y / 80) % 3];
        for (unsigned i = 0; i < LCD_WIDTH * STRIPE_HEIGHT; ++i) stripe[i] = color;
        esp_err_t err = esp_lcd_panel_draw_bitmap(panel, 0, y, LCD_WIDTH,
                                                  y + STRIPE_HEIGHT, stripe);
        if (err != ESP_OK) return err;
    }
    return ESP_OK;
}

esp_err_t c5_display_init(void) {
    // Keep other shared-SPI targets deselected; their drivers are not active.
    const gpio_config_t selects = {
        .pin_bit_mask = (1ULL << TOUCH_CS) | (1ULL << SD_CS),
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_ERROR_CHECK(gpio_config(&selects));
    ESP_ERROR_CHECK(gpio_set_level(TOUCH_CS, 1));
    ESP_ERROR_CHECK(gpio_set_level(SD_CS, 1));

    const gpio_config_t backlight = {
        .pin_bit_mask = (1ULL << LCD_BL),
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_ERROR_CHECK(gpio_config(&backlight));
    ESP_ERROR_CHECK(gpio_set_level(LCD_BL, 0));

    const spi_bus_config_t spi = {
        .sclk_io_num = LCD_SCLK,
        .mosi_io_num = LCD_MOSI,
        .miso_io_num = LCD_MISO,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = LCD_WIDTH * STRIPE_HEIGHT * sizeof(uint16_t) + 8,
    };
    esp_err_t err = spi_bus_initialize(LCD_SPI_HOST, &spi, SPI_DMA_CH_AUTO);
    if (err != ESP_OK) return err;

    const esp_lcd_panel_io_spi_config_t io_config = {
        .cs_gpio_num = LCD_CS,
        .dc_gpio_num = LCD_DC,
        .spi_mode = 0,
        .pclk_hz = 20 * 1000 * 1000,
        .trans_queue_depth = 10,
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
    };
    esp_lcd_panel_io_handle_t io = NULL;
    err = esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)LCD_SPI_HOST,
                                   &io_config, &io);
    if (err != ESP_OK) return err;

    const esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num = -1,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_BGR,
        .bits_per_pixel = 16,
    };
    esp_lcd_panel_handle_t panel = NULL;
    err = esp_lcd_new_panel_st7789(io, &panel_config, &panel);
    if (err != ESP_OK) return err;
    if ((err = esp_lcd_panel_reset(panel)) != ESP_OK) return err;
    if ((err = esp_lcd_panel_init(panel)) != ESP_OK) return err;
    if ((err = esp_lcd_panel_swap_xy(panel, true)) != ESP_OK) return err;
    if ((err = esp_lcd_panel_disp_on_off(panel, true)) != ESP_OK) return err;
    if ((err = panel_test_pattern(panel)) != ESP_OK) return err;
    return gpio_set_level(LCD_BL, 1);
}
#else
esp_err_t c5_display_init(void) { return ESP_OK; }
#endif
