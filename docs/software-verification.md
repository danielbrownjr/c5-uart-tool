# M1 software contract and verification

M1 is software acceptance for the Waveshare ESP32-C5-WIFI6-KIT-NXRX 32R8U profile. No physical device validation is implied. Issues #2–#4 track this work; #5–#7 retain independent physical authorization gates.

## Profile and receive-only routing

ESP-IDF v6.1's [flash Kconfig](https://github.com/espressif/esp-idf/blob/v6.1/components/esptool_py/Kconfig.projbuild) supports 32 MB explicitly. Defaults select 32 MB, DIO, 80 MHz, GPIO4, 115200 8N1, no flow control and no PSRAM. The standard single-app layout remains bootloader `0x2000`, partition table `0x8000`, factory application `0x10000` / 1 MiB, NVS `0x9000` / 24 KiB and PHY data `0xf000` / 4 KiB. Increasing declared capacity does not expand partitions or authorize writing existing flash.

The [OEM schematic](https://files.waveshare.com/wiki/ESP32-C5-WIFI6-KIT-NXRX/ESP32-C5-WIFI6-KIT-NXRX-Schematic.pdf) routes GPIO4 to P2-8 independently of CH343P. Native USB is H1; H2 is the CH343P UART bridge. The board wiki returned HTTP 403 during this investigation; the schematic and IDF sources were accessible. Sticker `32R8U` suggests the selected capacity, but actual flash/PSRAM capacity and electrical behavior have not been read from a device.

UART1 is exclusively owned from application startup. Only its RX route is assigned; TX, RTS, CTS, DTR and DSR use `UART_PIN_NO_CHANGE`. In v6.1 that sentinel **does not detach an existing route**. No component configures a UART1 output, no UART data write is used, and GPIO4 is explicitly input-only with no pull. The software assumes normal reset/startup, not reuse after another application component has configured UART1. Compile-time checks reject a different target, flash capacity or competing application console. GPIO configuration is fixed to 4 for this board profile.

Native USB uses `usb_serial_jtag_driver_install` and `usb_serial_jtag_write_bytes`, not stdout or the bridge. Application primary and secondary consoles are disabled to avoid concurrent text writers. ROM/bootloader output may precede the stream; the decoder ignores leading noise. No USB commands are forwarded to UART. Host DTR/RTS are deasserted before port opening; OS/USB open behavior still requires hardware verification.

## Transport and loss semantics

Data frames retain `C5RX`; status frames use `C5ST`. Each envelope is four magic bytes, u16 payload length, u32 sequence, u32 receiver uptime in milliseconds, payload, u16 CRC16/CCITT-FALSE. Integers are little endian. CRC covers length, sequence, uptime and payload, excluding magic. Data payloads are 0–256 bytes. Status payloads are exactly 20 bytes: five u32 cumulative counters since boot, in order:

1. Observed UART FIFO overflow events.
2. Observed UART RX buffer full events (pressure, not necessarily byte loss).
3. Observed UART parity error events (parity is disabled in this profile).
4. Observed UART framing error events.
5. Failed/short USB frame enqueue attempts, including failed status frames.

A status frame is attempted on the first loop and every second, including during UART silence. Every attempted frame consumes one sequence number. Counters and sequence wrap modulo 2^32. A failed status enqueue is visible in a later status if one arrives. The 4096-byte UART ring buffer and 64-event queue are bounded. The loop drains events independently of data reads and never flushes buffered UART bytes as an overflow workaround. Event queue saturation can lose notifications: counters are lower bounds, not exact byte loss.

USB uses a 1024-byte TX ring buffer and a 20 ms enqueue timeout. The v6.1 driver enqueues a whole item or returns zero; an unexpected short return is also counted. Its mutex and ring-buffer waits are bounded individually, so scheduling/contention can extend wall time beyond 20 ms. This application is the only writer and never calls an unbounded flush. Accepted enqueues are **not host delivery acknowledgements**. Disconnects, queued data lost on reset, FIFO overflow and exhausted buffers can lose bytes. No lossless claim or throughput guarantee is made, especially at configurable rates above 115200. Hardware backpressure/reconnect/stress testing belongs to M2.

Sequence gaps count missing transport frames of either kind, not missing UART bytes. Backward receiver uptime is flagged as a possible restart/reordering and suppresses gap arithmetic for that transition; short reboot intervals can be ambiguous. Uptime wraps every ~49.7 days. Counters reset on reboot and also wrap. A fresh host capture uses new files and makes no continuity assumption about its first frame.

## Decoder and file recovery

The decoder handles fragmented magic/frames, binary payloads containing magic, leading noise, invalid lengths and CRC failures. It rejects status lengths other than 20. A plausible damaged length may delay recovery until at most a 272-byte candidate is available; it does not speculatively select a magic embedded in legitimate binary payload. If input ends sooner, pending transport bytes are recorded in the end event and omitted from raw output. No framing scheme with magic and CRC16 can guarantee recovery from arbitrary adversarial noise or rule out checksum collisions.

The CLI preflights both destinations and uses exclusive creation. Existing outputs and aliases are rejected before opening the device. An exclusive-creation race can leave a newly created empty first file; it never overwrites an existing file. Ctrl-C and serial exceptions close both files; the latter exits rather than silently appending a new session. The JSONL end record reports parser corruption and pending bytes when the log remains writable. Raw payload is flushed before its metadata record. Disk-full/process-kill/power failure may leave raw ahead of JSONL or a partial JSONL tail; the pair is not atomic and no fsync durability is promised. Preserve those files and choose new paths after interruption.

## Reproducible verification and retention

On an already provisioned IDF v6.1 environment:

```sh
idf.py set-target esp32c5
bash tools/build-verify.sh
python3 -m unittest discover -s tests -v
```

`build-verify.sh` never flashes. It records actual source and IDF SHAs, compiler/Python/CMake/Ninja versions, build output, decoded image information and partition CSV. `verify_artifacts.py` checks effective sdkconfig, app and bootloader header capacity/mode, flash arguments and standard offsets. It retains all flash-set files plus ELF/map, compile commands, project description and effective configuration with SHA-256 hashes. CI checks out the PR source head explicitly, so the manifest identifies the implementation SHA rather than a synthetic merge SHA. Hosted artifacts have 90-day retention; download `build/retained` for durable local storage.

Host tests compile the real C encoder, compare every supported payload length against Python, exercise fragmentation/noise/checksum/length recovery, status encoding, sequence/uptime wrap, interruption, serial failure and exclusive file handling. A separate C harness runs the actual capture loop against driver doubles, checking RX-only configuration and overflow/enqueue-failure reporting with undefined-behavior instrumentation. These doubles establish software control flow only. Actual target compilation/linking, linked artifact inspection and physical validation are separate evidence levels.

Review actual CI logs and check annotations for the tested head. Node action-runtime deprecations block acceptance even if jobs pass. Other warnings must be recorded and assessed. No host installation, device probe, wiring or flashing is part of these commands or M1.
