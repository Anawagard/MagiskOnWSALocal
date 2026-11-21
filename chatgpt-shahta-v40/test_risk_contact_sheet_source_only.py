"""Source-only regression for diagnostic contact sheets; never builds Android."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

SCRIPT = Path(__file__).with_name("audit_ore_biome_composites_source_only.py")
spec = importlib.util.spec_from_file_location("ore_composites", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class RiskSheetTests(unittest.TestCase):
    def test_unscorable_core_is_not_hidden(self):
        risks = {
            "unscorable_core_locations": [{"biome": 1, "ore": 2}],
            "worst_pairs": [{"biome": 3, "ore": 4,
                             "affected_core_fraction": 0.5}],
        }
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "risk.png"
            with patch.object(audit, "summarize_risks", return_value=risks), \
                 patch.object(audit, "read_rgb",
                              return_value=Image.new("RGB", (360, 570), (0, 0, 0))), \
                 patch.object(audit, "read_ore",
                              return_value=Image.new("RGBA", (96, 96), (255, 255, 255, 128))):
                self.assertEqual(audit.render_risk_contact_sheet(folder, [], output, 2), 2)
            with Image.open(output) as sheet:
                self.assertEqual(sheet.size, (256, 156))
                # One 50%-alpha white layer over black must be ~128, not ~64.
                self.assertTrue(all(126 <= x <= 129 for x in sheet.getpixel((64, 64))))
            self.assertTrue(output.exists())

    def test_limit_and_empty_risks(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "risk.png"
            with patch.object(audit, "summarize_risks", return_value={
                "unscorable_core_locations": [], "worst_pairs": []
            }):
                self.assertEqual(audit.render_risk_contact_sheet(folder, [], output), 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
