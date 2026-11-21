"""Source-only regression checks for raster input validation.

Run with: python -m unittest test_ore_raster_inputs_source_only.py
No Android SDK or APK build required.
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from audit_ore_biome_composites_source_only import (
    BACKGROUND_SIZE, ORE_SIZE, SAMPLE_SIZE, read_ore, read_rgb,
)


class OreRasterInputsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_valid_rgba_ore_is_downsampled_and_retains_alpha(self):
        path = self.root / "ore.png"
        Image.new("RGBA", ORE_SIZE, (25, 150, 190, 128)).save(path)
        result = read_ore(path)
        self.assertEqual(result.mode, "RGBA")
        self.assertEqual(result.size, (SAMPLE_SIZE, SAMPLE_SIZE))
        self.assertEqual(result.getpixel((SAMPLE_SIZE // 2, SAMPLE_SIZE // 2))[3], 128)

    def test_rgb_ore_without_alpha_is_rejected(self):
        path = self.root / "ore.png"
        Image.new("RGB", ORE_SIZE, (25, 150, 190)).save(path)
        with self.assertRaisesRegex(ValueError, "alpha"):
            read_ore(path)

    def test_wrong_ore_dimensions_are_rejected(self):
        path = self.root / "ore.png"
        Image.new("RGBA", (ORE_SIZE[0] - 1, ORE_SIZE[1]), (0, 0, 0, 0)).save(path)
        with self.assertRaisesRegex(ValueError, "expected PNG"):
            read_ore(path)

    def test_palette_ore_with_transparency_is_accepted(self):
        path = self.root / "ore.png"
        image = Image.new("P", ORE_SIZE, 0)
        image.putpalette([0, 0, 0, 255, 255, 255] + [0] * (256 * 3 - 6))
        image.info["transparency"] = 0
        image.putpixel((ORE_SIZE[0] // 2, ORE_SIZE[1] // 2), 1)
        image.save(path)
        result = read_ore(path)
        self.assertEqual(result.mode, "RGBA")
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertGreater(result.getpixel((SAMPLE_SIZE // 2, SAMPLE_SIZE // 2))[3], 0)

    def test_jpeg_biome_contract(self):
        path = self.root / "biome.jpg"
        Image.new("RGB", BACKGROUND_SIZE, (30, 40, 50)).save(path, format="JPEG")
        result = read_rgb(path, BACKGROUND_SIZE, "JPEG")
        self.assertEqual(result.mode, "RGB")
        self.assertEqual(result.size, BACKGROUND_SIZE)

    def test_png_disguised_as_jpeg_is_rejected(self):
        path = self.root / "biome.jpg"
        Image.new("RGB", BACKGROUND_SIZE, (30, 40, 50)).save(path, format="PNG")
        with self.assertRaisesRegex(ValueError, "expected JPEG"):
            read_rgb(path, BACKGROUND_SIZE, "JPEG")


if __name__ == "__main__":
    unittest.main()
