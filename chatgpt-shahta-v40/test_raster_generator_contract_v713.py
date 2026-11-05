"""Source-only contract for deterministic 24-biome / 24-ore raster generation.

Does not import generate_art_v70: importing it would write image assets.
No Android SDK, Gradle or GitHub Actions is used.
Run: python3 -m unittest discover -s chatgpt-shahta-v40 -p 'test_raster_generator_contract_v713.py'
"""
import ast
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "generate_art_v70.py"


def assignments(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = node.value
    return result


class RasterGeneratorContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(SOURCE))
        cls.values = assignments(cls.tree)

    def test_exactly_24_distinct_biome_and_ore_palettes(self):
        for name in ("SCENES", "ORES"):
            palette = ast.literal_eval(self.values[name])
            self.assertEqual(len(palette), 24, name)
            self.assertEqual(len(set(palette)), 24, name)
            for rgb in palette:
                self.assertEqual(len(rgb), 3)
                self.assertTrue(all(isinstance(c, int) and 0 <= c <= 255 for c in rgb))

    def test_no_unseeded_random_generator(self):
        # A random generator with no seed breaks reproducibility of the art.
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "default_rng":
                    self.assertEqual(len(node.args), 1, "Unseeded default_rng()")

    def test_generator_runs_decoded_asset_audit(self):
        self.assertIn("from audit_raster_assets_v710 import audit", self.source)
        self.assertIn("audit_raster_assets(OUT)", self.source)

    def test_no_android_build_or_workflow_side_effects(self):
        forbidden = ("subprocess", "os.system", "gradlew", "workflow_dispatch",
                     "requests.post", "urllib.request")
        for token in forbidden:
            self.assertNotIn(token, self.source, token)


if __name__ == "__main__":
    unittest.main()
