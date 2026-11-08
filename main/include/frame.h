#pragma once

#include <stddef.h>
#include <stdint.h>

#define C5_FRAME_MAX_PAYLOAD 256U
#define C5_FRAME_OVERHEAD 16U
#define C5_STATUS_COUNTERS 5U

// Wire format: "C5RX" + len(u16 LE) + seq(u32 LE) + uptime_ms(u32 LE)
//              + payload(len bytes) + CRC16/CCITT-FALSE(u16 LE).
// CRC covers bytes after magic, including metadata and payload.
size_t c5_frame_encode(uint8_t *out, size_t capacity,
                       const uint8_t *payload, size_t length,
                       uint32_t sequence, uint32_t uptime_ms);

// C5ST: same header/CRC, five u32 LE cumulative counters since boot:
// FIFO overflow, RX buffer full, parity error, framing error, USB enqueue failure.
size_t c5_status_encode(uint8_t *out, size_t capacity,
                        const uint32_t counters[C5_STATUS_COUNTERS],
                        uint32_t sequence, uint32_t uptime_ms);
