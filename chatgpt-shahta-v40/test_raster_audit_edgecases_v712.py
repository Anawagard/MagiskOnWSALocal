"""Additional source-only adversarial tests for raster silhouette and texture checks.

No Android SDK, Gradle, or build workflow is invoked.
Run: python3 -m unittest discover -s chatgpt-shahta-v40 -p 'test_raster_audit_edgecases_v712.py'
"""
import unittest
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw

from test_raster_audit_contract_v711 import audit_module, fixture


class RasterAuditEdgeCases(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="shahta-raster-edge-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture(self.root)

    def test_few_bright_speckles_do_not_mask_flat_stone(self):
        path = self.root / "ore_23.png"
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)
        draw.ellipse((45, 45, 255, 255), fill=(105, 110, 115, 255))
        # Less than five percent of visible pixels vary. The robust
        # percentile spread should still identify a flat placeholder.
        for y in range(90, 210, 19):
            for x in range(90, 210, 19):
                im.putpixel((x, y), (245, 240, 230, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "texture"):
            audit_module.audit(self.root)

    def test_tiny_stone_silhouette_is_rejected(self):
        path = self.root / "ore_23.png"
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        # Keep the center opaque and introduce strong interior variation.
        for y in range(125, 175):
            for x in range(125, 175):
                value = (x * 13 + y * 19) % 160
                im.putpixel((x, y), (50 + value, 40 + value, 30 + value, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "too few visible pixels"):
            audit_module.audit(self.root)

    def test_flat_ore_strip_with_enough_coverage_is_rejected(self):
        # 296x40 opaque strip covers 13.2% of the image and includes the
        # centre, so it previously passed coverage and centre checks.
        path = self.root / "ore_23.png"
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        for y in range(130, 170):
            for x in range(2, 298):
                v = (x * 13 + y * 19) % 160
                im.putpixel((x, y), (50 + v, 40 + v, 30 + v, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "too narrow or flat"):
            audit_module.audit(self.root)

    def test_ore_with_opaque_bottom_right_corner_is_rejected(self):
        path = self.root / "ore_23.png"
        with Image.open(path) as image:
            im = image.convert("RGBA")
        # Keep all normal ore texture intact, but add a stray pixel in a
        # corner that would appear as a square artifact during rendering.
        im.putpixel((299, 299), (180, 190, 200, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "nontransparent border pixel"):
            audit_module.audit(self.root)

    def test_ore_with_opaque_top_edge_pixel_is_rejected(self):
        path = self.root / "ore_23.png"
        with Image.open(path) as image:
            im = image.convert("RGBA")
        # A border defect between corners escaped the earlier corner-only
        # validation and can become a bright seam when sprites are scaled.
        im.putpixel((150, 0), (180, 190, 200, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "nontransparent border pixel"):
            audit_module.audit(self.root)

    def test_ore_alpha_fringe_one_pixel_inside_border_is_rejected(self):
        path = self.root / "ore_23.png"
        with Image.open(path) as image:
            im = image.convert("RGBA")
        # A transparent outer row alone does not protect bilinear sampling
        # against an accidentally clipped antialiased silhouette.
        im.putpixel((150, 1), (170, 190, 210, 24))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "clipped alpha fringe"):
            audit_module.audit(self.root)

    def test_disconnected_opaque_debris_is_rejected(self):
        # A noisy stone can pass coverage, bounding-box, and centre checks
        # even when a substantial portion consists of floating debris.
        path = self.root / "ore_23.png"
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        # Central body: 100x100 connected opaque pixels.
        for y in range(100, 200):
            for x in range(100, 200):
                v = (x * 13 + y * 19) % 160
                im.putpixel((x, y), (50 + v, 40 + v, 30 + v, 255))
        # Four disconnected 30x30 islands: 26.5% of all opaque pixels.
        for x0, y0 in ((35, 35), (235, 35), (35, 235), (235, 235)):
            for y in range(y0, y0 + 30):
                for x in range(x0, x0 + 30):
                    v = (x * 17 + y * 11) % 160
                    im.putpixel((x, y), (50 + v, 40 + v, 30 + v, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "disconnected opaque fragments"):
            audit_module.audit(self.root)

    def test_fully_opaque_stone_is_rejected(self):
        path = self.root / "ore_23.png"
        im = Image.new("RGBA", (300, 300))
        for y in range(300):
            for x in range(300):
                value = (x * 13 + y * 19) % 160
                im.putpixel((x, y), (50 + value, 40 + value, 30 + value, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "transparent pixels"):
            audit_module.audit(self.root)

    def test_isolated_highlights_do_not_mask_flat_biome(self):
        path = self.root / "biome_23.jpg"
        im = Image.new("RGB", (360, 570), (85, 90, 95))
        # Sparse white spots raise min/max but cover far below 5% of pixels.
        for y in range(10, 560, 14):
            for x in range(10, 350, 14):
                im.putpixel((x, y), (245, 245, 245))
        im.save(path, quality=95)
        with self.assertRaisesRegex(RuntimeError, "distributed texture"):
            audit_module.audit(self.root)

    def test_nearly_invisible_miner_is_rejected(self):
        path = self.root / "miner.png"
        im = Image.new("RGBA", (240, 340), (0, 0, 0, 0))
        # A noisy one-percent patch can easily exceed the PNG size gate.
        # It must still fail the silhouette-coverage contract.
        for y in range(48, 61):
            for x in range(48, 61):
                v = (x * 37 + y * 61 + x * y) % 200
                im.putpixel((x, y), (v, 255 - v, 90, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "Miner silhouette coverage"):
            audit_module.audit(self.root)

    def test_nearly_invisible_fracture_overlay_is_rejected(self):
        path = self.root / "fractures.png"
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        # Preserve an alpha-capable PNG and enough compressed detail to pass
        # the file-size check, but expose far less than 0.2% of the pixels.
        for y in range(10, 20):
            for x in range(10, 20):
                v = (x * 47 + y * 71) % 256
                im.putpixel((x, y), (v, 255 - v, 90, 200))
        # Invisible RGB noise must not count as a visible crack.
        for y in range(300):
            for x in range(300):
                if not (10 <= x < 20 and 10 <= y < 20):
                    v = (x * 17 + y * 23) % 256
                    im.putpixel((x, y), (v, 255 - v, 50, 0))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "Fracture overlay is nearly invisible"):
            audit_module.audit(self.root)

    def test_nearly_identical_button_states_are_rejected(self):
        # Two different PNG files may evade exact-content deduplication while
        # looking identical to players, obscuring the disabled state.
        with Image.open(self.root / "button.png") as image:
            enabled = image.convert("RGBA")
        enabled.putpixel((80, 32), (220, 230, 240, 255))
        enabled.save(self.root / "button_off.png")
        with self.assertRaisesRegex(RuntimeError, "Button states are visually indistinguishable"):
            audit_module.audit(self.root)

    def test_localized_button_badge_does_not_disguise_identical_state(self):
        # A bright badge on 12.5% of the button can raise the global mean
        # RGB delta above six, while 87.5% of the control looks unchanged.
        # The disabled state must differ across a meaningful surface area.
        enabled = Image.new("RGBA", (160, 64), (35, 45, 60, 255))
        enabled.save(self.root / "button.png")
        disabled = enabled.copy()
        for y in range(8, 56):
            for x in range(0, 20):
                disabled.putpixel((x, y), (255, 255, 255, 255))
        disabled.save(self.root / "button_off.png")
        with self.assertRaisesRegex(RuntimeError, "Button states are visually indistinguishable"):
            audit_module.audit(self.root)

    def test_button_state_difference_confined_to_left_half_is_rejected(self):
        # A bright stripe covering 25% of the full control passes global
        # average and changed-area thresholds, yet the right half gives no
        # indication that the button is disabled.
        enabled = Image.new("RGBA", (160, 64), (35, 45, 60, 255))
        enabled.save(self.root / "button.png")
        disabled = enabled.copy()
        for y in range(64):
            for x in range(40):
                disabled.putpixel((x, y), (230, 230, 230, 255))
        disabled.save(self.root / "button_off.png")
        with self.assertRaisesRegex(RuntimeError, "Button states are visually indistinguishable"):
            audit_module.audit(self.root)

    def test_button_state_difference_only_on_top_half_is_rejected(self):
        # The previous left/right check accepted this 50%-area horizontal
        # band, despite the entire lower half looking unchanged.
        enabled = Image.new("RGBA", (160, 64), (35, 45, 60, 255))
        enabled.save(self.root / "button.png")
        disabled = enabled.copy()
        for y in range(32):
            for x in range(160):
                disabled.putpixel((x, y), (230, 230, 230, 255))
        disabled.save(self.root / "button_off.png")
        with self.assertRaisesRegex(RuntimeError, "Button states are visually indistinguishable"):
            audit_module.audit(self.root)

    def test_recompressed_cave_clone_is_rejected(self):
        # A JPEG re-encode changes compressed bytes and decoded pixels,
        # but should not count as a distinct biome illustration.
        source = self.root / "biome_22.jpg"
        target = self.root / "biome_23.jpg"
        with Image.open(source) as image:
            image.convert("RGB").save(target, quality=82)
        with self.assertRaisesRegex(RuntimeError, "Near-duplicate cave backgrounds"):
            audit_module.audit(self.root)

    def test_mirrored_cave_clone_is_rejected(self):
        # A horizontal reflection changes every asymmetric pixel yet
        # reuses the same cave art rather than providing a distinct biome.
        from PIL import ImageOps
        source = self.root / "biome_22.jpg"
        target = self.root / "biome_23.jpg"
        with Image.open(source) as image:
            ImageOps.mirror(image.convert("RGB")).save(target, quality=95)
        with self.assertRaisesRegex(RuntimeError, "Near-duplicate cave backgrounds"):
            audit_module.audit(self.root)

    def test_mirrored_ore_clone_is_rejected(self):
        # A flipped ore silhouette must not count as a unique mineral,
        # even though its PNG pixels and file hash differ.
        from PIL import ImageOps
        source = self.root / "ore_22.png"
        target = self.root / "ore_23.png"
        with Image.open(source) as image:
            ImageOps.mirror(image.convert("RGBA")).save(target)
        with self.assertRaisesRegex(RuntimeError, "Near-duplicate ore sprites"):
            audit_module.audit(self.root)

    def test_reencoded_ore_clone_is_rejected(self):
        # Metadata and lossless PNG encoding can change without altering
        # visible art. The audit must catch the duplicate appearance.
        source = self.root / "ore_22.png"
        target = self.root / "ore_23.png"
        with Image.open(source) as image:
            image.convert("RGBA").save(target, compress_level=0)
        with self.assertRaisesRegex(RuntimeError, "Duplicate raster content|Near-duplicate ore sprites"):
            audit_module.audit(self.root)

    def test_vertically_flipped_cave_clone_is_rejected(self):
        from PIL import ImageOps
        with Image.open(self.root / "biome_22.jpg") as image:
            ImageOps.flip(image.convert("RGB")).save(
                self.root / "biome_23.jpg", quality=95)
        with self.assertRaisesRegex(RuntimeError, "Near-duplicate cave backgrounds"):
            audit_module.audit(self.root)

    def test_rotated_ore_clone_is_rejected(self):
        from PIL import ImageOps
        with Image.open(self.root / "ore_22.png") as image:
            ImageOps.flip(ImageOps.mirror(image.convert("RGBA"))).save(
                self.root / "ore_23.png")
        with self.assertRaisesRegex(RuntimeError, "Near-duplicate ore sprites"):
            audit_module.audit(self.root)

    def test_vertically_flipped_ore_clone_is_rejected(self):
        # Vertical reflections must be caught independently of horizontal
        # mirroring; neither creates an additional authored mineral texture.
        from PIL import ImageOps
        with Image.open(self.root / "ore_22.png") as image:
            ImageOps.flip(image.convert("RGBA")).save(
                self.root / "ore_23.png")
        with self.assertRaisesRegex(RuntimeError, "Near-duplicate ore sprites"):
            audit_module.audit(self.root)

    def test_rotated_cave_clone_is_rejected(self):
        # A 180-degree rotation preserves the background dimensions but
        # should not be accepted as a genuinely distinct biome.
        from PIL import ImageOps
        with Image.open(self.root / "biome_22.jpg") as image:
            rotated = ImageOps.flip(ImageOps.mirror(image.convert("RGB")))
            rotated.save(self.root / "biome_23.jpg", quality=95)
        with self.assertRaisesRegex(RuntimeError, "Near-duplicate cave backgrounds"):
            audit_module.audit(self.root)

    def test_wrong_miner_dimensions_are_rejected(self):
        path = self.root / "miner.png"
        with Image.open(path) as image:
            resized = image.resize((239, 340))
        resized.save(path)
        with self.assertRaisesRegex(RuntimeError, "Incorrect miner sprite dimensions"):
            audit_module.audit(self.root)

    def test_wrong_background_encoding_is_rejected(self):
        path = self.root / "biome_23.jpg"
        with Image.open(path) as image:
            decoded = image.copy()
        decoded.save(path, format="PNG")
        with self.assertRaisesRegex(RuntimeError, "Unexpected encoding"):
            audit_module.audit(self.root)


if __name__ == "__main__":
    unittest.main()
