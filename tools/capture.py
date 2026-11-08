#!/usr/bin/env python3
"""Capture C5 UART Tool frames into exact UART bytes and JSONL event metadata."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from protocol import Decoder, STATUS_FIELDS


def sequence_gap(previous, frame):
    """Modulo wrap is normal; backward uptime means possible reboot/reordering."""
    if previous is None:
        return None, False
    reboot = ((frame.uptime_ms - previous.uptime_ms) & 0xFFFFFFFF) > 0x7FFFFFFF
    return (None if reboot else (frame.sequence - previous.sequence - 1) & 0xFFFFFFFF), reboot


def record(device, binary, log):
    """Keep a recoverable raw prefix on interruption; never write status as UART."""
    decoder = Decoder()
    previous = None
    reason = "error"

    def event(value):
        value["utc"] = datetime.now(timezone.utc).isoformat()
        log.write(json.dumps(value) + "\n")
        log.flush()

    event({"type": "start", "protocol": "C5RX+C5ST", "version": 1})
    try:
        while True:
            chunk = device.read(2048)
            for frame in decoder.feed(chunk):
                gap, reboot = sequence_gap(previous, frame)
                previous = frame
                entry = {"type": frame.kind, "sequence": frame.sequence,
                         "uptime_ms": frame.uptime_ms, "length": len(frame.payload),
                         "missing_frames": gap, "possible_restart": reboot,
                         "decoder_corrupt": decoder.corrupt}
                if frame.kind == "data":
                    # Flush raw first. If JSONL fails, raw may be ahead of metadata.
                    binary.write(frame.payload)
                    binary.flush()
                    entry["hex"] = frame.payload.hex()
                else:
                    entry["counters"] = dict(zip(STATUS_FIELDS,
                        (int.from_bytes(frame.payload[i:i + 4], "little")
                         for i in range(0, len(frame.payload), 4))))
                event(entry)
    except KeyboardInterrupt:
        reason = "interrupted"
        raise
    finally:
        event({"type": "end", "reason": reason, "decoder_corrupt": decoder.corrupt,
               "pending_transport_bytes": len(decoder.buffer)})


def capture(port: str, raw: Path, events: Path, baud: int) -> None:
    if raw.resolve() == events.resolve():
        raise SystemExit("Raw and event paths must differ")
    # Preflight both before creating either. Exclusive creation also guards races.
    for path in (raw, events):
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)
    try:
        import serial
    except ImportError as exc:
        raise SystemExit("Install pyserial in a virtual environment: pip install -r tools/requirements.txt") from exc
    with raw.open("xb") as binary, events.open("x", encoding="utf-8") as log:
        # Deassert control lines before opening; never request reset/boot toggles.
        # USB stacks may still toggle them during open; physical behavior is gated.
        with serial.Serial(port=None, baudrate=baud, timeout=0.5) as device:
            device.dtr = False
            device.rts = False
            device.port = port
            device.open()
            print(f"Recording from {port}; ctrl-C to stop. Target UART baud is configured in firmware.", file=sys.stderr)
            record(device, binary, log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="C5 native USB Serial/JTAG port")
    parser.add_argument("--raw", type=Path, required=True, help="New output file for exact UART payload bytes")
    parser.add_argument("--events", type=Path, required=True, help="New JSONL log with timestamps/hex data")
    parser.add_argument("--usb-baud", type=int, default=115200,
                        help="USB CDC host setting; does not change target UART")
    args = parser.parse_args()
    try:
        capture(args.port, args.raw, args.events, args.usb_baud)
    except KeyboardInterrupt:
        print("Capture stopped by operator", file=sys.stderr)
    except FileExistsError:
        raise SystemExit("Output exists. Choose new paths; existing captures are never overwritten.")
    except OSError as exc:
        raise SystemExit(f"Capture failed: {exc}. Retain output files; use new paths to reconnect.") from exc
