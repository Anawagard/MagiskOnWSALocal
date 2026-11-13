"""Source-only regression of v7.3 settings layout and exact tap regions.

Run: python3 chatgpt-shahta-v40/test_settings_hitboxes_v126.py
No Android project, Gradle, network or APK needed.
"""
from pathlib import Path
import re
import unittest

PATCH = Path(__file__).with_name("patch_modernist_v73.py").read_text(encoding="utf-8")


def extract(pattern):
    match = re.search(pattern, PATCH)
    if match is None:
        raise AssertionError(f"Missing settings geometry: {pattern}")
    return tuple(map(int, match.groups()))


class SettingsHitboxTests(unittest.TestCase):
    def test_audio_toggle_matches_painted_button(self):
        button = extract(r'button\(c,(218),(251),(105),(50),soundEnabled')
        touch = extract(r'if\(x>=(218)&&x<=(323)&&y>=(251)&&y<=(301)\)\{soundEnabled')
        x, y, w, h = button
        self.assertEqual(touch, (x, x+w, y, y+h))

    def test_effects_toggle_matches_painted_button(self):
        button = extract(r'button\(c,(218),(461),(105),(50),fxEnabled')
        touch = extract(r'if\(x>=(218)&&x<=(323)&&y>=(461)&&y<=(511)\)\{fxEnabled')
        x, y, w, h = button
        self.assertEqual(touch, (x, x+w, y, y+h))

    def test_volume_slider_is_tappable_along_full_track(self):
        x0, y0, x1, y1 = extract(r'c\.drawRoundRect\((42),(393),(318),(401),4,4,p\)')
        tx0, tx1, ty0, ty1 = extract(
            r'else if\(x>=(35)&&x<=(325)&&y>=(383)&&y<=(414)\)\{soundVolume')
        self.assertLessEqual(tx0, x0)
        self.assertGreaterEqual(tx1, x1)
        self.assertLessEqual(ty0, y0)
        self.assertGreaterEqual(ty1, y1)
        # The inverse mapping must use the same track origin and length.
        self.assertIn('(x-42f)/276f*20f', PATCH)
        for x, expected in ((42, 0), (180, 50), (318, 100)):
            volume = max(0, min(100, round((x-42)/276*20)*5))
            self.assertEqual(volume, expected)

    def test_close_button_matches_painted_button(self):
        button = extract(r'button\(c,(18),(548),(324),(61),"НАЗАД В ЛАВКУ"')
        self.assertEqual(button, (18, 548, 324, 61))
        self.assertIn('x>=18&&x<=342&&y>=548&&y<=609', PATCH)

    def test_settings_controls_are_disjoint(self):
        # Distinct painted controls cannot overlap, preventing double actions.
        regions = [(218, 251, 323, 301), (35, 383, 325, 414),
                   (218, 461, 323, 511), (18, 548, 342, 609)]
        for i, a in enumerate(regions):
            for b in regions[i+1:]:
                overlap = max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])
                self.assertFalse(overlap, (a, b))


if __name__ == "__main__":
    unittest.main()
