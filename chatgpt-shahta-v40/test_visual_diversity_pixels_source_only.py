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
            base = np.zeros((128, 128, 4), dtype=np.uint8)
            yy, xx = np.indices((128, 128))
            mask = (xx - 64) ** 2 + (yy - 64) ** 2 < 40 ** 2
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

    def test_duplicate_ore_is_rejected_even_with_different_hidden_rgb(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            yy, xx = np.indices((128, 128))
            for i, name in enumerate(BIOMES):
                rgb = np.stack(((xx + i * 11) % 256, (yy * 2 + i * 7) % 256,
                                (xx + yy + i * 13) % 256), axis=2).astype(np.uint8)
                Image.fromarray(rgb, 'RGB').save(folder / name, quality=95)
            for i, name in enumerate(ORES):
                rgba = np.zeros((128, 128, 4), dtype=np.uint8)
                mask = (xx - 64) ** 2 + (yy - 64) ** 2 < 40 ** 2
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
