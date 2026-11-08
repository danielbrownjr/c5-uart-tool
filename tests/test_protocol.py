import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from protocol import Decoder, MAGIC, crc16


def pack(data: bytes, seq: int = 0, uptime: int = 3) -> bytes:
    header = len(data).to_bytes(2, "little") + seq.to_bytes(4, "little") + uptime.to_bytes(4, "little")
    return MAGIC + header + data + crc16(header + data).to_bytes(2, "little")


class DecoderTests(unittest.TestCase):
    def test_crc_reference_vector(self):
        self.assertEqual(crc16(b"123456789"), 0x29B1)

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

    def test_seeded_noise_fragmentation_and_maximum_payload(self):
        randomizer = random.Random(12345)
        decoder = Decoder()
        payload = bytes(range(256))
        stream = randomizer.randbytes(4096) + pack(payload, 0xFFFFFFFF)
        output = []
        while stream:
            size = randomizer.randrange(1, 40)
            output.extend(decoder.feed(stream[:size]))
            stream = stream[size:]
        self.assertEqual([frame.payload for frame in output], [payload])

    def test_corrupt_plausible_length_eventually_recovers(self):
        decoder = Decoder()
        damaged = bytearray(pack(b'a'))
        damaged[4:6] = (256).to_bytes(2, 'little')
        self.assertEqual(decoder.feed(damaged + pack(b'good', 2)), [])
        # A truncated plausible length must wait for its bounded candidate; do
        # not mistake an embedded valid frame in a binary payload for resync.
        result = decoder.feed(b'\0' * 272)
        self.assertEqual([f.payload for f in result], [b'good'])
        self.assertLessEqual(len(decoder.buffer), 271)

    def test_embedded_frame_is_payload_and_bad_status_length_recovers(self):
        embedded = pack(b'inner')
        self.assertEqual(Decoder().feed(pack(embedded))[0].payload, embedded)
        malformed = pack(b'x').replace(b'C5RX', b'C5ST', 1)
        self.assertEqual([f.payload for f in Decoder().feed(malformed + pack(b'ok'))], [b'ok'])

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
