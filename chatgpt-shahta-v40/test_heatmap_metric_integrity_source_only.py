"""Source-only regression: heatmap must reject inconsistent 576-row metrics.

No Android build or raster generation is performed.
"""
import tempfile
import unittest
from pathlib import Path

from audit_ore_biome_composites_source_only import render_visibility_heatmap


def valid_rows():
    return [
        {"biome": biome, "ore": ore, "score": 0.2,
         "visible_coverage": 0.6, "weakest_decile": 0.1,
         "core_coverage": 0.4, "core_mean_contrast": 0.2,
         "core_weakest_decile": 0.1, "core_low_contrast_fraction": 0.0}
        for biome in range(1, 25) for ore in range(1, 25)
    ]


class HeatmapMetricIntegrityTests(unittest.TestCase):
    def test_valid_complete_matrix_publishes(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "heatmap.png"
            render_visibility_heatmap(valid_rows(), output)
            self.assertTrue(output.is_file())
            self.assertEqual(output.read_bytes()[:8], bytes.fromhex("89504e470d0a1a0a"))

    def test_opaque_core_cannot_exceed_visible_coverage(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "heatmap.png"
            output.write_bytes(b"previous diagnostic")
            rows = valid_rows()
            rows[0]["visible_coverage"] = 0.2
            rows[0]["core_coverage"] = 0.4
            with self.assertRaisesRegex(ValueError, "Opaque core exceeds"):
                render_visibility_heatmap(rows, output)
            self.assertEqual(output.read_bytes(), b"previous diagnostic")

    def test_core_contribution_cannot_exceed_overall_mean(self):
        # Core is 40% of the entire image and 2/3 of visible pixels.
        # A core mean of 0.2 forces overall visible mean >= 0.13333.
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "heatmap.png"
            output.write_bytes(b"previous heatmap")
            rows = valid_rows()
            rows[0]["score"] = 0.05
            with self.assertRaisesRegex(ValueError, "Inconsistent overall/core contrast"):
                render_visibility_heatmap(rows, output)
            self.assertEqual(output.read_bytes(), b"previous heatmap")

    def test_invalid_metrics_fail_without_overwriting_existing_image(self):
        invalid = [
            ("score", float("nan")),
            ("visible_coverage", -0.1),
            ("weakest_decile", 1.1),
            ("core_coverage", 0.0),
            ("core_mean_contrast", None),
            ("core_weakest_decile", True),
            ("core_low_contrast_fraction", None),
        ]
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "heatmap.png"
            output.write_bytes(b"existing report")
            for field, value in invalid:
                with self.subTest(field=field, value=value):
                    rows = valid_rows()
                    rows[0][field] = value
                    with self.assertRaises(ValueError):
                        render_visibility_heatmap(rows, output)
                    self.assertEqual(output.read_bytes(), b"existing report")


if __name__ == "__main__":
    unittest.main()
