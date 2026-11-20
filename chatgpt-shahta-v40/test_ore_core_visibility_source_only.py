"""Regression tests for opaque-core ore visibility metrics; no Android build."""
import unittest
import numpy as np
from audit_ore_biome_composites_source_only import visibility_details


class OpaqueCoreMetrics(unittest.TestCase):
    def test_fringe_does_not_mask_opaque_core(self):
        bg = np.zeros((2, 2, 3), dtype=np.uint8)
        ore = np.full((2, 2, 4), 255, dtype=np.uint8)
        ore[:, :, :3] = 255
        ore[0, 0, 3] = 1
        result = visibility_details(bg, ore)
        self.assertEqual(result["visible_coverage"], 1.0)
        self.assertEqual(result["core_coverage"], 0.75)
        self.assertEqual(result["core_weakest_decile"], 1.0)
        self.assertLess(result["weakest_decile"], 1.0)

    def test_only_fringe_has_no_core_score(self):
        bg = np.zeros((2, 2, 3), dtype=np.uint8)
        ore = np.full((2, 2, 4), 255, dtype=np.uint8)
        ore[:, :, 3] = 1
        result = visibility_details(bg, ore)
        self.assertEqual(result["core_coverage"], 0.0)
        self.assertIsNone(result["core_weakest_decile"])

    def test_half_alpha_counts_as_core(self):
        bg = np.zeros((1, 1, 3), dtype=np.uint8)
        ore = np.array([[[255, 255, 255, 128]]], dtype=np.uint8)
        result = visibility_details(bg, ore)
        self.assertEqual(result["core_coverage"], 1.0)
        self.assertAlmostEqual(result["core_weakest_decile"], 128 / 255, places=6)


if __name__ == "__main__":
    unittest.main()
