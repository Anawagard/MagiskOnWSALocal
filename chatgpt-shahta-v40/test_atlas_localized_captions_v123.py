"""Source-only regression checks for localized contact-sheet captions."""
import tempfile
import unittest
from unittest.mock import patch
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


    def test_multiline_caption_cannot_draw_into_next_row(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sprite = root / "sprite.png"
            Image.new("RGBA", (40, 40), (12, 210, 195, 160)).save(sprite)
            normal = root / "normal.png"
            malicious = root / "multiline.png"
            paths = [sprite, sprite]
            sheet(paths, 1, (120, 100), "ORE", normal,
                  captions=["РУДА", "SECOND"])
            sheet(paths, 1, (120, 100), "ORE", malicious,
                  captions=["РУДА\n" * 50 + "SECOND", "SECOND"])
            with Image.open(normal) as before, Image.open(malicious) as after:
                self.assertEqual(after.size, (120, 200))
                # Caption in row one must never modify pixels in row two.
                self.assertEqual(before.crop((0, 100, 120, 200)).tobytes(),
                                 after.crop((0, 100, 120, 200)).tobytes())


    def test_bitmap_font_fallback_accepts_localized_caption(self):
        """Missing DejaVu must not abort a contact-sheet export."""
        from PIL import ImageFont
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sprite = root / "sprite.png"
            output = root / "fallback.png"
            Image.new("RGBA", (40, 40), (12, 210, 195, 160)).save(sprite)
            with patch.object(ImageFont, "truetype", side_effect=OSError("font missing")):
                sheet([sprite], 1, (120, 100), "ORE", output,
                      captions=["РУДА – минерал"])
            with Image.open(output) as rendered:
                self.assertEqual(rendered.size, (120, 100))


    def test_control_characters_do_not_change_other_tiles(self):
        """Real CR, LF, tabs and Unicode separators cannot escape their cell."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sprite = root / "sprite.png"
            Image.new("RGBA", (40, 40), (12, 210, 195, 160)).save(sprite)
            clean = root / "clean.png"
            hostile = root / "hostile.png"
            paths = [sprite] * 4
            sheet(paths, 2, (120, 100), "ORE", clean,
                  captions=["TOP", "SAFE", "BOTTOM", "SAFE"])
            sheet(paths, 2, (120, 100), "ORE", hostile,
                  captions=["TOP\r\n\t" * 80 + "\u2028" + "OVERFLOW",
                            "SAFE", "BOTTOM", "SAFE"])
            with Image.open(clean) as before, Image.open(hostile) as after:
                self.assertEqual(after.size, (240, 200))
                # Other columns and the following row are pixel-identical.
                self.assertEqual(before.crop((120, 0, 240, 200)).tobytes(),
                                 after.crop((120, 0, 240, 200)).tobytes())
                self.assertEqual(before.crop((0, 100, 120, 200)).tobytes(),
                                 after.crop((0, 100, 120, 200)).tobytes())


if __name__ == "__main__":
    unittest.main()
