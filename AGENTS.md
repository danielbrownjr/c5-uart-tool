# C5 UART Tool engineering contract

## Hardware target

Official **Waveshare ESP32-C5-WIFI6-KIT-NXRX**, identified by the physical rear PCB silkscreen. Model sticker `32R8U` suggests 32 MB flash / 8 MB PSRAM, subject to independent on-device verification. Read `docs/hardware-bringup.md` and the linked OEM schematic before making any hardware assumptions.

- Receiver: UART1 RX on **GPIO4 / header P2 pin 8** according to the Waveshare schematic.
- USB output: **native USB** connector marked `USB`. Do not confuse this with CH343P `UART` connector.
- Receive-only: no target TX, reset, boot, PMIC or power control.
- `sdkconfig.defaults` selects the NXRX 32R8U **32 MB** profile (DIO/80 MHz), with PSRAM unused. Build verification checks effective configuration and image headers. Actual device capacity still requires separately authorized verification before physical flashing.

## Development bounds

Autonomous, scoped branch/PR implementation, host tests, CI inspection and docs are permitted. Flashing, wiring, host tooling changes/installation, merges, tags, releases and persistent hardware operations require separate explicit authorization. Do not change StickShift firmware as part of C5 tooling work.

Keep C framing and Python decoding consistent; test parser noise, fragmentation, CRC failure and complete recovery. Verify native ESP32-C5 linking and exact-candidate artifacts independently of host unit tests. Check all CI warnings, including Node.js action-runtime deprecations as blockers. Do not claim actual hardware acceptance from green CI.

Roadmap execution follows GitHub issues and gated milestones. Don't scope-creep into radio, Bluetooth, displays, networking, power controls or persistent storage for v0.1. Sanitized reports/artifacts belong to verified personal Techbenders project location, not the ILS work Drive.
