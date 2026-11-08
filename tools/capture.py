#!/usr/bin/env python3
"""Capture C5 UART Tool frames into exact UART bytes and JSONL event metadata."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from protocol import Decoder


def capture(port: str, raw: Path, events: Path, baud: int) -> None:
    try:
        import serial
    except ImportError as exc:
        raise SystemExit("Install pyserial in a virtual environment: pip install -r tools/requirements.txt") from exc
    if raw.resolve() == events.resolve():
        raise SystemExit("Raw and event paths must differ")
    decoder = Decoder()
    previous = None
    with serial.Serial(port, baudrate=baud, timeout=0.5) as device, raw.open("xb") as binary, events.open("x", encoding="utf-8") as log:
        print(f"Recording from {port}; ctrl-C to stop. Target UART baud is configured in firmware.", file=sys.stderr)
        while True:
            chunk = device.read(2048)
            for frame in decoder.feed(chunk):
                binary.write(frame.payload)
                now = datetime.now(timezone.utc).isoformat()
                gap = None if previous is None else ((frame.sequence - previous - 1) & 0xFFFFFFFF)
                previous = frame.sequence
                event = {"utc": now, "sequence": frame.sequence, "uptime_ms": frame.uptime_ms,
                         "length": len(frame.payload), "missing_frames": gap,
                         "hex": frame.payload.hex()}
                log.write(json.dumps(event) + "\n")
                binary.flush()
                log.flush()


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
