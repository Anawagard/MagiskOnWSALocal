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

    def test_raster_audit_runs_after_final_sprite_write(self):
        tree = source_tree()
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('audit_raster_assets(OUT)', source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        audit_lines = [node.lineno for node in calls
                       if isinstance(node.func, ast.Name)
                       and node.func.id == "audit_raster_assets"]
        self.assertEqual(len(audit_lines), 1)
        # Only top-level writes are relevant: function bodies execute earlier,
        # but their definition positions are not their runtime write order.
        final_saves = [node.lineno for statement in tree.body
                       for node in ast.walk(statement)
                       if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and isinstance(node, ast.Call)
                       and isinstance(node.func, ast.Attribute)
                       and node.func.attr == "save"]
        self.assertTrue(final_saves)
        self.assertLess(max(final_saves), audit_lines[0])

    def test_auditor_requires_every_raster_resource(self):
        auditor = SOURCE.with_name("audit_raster_assets_v710.py")
        source = auditor.read_text(encoding="utf-8")
        ast.parse(source, filename=str(auditor))
        for marker in ('range(24)', 'range(1, 5)', 'im.verify()', 'im.load()',
                       'panel.png', 'button.png', 'button_off.png',
                       'header.png', 'nav.png', 'fractures.png', 'miner.png'):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
