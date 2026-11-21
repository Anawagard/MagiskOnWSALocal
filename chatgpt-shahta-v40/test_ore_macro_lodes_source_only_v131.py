"""Ensure all 24 ore sprites gain visible, clipped mineral macro-lodes.

Runs the *actual* ore renderer in isolation; deliberately removes only the
new lode overlay in a temporary AST copy for before/after pixel comparison.
No Android sources, SDK, Gradle, workflow dispatch or APK build required.
Run: python -m unittest chatgpt-shahta-v40/test_ore_macro_lodes_source_only_v131.py
"""
import ast
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


HERE = Path(__file__).resolve().parent
GENERATOR = HERE / "generate_art_v70.py"


def load_renderers():
    try:
        import numpy as np
        import math
        from PIL import Image, ImageDraw, ImageFilter, ImageChops
    except ImportError as error:
        raise unittest.SkipTest(f"Raster dependencies unavailable: {error}")
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"), str(GENERATOR))
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef)
                 and node.name in ("field", "image_array", "ore")]
    if {f.name for f in functions} != {"field", "image_array", "ore"}:
        raise AssertionError("Missing pure ore renderer dependencies")
    ore_func = next(f for f in functions if f.name == "ore")
    backup = copy.deepcopy(ore_func)
    start = next((i for i, statement in enumerate(backup.body)
                  if isinstance(statement, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "lodes"
                          for t in statement.targets)), None)
    end = next((i for i, statement in enumerate(backup.body)
                if isinstance(statement, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "im"
                        for t in statement.targets)
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Attribute)
                and statement.value.func.attr == "alpha_composite"
                and len(statement.value.args) == 2
                and isinstance(statement.value.args[1], ast.Name)
                and statement.value.args[1].id == "lodes"), None)
    if start is None or end is None or not start < end:
        raise AssertionError("Lode overlay bounds missing or malformed")
    # Every statement introduced for the lode overlay must lie in this region;
    # preserve the original renderer's seeded randomness and all other layers.
    backup.body = backup.body[:start] + backup.body[end + 1:]
    ast.fix_missing_locations(backup)

    imports = {"np": np, "math": math, "Image": Image,
               "ImageDraw": ImageDraw, "ImageFilter": ImageFilter,
               "ImageChops": ImageChops, "R": Image.Resampling.BICUBIC}
    original = dict(imports)
    baseline = dict(imports)
    def compile_funcs(target, ore):
        nodes = [copy.deepcopy(f) if f.name != "ore" else ore for f in functions]
        module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
        exec(compile(module, str(GENERATOR), "exec"), target)
    compile_funcs(original, ore_func)
    compile_funcs(baseline, backup)
    colors = [ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign) and any(
                  isinstance(t, ast.Name) and t.id == "ORES"
                  for t in node.targets)]
    if len(colors) != 1 or len(colors[0]) != 24:
        raise AssertionError("Expected exactly 24 ore palettes")
    return original["ore"], baseline["ore"], colors[0], np, Image


class OreMacroLodeRasterTests(unittest.TestCase):
    def test_all_24_lodes_are_visible_and_keep_transparent_margins(self):
        ore, baseline, palettes, np, Image = load_renderers()
        changed_counts = []
        with TemporaryDirectory() as folder:
            before = Path(folder) / "before.png"
            after = Path(folder) / "after.png"
            for index, color in enumerate(palettes):
                with self.subTest(index=index):
                    baseline(index, color, before)
                    ore(index, color, after)
                    with Image.open(before) as a, Image.open(after) as b:
                        lhs, rhs = np.asarray(a.convert("RGBA")), np.asarray(b.convert("RGBA"))
                    self.assertEqual(lhs.shape, (300, 300, 4))
                    self.assertEqual(rhs.shape, lhs.shape)
                    # The original mask defines the silhouette; no marks may
                    # create pixels outside the transparent old bounds.
                    self.assertEqual(int(rhs[:, :, 3][lhs[:, :, 3] == 0].max()), 0)
                    for edge in (rhs[0, :, 3], rhs[-1, :, 3],
                                 rhs[:, 0, 3], rhs[:, -1, 3]):
                        self.assertEqual(int(edge.max()), 0)
                    rgb_delta = np.max(abs(lhs[:, :, :3].astype(np.int16) -
                                           rhs[:, :, :3].astype(np.int16)), axis=2)
                    changed = int(((rgb_delta >= 8) & (lhs[:, :, 3] > 200)).sum())
                    self.assertGreater(changed, 100, f"Ore {index}: invisible lodes")
                    changed_counts.append(changed)
        self.assertEqual(len(changed_counts), 24)
        # Macrostructure cannot have identical occupancy in every rock.
        self.assertGreater(len(set(changed_counts)), 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
