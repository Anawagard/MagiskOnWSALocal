"""Source-only raster checks for the five modernist UI skins.

Extract only pure functions from generate_art_v70.py: no Android baseline,
Gradle, GitHub Actions, or writes to the repository's asset directory.
"""
import ast
import hashlib
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SOURCE = Path(__file__).with_name("generate_art_v70.py")
SKINS = (
    ("panel", (23, 32, 47), (85, 125, 148), (400, 96), False),
    ("button", (21, 103, 109), (92, 227, 207), (160, 64), True),
    ("button_off", (32, 44, 58), (91, 112, 131), (160, 64), False),
    ("header", (17, 27, 42), (85, 132, 156), (360, 88), False),
    ("nav", (17, 28, 42), (90, 150, 164), (360, 50), False),
)


class ModernistSkinRasterContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import numpy as np
            from PIL import Image, ImageDraw
        except ImportError as exc:
            raise unittest.SkipTest(f"numpy/Pillow required: {exc}")
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        wanted = {"image_array", "panel_art"}
        functions = [node for node in tree.body
                     if isinstance(node, ast.FunctionDef) and node.name in wanted]
        if {node.name for node in functions} != wanted:
            raise AssertionError("Missing modernist raster functions")
        namespace = {"np": np, "math": math, "Image": Image, "ImageDraw": ImageDraw}
        exec(compile(ast.Module(body=functions, type_ignores=[]),
                     str(SOURCE), "exec"), namespace)
        cls.render = namespace["panel_art"]
        cls.Image = Image
        cls.np = np

    def test_all_five_skins_are_distinct_textured_rgba(self):
        digests = set()
        with TemporaryDirectory() as folder:
            for name, base, border, size, bright in SKINS:
                target = Path(folder) / (name + ".png")
                self.render(target, base, border, size=size, bright=bright)
                with self.Image.open(target) as im:
                    self.assertEqual(im.format, "PNG", name)
                    self.assertEqual(im.mode, "RGBA", name)
                    self.assertEqual(im.size, size, name)
                    pixels = self.np.asarray(im.convert("RGBA"))
                    self.assertEqual(int(pixels[:, :, 3].min()), 255, name)
                    # A flat replacement or broken brush texture must fail.
                    patch = pixels[20:35, 35:65, :3].astype(self.np.float32)
                    self.assertGreater(float(patch.std(axis=(0, 1)).max()), 0.2, name)
                    digests.add(hashlib.sha256(pixels.tobytes()).digest())
            self.assertEqual(len(digests), len(SKINS))

    def test_deterministic_output_and_turquoise_active_button(self):
        with TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.png", Path(folder) / "b.png"
            name, base, border, size, bright = SKINS[1]
            self.render(a, base, border, size=size, bright=bright)
            self.render(b, base, border, size=size, bright=bright)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with self.Image.open(a) as im:
                # The active-state accent rail must remain a visible turquoise.
                r, g, blue, alpha = im.getpixel((9, size[1] // 2))
                self.assertGreater(g, r + 40)
                self.assertGreater(blue, r + 30)
                self.assertEqual(alpha, 255)


if __name__ == "__main__":
    unittest.main()
