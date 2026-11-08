# C5 UART Tool roadmap

Official target: **Waveshare ESP32-C5-WIFI6-KIT-NXRX**, ESP32-C5-WROOM-1U, photo sticker **32R8U** (expected 32 MB flash/8 MB PSRAM; not electrically measured). Physical wiring/flashing remains separately authorized.

## GitHub milestone definitions

Create these **actual GitHub repository milestones** when the GitHub API/CLI is available. These exact titles and descriptions are the stable cross-reference; Milestones 1, 2 and 3 were created and their issue associations read back on 2026-11-08.

### M1 - Waveshare firmware acceptance

Description: Resolve the flash geometry mismatch, validate native USB/UART RX-only design and recoverability, exercise host parser, link exact ESP32-C5 target firmware, verify warnings and archive reproducible artifacts. **Software acceptance only**, no physical tests.

- [#2: Reconcile 32R8U flash geometry and effective sdkconfig](https://github.com/danielbrownjr/c5-uart-tool/issues/2)
- [#3: Validate USB transport and RX-only peripheral configuration](https://github.com/danielbrownjr/c5-uart-tool/issues/3)
- [#4: Harden host capture protocol, tests and CI artifact provenance](https://github.com/danielbrownjr/c5-uart-tool/issues/4)

### M2 - C5 board bring-up (separate physical authorization)

Description: Verify the exact Waveshare board, pin orientation, and flash identity, then complete separately authorized C5 flash and receive-only known-byte capture. **The existence of this milestone or issue does not authorize physical work**.

- [#5: Physical revision/header/USB identification](https://github.com/danielbrownjr/c5-uart-tool/issues/5)
- [#6: C5 firmware flash and known-byte receive-only acceptance](https://github.com/danielbrownjr/c5-uart-tool/issues/6)

### M3 - StickS3 normal-boot diagnosis (separate physical authorization)

Description: Capture and interpret the currently failing StickS3 serial-only firmware's normal-boot UART0, with no change to StickS3 firmware. Preserve original evidence.

- [#7: Receive-only StickS3 normal-boot trace](https://github.com/danielbrownjr/c5-uart-tool/issues/7)

## Dependency and stopping policy

1. Execute **M1** autonomously on an implementation feature branch. Do not infer hardware readiness from a green CI build.
2. **M2** electrical work and flashing require Dan's explicit per-operation approval.
3. **M3** physical wiring and boot capture require explicit approval after M2 acceptance.
4. Do not merge, tag, release, flash or change host toolchain configuration without authorization.
5. Exact milestone creation should be idempotent: check existing milestone titles, create missing ones, and attach each issue only to its corresponding milestone. Never duplicate them.
6. Update draft PR #1 with verified evidence and issue references; current documentation-specific commits may not require redundant hosted builds.
