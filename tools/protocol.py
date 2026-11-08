"""Incremental decoder for C5 UART Tool's framed USB transport."""

from dataclasses import dataclass

MAGIC = b"C5RX"
STATUS_MAGIC = b"C5ST"
STATUS_FIELDS = ("uart_fifo_overflow", "uart_buffer_full", "uart_parity_error",
                 "uart_frame_error", "usb_enqueue_failures")
MAX_PAYLOAD = 256
OVERHEAD = 16


def crc16(data: bytes) -> int:
    value = 0xFFFF
    for byte in data:
        value ^= byte << 8
        for _ in range(8):
            value = ((value << 1) ^ 0x1021) & 0xFFFF if value & 0x8000 else (value << 1) & 0xFFFF
    return value


@dataclass(frozen=True)
class Frame:
    sequence: int
    uptime_ms: int
    payload: bytes
    kind: str = "data"


class Decoder:
    def __init__(self):
        self.buffer = bytearray()
        self.corrupt = 0

    def feed(self, data: bytes) -> list[Frame]:
        self.buffer.extend(data)
        frames = []
        while True:
            positions = [p for magic in (MAGIC, STATUS_MAGIC)
                         if (p := self.buffer.find(magic)) >= 0]
            if not positions:
                # Preserve a possible split magic prefix.
                self.buffer[:] = self.buffer[-3:]
                break
            pos = min(positions)
            if pos:
                del self.buffer[:pos]
            if len(self.buffer) < OVERHEAD:
                break
            length = int.from_bytes(self.buffer[4:6], "little")
            status = self.buffer[:4] == STATUS_MAGIC
            if length > MAX_PAYLOAD or (status and length != 4 * len(STATUS_FIELDS)):
                self.corrupt += 1
                del self.buffer[0]
                continue
            total = OVERHEAD + length
            if len(self.buffer) < total:
                break
            expected = int.from_bytes(self.buffer[total - 2:total], "little")
            actual = crc16(self.buffer[4:total - 2])
            if actual != expected:
                self.corrupt += 1
                del self.buffer[0]
                continue
            frames.append(Frame(
                int.from_bytes(self.buffer[6:10], "little"),
                int.from_bytes(self.buffer[10:14], "little"),
                bytes(self.buffer[14:total - 2]),
                "status" if status else "data",
            ))
            del self.buffer[:total]
        return frames
