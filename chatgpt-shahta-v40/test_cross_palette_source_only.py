"""Source-only regression tests for 24x24 biome/ore tint comparisons.

No Android builds, asset writes, or subprocess calls.
"""
import math
import unittest
from unittest.mock import patch

from audit_cross_palette_source_only import cross_palette_collisions
from audit_palette_perception_source_only import oklab, palettes


class CrossPaletteTests(unittest.TestCase):
    def test_full_matrix_is_complete_sorted_and_finite(self):
        results = cross_palette_collisions(576)
        self.assertEqual(len(results), 576)
        self.assertEqual(len({(i, j) for _, i, j in results}), 576)
        self.assertEqual({i for _, i, _ in results}, set(range(24)))
        self.assertEqual({j for _, _, j in results}, set(range(24)))
        self.assertEqual(results, sorted(results))
        self.assertTrue(all(math.isfinite(d) and d >= 0 for d, _, _ in results))

    def test_limits_and_prefix_consistency(self):
        full = cross_palette_collisions(576)
        for limit in (1, 3, 10, 24, 575, 576):
            with self.subTest(limit=limit):
                self.assertEqual(cross_palette_collisions(limit), full[:limit])
        for bad in (0, -1, 577, True, False, 1.0, "10", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    cross_palette_collisions(bad)

    def test_distances_match_independent_pair_calculation(self):
        data = palettes()
        results = cross_palette_collisions(576)
        for distance, i, j in results:
            self.assertAlmostEqual(
                distance,
                math.dist(oklab(data["SCENES"][i]), oklab(data["ORES"][j])),
                places=12,
            )

    def test_ties_have_deterministic_index_order(self):
        # A diagnostic must remain deterministic even if categories share tints.
        identical = [(i, i, i) for i in range(24)]
        with patch("audit_cross_palette_source_only.palettes",
                   return_value={"SCENES": identical, "ORES": identical}):
            results = cross_palette_collisions(24)
        self.assertEqual([(i, j) for _, i, j in results],
                         [(i, i) for i in range(24)])
        self.assertTrue(all(distance == 0 for distance, _, _ in results))


if __name__ == "__main__":
    unittest.main()
