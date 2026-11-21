"""Dependency-free source-only checks for v7.0 raster asset contracts.

No Android build, generator execution, repository writes, or network required.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
GENERATOR = ROOT / "generate_art_v70.py"
RENDERER = ROOT / "patch_full_redesign_v70.py"

def literal_palette(tree, name):
    matches = [ast.literal_eval(n.value) for n in tree.body
               if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(matches) != 1:
        raise AssertionError(f"Expected one {name} palette")
    return matches[0]

class AssetContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = GENERATOR.read_text(encoding="utf-8")
        cls.renderer = RENDERER.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_24_distinct_valid_palettes(self):
        for name in ("SCENES", "ORES"):
            colors = literal_palette(self.tree, name)
            self.assertEqual(len(colors), 24, name)
            self.assertEqual(len(set(map(tuple, colors))), 24, name)
            for rgb in colors:
                self.assertEqual(len(rgb), 3)
                self.assertTrue(all(type(x) is int and 0 <= x <= 255 for x in rgb))

    def test_generated_names_match_android_renderer(self):
        self.assertIn('OUT/("biome_%02d.jpg"%i)', self.source)
        self.assertIn('OUT/("ore_%02d.png"%i)', self.source)
        self.assertIn('String.format(Locale.US,"biome_%02d.jpg"', self.renderer)
        self.assertIn('String.format(Locale.US,"ore_%02d.png"', self.renderer)
        for name in ("panel.png", "button.png", "button_off.png", "header.png", "nav.png"):
            self.assertIn('OUT/"' + name + '"', self.source, name)
            self.assertIn('"' + name + '"', self.renderer, name)

    def test_ore_indices_are_bounded(self):
        # Every dynamic ore lookup in the modernist renderer is explicitly bounded.
        self.assertIn('k%24', self.renderer)
        self.assertIn('Math.abs(kind)%24', self.renderer)
        # Biome index must be clamped before interpolating an asset name.
        self.assertIn('Math.max(0,Math.min(23,biome))', self.renderer)

    def test_graphite_turquoise_palette_contrast(self):
        # WCAG relative luminance math: compare active accent against dark graphite.
        def luminance(rgb):
            c = [v / 255 for v in rgb]
            c = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]
            return .2126*c[0] + .7152*c[1] + .0722*c[2]
        graphite = (17, 27, 42)
        turquoise = (93, 224, 210)
        contrast = (luminance(turquoise) + .05) / (luminance(graphite) + .05)
        self.assertGreaterEqual(contrast, 7.0)

if __name__ == "__main__":
    unittest.main()
