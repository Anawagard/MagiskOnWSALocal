"""Regression tests for the source-only opacity-sweep palette audit."""
import math
import unittest
from unittest.mock import patch

from audit_cross_palette_source_only import (
    alpha_sensitivity_report, composited_palette_collisions,
)


class AlphaSensitivityTests(unittest.TestCase):
    def test_full_matrix_and_deterministic_order(self):
        rows = alpha_sensitivity_report(limit=576)
        self.assertEqual(len(rows), 576)
        self.assertEqual(len({(i, j) for _, i, j, _ in rows}), 576)
        self.assertEqual(rows, sorted(rows, key=lambda r: (r[0], r[1], r[2])))
        self.assertTrue(all(len(distances) == 4 and all(
            math.isfinite(d) and d >= 0 for d in distances)
            and score == max(distances)
            for score, _, _, distances in rows))
        self.assertEqual(alpha_sensitivity_report(limit=5), rows[:5])

    def test_single_alpha_matches_existing_composite_audit(self):
        baseline = composited_palette_collisions(alpha=0.65, limit=576)
        swept = alpha_sensitivity_report(alphas=(0.65,), limit=576)
        self.assertEqual([(score, i, j) for score, i, j, _ in swept], baseline)

    def test_alpha_zero_is_invisible_for_all_pairs(self):
        rows = alpha_sensitivity_report(alphas=(0,), limit=576)
        self.assertTrue(all(score == 0 and distances == (0,)
                            for score, _, _, distances in rows))

    def test_invalid_inputs_fail_closed(self):
        for bad in ((), [], (0.5, 0.5), (float('nan'),),
                    (float('inf'),), (-0.1,), (1.1,), (True,),
                    ('0.5',), None):
            with self.subTest(alphas=bad), self.assertRaises(ValueError):
                alpha_sensitivity_report(alphas=bad)
        for bad in (0, 577, True, 1.5):
            with self.subTest(limit=bad), self.assertRaises(ValueError):
                alpha_sensitivity_report(limit=bad)

    def test_ranking_uses_worst_case_not_average(self):
        data = {'SCENES': [(0, 0, 0)] * 24,
                'ORES': [(255, 255, 255)] * 24}
        with patch('audit_cross_palette_source_only.palettes', return_value=data):
            rows = alpha_sensitivity_report(alphas=(0, 1), limit=576)
        self.assertTrue(all(distances[0] == 0 and score == distances[1]
                            for score, _, _, distances in rows))


if __name__ == '__main__':
    unittest.main()
