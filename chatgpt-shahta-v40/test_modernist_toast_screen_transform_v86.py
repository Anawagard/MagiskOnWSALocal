"""Source-only regression: toast clearance under viewport and page offsets.

No Android SDK, Gradle or APK. Extract coordinates from the v7.8 patch
rather than copying the layout constants into the test.
"""
from pathlib import Path
import ast
import re

patch = Path(__file__).with_name("patch_modernist_v78.py").read_text(encoding="utf-8")
ast.parse(patch)
replacement = re.search(r"new = '''(.*?)'''", patch, re.S)
assert replacement, "toast replacement missing"
body = replacement.group(1)
box = re.search(r'v72NineSlice\(canvas,"panel.png",(\d+),(\d+),(\d+),(\d+),', body)
assert box, "toast panel missing"
x, y, w, h = map(int, box.groups())
assert x >= 0 and x + w <= 360 and y >= 0 and y + h <= 720

# Navigation is fixed at y=88..136; feature-page content may be offset +60.
nav_bottom = 136
telemetry_bottom = 176
ore_top = 210
checks = 0
for shift in (0, 60):
    top, bottom = y + shift, y + h + shift
    assert top > nav_bottom, ("nav overlap", shift)
    assert top >= telemetry_bottom + shift + 2, ("telemetry overlap", shift)
    assert bottom <= ore_top + shift - 6, ("ore overlap", shift)
    for width, height in ((320, 568), (360, 720), (393, 852),
                          (720, 1280), (1080, 2400), (1272, 2772)):
        scale = min(width / 360, height / 720)
        offset_y = (height - 720 * scale) / 2
        physical_bottom = offset_y + bottom * scale
        physical_ore_top = offset_y + (ore_top + shift) * scale
        assert physical_ore_top - physical_bottom >= 6 * scale - 1e-7
        checks += 1
print(f"PASS: toast clearance on {checks} viewport/offset combinations")
