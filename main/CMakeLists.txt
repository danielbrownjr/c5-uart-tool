idf_component_register(
    SRCS "main.c" "capture.c" "frame.c" "display.c"
    INCLUDE_DIRS "." "include"
    REQUIRES esp_driver_uart esp_driver_usb_serial_jtag esp_driver_gpio esp_timer esp_lcd esp_driver_spi
)
