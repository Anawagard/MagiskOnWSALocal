"""Reject misleading filename extensions in source-only raster quality checks."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from audit_visual_diversity import inspect


class EncodedRasterFormatTests(unittest.TestCase):
    def test_png_bytes_disguised_as_biome_jpeg_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "biome_00.jpg"
            yy, xx = np.indices((570, 360))
            rgb = np.stack(((xx * 3 + yy) % 256,
                            (yy * 5 + xx) % 256,
                            (xx + yy * 7) % 256), axis=-1).astype(np.uint8)
            Image.fromarray(rgb, "RGB").save(path, format="PNG")
            with self.assertRaisesRegex(ValueError, "expected JPEG encoding"):
                inspect(path, ore=False)

    def test_jpeg_bytes_disguised_as_ore_png_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ore_00.png"
            Image.new("RGB", (300, 300), (90, 110, 130)).save(
                path, format="JPEG"
            )
            with self.assertRaisesRegex(ValueError, "expected PNG encoding"):
                inspect(path, ore=True)

    def test_valid_jpeg_biome_remains_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "biome_00.jpg"
            yy, xx = np.indices((570, 360))
            rgb = np.stack(((xx * 3 + yy) % 256,
                            (yy * 5 + xx) % 256,
                            (xx + yy * 7) % 256), axis=-1).astype(np.uint8)
            Image.fromarray(rgb, "RGB").save(path, format="JPEG", quality=90)
            entry, thumb = inspect(path, ore=False)
            self.assertEqual(entry["size"], [360, 570])
            self.assertEqual(thumb.shape, (32, 32, 3))


if __name__ == "__main__":
    unittest.main()
