"""Source-only regression of the 24x24 visibility matrix visualization.

No Android project restoration, Gradle, APK, or Actions. The renderer accepts
synthetic score rows, so test execution never needs generated production art.
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from audit_ore_biome_composites_source_only import (
    COUNT, render_visibility_heatmap,
)


class VisibilityHeatmapTests(unittest.TestCase):
    def make_scores(self):
        return [
            {"biome": biome, "ore": ore,
             "core_low_contrast_fraction": (
                 None if (biome, ore) == (2, 3)
                 else 0.75 if (biome, ore) == (1, 24)
                 else 0.0)}
            for biome in range(1, COUNT + 1)
            for ore in range(1, COUNT + 1)
        ]

    def test_all_576_tiles_are_present_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "first.png", Path(directory) / "second.png"
            scores = self.make_scores()
            render_visibility_heatmap(scores, first)
            render_visibility_heatmap(list(reversed(scores)), second)
            with Image.open(first) as a, Image.open(second) as b:
                self.assertEqual(a.format, "PNG")
                self.assertEqual(a.size, (692, 720))
                self.assertEqual(a.tobytes(), b.tobytes())
                self.assertEqual(a.getpixel((70 + 23*25 + 12, 65 + 12))[0] > 150, True)
                missing = a.getpixel((70 + 2*25 + 12, 65 + 25 + 12))
                self.assertGreater(missing[0], missing[1])
                self.assertGreater(missing[2], missing[1])
                safe = a.getpixel((70 + 12, 65 + 12))
                self.assertGreater(safe[1], safe[0])

    def test_incomplete_or_duplicate_matrix_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "matrix.png"
            scores = self.make_scores()
            for invalid in (scores[:-1], scores[:-1] + [scores[0]]):
                with self.assertRaisesRegex(ValueError, "576 unique"):
                    render_visibility_heatmap(invalid, output)
                self.assertFalse(output.exists())

    def test_rejects_fractional_boolean_and_nonfinite_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "matrix.png"
            for key, value in (
                ("biome", 1.5), ("ore", True),
                ("core_low_contrast_fraction", float("nan")),
                ("core_low_contrast_fraction", float("inf")),
                ("core_low_contrast_fraction", -0.01),
                ("core_low_contrast_fraction", 1.01),
                ("core_low_contrast_fraction", "0.2"),
            ):
                scores = self.make_scores()
                scores[0] = {**scores[0], key: value}
                with self.subTest(key=key, value=value):
                    with self.assertRaises(ValueError):
                        render_visibility_heatmap(scores, output)
                    self.assertFalse(output.exists())

    def test_rejects_production_asset_names(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "production raster"):
                render_visibility_heatmap(
                    self.make_scores(), Path(directory) / "ore_03.png")


if __name__ == "__main__":
    unittest.main()
