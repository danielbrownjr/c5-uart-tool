# RockBase NM-CYD-C5 first-flash readiness gate

**Status:** planning and preflight, not authorization to flash. This document covers the initial ST7789 RGB color-bar experiment only. Keep the original Waveshare firmware and PR #1 unchanged. No external UART device or SD card should be attached for the first power-on test.

## Software promotion gate

Before considering a flash, inspect a **completed successful** GitHub Actions run for the **exact** CYD PR head. Require:
- All host tests, including display-failure UART-startup and generated-config mismatch regressions, pass.
- Both Waveshare (32 MB) and RockBase CYD (16 MB) native ESP32-C5 builds/link pass.
- `build-cyd/retained/` contains the **16 MB** effective config, bootloader/application/partition images, flash arguments, and SHA-256 manifest matching that exact head. Preserve the complete artifacts, not just the application binary.
- No compiler warnings, action-runtime deprecations, or unexplained CI warnings.
- Any outstanding review blockers resolved; a focused re-review is only needed if the original independent review's substantive findings warrant it.

Do not use the Waveshare 32 MB image on this board. Do not confuse a successful build with physical verification.

## Physical readiness, separately authorized

1. Confirm the actual PCB is **RockBase NM-CYD-C5**, with the manufacturer's documented flash/module variant and connectors. The box and published docs are the working baseline unless contradicted by physical evidence.
2. Confirm the actual chip/flash geometry via a read-only ESP32-C5 device query before any writes, and reconcile with the 16 MB candidate; stop on disagreement.
3. Identify the actual ESP32-C5 native USB interface and ROM download/recovery method. Do not assume the CH340 port is equivalent. Verify the serial device identity rather than guessing a `/dev/cu.*` path.
4. Determine whether original firmware/data must be preserved. Where necessary, arrange a verified recovery image/backup before any erase or write; no blanket erase.
5. Power the CYD on its own, with **no external UART wires** and **no microSD card** for this test.
6. Only after a separate flash authorization, use the exact validated CYD image set and offsets from its retained `flasher_args.json` / `flash_args`. Do not manually substitute 32 MB arguments or reuse stale build outputs.
7. Observe RGB bands, orientation, offsets, backlight, repeated resets, and USB framed status messages. Note: a lit LCD proves neither touch nor UART external wiring.
8. With separate wiring authorization, verify the actual P5 RX/GND orientation and compatible 3.3 V TTL levels before connecting target TX to GPIO4 plus common ground. Never attach target RX, power rails, reset, or boot pins for this receiver-only milestone.

**Stop** on unknown device identity, flash-size mismatch, unstable USB, surprising heat, wiring ambiguity, unexplained resets, or loss of recovery access. Preserve and report observed evidence.

## Expected demonstration

- Asymmetric top-to-bottom bands: red 40 px, green 80 px, blue 120 px across the 320×240 display. Photograph the order, actual colors, and any mirrored/clipped edges. Unequal heights distinguish a vertical flip from red/blue channel swapping.
- Receive-only UART firmware still initializes after display failure; the first display error is retained in the `last_display_error` variable, inspectable by symbol in the ELF/debugger. The `c5_display_last_error()` function may be removed by linker section garbage collection when unreferenced (the binary USB transport is not polluted with debug text).
- Native USB framed heartbeat/status where supported.

Touch controls and live UART hex/ASCII rendering are later milestones. This build is **not** a complete touchscreen serial monitor.

## First-photo display correction (2026-11-12)

The photographed initial CYD display showed top-to-bottom **magenta/pink (large)**, **cyan (medium)** and **blue (small)** while physically held portrait. This establishes that the screen and backlight respond, but the RGB565 hues were not correct and the asymmetric band order appeared vertically reversed. Device/photography colors are observations, not a proven controller-specific root cause.

The targeted next firmware candidate uses the vendor MicroPython reference's MSB-first RGB565 convention: big-endian panel data mode with swapped native little-endian 16-bit test words, preserving the vendor's BGR setting. A panel Y mirror was also requested after XY swap to correct the observed band order. These are hypotheses pending another photo, not verified physical corrections.

Expected on the next photo with the board upright in the same orientation: **red 40 px at top, green 80 px center, blue 120 px bottom**. Photograph the complete screen and note if red/blue channels remain swapped, the order remains reversed, or colors are non-primary. Keep flash/recovery/USB validation separate from screen acceptance. This test does not involve UART target wiring, touch, or microSD.
