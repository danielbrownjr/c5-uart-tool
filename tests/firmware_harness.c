// Host driver doubles exercise control flow only, never peripheral behavior.
#include <assert.h>
#include <setjmp.h>
#include <string.h>
#include "capture.h"
#include "frame.h"

static jmp_buf done;
static unsigned reads, writes, queue_index;
static uint8_t sent[3][272];
static size_t sizes[3];
static const unsigned types[] = {UART_FIFO_OVF, UART_BUFFER_FULL, UART_PARITY_ERR, UART_FRAME_ERR};

esp_err_t uart_param_config(int uart, const uart_config_t *config) {
    assert(uart == UART_NUM_1 && config->flow_ctrl == UART_HW_FLOWCTRL_DISABLE);
    assert(config->baud_rate == 115200 && config->data_bits == UART_DATA_8_BITS);
    assert(config->parity == UART_PARITY_DISABLE && config->stop_bits == UART_STOP_BITS_1);
    return ESP_OK;
}
esp_err_t uart_set_pin(int uart, int tx, int rx, int rts, int cts, int dtr, int dsr) {
    assert(uart == UART_NUM_1 && rx == 4);
    assert(tx == -1 && rts == -1 && cts == -1 && dtr == -1 && dsr == -1);
    return ESP_OK;
}
esp_err_t gpio_set_direction(int pin, int mode) {
    assert(pin == 4 && mode == GPIO_MODE_INPUT); return ESP_OK;
}
esp_err_t gpio_set_pull_mode(int pin, int mode) {
    assert(pin == 4 && mode == GPIO_FLOATING); return ESP_OK;
}
esp_err_t uart_driver_install(int uart, int rx, int tx, int count, QueueHandle_t *queue, int flags) {
    assert(uart == UART_NUM_1 && rx == 4096 && tx == 0 && count == 64 && flags == 0);
    *queue = (void *)1; return ESP_OK;
}
esp_err_t usb_serial_jtag_driver_install(usb_serial_jtag_driver_config_t *config) {
    assert(config->tx_buffer_size == 1024 && config->rx_buffer_size == 256); return ESP_OK;
}
int uart_read_bytes(int uart, void *data, size_t size, unsigned timeout) {
    assert(uart == UART_NUM_1 && size == 256 && timeout == 20);
    if (++reads == 3) longjmp(done, 1);
    memcpy(data, "\0\xff\r\n", 4); return 4;
}
int xQueueReceive(QueueHandle_t queue, uart_event_t *event, unsigned timeout) {
    assert(queue == (void *)1 && timeout == 0);
    if (queue_index == 4) return 0;
    event->type = types[queue_index++]; return pdTRUE;
}
int64_t esp_timer_get_time(void) { return reads == 1 ? 0 : 1000000; }
int usb_serial_jtag_write_bytes(const void *data, size_t size, unsigned timeout) {
    assert(timeout == 20 && size <= 272);
    // Fail the first UART data enqueue; the next status must expose it.
    if (writes == 1) { ++writes; return 0; }
    unsigned index = writes == 0 ? 0 : writes - 1;
    assert(index < 3);
    memcpy(sent[index], data, size); sizes[index] = size; ++writes;
    return (int)size;
}
int main(void) {
    assert(c5_capture_init(5, 115200) == ESP_ERR_INVALID_ARG);
    assert(c5_capture_init(4, 115200) == ESP_OK);
    if (!setjmp(done)) c5_capture_run();
    assert(writes == 4);
    assert(sizes[0] == 36 && sizes[1] == 36 && sizes[2] == 20);
    assert(memcmp(sent[0], "C5ST", 4) == 0 && sent[0][6] == 0);
    assert(sent[0][14] == 1 && sent[0][18] == 1 && sent[0][22] == 1 && sent[0][26] == 1);
    assert(sent[0][30] == 0 && sent[1][30] == 1 && sent[1][6] == 2);
    assert(memcmp(sent[2], "C5RX", 4) == 0 && sent[2][6] == 3);
    assert(memcmp(sent[2] + 14, "\0\xff\r\n", 4) == 0);
    return 0;
}
