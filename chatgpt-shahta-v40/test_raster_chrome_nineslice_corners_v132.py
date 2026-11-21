"""Pixel-level check that graphite chrome motifs survive Java nine-slicing.

Extracts only pure image_array/panel_art functions via AST. The reference
removes decoration without changing the underlying art, then compares pixels
at source resolution and after a mathematical 9-slice resize. All generated
PNGs are temporary. Never touches Android, Gradle, APK or GitHub Actions.
"""
import ast
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

GEN = Path(__file__).with_name("generate_art_v70.py")
SKINS = (
    ("panel", (400, 96), (23, 32, 47), (85, 125, 148), False),
    ("button", (160, 64), (21, 103, 109), (92, 227, 207), True),
    ("button_off", (160, 64), (32, 44, 58), (91, 112, 131), False),
    ("header", (360, 88), (17, 27, 42), (85, 132, 156), False),
    ("nav", (360, 50), (17, 28, 42), (90, 150, 164), False),
)
TARGETS = ((64, 44), (165, 145), (324, 26), (340, 49), (360, 50))


def load_renderers():
    try:
        import numpy as np
        from PIL import Image, ImageDraw
    except ImportError as exc:
        # This test is a mandatory pixel gate in the full rehearsal.
        # SkipTest would report success without examining a single PNG.
        raise RuntimeError("Required raster audit dependencies missing: numpy/Pillow") from exc
    tree = ast.parse(GEN.read_text(encoding="utf-8"), filename=str(GEN))
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in ("image_array", "panel_art")]
    if {f.name for f in funcs} != {"image_array", "panel_art"}:
        raise AssertionError("Pure renderer functions missing")
    full = next(f for f in funcs if f.name == "panel_art")
    stripped = copy.deepcopy(full)

    def assigned(statement, variable):
        return isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable
            for target in statement.targets)

    start = next((i for i, n in enumerate(stripped.body)
                  if assigned(n, "trace_rgb")), None)
    end = next((i for i, n in enumerate(stripped.body)
                if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Attribute)
                and n.value.func.attr == "save"
                and isinstance(n.value.func.value, ast.Name)
                and n.value.func.value.id == "im"), None)
    if start is None or end is None or not start < end:
        raise AssertionError("Cannot isolate fixed-corner ornament layer")
    stripped.body = stripped.body[:start] + stripped.body[end:]
    ast.fix_missing_locations(stripped)

    def compile_art(panel):
        ns = {"np": np, "Image": Image, "ImageDraw": ImageDraw}
        nodes = [copy.deepcopy(f) if f.name != "panel_art" else panel
                 for f in funcs]
        module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
        exec(compile(module, str(GEN), "exec"), ns)
        return ns["panel_art"]
    return compile_art(full), compile_art(stripped), np, Image


def nine_slice(src, size, Image):
    sw, sh = src.size
    w, h = size
    sx, sy = min(18, sw // 4), min(18, sh // 4)
    # Java draws with floating-point destination seams. A preview raster
    # must not silently collapse a fractional seam to zero or omit a slice.
    dx, dy = min(11.0, w / 3.0), min(11.0, h / 3.0)
    if not (0 < dx < w / 2 and 0 < dy < h / 2):
        raise AssertionError(f"Invalid nine-slice target: {size}")
    # Integer rasterization is only an approximation of Android Canvas:
    # round the seam locations, not the source dimensions.
    ix, iy = round(dx), round(dy)
    src_x, src_y = (0, sx, sw - sx, sw), (0, sy, sh - sy, sh)
    dst_x, dst_y = (0, ix, w - ix, w), (0, iy, h - iy, h)
    output = Image.new("RGBA", size)
    for row in range(3):
        for col in range(3):
            crop = src.crop((src_x[col], src_y[row],
                             src_x[col + 1], src_y[row + 1]))
            area = (dst_x[col + 1] - dst_x[col],
                    dst_y[row + 1] - dst_y[row])
            if min(area) <= 0:
                raise AssertionError(f"Degenerate slice {size}")
            output.paste(crop.resize(area, Image.Resampling.BILINEAR),
                         (dst_x[col], dst_y[row]))
    return output, ix, iy


class ChromeNineSliceCornerTests(unittest.TestCase):
    def test_all_technical_motifs_stay_in_fixed_corner_pixels(self):
        draw, plain, np, Image = load_renderers()
        with TemporaryDirectory() as folder:
            for name, size, base, border, bright in SKINS:
                with self.subTest(skin=name):
                    a, b = Path(folder) / "plain.png", Path(folder) / "decorated.png"
                    plain(a, base, border, size=size, bright=bright)
                    draw(b, base, border, size=size, bright=bright)
                    with Image.open(a) as src_a, Image.open(b) as src_b:
                        original, ornamented = src_a.convert("RGBA"), src_b.convert("RGBA")
                    w, h = size
                    before, after = np.asarray(original), np.asarray(ornamented)
                    diff = np.any(before != after, axis=2)
                    yy, xx = np.indices((h, w))
                    allowed = ((xx < 18) | (xx >= w - 18)) & (
                        (yy < 18) | (yy >= h - 18))
                    self.assertFalse(np.any(diff & ~allowed), name)
                    for corner in (allowed & (xx < 18) & (yy < 18),
                                   allowed & (xx >= w - 18) & (yy < 18),
                                   allowed & (xx < 18) & (yy >= h - 18),
                                   allowed & (xx >= w - 18) & (yy >= h - 18)):
                        self.assertGreater(int((diff & corner).sum()), 0, name)
                    for dest in TARGETS:
                        target_a, dx, dy = nine_slice(original, dest, Image)
                        target_b, _, _ = nine_slice(ornamented, dest, Image)
                        resized_diff = np.any(
                            np.asarray(target_a) != np.asarray(target_b), axis=2)
                        ww, hh = dest
                        Y, X = np.indices((hh, ww))
                        fixed = ((X < dx) | (X >= ww - dx)) & (
                            (Y < dy) | (Y >= hh - dy))
                        self.assertFalse(np.any(resized_diff & ~fixed),
                                         f"{name} -> {dest}")
                        self.assertGreater(int(resized_diff.sum()), 0,
                                           f"Lost ornament {name} -> {dest}")


    def test_all_five_real_raster_surfaces_keep_readable_body_text(self):
        """Sample actual rendered chrome under labels, not just palette literals.

        Covers source skins and the compact purchase-button geometry. Text
        ink is the light foreground used by the modernist UI. Sampling the
        central 50% avoids intentionally luminous focus rails and borders.
        """
        draw, _, np, Image = load_renderers()

        def luminance(rgb):
            values = [float(v) / 255.0 for v in rgb]
            linear = [v / 12.92 if v <= 0.04045
                      else ((v + 0.055) / 1.055) ** 2.4
                      for v in values]
            return sum(a * b for a, b in
                       zip(linear, (0.2126, 0.7152, 0.0722)))

        foreground = luminance((240, 255, 251))
        with TemporaryDirectory() as folder:
            for name, size, base, border, bright in SKINS:
                with self.subTest(skin=name):
                    path = Path(folder) / (name + ".png")
                    draw(path, base, border, size=size, bright=bright)
                    with Image.open(path) as im:
                        src = im.convert("RGB")
                    # Exercise every real control geometry, including the
                    # thin 26px toast, not just one large card and one tab.
                    for target in (size, *TARGETS):
                        resized = (src if target == size else
                                   nine_slice(src.convert("RGBA"), target, Image)[0]
                                   .convert("RGB"))
                        w, h = resized.size
                        # Scan every pixel in the central label-safe region.
                        # Five point samples could miss a bright local streak
                        # or a stretched gradient under Cyrillic text.
                        x0, x1 = int(w * .30), max(int(w * .30) + 1, int(w * .70))
                        y0, y1 = int(h * .35), max(int(h * .35) + 1, int(h * .65))
                        region = np.asarray(resized)[y0:y1, x0:x1, :3]
                        self.assertGreater(region.size, 0, f"{name} {target}")
                        pixels = region.astype(np.float64) / 255.0
                        linear = np.where(pixels <= .04045, pixels / 12.92,
                                          ((pixels + .055) / 1.055) ** 2.4)
                        background = (linear[..., 0] * .2126 +
                                      linear[..., 1] * .7152 +
                                      linear[..., 2] * .0722)
                        # Foreground is deliberately lighter than every
                        # background sample; reject violations rather than
                        # accidentally inverting the contrast formula.
                        self.assertLess(float(background.max()), foreground,
                                        f"{name} {target}: inverted text palette")
                        worst_contrast = (foreground + .05) / (
                            float(background.max()) + .05)
                        self.assertGreaterEqual(
                            worst_contrast, 4.5,
                            f"{name} {target}: worst text contrast "
                            f"{worst_contrast:.2f} at centre region")


if __name__ == "__main__":
    unittest.main(verbosity=2)
