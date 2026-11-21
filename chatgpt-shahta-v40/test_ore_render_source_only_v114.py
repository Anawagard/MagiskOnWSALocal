"""Render-test the 24 ore sprites without importing the side-effectful asset generator.

Only the pure ore dependencies are extracted from its AST. No Android project,
Gradle invocation, GitHub workflow, or repository asset directory is touched.
"""
import ast
import hashlib
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "generate_art_v70.py"


class OreRasterRenderContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import numpy as np
            from PIL import Image, ImageDraw, ImageFilter, ImageChops
        except ImportError as exc:
            raise unittest.SkipTest(f"Raster test requires numpy and Pillow: {exc}")
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        names = {"field", "image_array", "ore"}
        funcs = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
        if {node.name for node in funcs} != names:
            raise AssertionError("Missing pure raster functions in generator")
        namespace = {"np": np, "math": math, "Image": Image,
                     "ImageDraw": ImageDraw, "ImageFilter": ImageFilter,
                     "ImageChops": ImageChops, "R": Image.Resampling.BICUBIC}
        exec(compile(ast.Module(body=funcs, type_ignores=[]),
                     str(SOURCE), "exec"), namespace)
        palettes = [ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "ORES"
                            for t in node.targets)]
        cls.ore = namespace["ore"]
        if len(palettes) != 1 or len(palettes[0]) != 24:
            raise AssertionError("Exactly 24 ore palettes required")
        cls.colors = palettes[0]
        cls.Image = Image
        cls.np = np

    def test_all_24_ores_have_unique_decoded_pixels_and_clipped_alpha(self):
        hashes = set()
        with TemporaryDirectory() as folder:
            for index, color in enumerate(self.colors):
                output = Path(folder) / f"ore_{index:02d}.png"
                self.ore(index, color, output)
                with self.Image.open(output) as loaded:
                    self.assertEqual(loaded.size, (300, 300), index)
                    self.assertEqual(loaded.mode, "RGBA", index)
                    pixels = self.np.asarray(loaded.convert("RGBA"))
                    alpha = pixels[:, :, 3]
                    self.assertEqual(int(alpha[0, 0]), 0, index)
                    self.assertEqual(int(alpha[-1, -1]), 0, index)
                    self.assertGreater(int((alpha > 200).sum()), 10000, index)
                    self.assertLess(int((alpha > 0).sum()), 70000, index)
                    # A silhouette-only or flat-color replacement must fail:
                    # the interior needs meaningful local mineral texture.
                    interior = pixels[120:180, 120:180, :3].astype(self.np.float32)
                    self.assertGreater(float(interior.std(axis=(0, 1)).max()), 4.0, index)
                    # Check transparent margins on all four sides, not just corners.
                    for edge in (alpha[0, :], alpha[-1, :],
                                 alpha[:, 0], alpha[:, -1]):
                        self.assertEqual(int(edge.max()), 0, index)
                    hashes.add(hashlib.sha256(pixels.tobytes()).digest())
            self.assertEqual(len(hashes), 24)

    def test_ore_render_is_reproducible(self):
        with TemporaryDirectory() as folder:
            a, b = Path(folder) / "first.png", Path(folder) / "second.png"
            self.ore(7, self.colors[7], a)
            self.ore(7, self.colors[7], b)
            with self.Image.open(a) as ia, self.Image.open(b) as ib:
                self.assertEqual(ia.tobytes(), ib.tobytes())


if __name__ == "__main__":
    unittest.main()
