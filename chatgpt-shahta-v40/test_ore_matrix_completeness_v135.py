"""Validate 24x24 risk reports fail closed on corrupt/incomplete rows.

Pure Python fixture tests; no image rendering, Gradle or Android execution.
"""
from pathlib import Path
import ast
import importlib.util
import sys
import unittest

HERE = Path(__file__).resolve().parent
AUDITOR = HERE / "audit_ore_biome_composites_source_only.py"
ast.parse(AUDITOR.read_text(encoding="utf-8"), filename=str(AUDITOR))
spec = importlib.util.spec_from_file_location("ore_matrix_v135", AUDITOR)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def fixture():
    return [
        dict(biome=i, ore=j, score=.15, visible_coverage=.55,
             weakest_decile=.07, core_coverage=.45,
             core_mean_contrast=.18, core_weakest_decile=.09,
             core_low_contrast_fraction=.1)
        for i in range(1, 25) for j in range(1, 25)
    ]


class MatrixCompleteness(unittest.TestCase):
    def test_complete_matrix_has_no_risks(self):
        summary = module.summarize_risks(fixture(), require_complete=True)
        self.assertEqual(summary["risk_pairs"], 0)
        self.assertEqual(summary["unscorable_core_pairs"], 0)
        self.assertEqual(sum(summary["risk_count_by_ore"].values()), 0)

    def test_missing_pair_rejected(self):
        with self.assertRaisesRegex(ValueError, "Expected 576"):
            module.summarize_risks(fixture()[:-1], require_complete=True)

    def test_duplicate_pair_rejected_even_when_row_count_correct(self):
        rows = fixture()
        rows[-1] = dict(rows[0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            module.summarize_risks(rows, require_complete=True)

    def test_nonfinite_and_out_of_range_metrics_rejected(self):
        for key, value in (("score", float("nan")),
                           ("visible_coverage", float("inf")),
                           ("weakest_decile", -0.1),
                           ("core_low_contrast_fraction", 1.1),
                           ("core_mean_contrast", None)):
            with self.subTest(key=key):
                rows = fixture()
                rows[7][key] = value
                with self.assertRaises(ValueError):
                    module.summarize_risks(rows, require_complete=True)

    def test_missing_core_metrics_are_explicitly_unscorable(self):
        rows = fixture()
        rows[0].update(core_coverage=0, core_mean_contrast=None,
                       core_weakest_decile=None, core_low_contrast_fraction=None)
        summary = module.summarize_risks(rows, require_complete=True)
        self.assertEqual(summary["unscorable_core_pairs"], 1)
        self.assertEqual(summary["unscorable_core_locations"],
                         [{"biome": 1, "ore": 1}])

    def test_invalid_indices_and_boolean_indices_rejected(self):
        for invalid in (0, 25, True, "1"):
            with self.subTest(invalid=invalid):
                rows = fixture()
                rows[1]["ore"] = invalid
                with self.assertRaises(ValueError):
                    module.summarize_risks(rows, require_complete=True)

    def test_core_without_metrics_rejected(self):
        rows = fixture()
        rows[0]["core_weakest_decile"] = None
        with self.assertRaises(ValueError):
            module.summarize_risks(rows, require_complete=True)


if __name__ == "__main__":
    unittest.main()
