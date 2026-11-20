"""End-to-end source-only fixture for the 24 x 24 raster visibility matrix.

Run: python -m unittest test_ore_matrix_integration_source_only.py
Does not invoke Gradle, Android, GitHub Actions, or change production assets.
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from audit_ore_biome_composites_source_only import (
    BACKGROUND_SIZE, COUNT, ORE_SIZE, analyze, summarize_risks,
    contrast_score, visibility_details,
)


class OreMatrixIntegrationTest(unittest.TestCase):
    def test_all_pairs_and_deterministic_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(COUNT):
                # Different biome colors and opaque ore colors keep every
                # input distinct; the transparent border exercises coverage.
                Image.new("RGB", BACKGROUND_SIZE,
                          (index * 9, 35, 90)).save(
                              root / f"biome_{index:02d}.jpg", "JPEG")
                ore = Image.new("RGBA", ORE_SIZE, (0, 0, 0, 0))
                ore.paste((220, index * 8, 60, 255), (40, 40, 260, 260))
                ore.save(root / f"ore_{index:02d}.png", "PNG")
            first = analyze(root)
            second = analyze(root)
            self.assertEqual(first, second)
            self.assertEqual(len(first), COUNT * COUNT)
            self.assertEqual(
                {(row["biome"], row["ore"]) for row in first},
                {(i, j) for i in range(1, COUNT + 1)
                 for j in range(1, COUNT + 1)},
            )
            self.assertEqual(
                first, sorted(first, key=lambda r:
                              (r["score"], r["biome"], r["ore"])))
            for row in first:
                self.assertTrue(0 <= row["score"] <= 1)
                self.assertTrue(0 < row["visible_coverage"] <= 1)
                self.assertTrue(0 < row["core_coverage"] <= 1)
                self.assertTrue(0 <= row["core_mean_contrast"] <= 1)
                self.assertTrue(0 <= row["core_low_contrast_fraction"] <= 1)
            summary = summarize_risks(first)
            self.assertEqual(summary["unscorable_core_pairs"], 0)
            self.assertEqual(summary["unscorable_core_locations"], [])
            self.assertEqual(sum(summary["risk_count_by_biome"].values()),
                             summary["risk_pairs"])
            self.assertEqual(sum(summary["risk_count_by_ore"].values()),
                             summary["risk_pairs"])

    def test_displayed_alpha_math_and_transparent_rgb(self):
        # A fully transparent RGB value must never affect the score.
        # Half-opacity ore must contribute half the displayed difference.
        background = Image.new("RGB", (2, 1), (0, 0, 0))
        ore = Image.new("RGBA", (2, 1))
        ore.putpixel((0, 0), (255, 255, 255, 128))
        ore.putpixel((1, 0), (255, 0, 255, 0))
        expected = 128 / 255
        self.assertAlmostEqual(contrast_score(background, ore), expected,
                               places=6)
        details = visibility_details(background, ore)
        self.assertAlmostEqual(details["visible_coverage"], 0.5)
        self.assertAlmostEqual(details["core_coverage"], 0.5)
        self.assertEqual(details["core_low_contrast_fraction"], 0.0)
        self.assertAlmostEqual(details["core_mean_contrast"], expected, places=6)
        # Transparent pixel colors are irrelevant even if wildly different.
        ore.putpixel((1, 0), (0, 255, 0, 0))
        self.assertAlmostEqual(contrast_score(background, ore), expected,
                               places=6)

    def test_translucent_fringe_is_not_misclassified_as_solid_core(self):
        background = Image.new("RGB", (2, 1), (0, 0, 0))
        ore = Image.new("RGBA", (2, 1))
        ore.putpixel((0, 0), (255, 255, 255, 255))
        ore.putpixel((1, 0), (0, 0, 0, 20))
        details = visibility_details(background, ore)
        self.assertEqual(details["visible_coverage"], 1.0)
        self.assertEqual(details["core_coverage"], 0.5)
        self.assertEqual(details["core_low_contrast_fraction"], 0.0)

    def test_soft_ore_without_opaque_core_is_reported_not_misclassified(self):
        # A translucent ore is visible but has no alpha>=0.5 solid core.
        # Its missing core statistics must remain JSON-safe nulls, not NaN.
        import json
        background = Image.new("RGB", (2, 2), (30, 40, 50))
        ore = Image.new("RGBA", (2, 2), (240, 200, 160, 64))
        details = visibility_details(background, ore)
        self.assertEqual(details["visible_coverage"], 1.0)
        self.assertEqual(details["core_coverage"], 0.0)
        for key in ("core_mean_contrast", "core_low_contrast_fraction",
                    "core_weakest_decile"):
            self.assertIsNone(details[key])
        row = {"biome": 1, "ore": 1, "score": contrast_score(background, ore),
               **details}
        summary = summarize_risks([row])
        self.assertEqual(summary["risk_pairs"], 0)
        self.assertEqual(summary["worst_pairs"], [])
        self.assertEqual(summary["unscorable_core_pairs"], 1)
        self.assertEqual(summary["unscorable_core_locations"],
                         [{"biome": 1, "ore": 1}])
        json.dumps({"scores": [row], "visibility_risks": summary},
                   allow_nan=False)

    def test_partial_matrix_fails_closed(self):
        # A complete first pair must not disguise missing remaining assets.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", BACKGROUND_SIZE, (30, 50, 70)).save(
                root / "biome_00.jpg", "JPEG")
            Image.new("RGBA", ORE_SIZE, (100, 150, 200, 255)).save(
                root / "ore_00.png", "PNG")
            with self.assertRaises(FileNotFoundError):
                analyze(root)

    def test_invalid_ore_format_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", BACKGROUND_SIZE, (30, 50, 70)).save(
                root / "biome_00.jpg", "JPEG")
            # A JPEG renamed to PNG must not be silently accepted.
            Image.new("RGB", ORE_SIZE, (100, 150, 200)).save(
                root / "ore_00.png", "JPEG")
            with self.assertRaises(ValueError):
                analyze(root)

    def test_fully_transparent_ore_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", BACKGROUND_SIZE, (30, 50, 70)).save(
                root / "biome_00.jpg", "JPEG")
            Image.new("RGBA", ORE_SIZE, (0, 0, 0, 0)).save(
                root / "ore_00.png", "PNG")
            with self.assertRaisesRegex(ValueError, "empty ore sprite"):
                analyze(root)

    def test_missing_asset_fails_instead_of_reporting_partial_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                analyze(Path(directory))


if __name__ == "__main__":
    unittest.main()
