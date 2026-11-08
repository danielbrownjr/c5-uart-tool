# C5 UART Tool

Receive-only 3.3 V UART diagnostic tool using the **Waveshare ESP32-C5-WIFI6-KIT-NXRX**. Initial use case: capture the normal-boot UART0 output of the M5Stack StickS3; the tool is intentionally independent of StickShift.

**Status:** experimental v0.1 on [draft PR #1](https://github.com/danielbrownjr/c5-uart-tool/pull/1). M1 implements software acceptance only; see [software verification](docs/software-verification.md) for the protocol, build evidence and limits. No physical flashing or device validation has occurred.

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

**Flash profile:** the build deliberately selects **32 MB / DIO / 80 MHz** for the apparent `32R8U` module. ESP-IDF v6.1 supports `CONFIG_ESPTOOLPY_FLASHSIZE_32MB`. The existing single-app partition table and flash offsets remain unchanged; PSRAM is not enabled. Generated configuration, app/bootloader headers and flash arguments are checked by `tools/verify_artifacts.py`. Device capacity and electrical acceptance remain M2 gates; the sticker is not a measurement.

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

`main/capture.c` reads UART1 and owns the native USB Serial/JTAG driver directly, with bounded writes and no application console. `main/frame.c` packages bytes with sequence, C5 uptime and CRC16. `tools/protocol.py` decodes the framing and resynchronizes after extraneous boot output. `tools/capture.py` stores exact payload bytes and UTC-reception-time metadata.

Frame format: `C5RX` magic + payload length (u16 LE) + sequence (u32 LE) + receiver uptime_ms (u32 LE) + 0..256 payload bytes + CRC16/CCITT-FALSE (u16 LE) covering metadata and payload. `C5ST` status frames use the same envelope with five cumulative u32 LE counters: UART FIFO overflow, RX buffer full, parity error, framing error, USB enqueue failures. Both frame kinds share sequence numbers. Receiver timestamps are **not** target timestamps. See [loss and recovery limits](docs/software-verification.md); sequence gaps cannot quantify dropped UART bytes.

## Build and tests

Requires an **already installed** ESP-IDF v6.1 environment. Do not install or alter Hephaestus tooling without authorization.

```sh
idf.py set-target esp32c5
bash tools/build-verify.sh  # build, inspect images/layout, hash retained artifacts
python3 -m unittest discover -s tests -v
```

Use a fresh build directory and effective `sdkconfig` for the committed defaults; stale 4 MB/console configurations are rejected. The build retains `build/retained/`, including a SHA-256 manifest. Do not flash without separate authorization and on-device capacity verification. Host tests need Python and GCC; the CLI additionally needs pyserial.

## Capture on host (after separately approved firmware flashing)

In an environment with pyserial available:

```sh
python3 tools/capture.py --port /dev/cu.usbmodemXXXX \
  --raw stickshift-boot.raw --events stickshift-boot.jsonl
```

On Linux, the port is commonly `/dev/ttyACM*`; confirm the actual enumerated device, never guess. USB host baud settings do not control the target's 115200 8N1 UART1 configuration. New capture files are created exclusively; never overwrite an earlier trace. Ctrl-C closes files, and a serial error exits without reconnecting. Reconnect using new paths so separate sessions stay distinct. JSONL includes start/end records and status counters; raw output contains UART payloads only. Files are flushed per record but are not an atomic pair or power-loss-durable storage.

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
2. Validated 32 MB software profile; separately verify flash capacity on the **actual** module before flashing.
3. Verified physical pad orientation, GPIO4 input capability, common ground, and USB selection.
4. Separately authorized C5 flash, USB enumeration and known-byte receive-only check.
5. Separately authorized connection to StickS3, followed by normal-boot UART0 capture.

Passing software gates does not authorize or prove the hardware gates.
