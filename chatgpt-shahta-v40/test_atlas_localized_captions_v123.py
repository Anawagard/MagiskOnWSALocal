"""Source-only regression checks for localized contact-sheet captions."""
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from preview_raster_source_only_v118 import sheet


class ContactSheetLocalizationTests(unittest.TestCase):
    def test_cyrillic_and_long_caption_stay_inside_tile(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sprite = root / "sprite.png"
            Image.new("RGBA", (40, 40), (12, 210, 195, 160)).save(sprite)
            baseline = root / "baseline.png"
            localized = root / "localized.png"
            sheet([sprite, sprite], 2, (120, 100), "ORE", baseline,
                  captions=["РУДА", ""])
            sheet([sprite, sprite], 2, (120, 100), "ORE", localized,
                  captions=["РУДА", "Очень длинное название руды " * 20])
            with Image.open(baseline) as before, Image.open(localized) as after:
                self.assertEqual(after.size, (240, 100))
                # The first cell must not change when the second caption grows.
                self.assertEqual(before.crop((0, 0, 120, 100)).tobytes(),
                                 after.crop((0, 0, 120, 100)).tobytes())
                # Rightmost eight pixels remain untouched by caption overflow.
                self.assertEqual(
                    before.crop((232, 0, 240, 24)).tobytes(),
                    after.crop((232, 0, 240, 24)).tobytes())


if __name__ == "__main__":
    unittest.main()
