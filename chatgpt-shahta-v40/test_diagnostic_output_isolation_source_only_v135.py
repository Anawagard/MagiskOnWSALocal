"""Source-only regression: art diagnostics cannot overwrite production rasters."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from audit_ore_biome_composites_source_only import (
    validate_diagnostic_destination, render_risk_contact_sheet,
    render_visibility_heatmap,
)


class DiagnosticIsolationTests(unittest.TestCase):
    def test_all_59_asset_names_and_nested_paths_rejected(self):
        names = (
            [f"biome_{i:02d}.jpg" for i in range(24)]
            + [f"ore_{i:02d}.png" for i in range(24)]
            + [f"menu_{i}.jpg" for i in range(1, 5)]
            + ["panel.png", "button.png", "button_off.png", "header.png",
               "nav.png", "fractures.png", "miner.png"]
        )
        self.assertEqual(len(names), 59)
        with TemporaryDirectory() as tmp:
            assets = Path(tmp) / "assets"
            assets.mkdir()
            for name in names:
                with self.subTest(name=name):
                    with self.assertRaises(ValueError):
                        validate_diagnostic_destination(assets, assets / name)
            with self.assertRaises(ValueError):
                validate_diagnostic_destination(assets, assets / "nested" / "audit.png")
            with self.assertRaises(ValueError):
                validate_diagnostic_destination(assets, assets)
            self.assertEqual(
                validate_diagnostic_destination(assets, Path(tmp) / "audit.png"),
                Path(tmp) / "audit.png",
            )

    def test_symlink_escape_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "assets"
            assets.mkdir()
            alias = root / "alias"
            try:
                alias.symlink_to(assets, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks unsupported")
            with self.assertRaises(ValueError):
                validate_diagnostic_destination(assets, alias / "panel.png")

    def test_risk_sheet_rejects_write_even_when_no_risks(self):
        with TemporaryDirectory() as tmp:
            assets = Path(tmp) / "assets"
            assets.mkdir()
            sentinel = assets / "panel.png"
            sentinel.write_bytes(b"keep")
            with self.assertRaises(ValueError):
                render_risk_contact_sheet(assets, [], sentinel)
            self.assertEqual(sentinel.read_bytes(), b"keep")

    def test_heatmap_rejects_write_before_raster_generation(self):
        with TemporaryDirectory() as tmp:
            assets = Path(tmp) / "assets"
            assets.mkdir()
            sentinel = assets / "nav.png"
            sentinel.write_bytes(b"keep")
            with self.assertRaises(ValueError):
                render_visibility_heatmap([], sentinel, assets=assets)
            self.assertEqual(sentinel.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
