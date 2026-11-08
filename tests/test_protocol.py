import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from protocol import Decoder, MAGIC, crc16


def pack(data: bytes, seq: int = 0, uptime: int = 3) -> bytes:
    header = len(data).to_bytes(2, "little") + seq.to_bytes(4, "little") + uptime.to_bytes(4, "little")
    return MAGIC + header + data + crc16(header + data).to_bytes(2, "little")


class DecoderTests(unittest.TestCase):
    def test_round_trip_preserves_binary_data(self):
        payload = b"\x00\xff\r\nC5RX\x7e"
        self.assertEqual(Decoder().feed(pack(payload))[0].payload, payload)

    def test_fragmentation(self):
        decoder = Decoder()
        frame = pack(b"boot", 7)
        output = []
        for byte in frame:
            output.extend(decoder.feed(bytes([byte])))
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0].sequence, 7)
        self.assertEqual(output[0].payload, b"boot")

    def test_boot_noise_and_bad_checksum_resync(self):
        decoder = Decoder()
        damaged = bytearray(pack(b"bad"))
        damaged[-1] ^= 0x80
        output = decoder.feed(b"ESP-ROM\r\n" + damaged + pack(b"good", 9))
        self.assertEqual([x.payload for x in output], [b"good"])
        self.assertGreater(decoder.corrupt, 0)

    def test_reject_oversize_and_recover(self):
        decoder = Decoder()
        oversize = MAGIC + (257).to_bytes(2, "little") + b"junk header"
        self.assertEqual([x.payload for x in decoder.feed(oversize + pack(b"ok"))], [b"ok"])

    def test_two_frames(self):
        decoder = Decoder()
        self.assertEqual([f.sequence for f in decoder.feed(pack(b"a", 10) + pack(b"b", 11))], [10, 11])

    def test_magic_across_boundary(self):
        decoder = Decoder()
        decoder.feed(b"noiseC5")
        output = decoder.feed(pack(b"test")[2:])
        self.assertEqual([f.payload for f in output], [b"test"])


if __name__ == "__main__":
    unittest.main()
