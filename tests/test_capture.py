import io
import sys
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from test_protocol import pack
from capture import capture, record, sequence_gap
from protocol import Decoder


class Device:
    def __init__(self, chunks, error=KeyboardInterrupt):
        self.chunks = iter(chunks)
        self.error = error

    def read(self, size):
        try:
            return next(self.chunks)
        except StopIteration:
            raise self.error()


class CaptureTests(unittest.TestCase):
    def test_cli_closes_files_and_deasserts_lines_before_open(self):
        class SerialDevice(Device):
            def __init__(self, port, **kwargs):
                self.port = port
                self.assert_initial = port is None
                super().__init__([pack(b'\x00\xff')])

            def __enter__(self):
                return self

            def open(self):
                assert self.assert_initial and self.port == 'native-usb'
                assert self.dtr is False and self.rts is False

            def __exit__(self, *args):
                self.closed = True

        device = SerialDevice(None)
        with tempfile.TemporaryDirectory() as folder:
            raw, log = Path(folder) / 'raw', Path(folder) / 'events'
            with patch.dict(sys.modules, {'serial': types.SimpleNamespace(Serial=lambda **kwargs: device)}):
                with self.assertRaises(KeyboardInterrupt):
                    capture('native-usb', raw, log, 115200)
            self.assertTrue(device.closed)
            self.assertEqual(raw.read_bytes(), b'\x00\xff')
            self.assertEqual(json.loads(log.read_text().splitlines()[-1])['reason'], 'interrupted')

    def test_interruption_preserves_binary_and_status(self):
        raw, log = io.BytesIO(), io.StringIO()
        status = pack(b'\0' * 20, 0).replace(b'C5RX', b'C5ST', 1)
        device = Device([status[:9], status[9:] + pack(b'\0\xff\r\n', 1), b'C5RX'])
        with self.assertRaises(KeyboardInterrupt):
            record(device, raw, log)
        self.assertEqual(raw.getvalue(), b'\0\xff\r\n')
        entries = [json.loads(line) for line in log.getvalue().splitlines()]
        self.assertEqual([e['type'] for e in entries], ['start', 'status', 'data', 'end'])
        self.assertEqual(entries[2]['missing_frames'], 0)
        self.assertEqual(entries[-1]['reason'], 'interrupted')
        self.assertGreater(entries[-1]['pending_transport_bytes'], 0)

    def test_unplug_retains_prefix_and_reports_error(self):
        raw, log = io.BytesIO(), io.StringIO()
        with self.assertRaises(OSError):
            record(Device([pack(b'boot')], OSError), raw, log)
        self.assertEqual(raw.getvalue(), b'boot')
        self.assertEqual(json.loads(log.getvalue().splitlines()[-1])['reason'], 'error')

    def test_wrap_gap_and_possible_restart(self):
        frames = Decoder().feed(pack(b'', 0xFFFFFFFF, 0xFFFFFFFE) + pack(b'', 0, 1) + pack(b'', 3, 100))
        self.assertEqual(sequence_gap(frames[0], frames[1]), (0, False))
        self.assertEqual(sequence_gap(frames[1], frames[2]), (2, False))
        reset = Decoder().feed(pack(b'', 0, 1))[0]
        self.assertEqual(sequence_gap(frames[2], reset), (None, True))

    def test_existing_either_output_is_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ('raw', 'events'):
                raw, events = Path(folder) / 'raw', Path(folder) / 'events'
                path = Path(folder) / name
                path.write_bytes(b'original')
                with self.assertRaises(FileExistsError):
                    capture('unused', raw, events, 115200)
                self.assertEqual(path.read_bytes(), b'original')
                self.assertFalse((events if name == 'raw' else raw).exists())
                path.unlink()

    def test_alias_outputs_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'same'
            with self.assertRaises(SystemExit):
                capture('unused', path, path, 115200)
            self.assertFalse(path.exists())
