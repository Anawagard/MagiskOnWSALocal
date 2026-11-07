"""Source-only regression tests for raster audit; never invokes Gradle or Android.

Run: python3 -m unittest chatgpt-shahta-v40/test_raster_audit_contract_v711.py
Requires Pillow. Fixtures are synthetic and must not be shipped as game art.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("raster_audit", HERE / "audit_raster_assets_v710.py")
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


def make_image(name, index):
    background = name.startswith(("biome_", "menu_"))
    if background:
        size = (360, 570)
    elif name.startswith("ore_") or name == "fractures.png":
        size = (300, 300)
    else:
        size = {
            "panel.png": (400, 96), "button.png": (160, 64),
            "button_off.png": (160, 64), "header.png": (360, 88),
            "nav.png": (360, 50), "miner.png": (240, 340),
        }[name]
    mode = "RGB" if background else "RGBA"
    im = Image.new(mode, size, (0, 0, 0) if background else (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w, h = size
    if name.startswith("ore_"):
        # Deterministic opaque core with substantial distributed colour detail.
        for y in range(45, 255):
            for x in range(45, 255):
                if ((x - 150) / 105) ** 2 + ((y - 150) / 105) ** 2 < 1:
                    v = (x * 17 + y * 31 + index * 13) % 160
                    im.putpixel((x, y), (55 + v, 35 + v, 25 + v, 255))
    elif background:
        for y in range(h):
            v = (y * 7 + index * 17) % 160
            d.line((0, y, w - 1, y), fill=(30 + v, 45 + v, 60 + v))
    else:
        d.rectangle((10, 10, w - 11, h - 11),
                    fill=(30 + index % 100, 70, 90, 255))
        # Add deterministic high-frequency texture so the >1 KiB audit gate
        # tests actual image contracts rather than rejecting tiny fixtures.
        for y in range(11, h - 11):
            for x in range(11, w - 11):
                v = (x * 19 + y * 37 + (x * y) % 127 + index * 11) % 140
                im.putpixel((x, y), (30 + v, 45 + v, 65 + v, 255))
        d.line((12, 12, w - 13, h - 13),
               fill=(200, 170, 120, 255), width=3)
    return im


def fixture(directory):
    names = ([f"biome_{i:02d}.jpg" for i in range(24)]
             + [f"ore_{i:02d}.png" for i in range(24)]
             + [f"menu_{i}.jpg" for i in range(1, 5)]
             + ["panel.png", "button.png", "button_off.png",
                "header.png", "nav.png", "fractures.png", "miner.png"])
    for i, name in enumerate(names):
        im = make_image(name, i)
        im.save(directory / name, quality=90 if name.endswith(".jpg") else None)
    return names


class RasterAuditContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="shahta-raster-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.names = fixture(self.root)

    def test_complete_valid_pack(self):
        audit_module.audit(self.root)

    def test_missing_biome_is_rejected(self):
        (self.root / "biome_23.jpg").unlink()
        with self.assertRaisesRegex(RuntimeError, "Missing raster assets"):
            audit_module.audit(self.root)

    def test_duplicate_ore_is_rejected(self):
        (self.root / "ore_23.png").write_bytes((self.root / "ore_22.png").read_bytes())
        with self.assertRaisesRegex(RuntimeError, "Duplicate raster content"):
            audit_module.audit(self.root)

    def test_hidden_rgb_does_not_disguise_duplicate_ore(self):
        # Transparent pixels can contain arbitrary invisible RGB data.
        # Android renders both sprites identically, so audit must reject them.
        source = self.root / "ore_22.png"
        target = self.root / "ore_23.png"
        with Image.open(source) as image:
            changed = image.convert("RGBA")
        changed.putpixel((0, 0), (173, 41, 229, 0))
        changed.save(target)
        with self.assertRaisesRegex(RuntimeError, "Duplicate raster content"):
            audit_module.audit(self.root)

    def test_different_alpha_masks_are_not_false_duplicates(self):
        # Both skins are pure black on a black matte, but have visibly
        # different translucency on a light background. Black-only hashes
        # incorrectly reject this legitimate pair as duplicate artwork.
        for offset, name in ((0, "button.png"), (47, "button_off.png")):
            image = Image.new("RGBA", (160, 64), (0, 0, 0, 0))
            for y in range(64):
                for x in range(160):
                    opacity = 48 + ((x * 19 + y * 37 + x * y + offset) % 160)
                    image.putpixel((x, y), (0, 0, 0, opacity))
            image.save(self.root / name)
        audit_module.audit(self.root)

    def test_flat_ore_is_rejected(self):
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((42, 42, 258, 258), fill=(110, 110, 110, 255))
        im.save(self.root / "ore_23.png")
        with self.assertRaisesRegex(RuntimeError, "texture"):
            audit_module.audit(self.root)

    def test_opaque_corner_is_rejected(self):
        path = self.root / "ore_23.png"
        with Image.open(path) as im:
            rgba = im.convert("RGBA")
        rgba.putpixel((0, 0), (40, 50, 60, 255))
        rgba.save(path)
        with self.assertRaisesRegex(RuntimeError, "nontransparent border pixel"):
            audit_module.audit(self.root)

    def test_palette_png_without_transparency_is_rejected(self):
        # Indexed PNGs are not necessarily transparent: Pillow reports mode P
        # even when the file has no tRNS transparency metadata.
        path = self.root / "panel.png"
        with Image.open(path) as im:
            indexed = im.convert("RGB").quantize(colors=64)
        indexed.save(path)
        with self.assertRaisesRegex(RuntimeError, "alpha/transparency"):
            audit_module.audit(self.root)

    def test_nearly_invisible_ui_skin_is_rejected(self):
        # Preserve valid dimensions, alpha mode and a nontrivial PNG size,
        # but make only ~1% of the button visible to catch blank exports.
        path = self.root / "button.png"
        im = Image.new("RGBA", (160, 64), (0, 0, 0, 0))
        for y in range(64):
            for x in range(160):
                if (x * 17 + y * 31) % 100 == 0:
                    im.putpixel((x, y), ((x * 13) % 256, (y * 19) % 256, 170, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "nearly invisible"):
            audit_module.audit(self.root)

    def test_wrong_panel_size_is_rejected(self):
        path = self.root / "panel.png"
        with Image.open(path) as im:
            changed = im.resize((399, 96))
        changed.save(path)
        with self.assertRaisesRegex(RuntimeError, "Incorrect UI sprite dimensions"):
            audit_module.audit(self.root)


if __name__ == "__main__":
    unittest.main()
