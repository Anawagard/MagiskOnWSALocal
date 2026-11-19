"""Source-only tests for composited ore/biome tint diagnostics."""
import math
import unittest
from unittest.mock import patch

from audit_cross_palette_source_only import blend_srgb, composited_palette_collisions


class CompositeTintTests(unittest.TestCase):
    def test_blending_endpoints_and_midpoint(self):
        self.assertEqual(blend_srgb((10, 20, 30), (110, 120, 130), 0), (10, 20, 30))
        self.assertEqual(blend_srgb((10, 20, 30), (110, 120, 130), 1), (110, 120, 130))
        self.assertEqual(blend_srgb((10, 20, 30), (110, 120, 130), 0.5), (60, 70, 80))

    def test_reject_invalid_alpha(self):
        for bad in (-0.01, 1.01, True, False, None, "0.5"):
            with self.subTest(alpha=bad), self.assertRaises(ValueError):
                blend_srgb((0, 0, 0), (255, 255, 255), bad)

    def test_reject_malformed_rgb_without_silent_zip_truncation(self):
        valid = (10, 20, 30)
        invalid = ((), (1, 2), (1, 2, 3, 4), (0, 0, 256),
                   (-1, 2, 3), (1.0, 2, 3), (True, 2, 3),
                   ("1", 2, 3), None, "123")
        for bad in invalid:
            with self.subTest(rgb=bad):
                with self.assertRaises(ValueError):
                    blend_srgb(bad, valid, 0.65)
                with self.assertRaises(ValueError):
                    blend_srgb(valid, bad, 0.65)
        self.assertEqual(blend_srgb([0, 128, 255], [255, 128, 0], 0),
                         (0, 128, 255))

    def test_complete_matrix_and_limits(self):
        full = composited_palette_collisions(limit=576)
        self.assertEqual(len(full), 576)
        self.assertEqual(len({(i, j) for _, i, j in full}), 576)
        self.assertEqual(full, sorted(full))
        self.assertTrue(all(math.isfinite(d) and d >= 0 for d, _, _ in full))
        self.assertEqual(composited_palette_collisions(limit=7), full[:7])
        for bad in (0, 577, True, 1.5):
            with self.subTest(limit=bad), self.assertRaises(ValueError):
                composited_palette_collisions(limit=bad)

    def test_transparent_ore_has_zero_difference(self):
        data = {"SCENES": [(i, i, i) for i in range(24)],
                "ORES": [(i, 0, 0) for i in range(24)]}
        with patch("audit_cross_palette_source_only.palettes", return_value=data):
            full = composited_palette_collisions(alpha=0, limit=576)
        self.assertTrue(all(d == 0 for d, _, _ in full))


if __name__ == "__main__":
    unittest.main()
