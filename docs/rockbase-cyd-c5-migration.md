# RockBase NM-CYD-C5 migration preflight

Status: **planning / software preparation only**. This is a second hardware target for C5 UART Tool; it does not supersede the Waveshare NXRX proof-of-concept or establish a bootable CYD firmware. Do not flash or wire hardware based solely on this file.

## Hardware identity and source policy

User's box identifies **NM-CYD-C5**, ESP32-C5, Chengdu Rockbass Technology Co., Ltd., rockbaseiot.com. Adopt the manufacturer model and published mapping as the working baseline unless a concrete conflict appears. Do not borrow the classic ESP32 CYD pinout.

Sources:
- Official product wiki: https://wiki.rockbaseiot.com/docs/products/nm-cyd-c5/
- Official source repository: https://github.com/RockBase-iot/NM-CYD-C5
- Official ESPectre project mapping: https://wiki.rockbaseiot.com/docs/projects/espectre-nm-cyd-c5/
- Official schematic linked from the wiki: https://github.com/RockBase-lab/NM-CYD-C5/tree/main/Documention/2-sch

| Function | Published mapping | Migration implication |
| --- | --- | --- |
| MCU | ESP32-C5 | Retain IDF esp32c5 target |
| Flash | **16 MB** | **Do not reuse NXRX 32 MB image/flash parameters** |
| PSRAM | 8 MB | Not needed for first RX-only/diagnostic UI |
| LCD | ST7789, 320×240 (landscape orientation planned), SPI | Add LCD driver/UI; some vendor configurations mention ILI9341 variant |
| LCD SCK / MISO / MOSI | GPIO6 / GPIO2 / GPIO7 | SPI bus shared with touch and SD |
| LCD CS / DC / BL | GPIO23 / GPIO24 / GPIO25 | Backlight active high per vendor ESPectre example |
| Touch | XPT2046, shared SPI, CS GPIO1 | Resistive controller; use polling for MVP |
| SD CS | GPIO10 | Leave inactive; prevent bus contention |
| UART input | **GPIO4**, P5 RX; also P1 IO4 | Keep receive-only UART1 RX, **verify physical connector orientation** |
| UART TX option | GPIO5, P5 TX | Not connected or enabled in MVP |
| Ground | P1 GND / appropriate verified header GND | Shared ground with external target |
| Host | Native USB-C and CH340 USB-UART-C | Verify correct native port before USB transport tests |
| LED | WS2812 GPIO27 | Not part of MVP |

**Known vendor discrepancy:** official product wiki calls the touchscreen capacitive in its overview, while the *same wiki's pinout*, official GitHub README, and official ESPectre mapping explicitly identify **XPT2046**, a resistive touch controller. Use XPT2046 as the software default rather than halting on the typo. LCD controller variation (ST7789 default; ILI9341 possible) should be a build-time board choice, not an assumed physical fact.

## Migration boundaries

1. Keep the Waveshare `feat/receive-only-uart-capture` implementation and PR #1 intact.
2. Add an isolated CYD `sdkconfig` profile selecting **16 MB**, with 115200 8N1 receive-only GPIO4. Do not silently edit the NXRX 32 MB default or old verification assumptions.
3. Separate board-specific display/SPI/touch drivers from platform-neutral capture protocol, USB framing, and Python parser.
4. Prefer native ESP-IDF display/touch drivers for the existing ESP-IDF v6.1 toolchain. Vendor Arduino/TFT_eSPI patches are references, not drop-in components.
5. Protect capture responsiveness: bounded RX queue/history, no waiting on screen rendering, and one owner of the shared SPI bus. Keep existing native USB capture behavior when possible.
6. First UI: fixed 115200 8N1, ASCII/hex live view, RX byte/error counters, pause display, clear view. No TX, network access, SD logging, voltage sensing, or active target control.
7. Preserve electrical rules: compatible **3.3 V TTL** only, GND + target TX to GPIO4, independently powered devices. No RS-232, target RX, supply rail, boot, or reset connection.
8. Firmware build/host tests and source inspection are software gates. Actual pin orientation/voltage checks, capacity inspection, flashing, and hardware tests require separate authorization.

## MVP verification checklist (not yet satisfied)

- [ ] CYD-specific 16 MB effective configuration verified against app/bootloader headers and flash arguments
- [ ] Native ESP32-C5 firmware build/link on exact candidate SHA, clean warnings and action runtimes
- [ ] ST7789 initializes with visible test content on real CYD
- [ ] XPT2046 touch mapping calibrated and controls function on real CYD
- [ ] Verified 3.3 V known-byte source appears on LCD, at 115200 8N1
- [ ] Existing Waveshare capture/protocol host regression tests pass unchanged
- [ ] USB host raw capture still works where supported, with no display-driven UART loss claim
- [ ] Physical gate: PCB revision, connectors, exact pads, real flash capacity and voltage checked before flashing/wiring

**Next software implementation:** create proper IDF board-profile selection, refactor the NXRX-only guards and verification script for explicitly selected 16/32 MB profiles, add panel and touch components, then run isolated CYD CI. No current CYD firmware has been built or flashed by this preparation.
