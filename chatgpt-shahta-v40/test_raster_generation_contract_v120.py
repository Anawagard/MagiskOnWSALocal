"""Source-only raster generation contract for all 24 biomes and ore sprites.

Run: python3 -m unittest chatgpt-shahta-v40/test_raster_generation_contract_v120.py
Does not restore the Android project, invoke Gradle or trigger Actions.
"""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

PREVIEW = Path(__file__).with_name("preview_raster_source_only_v118.py")


class RasterGenerationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import numpy  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(f"Raster dependencies unavailable: {exc}")
        spec = importlib.util.spec_from_file_location("shahta_raster_preview", PREVIEW)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.preview = module
        cls.render = module.load_renderers()

    def test_all_biomes_and_ores_render_distinct_with_correct_geometry(self):
        from PIL import Image
        with TemporaryDirectory() as folder:
            root = Path(folder)
            biomes, ores = [], []
            for index in range(24):
                biome = root / f"biome_{index:02}.jpg"
                ore = root / f"ore_{index:02}.png"
                self.render["cave"](index, self.render["SCENES"][index], biome)
                self.render["ore"](index, self.render["ORES"][index], ore)
                with Image.open(biome) as im:
                    self.assertEqual(im.size, (360, 570), f"biome {index}")
                    self.assertEqual(im.format, "JPEG")
                    im.verify()
                with Image.open(ore) as im:
                    self.assertEqual(im.size, (300, 300), f"ore {index}")
                    self.assertEqual(im.format, "PNG")
                    self.assertIn("A", im.getbands())
                    alpha = im.getchannel("A")
                    self.assertEqual(alpha.getextrema(), (0, 255))
                    # Reject nearly invisible or full-frame rocks: geometry
                    # must leave tappable, recognizable transparent margins.
                    opaque_fraction = sum(n for value, n in enumerate(alpha.histogram())
                                          if value >= 128) / (300 * 300)
                    self.assertGreater(opaque_fraction, .15, f"ore {index}")
                    self.assertLess(opaque_fraction, .85, f"ore {index}")
                biomes.append(biome)
                ores.append(ore)
            self.assertEqual(self.preview.audit_unique_images(biomes, "BIOME"), 24)
            self.assertEqual(self.preview.audit_unique_images(ores, "ORE"), 24)

    def test_all_four_menu_backgrounds_are_distinct(self):
        from PIL import Image
        with TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            colors = ((59, 118, 137), (132, 74, 51),
                      (73, 108, 133), (101, 93, 143))
            for i, color in enumerate(colors, 31):
                target = root / f"menu_{i}.jpg"
                self.render["cave"](i, color, target)
                with Image.open(target) as im:
                    self.assertEqual(im.size, (360, 570))
                    im.verify()
                paths.append(target)
            self.assertEqual(self.preview.audit_unique_images(paths, "MENU"), 4)


if __name__ == "__main__":
    unittest.main()
