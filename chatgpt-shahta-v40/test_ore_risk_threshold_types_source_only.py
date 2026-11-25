"""Source-only input validation for ore visibility risk thresholds.

Runs without generating Android assets, APKs, or invoking workflows.
"""
import unittest

from audit_ore_biome_composites_source_only import summarize_risks


class RiskThresholdInputTests(unittest.TestCase):
    def test_rejects_non_numeric_and_boolean_thresholds(self):
        for value in (True, False, None, "0.08", [], float("nan"), float("inf"), -0.1, 1.1):
            for name in ("low_contrast_threshold", "affected_fraction"):
                with self.subTest(name=name, value=repr(value)):
                    with self.assertRaises(ValueError):
                        summarize_risks([], **{name: value})

    def test_supported_numeric_thresholds_still_work(self):
        summary = summarize_risks([], low_contrast_threshold=0.08, affected_fraction=0.25)
        self.assertEqual(summary["risk_pairs"], 0)
        self.assertEqual(summary["unscorable_core_pairs"], 0)


if __name__ == "__main__":
    unittest.main()
