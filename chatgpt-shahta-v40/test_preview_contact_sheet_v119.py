"""Source-only contact-sheet regression: no Android SDK, Gradle or Actions.

Run: python3 -m unittest chatgpt-shahta-v40/test_preview_contact_sheet_v119.py
"""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

PREVIEW = Path(__file__).with_name("preview_raster_source_only_v118.py")


class ContactSheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PIL import Image
        except ImportError as exc:
            raise unittest.SkipTest(f"Pillow required: {exc}")
        cls.Image = Image
        spec = importlib.util.spec_from_file_location("shahta_preview_v118", PREVIEW)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.preview = module

    def test_sheet_dimensions_order_and_alpha_compositing(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            colors = [(230, 60, 60, 255), (50, 230, 80, 255),
                      (60, 100, 230, 255), (255, 255, 255, 0),
                      (230, 170, 60, 255)]
            for i, color in enumerate(colors):
                path = root / f"tile_{i}.png"
                self.Image.new("RGBA", (40, 40), color).save(path)
                paths.append(path)
            target = root / "contact.png"
            self.preview.sheet(paths, 3, (100, 100), "TEST", target)
            with self.Image.open(target) as result:
                self.assertEqual(result.size, (300, 200))
                self.assertEqual(result.mode, "RGB")
                self.assertEqual(result.getpixel((50, 50)), (230, 60, 60))
                self.assertEqual(result.getpixel((150, 50)), (50, 230, 80))
                self.assertEqual(result.getpixel((250, 50)), (60, 100, 230))
                # A transparent PNG must reveal graphite, not black/white.
                self.assertEqual(result.getpixel((50, 150)), (13, 20, 31))
                self.assertEqual(result.getpixel((150, 150)), (230, 170, 60))
                self.assertEqual(result.getpixel((250, 150)), (13, 20, 31))

    def test_sheet_reproducibility(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            tile = root / "tile.png"
            self.Image.new("RGBA", (25, 25), (93, 224, 210, 255)).save(tile)
            first, second = root / "a.png", root / "b.png"
            self.preview.sheet([tile], 2, (90, 90), "ORE", first)
            self.preview.sheet([tile], 2, (90, 90), "ORE", second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_invalid_sheet_geometry_and_caption_mismatch(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            tile = root / "tile.png"
            self.Image.new("RGBA", (30, 30), (93, 224, 210, 255)).save(tile)
            dest = root / "sheet.png"
            cases = [
                ([], 2, (90, 90), None),
                ([tile], 0, (90, 90), None),
                ([tile], 2, (16, 90), None),
                ([tile], 2, (90, 35), None),
                ([tile], 2, (90, 90), ["ONE", "EXTRA"]),
            ]
            for paths, columns, cell, captions in cases:
                with self.subTest(paths=len(paths), columns=columns, cell=cell, captions=captions):
                    with self.assertRaises(ValueError):
                        self.preview.sheet(paths, columns, cell, "TEST", dest, captions=captions)

    def test_named_skin_captions(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            tile = root / "tile.png"
            self.Image.new("RGBA", (40, 40), (93, 224, 210, 255)).save(tile)
            first, second = root / "named.png", root / "indexed.png"
            self.preview.sheet([tile], 2, (120, 100), "SKIN", first, captions=["PANEL"])
            self.preview.sheet([tile], 2, (120, 100), "SKIN", second)
            with self.Image.open(first) as named, self.Image.open(second) as indexed:
                self.assertEqual(named.size, indexed.size)
                self.assertNotEqual(named.tobytes(), indexed.tobytes())

    def test_generator_coverage_and_no_android_import(self):
        source = PREVIEW.read_text(encoding="utf-8")
        self.assertIn('range(24)', source)
        self.assertIn('load_renderers()', source)
        self.assertIn('range(24)', source)
        self.assertIn('enumerate(((59, 118, 137)', source)
        self.assertIn('env["cave"](30 + j, base, target)', source)
        self.assertIn('menus_contact.png', source)
        self.assertIn('Created 4 contact sheets', source)
        self.assertNotIn('subprocess', source)
        self.assertNotIn('gradlew', source)
        self.assertNotIn('workflow_dispatch', source)


if __name__ == "__main__":
    unittest.main()
