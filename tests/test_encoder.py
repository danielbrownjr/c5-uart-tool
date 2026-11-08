"""Compile the real firmware encoder and compare its wire output to Python."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_protocol import pack
from protocol import Decoder

ROOT = Path(__file__).resolve().parents[1]


class EncoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        library = Path(cls.temp.name) / 'frame.so'
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared',
                        '-fPIC', '-I', str(ROOT / 'main/include'),
                        str(ROOT / 'main/frame.c'), '-o', str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.c5_frame_encode.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32]
        cls.lib.c5_frame_encode.restype = ctypes.c_size_t
        cls.lib.c5_status_encode.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32]
        cls.lib.c5_status_encode.restype = ctypes.c_size_t

    def test_all_payload_sizes_and_binary_values(self):
        for length in range(257):
            payload = bytes(i % 256 for i in range(length))
            out = ctypes.create_string_buffer(272)
            size = self.lib.c5_frame_encode(out, 272, payload, length, 0xFFFFFFFF, 0xFFFFFFFF)
            self.assertEqual(out.raw[:size], pack(payload, 0xFFFFFFFF, 0xFFFFFFFF))
            self.assertEqual(Decoder().feed(out.raw[:size])[0].payload, payload)

    def test_invalid_arguments_do_not_touch_output(self):
        out = ctypes.create_string_buffer(b'Z' * 272, 272)
        for capacity, payload, length in [(271, b'x' * 256, 256), (272, b'x' * 257, 257), (272, None, 1)]:
            self.assertEqual(self.lib.c5_frame_encode(out, capacity, payload, length, 0, 0), 0)
            self.assertEqual(out.raw, b'Z' * 272)
        self.assertEqual(self.lib.c5_frame_encode(None, 272, b'a', 1, 0, 0), 0)

    def test_status_wire_order(self):
        out = ctypes.create_string_buffer(272)
        values = (ctypes.c_uint32 * 5)(1, 256, 65536, 0xFFFFFFFF, 42)
        size = self.lib.c5_status_encode(out, 272, values, 10, 1234)
        frame = Decoder().feed(out.raw[:size])[0]
        self.assertEqual((frame.kind, frame.sequence, frame.uptime_ms), ('status', 10, 1234))
        self.assertEqual(frame.payload, b''.join(int(v).to_bytes(4, 'little') for v in values))
