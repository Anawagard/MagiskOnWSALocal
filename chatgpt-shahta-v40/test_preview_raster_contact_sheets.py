"""Source-only regression tests for raster contact sheets; no Android build."""
import importlib.util
import tempfile
import sys
from unittest.mock import patch
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


    def run_validation(self):
        # Exercise the actual CLI validation path, not only make_sheet().
        with patch.object(sys, "argv", ["preview_raster_contact_sheets.py",
                                       str(self.assets), str(self.output)]):
            module.main()

    def test_cli_accepts_complete_valid_art_pack(self):
        self.run_validation()
        self.assertTrue((self.output / "biome_contact_sheet.png").is_file())
        self.assertTrue((self.output / "ore_contact_sheet.png").is_file())

    def test_cli_rejects_opaque_ore_before_writing_sheets(self):
        Image.new("RGB", (300, 300), (50, 70, 90)).save(
            self.assets / "ore_07.png")
        with self.assertRaisesRegex(ValueError, "transparency"):
            self.run_validation()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_cli_rejects_identical_decoded_ore_pixels(self):
        # Same decoded image even when the PNG encoding differs.
        with Image.open(self.assets / "ore_03.png") as image:
            image.save(self.assets / "ore_04.png", compress_level=0)
        with self.assertRaisesRegex(ValueError, "identical pixels"):
            self.run_validation()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_cli_rejects_missing_asset_without_partial_output(self):
        (self.assets / "biome_23.jpg").unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_validation()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_cli_rejects_corrupt_image_without_partial_output(self):
        (self.assets / "ore_12.png").write_bytes(b"not a PNG")
        with self.assertRaises((OSError, SyntaxError)):
            self.run_validation()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_cli_rejects_nearly_invisible_ore(self):
        image = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        # One opaque pixel passes alpha extrema but is not visible in gameplay.
        image.putpixel((150, 150), (90, 150, 210, 255))
        image.save(self.assets / "ore_12.png")
        with self.assertRaisesRegex(ValueError, "fewer than 1%"):
            self.run_validation()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_cli_rejects_ore_without_opaque_mineral_pixels(self):
        image = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        image.putpixel((150, 150), (90, 150, 210, 128))
        image.save(self.assets / "ore_12.png")
        with self.assertRaisesRegex(ValueError, "fully opaque"):
            self.run_validation()
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
