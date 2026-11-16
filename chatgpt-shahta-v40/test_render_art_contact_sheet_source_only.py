"""Regression tests for the three-sheet v7 art reviewer; source-only, no APK."""
import tempfile
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
import render_art_contact_sheet as reviewer


class ReviewSheetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.assets = root / "assets"
        self.output = root / "review"
        self.assets.mkdir()
        self.output.mkdir()
        for group, names, _ in reviewer.GROUPS:
            for index, name in enumerate(names):
                color = ((index * 29 + len(group) * 17) % 256, 80, 170)
                image = Image.new("RGBA" if name.endswith(".png") else "RGB",
                                  (48, 64), color + (255,) if name.endswith(".png") else color)
                image.save(self.assets / name)

    def test_complete_pack_produces_three_valid_sheets(self):
        paths = reviewer.generate(self.assets, self.output)
        self.assertEqual({p.name for p in paths},
                         {"shahta_biomes_contact_sheet.png",
                          "shahta_ores_contact_sheet.png",
                          "shahta_interface_contact_sheet.png"})
        for path in paths:
            with Image.open(path) as image:
                image.load()
                self.assertEqual(image.mode, "RGB")
                self.assertGreater(image.width, 700)
                self.assertGreater(image.height, 300)

    def test_missing_last_resource_does_not_overwrite_existing_review(self):
        old = self.output / "shahta_biomes_contact_sheet.png"
        old.write_bytes(b"previous review")
        (self.assets / reviewer.UI[-1]).unlink()
        with self.assertRaises(FileNotFoundError):
            reviewer.generate(self.assets, self.output)
        self.assertEqual(old.read_bytes(), b"previous review")
        self.assertEqual([p.name for p in self.output.iterdir()], [old.name])

    def test_publish_failure_rolls_back_previous_generation(self):
        # Simulate the second rename failing after the first sheet was replaced.
        expected = {}
        for group, _, _ in reviewer.GROUPS:
            path = self.output / f"shahta_{group}_contact_sheet.png"
            path.write_bytes(f"old-{group}".encode())
            expected[path.name] = path.read_bytes()
        original_replace = os.replace
        calls = [0]

        def fail_second(source, target):
            calls[0] += 1
            if calls[0] == 2:
                raise OSError("simulated publication failure")
            return original_replace(source, target)

        with patch.object(reviewer.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "publication failure"):
                reviewer.generate(self.assets, self.output)
        self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()},
                         expected)

    def test_render_failure_does_not_publish_staged_sheets(self):
        original_save = Image.Image.save
        calls = [0]

        def fail_on_third(image, fp, *args, **kwargs):
            calls[0] += 1
            if calls[0] == 3:
                raise OSError("simulated final-sheet write failure")
            return original_save(image, fp, *args, **kwargs)

        with patch.object(Image.Image, "save", fail_on_third):
            with self.assertRaisesRegex(OSError, "simulated"):
                reviewer.generate(self.assets, self.output)
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
