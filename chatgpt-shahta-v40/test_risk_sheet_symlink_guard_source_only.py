"""Regression: a contact-sheet path must never overwrite an aliased source asset.

Source-only: no Android build, Gradle, emulator or GitHub Actions.
"""
import tempfile
import unittest
from pathlib import Path

from audit_ore_biome_composites_source_only import render_risk_contact_sheet


class RiskSheetSymlinkGuardTests(unittest.TestCase):
    def test_direct_asset_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "overwrite a source texture"):
                render_risk_contact_sheet(root, [], root / "ore_00.png")

    def test_symlinked_source_texture_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "actual-ore.png"
            target.write_bytes(b"original-art")
            (root / "ore_00.png").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "overwrite a source texture"):
                render_risk_contact_sheet(root, [], target)
            self.assertEqual(target.read_bytes(), b"original-art")

    def test_symlinked_output_alias_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "ore_00.png"
            target.write_bytes(b"original-art")
            alias = root / "sheet.png"
            alias.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "overwrite a source texture"):
                render_risk_contact_sheet(root, [], alias)
            self.assertEqual(target.read_bytes(), b"original-art")


if __name__ == "__main__":
    unittest.main()
