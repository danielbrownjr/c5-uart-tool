# Waveshare ESP32-C5-WIFI6-KIT-NXRX: bring-up contract

**Target:** the official Waveshare `ESP32-C5-WIFI6-KIT-NXRX` board photographed with rear PCB silkscreen and a `32R8U` model sticker.

**This document does not authorize physical wiring, C5 flashing, toolchain installation or writes to the StickS3.**

## OEM evidence and signal mapping

The [Waveshare NXRX schematic](https://files.waveshare.com/wiki/ESP32-C5-WIFI6-KIT-NXRX/ESP32-C5-WIFI6-KIT-NXRX-Schematic.pdf) identifies:

| Signal | Waveshare schematic | Physical board |
| --- | --- | --- |
| UART sniffer RX input | P2 **pin 8**, `GPIO4` | Side castellated pad `IO4` |
| Common ground | P2 pin 1 `GND` or P1 pin 16 `GND` | Pad marked `GND`; verify orientation |
| Host USB output | H1 native USB interface | USB-C marked **`USB`** |
| Onboard USB-to-UART | H2 and CH343P, `UART_RXD`/`UART_TXD` | USB-C marked **`UART`**; not used for capture input |

GPIO4 is exposed independently of the dedicated bridge's UART nets in the published schematic. This confirms the **design** supports the chosen input; physical pad/silk orientation and actual revision remain the final gate.

The sticker `32R8U` indicates an expected **32 MB flash / 8 MB PSRAM** variant. Before any flashing, read chip identity and flash geometry with a **separately approved** read-only device probe; reconcile the effective ESP-IDF `sdkconfig` and flash arguments. M1 selects `CONFIG_ESPTOOLPY_FLASHSIZE_32MB=y` with DIO/80 MHz and verifies generated images and flash arguments. This resolves the software default mismatch, **not** the unmeasured device capacity. PSRAM remains unused. Do not change chip fuses, bootloader, partitions or full-flash contents as a workaround.

Waveshare's board may be flashed with Biscuit firmware, but that fact alone does not prove the wiring or flash size. The silkscreen plus schematic are the authoritative board-identification basis.

## Planned wiring, subject to separate approval

| Source | Destination |
| --- | --- |
| StickS3 Hat2-Bus **pin 10**, ESP32-S3 GPIO43/U0TXD | Waveshare **P2 pin 8**, GPIO4/IO4, receive-only |
| StickS3 Hat2-Bus **pin 1**, GND | Waveshare header **GND** |
| Waveshare native **USB** Type-C | Host USB port |
| StickS3 USB | Its own independent power/host USB |

No physical connection to StickS3 RX, its power rails, boot pins, reset pins, PMIC, or any Waveshare TX output. **Never cross-wire 5 V or battery rails.** Confirm 3.3 V logic and ground with appropriate inspection/measurement, and verify pad orientation against the exact physical board rather than rotating a photograph mentally.

## Ordered acceptance gates

1. **Software:** host decoder tests and linked ESP32-C5 firmware image validated at the exact candidate SHA, with clean action runtimes.
2. **Flash configuration:** actual flash capacity, flash mode/frequency, partition layout and image set agree. The 32 MB software profile is checked; actual capacity and recovery path must still be established.
3. **Hardware identity:** PCB revision, module, `IO4`, `GND`, `USB`, and `UART` labels independently confirmed. No powered external wiring.
4. **C5 bring-up, separately authorized:** known-good backup/recovery as relevant, scoped C5 flash, native USB enumeration, then a receive-only known-byte test from an independently verified 3.3 V source.
5. **StickS3 test, separately authorized:** preserve its currently failing application; capture UART0 at 115200 8N1 starting *before* normal power-on. Record reset reason, ROM/bootloader output and host USB enumeration separately.

The StickS3's currently installed firmware routes app logs to USB, not UART0. An empty UART0 trace after the second-stage bootloader **does not establish application health or failure**.

Stop on unexpected heating, unknown voltage, contention, resets, unstable USB, or ambiguous pin identity. Capture logs without modifying them; never commit sensitive raw traces or full device backups.

## References

- Waveshare schematic: https://files.waveshare.com/wiki/ESP32-C5-WIFI6-KIT-NXRX/ESP32-C5-WIFI6-KIT-NXRX-Schematic.pdf
- Waveshare guide: https://www.waveshare.com/wiki/ESP32-C5-WIFI6-KIT-NXRX
- ESP-IDF UART: https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c5/api-reference/peripherals/uart.html
- ESP-IDF USB Serial/JTAG: https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c5/api-guides/usb-serial-jtag-console.html
- StickS3: https://docs.m5stack.com/en/core/StickS3
