"""Regression checks for multi-opacity biome/ore tint collision ranking.

Source-only: does not load Android, invoke Gradle or generate APKs.
"""
import math
import unittest
from unittest.mock import patch

from audit_cross_palette_source_only import (
    alpha_sensitivity_report, blend_srgb, composited_palette_collisions,
)


class AlphaSensitivityTests(unittest.TestCase):
    def test_all_pairs_and_stable_ranking(self):
        full = alpha_sensitivity_report(limit=576)
        self.assertEqual(len(full), 24 * 24)
        self.assertEqual(len({(i, j) for _, i, j, _ in full}), 576)
        self.assertEqual(full, sorted(full, key=lambda row: (row[0], row[1], row[2])))
        for worst, biome, ore, distances in full:
            self.assertTrue(0 <= biome < 24 and 0 <= ore < 24)
            self.assertEqual(len(distances), 4)
            self.assertTrue(all(math.isfinite(d) and d >= 0 for d in distances))
            self.assertAlmostEqual(worst, max(distances))
        self.assertEqual(alpha_sensitivity_report(limit=5), full[:5])

    def test_single_alpha_agrees_with_composite_report(self):
        for alpha in (0, 0.35, 0.65, 1):
            with self.subTest(alpha=alpha):
                ranked = alpha_sensitivity_report(alphas=[alpha], limit=576)
                simple = composited_palette_collisions(alpha=alpha, limit=576)
                self.assertEqual(
                    [(d, i, j) for d, i, j, _ in ranked],
                    simple,
                )
                self.assertTrue(all(distances == (d,) for d, _, _, distances in ranked))

    def test_reject_invalid_opacity_sequences_and_limits(self):
        for bad in (None, (), [], "0.5", [None], [[0.5]], [True],
                    [-0.01], [1.01], [float("nan")], [float("inf")],
                    [0.5, 0.5], [0, False], [0.25, 0.25]):
            with self.subTest(alphas=bad), self.assertRaises(ValueError):
                alpha_sensitivity_report(alphas=bad)
        for bad in (0, -1, 577, True, 1.5, None):
            with self.subTest(limit=bad), self.assertRaises(ValueError):
                alpha_sensitivity_report(limit=bad)

    def test_zero_alpha_and_identical_colors(self):
        colors = {"SCENES": [(20, 40, 60)] * 24,
                  "ORES": [(20, 40, 60)] * 24}
        with patch("audit_cross_palette_source_only.palettes", return_value=colors):
            result = alpha_sensitivity_report(alphas=[0, 0.5, 1], limit=576)
        self.assertEqual(len(result), 576)
        self.assertTrue(all(row[0] == 0 and row[3] == (0, 0, 0) for row in result))

    def test_blend_is_bounded_for_all_channel_extremes(self):
        for background in (0, 255):
            for foreground in (0, 255):
                for alpha in (0, 0.25, 0.5, 0.75, 1):
                    value = blend_srgb((background,) * 3, (foreground,) * 3, alpha)
                    self.assertTrue(all(0 <= c <= 255 for c in value))


if __name__ == "__main__":
    unittest.main()
