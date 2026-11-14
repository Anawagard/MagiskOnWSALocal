"""Source-only viewport regression for v7.9 toast overlays on all five pages.

Uses the Java placement expression from the patch, rather than a second
hard-coded table. No Android build or external dependencies.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
patch = (ROOT / "patch_modernist_v79.py").read_text(encoding="utf-8")
match = re.search(
    r"int toastY = page==0 \\? (\\d+) : \\(page==1 \\? (\\d+) : (\\d+)\\);",
    patch,
)
if not match:
    raise RuntimeError("Missing v7.9 Java toast placement expression")
mine, shop, feature = map(int, match.groups())
tops = (mine, shop, feature, feature, feature)
assert tops == (178, 655, 145, 145, 145)

W, H = 360, 720
viewports = ((240, 320), (280, 560), (320, 568), (360, 720),
             (393, 873), (720, 1280), (1080, 2400), (1272, 2772))
checks = 0
for width, height in viewports:
    scale = min(width / W, height / H)
    ox = (width - W * scale) / 2
    oy = (height - H * scale) / 2
    assert scale > 0 and ox >= -1e-9 and oy >= -1e-9
    for page, top in enumerate(tops):
        left, right = 18, 342
        bottom = top + 26
        # Rendered toast stays within the logical screen and away from nav.
        assert 0 <= left < right <= W and 137 < top < bottom <= 682
        assert (bottom < 210 if page == 0 else
                top > 653 if page == 1 else bottom < 205)
        # Physical pixel corners map back to the same logical rectangle.
        for x, y in ((left, top), (right, top), (left, bottom),
                     (right, bottom), ((left + right) / 2, (top + bottom) / 2)):
            px, py = ox + x * scale, oy + y * scale
            assert -1e-8 <= px <= width + 1e-8
            assert -1e-8 <= py <= height + 1e-8
            assert abs((px - ox) / scale - x) < 1e-8
            assert abs((py - oy) / scale - y) < 1e-8
            checks += 1
print(f"PASS: {checks} five-page toast viewport checks across {len(viewports)} sizes; source-only")
