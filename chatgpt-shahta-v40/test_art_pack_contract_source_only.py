"""Source-only contract checks for the complete v7 raster resource pack.

Parses the generator without importing NumPy/Pillow or generating APKs.
Run: python -m unittest test_art_pack_contract_source_only.py
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).with_name("generate_art_v70.py")


def source_tree():
    return ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))


def palette(tree, name):
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in statement.targets
        ):
            return ast.literal_eval(statement.value)
    raise AssertionError(f"Missing palette: {name}")


class ArtPackContract(unittest.TestCase):
    def test_all_biomes_and_ores_have_distinct_valid_palettes(self):
        tree = source_tree()
        for name in ("SCENES", "ORES"):
            colors = palette(tree, name)
            self.assertEqual(len(colors), 24, name)
            self.assertEqual(len(set(map(tuple, colors))), 24, name)
            for rgb in colors:
                self.assertEqual(len(rgb), 3)
                self.assertTrue(all(isinstance(c, int) and 0 <= c <= 255 for c in rgb))

    def test_expected_output_names_and_formats(self):
        source = SOURCE.read_text(encoding="utf-8")
        for expression in (
            'OUT/("biome_%02d.jpg"%i)',
            'OUT/("ore_%02d.png"%i)',
            'OUT/("menu_%d.jpg"%j)',
            'OUT/"panel.png"',
            'OUT/"button.png"',
            'OUT/"button_off.png"',
            'OUT/"header.png"',
            'OUT/"nav.png"',
            'OUT/"fractures.png"',
            'OUT/"miner.png"',
        ):
            self.assertIn(expression, source)

    def test_resource_generation_remains_standalone(self):
        tree = source_tree()
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name.startswith(("gradle", "subprocess", "requests")) for name in imports))
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('SHAHTA_ART_PREVIEW_DIR', source)
        self.assertIn('audit_raster_assets(OUT)', source)
        self.assertIn('generate_miner_sprite().save(OUT/"miner.png"', source)


if __name__ == "__main__":
    unittest.main()
