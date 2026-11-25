"""Source-only cross-check of raster producer and Android consumer contracts.

No Android build, emulator, Pillow, or APK is required.
Run: python -m unittest test_raster_consumer_contract_source_only.py
"""
import ast
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
GENERATOR = HERE / "generate_art_v70.py"
CONSUMER = HERE / "patch_full_redesign_v70.py"
AUDITOR = HERE / "audit_raster_assets_v710.py"


class RasterConsumerContract(unittest.TestCase):
    def test_all_sources_parse_without_executing(self):
        for path in (GENERATOR, CONSUMER, AUDITOR):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_java_asset_names_are_generated(self):
        producer = GENERATOR.read_text(encoding="utf-8")
        consumer = CONSUMER.read_text(encoding="utf-8")
        expected = {
            *(f"biome_{i:02d}.jpg" for i in range(24)),
            *(f"ore_{i:02d}.png" for i in range(24)),
            *(f"menu_{i}.jpg" for i in range(1, 5)),
            "panel.png", "button.png", "button_off.png",
            "header.png", "nav.png", "fractures.png", "miner.png",
        }
        self.assertEqual(len(expected), 59)
        for marker in ('OUT/("biome_%02d.jpg"%i)', 'OUT/("ore_%02d.png"%i)',
                       'OUT/("menu_%d.jpg"%j)'):
            self.assertIn(marker, producer)
        for name in expected:
            if name.startswith(("biome_", "ore_", "menu_")):
                continue
            self.assertIn('OUT/"' + name + '"', producer)
        self.assertIn('"shahta_v70/"+name', consumer)
        self.assertIn('"biome_%02d.jpg"', consumer)
        self.assertIn('"menu_"+tab+".jpg"', consumer)
        self.assertIn('"ore_03.png"', consumer)
        self.assertIn('"ore_07.png"', consumer)
        self.assertIn('v70Draw(c,"nav.png"', consumer)
        self.assertIn('v70Draw(c,"header.png"', consumer)

    def test_dynamic_navigation_ore_icons_exist(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        match = re.search(r'V70_ICONS\s*=\s*\{([^}]+)\}', consumer)
        self.assertIsNotNone(match, "Navigation icon list is missing")
        icons = re.findall(r'"([^"]+)"', match.group(1))
        self.assertEqual(len(icons), 5)
        self.assertEqual(len(set(icons)), 5)
        self.assertTrue(all(re.fullmatch(r'ore_(\d\d)\.png', x) for x in icons))
        self.assertTrue(all(0 <= int(x[4:6]) < 24 for x in icons))

    def test_auditor_covers_all_produced_families(self):
        audit = AUDITOR.read_text(encoding="utf-8")
        for marker in ('range(24)', 'range(1, 5)', '"panel.png"',
                       '"button_off.png"', '"fractures.png"', '"miner.png"'):
            self.assertIn(marker, audit)


if __name__ == "__main__":
    unittest.main()
