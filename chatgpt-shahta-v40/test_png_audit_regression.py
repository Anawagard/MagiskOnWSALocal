"""Source-only regression checks for the PNG framing auditor.

No Gradle, Android SDK, network, or GitHub Actions required.
Run: python -m unittest chatgpt-shahta-v40/test_png_audit_regression.py
"""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("shahta_png_audit", HERE / "audit_raster_assets.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def chunk(kind, payload=b""):
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))


def png(*, width=300, height=300, mode=6, corrupt_crc=False,
        truncate=False, trailing=False, missing_idat=False):
    header = struct.pack(">IIBBBBB", width, height, 8, mode, 0, 0, 0)
    # A real, independently decompressible 1x1 RGBA image for the default
    # dimensions below; framing tests intentionally do not decode pixels.
    data = (b"" if missing_idat else chunk(b"IDAT", zlib.compress(bytes([0,0,0,0,255]))))
    output = audit.PNG_SIGNATURE + chunk(b"IHDR", header) + data + chunk(b"IEND")
    if corrupt_crc:
        output = output[:-5] + bytes([output[-5] ^ 1]) + output[-4:]
    if truncate:
        output = output[:-3]
    if trailing:
        output += b"junk"
    return output


class PNGFramingRegression(unittest.TestCase):
    def inspect(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ore_00.png"
            path.write_bytes(data)
            return audit.inspect_png(path)

    def test_valid_header_and_alpha(self):
        self.assertEqual(self.inspect(png()), (300, 300, 6))

    def test_corruptions_rejected(self):
        for label, payload in (
            ("bad signature", b"not a PNG"),
            ("bad crc", png(corrupt_crc=True)),
            ("truncated", png(truncate=True)),
            ("trailing bytes", png(trailing=True)),
            ("missing IDAT", png(missing_idat=True)),
            ("zero width", png(width=0)),
            ("excessive width", png(width=8193)),
            ("unsupported color", png(mode=1)),
        ):
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.inspect(payload)


if __name__ == "__main__":
    unittest.main()
