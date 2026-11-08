#include "frame.h"

#include <string.h>

static void put16(uint8_t *out, uint16_t v) {
    out[0] = (uint8_t)v;
    out[1] = (uint8_t)(v >> 8);
}

static void put32(uint8_t *out, uint32_t v) {
    for (unsigned i = 0; i < 4; ++i) out[i] = (uint8_t)(v >> (8 * i));
}

static uint16_t crc16(const uint8_t *data, size_t len) {
    uint16_t crc = 0xffff;
    for (size_t i = 0; i < len; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (unsigned j = 0; j < 8; ++j)
            crc = (crc & 0x8000U) ? (uint16_t)((crc << 1) ^ 0x1021U)
                                  : (uint16_t)(crc << 1);
    }
    return crc;
}

size_t c5_frame_encode(uint8_t *out, size_t capacity,
                       const uint8_t *payload, size_t length,
                       uint32_t sequence, uint32_t uptime_ms) {
    if (!out || (!payload && length) || length > C5_FRAME_MAX_PAYLOAD ||
        capacity < length + C5_FRAME_OVERHEAD) return 0;
    memcpy(out, "C5RX", 4);
    put16(out + 4, (uint16_t)length);
    put32(out + 6, sequence);
    put32(out + 10, uptime_ms);
    if (length) memcpy(out + 14, payload, length);
    put16(out + 14 + length, crc16(out + 4, 10 + length));
    return C5_FRAME_OVERHEAD + length;
}
