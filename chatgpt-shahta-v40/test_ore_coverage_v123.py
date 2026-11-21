"""Source-only regression for effective alpha coverage in ore sprites.

Run: python3 -m unittest discover -s chatgpt-shahta-v40 -p 'test_ore_coverage_v123.py'
No Gradle, APK, emulator or GitHub Actions.
"""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

PREVIEW = Path(__file__).with_name("preview_raster_source_only_v118.py")


class OreCoverageContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PIL import Image  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(str(exc))
        spec = importlib.util.spec_from_file_location("ore_preview", PREVIEW)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.audit = staticmethod(module.audit_ore_alpha)

    def make_ore(self, folder, visible):
        from PIL import Image
        image = Image.new("RGBA", (10, 10), (20, 180, 170, 0))
        for x in range(visible):
            image.putpixel((x % 10, x // 10), (20, 180, 170, 255))
        path = Path(folder) / "ore.png"
        image.save(path)
        return path

    def test_rejects_nearly_invisible_sprite(self):
        with TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "visible coverage"):
                self.audit([self.make_ore(folder, 1)])

    def test_rejects_sprite_without_transparent_margin(self):
        with TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "visible coverage"):
                self.audit([self.make_ore(folder, 99)])

    def test_accepts_readable_sprite_with_margin(self):
        with TemporaryDirectory() as folder:
            self.audit([self.make_ore(folder, 40)])

    def test_rejects_only_semitransparent_pixels(self):
        from PIL import Image
        with TemporaryDirectory() as folder:
            path = Path(folder) / "ore.png"
            Image.new("RGBA", (10, 10), (20, 180, 170, 127)).save(path)
            with self.assertRaisesRegex(ValueError, "alpha contract"):
                self.audit([path])


if __name__ == "__main__":
    unittest.main()
