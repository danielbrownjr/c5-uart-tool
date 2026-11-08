# C5 UART Tool: hardware preflight and acceptance

**No wiring or flashing is authorized by this document.**

## Board identity gate

Record actual silkscreen, board vendor/revision, C5 module type, which USB-C
connector terminates at native USB GPIO13/14, and which header GPIO is free.
Biscuit image compatibility alone does not prove pinout equivalence.

The default firmware RX pin GPIO4 is provisional. A verified board schematic
must show it is safely exposed and not driven/connected to conflicting hardware.
Select a different verified input-capable pin with `idf.py menuconfig` if needed.
Do not use UART0 TX/RX shared with an onboard USB-UART bridge. Confirm C5 RX
is 3.3 V and input-only.

## Wiring gate, after separate approval

- StickS3 Hat2-Bus GPIO43/U0TXD (pin 10 per M5Stack documentation)
  to the verified C5 receive GPIO.
- StickS3 Hat2-Bus GND (pin 1) to C5 GND.
- Connect C5 native USB to host.
- Power StickS3 independently by its own USB interface.
- Leave C5 UART TX, target RX, 3.3 V, 5 V, reset, boot and PMIC lines unconnected.

Inspect pin-1 orientation from the actual board before wiring. Never infer the
header orientation solely from a perspective photo or a generic pin diagram.

## Bring-up evidence

With approved C5 flashing, first perform a known-byte 115200 8N1 RX test with
a confirmed 3.3 V TTL source before connecting the StickS3. Verify raw output,
CRC-valid frames, sequence continuity and reasonable timestamps.

Then arm host capture before StickS3 normal power-on. Capture:

- ESP-ROM boot mode and reset reason
- second-stage bootloader and partition selection
- earliest application marker or panic/reset trace
- changes in USB enumeration separately from UART events

The current StickShift serial firmware uses USB as its application console, so
UART0 may stop emitting after the bootloader even when application code runs.
Do not infer successful startup or a crash solely from silence.

Stop on unexpected voltage, conflicting outputs, abnormal heat, unexplained
reboots, or uncertain board identity. Preserve unedited raw evidence.

## References

- https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c5/api-reference/peripherals/uart.html
- https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c5/api-guides/usb-serial-jtag-console.html
- https://docs.m5stack.com/en/core/StickS3
