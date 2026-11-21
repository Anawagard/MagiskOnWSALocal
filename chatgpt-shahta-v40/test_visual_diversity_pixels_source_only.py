"""Pixel-level regression checks for audit_visual_diversity.py; no Android build.

Run from chatgpt-shahta-v40: python -m unittest test_visual_diversity_pixels_source_only.py
Requires the same NumPy/Pillow dependencies as the artwork generator.
"""
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from audit_visual_diversity import BIOMES, ORES, audit, inspect


class VisualDiversityPixelTests(unittest.TestCase):
    def test_hidden_rgb_does_not_change_visible_ore_fingerprint(self):
        with tempfile.TemporaryDirectory() as temp:
            base = np.zeros((300, 300, 4), dtype=np.uint8)
            yy, xx = np.indices((300, 300))
            mask = (xx - 150) ** 2 + (yy - 150) ** 2 < 90 ** 2
            base[mask, :3] = np.stack((xx[mask] * 2, yy[mask] * 2, 180 + xx[mask] // 4), axis=1)
            base[mask, 3] = 255
            other = base.copy()
            other[~mask, :3] = [245, 80, 15]
            first, second = Path(temp) / 'a.png', Path(temp) / 'b.png'
            Image.fromarray(base, 'RGBA').save(first)
            Image.fromarray(other, 'RGBA').save(second)
            _, thumb_a = inspect(first, True)
            _, thumb_b = inspect(second, True)
            self.assertLess(float(np.mean(np.abs(thumb_a - thumb_b))), 1.5)

    def test_wrong_dimensions_are_rejected_before_pixel_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'ore_bad.png'
            Image.new('RGBA', (360, 570), (100, 150, 190, 255)).save(path)
            with self.assertRaisesRegex(ValueError, 'expected 300x300 raster'):
                inspect(path, True)
            path = Path(temp) / 'biome_bad.jpg'
            Image.new('RGB', (300, 300), (50, 70, 90)).save(path)
            with self.assertRaisesRegex(ValueError, 'expected 360x570 raster'):
                inspect(path, False)

    def test_duplicate_ore_is_rejected_even_with_different_hidden_rgb(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            yy, xx = np.indices((300, 300))
            for i, name in enumerate(BIOMES):
                rgb = np.stack(((xx + i * 11) % 256, (yy * 2 + i * 7) % 256,
                                (xx + yy + i * 13) % 256), axis=2).astype(np.uint8)
                Image.fromarray(rgb, 'RGB').resize((360, 570)).save(folder / name, quality=95)
            for i, name in enumerate(ORES):
                rgba = np.zeros((300, 300, 4), dtype=np.uint8)
                mask = (xx - 150) ** 2 + (yy - 150) ** 2 < 90 ** 2
                rgba[mask, :3] = np.stack(((xx[mask] * 2 + i * 9) % 256,
                                            (yy[mask] * 2 + i * 13) % 256,
                                            (xx[mask] + yy[mask] + i * 17) % 256), axis=1)
                rgba[mask, 3] = 255
                if i == 1:
                    rgba = np.asarray(Image.open(folder / ORES[0]).convert('RGBA')).copy()
                    rgba[~mask, :3] = [255, 0, 255]
                Image.fromarray(rgba, 'RGBA').save(folder / name)
            with self.assertRaisesRegex(ValueError, 'visually duplicated ore_00.png / ore_01.png'):
                audit(folder)


if __name__ == '__main__':
    unittest.main()
