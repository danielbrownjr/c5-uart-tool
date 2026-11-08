idf_component_register(
    SRCS "main.c" "capture.c" "frame.c"
    INCLUDE_DIRS "." "include"
    REQUIRES esp_driver_uart esp_timer
)
