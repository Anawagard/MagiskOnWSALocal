"""Source-only reproducibility regression for the actual raster renderers.

No Android baseline, Gradle, APK or GitHub Actions are used.
Run: python3 -m unittest chatgpt-shahta-v40/test_raster_determinism_v122.py
"""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

PREVIEW = Path(__file__).with_name("preview_raster_source_only_v118.py")


class RasterDeterminism(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import numpy  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(f"Raster dependencies unavailable: {exc}")
        spec = importlib.util.spec_from_file_location("shahta_preview_determinism", PREVIEW)
        preview = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preview)
        cls.render = preview.load_renderers()

    @staticmethod
    def decoded_digest(path):
        from PIL import Image
        with Image.open(path) as im:
            im.load()
            return hashlib.sha256(
                im.mode.encode("ascii") + repr(im.size).encode("ascii") + im.tobytes()
            ).hexdigest()

    def test_every_biome_is_reproducible(self):
        with TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.jpg", Path(folder) / "b.jpg"
            for i, color in enumerate(self.render["SCENES"]):
                self.render["cave"](i, color, a)
                self.render["cave"](i, color, b)
                self.assertEqual(self.decoded_digest(a), self.decoded_digest(b),
                                 f"Biome {i} changes between identical runs")

    def test_every_ore_is_reproducible(self):
        with TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.png", Path(folder) / "b.png"
            for i, color in enumerate(self.render["ORES"]):
                self.render["ore"](i, color, a)
                self.render["ore"](i, color, b)
                self.assertEqual(self.decoded_digest(a), self.decoded_digest(b),
                                 f"Ore {i} changes between identical runs")

    def test_menu_and_chrome_are_reproducible(self):
        menus = ((59, 118, 137), (132, 74, 51),
                 (73, 108, 133), (101, 93, 143))
        skins = (
            ((23, 32, 47), (85, 125, 148), (400, 96), False),
            ((21, 103, 109), (92, 227, 207), (160, 64), True),
            ((32, 44, 58), (91, 112, 131), (160, 64), False),
            ((17, 27, 42), (85, 132, 156), (360, 88), False),
            ((17, 28, 42), (90, 150, 164), (360, 50), False),
        )
        with TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.png", Path(folder) / "b.png"
            for i, color in enumerate(menus, 31):
                self.render["cave"](i, color, a)
                self.render["cave"](i, color, b)
                self.assertEqual(self.decoded_digest(a), self.decoded_digest(b),
                                 f"Menu {i} is nondeterministic")
            for index, (base, border, size, bright) in enumerate(skins):
                self.render["panel_art"](a, base, border, size=size, bright=bright)
                self.render["panel_art"](b, base, border, size=size, bright=bright)
                self.assertEqual(self.decoded_digest(a), self.decoded_digest(b),
                                 f"Chrome {index} is nondeterministic")


if __name__ == "__main__":
    unittest.main()
