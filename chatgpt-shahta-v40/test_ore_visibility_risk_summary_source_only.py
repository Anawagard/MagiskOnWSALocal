"""Source-only regression checks for actionable biome/ore risk reporting."""
import unittest
from audit_ore_biome_composites_source_only import summarize_risks, COUNT


def row(biome, ore, fraction, decile=0.02):
    return {
        "biome": biome, "ore": ore,
        "core_low_contrast_fraction": fraction,
        "core_weakest_decile": decile if fraction is not None else None,
    }


class RiskSummaryTests(unittest.TestCase):
    def test_threshold_and_counts(self):
        result = summarize_risks([
            row(1, 1, 0.25), row(1, 2, 0.5),
            row(2, 1, 0.249999), row(2, 2, None),
        ])
        self.assertEqual(result["risk_pairs"], 2)
        self.assertEqual(result["risk_count_by_biome"]["1"], 2)
        self.assertEqual(result["risk_count_by_biome"]["2"], 0)
        self.assertEqual(result["risk_count_by_ore"]["1"], 1)
        self.assertEqual(result["risk_count_by_ore"]["2"], 1)
        self.assertEqual(len(result["risk_count_by_biome"]), COUNT)
        self.assertEqual([(r["biome"], r["ore"]) for r in result["worst_pairs"]],
                         [(1, 2), (1, 1)])

    def test_deterministic_ties(self):
        result = summarize_risks([row(2, 2, 0.5), row(1, 2, 0.5),
                                  row(1, 1, 0.5)])
        self.assertEqual([(r["biome"], r["ore"]) for r in result["worst_pairs"]],
                         [(1, 1), (1, 2), (2, 2)])

    def test_empty_and_missing_core(self):
        result = summarize_risks([row(1, 1, None)])
        self.assertEqual(result["risk_pairs"], 0)
        self.assertEqual(result["worst_pairs"], [])

    def test_nondefault_displayed_cutoff_is_rejected(self):
        # The per-pair fraction is measured at 0.08, not recomputed here.
        for value in (0.0, 0.05, 0.1, 1.0):
            with self.assertRaisesRegex(ValueError, "precomputed scores"):
                summarize_risks([row(1, 1, 0.5)], low_contrast_threshold=value)
        self.assertEqual(summarize_risks([row(1, 1, 0.5)],
                                         low_contrast_threshold=0.08)["risk_pairs"], 1)

    def test_invalid_thresholds(self):
        for value in (-0.01, 1.01):
            with self.assertRaises(ValueError):
                summarize_risks([], affected_fraction=value)
            with self.assertRaises(ValueError):
                summarize_risks([], low_contrast_threshold=value)


if __name__ == "__main__":
    unittest.main()
