# C5 UART Tool

Receive-only 3.3 V UART diagnostic tool using the **Waveshare ESP32-C5-WIFI6-KIT-NXRX**. Initial use case: capture the normal-boot UART0 output of the M5Stack StickS3; the tool is intentionally independent of StickShift.

**Status:** experimental v0.1 on draft PR #1. Host tests and ESP32-C5 target build passed in [CI run 42505926780](https://github.com/danielbrownjr/c5-uart-tool/actions/runs/42505926780). No hardware validation or flashing has been performed by this repository.

## Supported target

- **Board:** Waveshare ESP32-C5-WIFI6-KIT-NXRX, identified by the rear PCB silkscreen in the project photos.
- **Module:** ESP32-C5-WROOM-1U with external antenna.
- **Observed sticker:** `32R8U`, suggesting a **32 MB flash / 8 MB PSRAM** variant. This is a model inference, not a chip-level flash-size measurement.
- **UART input:** GPIO4, on **P2 pin 8** in the published NXRX schematic, labeled `IO4` on the board.
- **Output:** native USB Serial/JTAG through the connector marked `USB`, **not** the `UART` USB-C connector with the onboard CH343P bridge.
- **Ground:** a physical header pad labeled `GND`, verified by board orientation before wiring.

Waveshare schematic: https://files.waveshare.com/wiki/ESP32-C5-WIFI6-KIT-NXRX/ESP32-C5-WIFI6-KIT-NXRX-Schematic.pdf

Waveshare board guide: https://www.waveshare.com/wiki/ESP32-C5-WIFI6-KIT-NXRX

GPIO4 is exposed on P2 pin 8 and is separate from the CH343P bridge's `UART_RXD`/`UART_TXD` header nets in this schematic. Firmware still needs physical verification of board revision and wiring before connection. Do not use `RXD` or `TXD` pads as the capture input; those belong to the onboard UART bridge.

**Blocking configuration warning:** `sdkconfig.defaults` currently selects **4 MB flash**. This contradicts the apparent 32 MB model sticker and must be corrected or deliberately justified and verified against the *effective sdkconfig* and detected device flash before **any C5 flashing**. See the flash-configuration issue in the roadmap. A green CI build is not proof the image matches the exact physical module.

## Safety contract

- Receive-only via **UART1 RX**. No UART TX writes, reset, boot, flow control, or target power connection.
- Use only compatible **3.3 V TTL** signals. No RS-232-level direct wiring.
- StickS3 **GPIO43/UART0 TX** to Waveshare **P2 pin 8 / GPIO4** only after the electrical and board identity gate passes.
- Connect **GND to GND**. Leave target RX and all 3.3 V/5 V supply rails unconnected between boards.
- Power each board independently through its own USB. Leave StickS3 boot pins alone.
- Do not mistake accepting third-party Biscuit firmware for sufficient electrical evidence; the confirmed PCB silkscreen and OEM schematic determine the target.

## Architecture

```text
StickS3 Hat2 GPIO43 (UART0 TX) --> Waveshare P2-8 GPIO4 (UART1 RX)
StickS3 Hat2 GND ----------------> Waveshare GND
Waveshare USB port (native) -----> Mac or Hephaestus
                                      |
                                 tools/capture.py
                                      |
                                raw UART + JSONL
```

`main/capture.c` reads UART1 and `main/frame.c` packages bytes with sequence, C5 uptime and CRC16. `tools/protocol.py` decodes the framing and resynchronizes after extraneous boot output. `tools/capture.py` stores exact payload bytes and UTC-reception-time metadata.

Frame format: `C5RX` magic + payload length (u16 LE) + sequence (u32 LE) + receiver uptime_ms (u32 LE) + 0..256 payload bytes + CRC16/CCITT-FALSE (u16 LE) covering metadata and payload. Receiver timestamps are **not** target timestamps. Dropped bytes within the C5 UART receive buffer are not guaranteed to be detectable by frame sequence numbers.

## Build and tests

Requires an **already installed** ESP-IDF v6.1 environment. Do not install or alter Hephaestus tooling without authorization.

```sh
idf.py set-target esp32c5
idf.py menuconfig   # confirm GPIO4, 115200, native USB console and actual flash profile
idf.py build
python3 -m unittest discover -s tests -v
```

Inspect the generated effective `sdkconfig` and app flash arguments; **do not flash** until the 4 MB vs 32 MB discrepancy is resolved. No host or hardware writes beyond an authorized development build are implied by these instructions.

## Capture on host (after separately approved firmware flashing)

In an environment with pyserial available:

```sh
python3 tools/capture.py --port /dev/cu.usbmodemXXXX \
  --raw stickshift-boot.raw --events stickshift-boot.jsonl
```

On Linux, the port is commonly `/dev/ttyACM*`; confirm the actual enumerated device, never guess. USB host baud settings do not control the target's 115200 8N1 UART1 configuration. New capture files are created exclusively; never overwrite an earlier trace.

## Repository layout

- `main/`: ESP-IDF source, receive-only UART driver and binary framing.
- `tools/`: Python USB decoder and capture CLI.
- `tests/`: deterministic host protocol tests.
- `docs/`: board-specific electrical preflight and verification gates.
- `.github/workflows/`: native ESP32-C5 build and host checks.
- `AGENTS.md`: scoped engineering contract.

Project roadmap is tracked in GitHub issues. Keep the draft PR open until exact-candidate verification, flash profile, and review acceptance. Retained non-ephemeral project artifacts belong in the personal Techbenders Drive, `Projects / C5 UART Tool`, in a verified folder. Raw host backups and private captures must not be committed.

## Acceptance gates

1. Verified host tests and ESP32-C5 target build, including action-runtime warnings.
2. Corrected and validated effective flash geometry for the **actual** Waveshare module.
3. Verified physical pad orientation, GPIO4 input capability, common ground, and USB selection.
4. Separately authorized C5 flash, USB enumeration and known-byte receive-only check.
5. Separately authorized connection to StickS3, followed by normal-boot UART0 capture.

Passing software gates does not authorize or prove the hardware gates.
