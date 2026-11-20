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
                self.assertTrue(0 <= row["core_low_contrast_fraction"] <= 1)
            summary = summarize_risks(first)
            self.assertEqual(sum(summary["risk_count_by_biome"].values()),
                             summary["risk_pairs"])
            self.assertEqual(sum(summary["risk_count_by_ore"].values()),
                             summary["risk_pairs"])

    def test_missing_asset_fails_instead_of_reporting_partial_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                analyze(Path(directory))


if __name__ == "__main__":
    unittest.main()
