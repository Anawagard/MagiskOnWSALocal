"""Source-only geometry regression for modernist raster chrome.

Run: python3 -m unittest discover -s chatgpt-shahta-v40 -p 'test_raster_chrome_v121.py'
No Gradle, APK, repository writes or GitHub Actions.
"""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

PREVIEW = Path(__file__).with_name("preview_raster_source_only_v118.py")

SKINS = (
    ("panel", (23, 32, 47), (85, 125, 148), (400, 96), False),
    ("button", (21, 103, 109), (92, 227, 207), (160, 64), True),
    ("button_off", (32, 44, 58), (91, 112, 131), (160, 64), False),
    ("header", (17, 27, 42), (85, 132, 156), (360, 88), False),
    ("nav", (17, 28, 42), (90, 150, 164), (360, 50), False),
)


class RasterChromeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import numpy  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(f"Raster dependencies unavailable: {exc}")
        spec = importlib.util.spec_from_file_location("shahta_chrome_preview", PREVIEW)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.render = module.load_renderers()
        cls.preview = module

    def test_all_five_chrome_assets_render_at_expected_dimensions(self):
        from PIL import Image
        with TemporaryDirectory() as folder:
            paths = []
            for name, base, border, size, bright in SKINS:
                path = Path(folder) / (name + ".png")
                self.render["panel_art"](path, base, border, size=size, bright=bright)
                with Image.open(path) as im:
                    self.assertEqual(im.format, "PNG", name)
                    self.assertEqual(im.size, size, name)
                    im.load()
                    self.assertIsNotNone(im.getbbox(), name)
                paths.append(path)
            self.assertEqual(self.preview.audit_unique_images(paths, "CHROME"), 5)

    def test_contact_sheet_contains_five_labeled_assets(self):
        from PIL import Image
        with TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            for name, base, border, size, bright in SKINS:
                path = root / (name + ".png")
                self.render["panel_art"](path, base, border, size=size, bright=bright)
                paths.append(path)
            output = root / "skins_contact.png"
            self.preview.sheet(paths, 2, (220, 135), "SKIN", output,
                               captions=[skin[0].upper() for skin in SKINS])
            with Image.open(output) as im:
                self.assertEqual(im.size, (440, 405))
                self.assertEqual(im.format, "PNG")
                im.verify()


if __name__ == "__main__":
    unittest.main()
