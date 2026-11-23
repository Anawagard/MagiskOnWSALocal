"""Source-only regression for five distinct modernist navigation identities.

Checks the actual v7.9 source patch and its v7.5 predecessor; no Android SDK,
Gradle, APK generation, workflow dispatch or network requests.
"""
import ast
from pathlib import Path
import math
import re

HERE = Path(__file__).resolve().parent
V75 = (HERE / "patch_modernist_v75.py").read_text(encoding="utf-8")
V79 = (HERE / "patch_modernist_v79.py").read_text(encoding="utf-8")

def string_assignment(source, name):
    matches = [
        node.value for node in ast.parse(source).body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    assert len(matches) == 1, (name, len(matches))
    return ast.literal_eval(matches[0])

old = string_assignment(V79, "nav_old")
new = string_assignment(V79, "nav_new")
toast = string_assignment(V79, "new")
assert V75.count(old) == 1, "The v7.9 patch cannot find the v7.5 navigation"
assert V75.count('private void drawBottom(Canvas c)') == 1
assert new not in V75
assert V79.count("current.count(nav_old) != 1") == 1
assert V79.count("replace(nav_old, nav_new, 1)") == 1

# The same five opaque identities must be used by the active nav and toasts.
def palette(code, variable):
    match = re.search(r"int " + variable + r"\s*=\s*(.*?);", code, re.S)
    assert match, variable
    return re.findall(r"0xff[0-9a-fA-F]{6}", match.group(1))

nav_colors = palette(new, "tabAccent")
toast_colors = palette(toast, "toastAccent")
assert nav_colors == toast_colors
assert len(nav_colors) == len(set(nav_colors)) == 5
assert all(int(color, 16) >> 24 == 255 for color in nav_colors)

# Three active cues, no modification to tab widths, layout or touch dispatch.
rects = (
    (18, 90, 36, 2),
    (18, 132, 36, 2),
    (9, 94, 2, 12),
)
for dx, y, width, height in rects:
    marker = f"rect(c,left+{dx},{y},{width},{height},tabAccent);"
    assert new.count(marker) == 1, marker
assert new.count("if(active){") == 1
assert "onTouchEvent" not in new and "shopPage" not in new
assert "left+4,90,64,44" in V75
assert "float left=i*72f;" in V75

checks = 0
for physical_width, physical_height in (
    (176, 320), (240, 320), (320, 568), (360, 720),
    (393, 852), (1080, 2400), (1272, 2772),
):
    scale = min(physical_width / 360, physical_height / 720)
    ox = (physical_width - 360 * scale) / 2
    oy = (physical_height - 720 * scale) / 2
    for tab in range(5):
        left = tab * 72
        # Existing visible/touch rectangle for each tab is x=left+4..68.
        for dx, y, width, height in rects:
            box = (left + dx, y, left + dx + width, y + height)
            assert left + 5 <= box[0] < box[2] <= left + 69
            assert 90 <= box[1] < box[3] <= 134
            px0, py0 = ox + box[0] * scale, oy + box[1] * scale
            px1, py1 = ox + box[2] * scale, oy + box[3] * scale
            assert 0 <= px0 < px1 <= physical_width
            assert 0 <= py0 < py1 <= physical_height
            assert math.isclose((px0 - ox) / scale, box[0], abs_tol=1e-6)
            assert math.isclose((py1 - oy) / scale, box[3], abs_tol=1e-6)
            checks += 1

print(f"PASS: five unique tab accents match toasts; {checks} scaled rail checks")
