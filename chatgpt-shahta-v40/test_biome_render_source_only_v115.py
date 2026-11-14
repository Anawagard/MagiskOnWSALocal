"""Source-only raster validation for all 24 biome backdrops.

Execute pure AST-extracted cave functions in a temporary directory. This never
imports the generator's top-level Android project setup or invokes Gradle.
"""
import ast
import hashlib
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SOURCE = Path(__file__).with_name("generate_art_v70.py")


class BiomeRasterContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import numpy as np
            from PIL import Image, ImageDraw, ImageFilter
        except ImportError as exc:
            raise unittest.SkipTest(f"numpy and Pillow required: {exc}")
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        needed = {"field", "image_array", "cave"}
        funcs = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in needed]
        if {node.name for node in funcs} != needed:
            raise AssertionError("Missing pure cave raster functions")
        scenes = [ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "SCENES"
                          for t in node.targets)]
        if len(scenes) != 1 or len(scenes[0]) != 24:
            raise AssertionError("Exactly 24 biome palettes required")
        namespace = {"np": np, "math": math, "Image": Image,
                     "ImageDraw": ImageDraw, "ImageFilter": ImageFilter,
                     "R": Image.Resampling.BICUBIC}
        exec(compile(ast.Module(body=funcs, type_ignores=[]),
                     str(SOURCE), "exec"), namespace)
        cls.cave = namespace["cave"]
        cls.scenes = scenes[0]
        cls.Image = Image
        cls.np = np

    def test_24_distinct_opaque_biomes_with_visible_texture(self):
        digests = set()
        with TemporaryDirectory() as folder:
            for index, palette in enumerate(self.scenes):
                target = Path(folder) / f"biome_{index:02d}.jpg"
                self.cave(index, palette, target)
                with self.Image.open(target) as im:
                    self.assertEqual(im.size, (360, 570), index)
                    self.assertEqual(im.format, "JPEG", index)
                    pixels = self.np.asarray(im.convert("RGB"), dtype=self.np.int16)
                    self.assertGreater(float(pixels.std()), 8.0, index)
                    # Textured pixels must vary inside a single region, not
                    # merely between differently colored flat panels.
                    patch = pixels[170:290, 110:240]
                    self.assertGreater(float(patch.std(axis=(0, 1)).max()), 5.0, index)
                    digests.add(hashlib.sha256(pixels.tobytes()).digest())
            self.assertEqual(len(digests), 24)

    def test_biome_and_menu_scene_reproducibility(self):
        with TemporaryDirectory() as folder:
            for index, color in [(0, self.scenes[0]), (23, self.scenes[23]),
                                 (31, (59, 118, 137))]:
                a = Path(folder) / "a.jpg"
                b = Path(folder) / "b.jpg"
                self.cave(index, color, a)
                self.cave(index, color, b)
                self.assertEqual(a.read_bytes(), b.read_bytes(), index)


if __name__ == "__main__":
    unittest.main()
