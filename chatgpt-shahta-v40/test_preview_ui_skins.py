"""Source-only regression tests for the nine-skin UI contact sheet.

Run: python -m unittest test_preview_ui_skins.py
No Android project, Gradle or GitHub Actions required.
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from preview_ui_skins import ASSETS, BG, build_preview


class UiSkinPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.assets = root / "assets"
        self.assets.mkdir()
        self.output = root / "ui_contact_sheet.png"
        for index, (name, size) in enumerate(ASSETS):
            if name.endswith(".jpg"):
                image = Image.new("RGB", size, (30 + index * 12, 44, 61))
                image.save(self.assets / name, format="JPEG")
            else:
                image = Image.new("RGBA", size, (35, 180, 166, 140))
                image.save(self.assets / name, format="PNG")

    def test_complete_sheet_and_dimensions(self):
        self.assertEqual(build_preview(self.assets, self.output), self.output)
        with Image.open(self.output) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (1040, 1020))
            self.assertEqual(image.mode, "RGB")
            # The empty margin retains the graphite design language.
            self.assertEqual(image.getpixel((1039, 1019)), BG)

    def test_missing_resource_rejected_without_output(self):
        (self.assets / "nav.png").unlink()
        with self.assertRaises(FileNotFoundError):
            build_preview(self.assets, self.output)
        self.assertFalse(self.output.exists())

    def test_wrong_resolution_rejected_without_output(self):
        Image.new("RGBA", (159, 64), (0, 0, 0, 255)).save(self.assets / "button.png")
        with self.assertRaises(ValueError):
            build_preview(self.assets, self.output)
        self.assertFalse(self.output.exists())

    def test_disguised_format_rejected(self):
        Image.new("RGB", (360, 570), (0, 0, 0)).save(
            self.assets / "menu_1.jpg", format="PNG"
        )
        with self.assertRaises(ValueError):
            build_preview(self.assets, self.output)
        self.assertFalse(self.output.exists())

    def test_corrupt_png_rejected_without_output(self):
        (self.assets / "header.png").write_bytes(b"not a valid png")
        with self.assertRaises(Exception):
            build_preview(self.assets, self.output)
        self.assertFalse(self.output.exists())

    def test_cannot_write_inside_asset_directory(self):
        with self.assertRaises(ValueError):
            build_preview(self.assets, self.assets / "contact.png")
        self.assertFalse((self.assets / "contact.png").exists())

    def test_missing_output_directory_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(self.assets, self.assets.parent / "missing" / "contact.png")


if __name__ == "__main__":
    unittest.main()
