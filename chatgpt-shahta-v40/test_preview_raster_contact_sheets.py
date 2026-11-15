"""Source-only regression tests for raster contact sheets; no Android build."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image

MODULE_PATH = Path(__file__).with_name("preview_raster_contact_sheets.py")
spec = importlib.util.spec_from_file_location("shahta_contact_sheets", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ContactSheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.assets = Path(self.temp.name) / "assets"
        self.output = Path(self.temp.name) / "output"
        self.assets.mkdir()
        self.output.mkdir()
        for i in range(24):
            # Unique decoded pixels even if JPEG compression merges subtle colors.
            biome = Image.new("RGB", (360, 570), (i * 9, 30 + i * 5, 80))
            biome.save(self.assets / f"biome_{i:02d}.jpg", quality=95)
            ore = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
            for y in range(70, 230):
                for x in range(70, 230):
                    ore.putpixel((x, y), (30 + i * 8, 190, 160, 255))
            ore.save(self.assets / f"ore_{i:02d}.png")

    def test_all_24_each_render_with_expected_sheet_geometry(self):
        for kind, expected in (("biome", (1164, 1304)), ("ore", (1164, 884))):
            path = module.make_sheet(self.assets, self.output, kind)
            with Image.open(path) as image:
                self.assertEqual(image.size, expected)
                self.assertEqual(image.mode, "RGB")

    def test_missing_file_fails(self):
        (self.assets / "ore_23.png").unlink()
        with self.assertRaises(FileNotFoundError):
            module.make_sheet(self.assets, self.output, "ore")

    def test_wrong_dimensions_fail(self):
        Image.new("RGBA", (100, 100)).save(self.assets / "ore_04.png")
        with self.assertRaisesRegex(ValueError, "expected"):
            module.make_sheet(self.assets, self.output, "ore")

    def test_distinct_indices_have_distinct_pixels(self):
        # Guards the fixture against accidental identical colors.
        import hashlib
        for kind, ext in (("biome", "jpg"), ("ore", "png")):
            digests = []
            for i in range(24):
                with Image.open(self.assets / f"{kind}_{i:02d}.{ext}") as image:
                    digests.append(hashlib.sha256(image.convert("RGBA").tobytes()).digest())
            self.assertEqual(len(set(digests)), 24)


if __name__ == "__main__":
    unittest.main()
