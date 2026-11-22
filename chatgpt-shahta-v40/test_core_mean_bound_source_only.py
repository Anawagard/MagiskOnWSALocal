"""Source-only mathematical consistency checks for opaque ore contrast metrics."""
import tempfile
import unittest
from pathlib import Path

from audit_ore_biome_composites_source_only import (
    render_visibility_heatmap, summarize_risks,
)


def rows():
    return [
        {"biome": b, "ore": o, "score": 0.2,
         "visible_coverage": 0.6, "weakest_decile": 0.1,
         "core_coverage": 0.4, "core_mean_contrast": 0.2,
         "core_weakest_decile": 0.1, "core_low_contrast_fraction": 0.0}
        for b in range(1, 25) for o in range(1, 25)
    ]


class CoreMeanBoundTests(unittest.TestCase):
    def test_impossible_mean_rejected_and_previous_report_preserved(self):
        data = rows()
        data[0]["core_low_contrast_fraction"] = 0.9
        data[0]["core_mean_contrast"] = 0.9
        with self.assertRaisesRegex(ValueError, "Inconsistent core contrast mean"):
            summarize_risks(data, require_complete=True)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "heatmap.png"
            output.write_bytes(b"previous report")
            with self.assertRaisesRegex(ValueError, "Inconsistent core contrast mean"):
                render_visibility_heatmap(data, output)
            self.assertEqual(output.read_bytes(), b"previous report")

    def test_impossible_low_mean_rejected_and_previous_report_preserved(self):
        data = rows()
        # 90% of opaque pixels have contrast >= 0.08; their mean alone
        # contributes at least 0.072, even if all remaining pixels are zero.
        data[0]["core_low_contrast_fraction"] = 0.1
        data[0]["core_mean_contrast"] = 0.01
        with self.assertRaisesRegex(ValueError, "Inconsistent core contrast mean"):
            summarize_risks(data, require_complete=True)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "heatmap.png"
            output.write_bytes(b"previous report")
            with self.assertRaisesRegex(ValueError, "Inconsistent core contrast mean"):
                render_visibility_heatmap(data, output)
            self.assertEqual(output.read_bytes(), b"previous report")

    def test_feasible_lower_bound_accepted(self):
        data = rows()
        data[0]["core_low_contrast_fraction"] = 0.1
        data[0]["core_mean_contrast"] = 0.072
        result = summarize_risks(data, require_complete=True)
        self.assertEqual(result["risk_pairs"], 0)

    def test_feasible_upper_bound_accepted(self):
        data = rows()
        data[0]["core_low_contrast_fraction"] = 0.5
        data[0]["core_mean_contrast"] = 0.54
        result = summarize_risks(data, require_complete=True)
        self.assertEqual(result["risk_pairs"], 1)


if __name__ == "__main__":
    unittest.main()
