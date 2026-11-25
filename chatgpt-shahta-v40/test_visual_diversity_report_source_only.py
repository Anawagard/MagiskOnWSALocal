"""Source-only regression for complete nearest-neighbor artwork reports.

Run: python -m unittest test_visual_diversity_report_source_only.py
No Android SDK, Gradle or APK is involved.
"""
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from audit_visual_diversity import BIOMES, ORES, audit


class VisualDiversityReportTests(unittest.TestCase):
    def test_complete_report_is_consistent_and_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            yy, xx = np.indices((570, 360))
            # Separate low-frequency colour profiles survive the audit's
            # downsampling, unlike high-frequency checkerboards.
            def texture(x, y, index):
                return np.stack((
                    index % 4 * 50 + (x // 3 + y // 6) % 96,
                    index // 4 % 3 * 66 + (y // 3 + x // 6) % 96,
                    index // 12 * 110 + (x // 5 + y // 4) % 96,
                ), axis=-1).astype(np.uint8)

            for i, name in enumerate(BIOMES):
                Image.fromarray(texture(xx, yy, i)).save(folder / name, quality=92)
            yy, xx = np.indices((300, 300))
            mask = (xx - 150) ** 2 + (yy - 150) ** 2 < 90 ** 2
            for i, name in enumerate(ORES):
                rgba = np.zeros((300, 300, 4), dtype=np.uint8)
                rgba[..., :3] = texture(xx, yy, i)
                rgba[..., 3] = np.where(mask, 255, 0).astype(np.uint8)
                Image.fromarray(rgba).save(folder / name)
            first = audit(folder)
            self.assertEqual(first, audit(folder))
            for label, names in (("biomes", BIOMES), ("ores", ORES)):
                self.assertEqual([item["file"] for item in first[label]], names)
                neighbors = first[f"{label}_nearest_neighbors"]
                self.assertEqual(len(neighbors), 24)
                self.assertEqual({n["file"] for n in neighbors}, set(names))
                for item in neighbors:
                    self.assertIn(item["nearest_file"], names)
                    self.assertNotEqual(item["file"], item["nearest_file"])
                    self.assertGreaterEqual(item["mean_channel_delta"], 1.5)
                closest = first[f"{label}_closest_pair"]
                self.assertEqual(len(closest["files"]), 2)
                self.assertEqual(
                    closest["mean_channel_delta"],
                    min(n["mean_channel_delta"] for n in neighbors),
                )


if __name__ == "__main__":
    unittest.main()
