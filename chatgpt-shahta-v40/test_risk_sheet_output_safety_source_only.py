"""Source-only guards: a risk-sheet path must not clobber game textures."""
import tempfile
import unittest
from pathlib import Path

from audit_ore_biome_composites_source_only import render_risk_contact_sheet


class RiskSheetOutputSafety(unittest.TestCase):
    def test_protects_every_biome_and_ore_even_if_not_yet_created(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for i in range(24):
                for filename in (f"biome_{i:02d}.jpg", f"ore_{i:02d}.png"):
                    with self.subTest(filename=filename):
                        with self.assertRaisesRegex(ValueError, "overwrite a source texture"):
                            render_risk_contact_sheet(root, [], root / filename)

    def test_rejects_invalid_limit_before_touching_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for limit in (0, -1, 577):
                with self.subTest(limit=limit):
                    with self.assertRaisesRegex(ValueError, "limit"):
                        render_risk_contact_sheet(root, [], root / "audit.png", limit=limit)

    def test_allows_non_asset_output_and_no_risks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / "audit.png"
            self.assertEqual(render_risk_contact_sheet(root, [], output), 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
