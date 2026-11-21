"""Screen-space notification regression for all five Shahta pages.

This test reads the generated Java replacement in the v7.9 source patch.
It models the actual +60 logical-pixel page translation, including the
untranslated notification overlay. Python only: never builds an APK.
"""
from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parent
v70 = (ROOT / "patch_full_redesign_v70.py").read_text(encoding="utf-8")
v71 = (ROOT / "patch_modernist_v71.py").read_text(encoding="utf-8")
v72 = (ROOT / "patch_modernist_v72.py").read_text(encoding="utf-8")
v73 = (ROOT / "patch_modernist_v73.py").read_text(encoding="utf-8")
v74 = (ROOT / "patch_modernist_v74.py").read_text(encoding="utf-8")
v77 = (ROOT / "patch_modernist_v77.py").read_text(encoding="utf-8")
v79 = (ROOT / "patch_modernist_v79.py").read_text(encoding="utf-8")
for name, source in (("v70", v70), ("v71", v71), ("v72", v72),
                     ("v73", v73), ("v74", v74), ("v77", v77), ("v79", v79)):
    ast.parse(source, filename=name)

# Authoritative screen-space transform: page art moves down 60; toast does not.
assert "canvas.translate(0,60);" in v70
assert "canvas.clipRect(0,87,360,653);" in v70
assert "canvas.translate(v71OffsetX(),v71OffsetY());" in v71
assert "c.clipRect(0,145,360,653);" in v72
assert 'v72NineSlice(c,"panel.png",10,94,340,49,255);' in (
    ROOT / "patch_modernist_v76.py").read_text(encoding="utf-8")
assert 'v72NineSlice(c,"panel.png",18,93,324,83,255);' in v77
assert 'v71ShopTile(c,10+(i%2)*175,164+(i/2)*153' in v74
assert 'v72NineSlice(c,"panel.png",14,153,332,477,255);' in v73
match = re.search(
    r"int toastY = page==0 \\? (\\d+) : \\(page==1 \\? (\\d+) : (\\d+)\\);",
    v79,
)
assert match, "Missing final Java toast placement"
mine, shop, feature = map(int, match.groups())
assert (mine, shop, feature) == (240, 691, 177)
assert 'v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);' in v79

PAGE_SHIFT = 60
MINE_TELEMETRY_BOTTOM = 176 + PAGE_SHIFT
MINE_ORE_TOP = 210 + PAGE_SHIFT
SHOP_CARD_BOTTOM = (164 + 2 * 153 + 145) + PAGE_SHIFT
SETTINGS_PANEL_BOTTOM = (153 + 477) + PAGE_SHIFT
FEATURE_TITLE_BASELINE = 114 + PAGE_SHIFT
FEATURE_CONTENT_TOP = 145 + PAGE_SHIFT
TOPS = (mine, shop, feature, feature, feature)
assert MINE_TELEMETRY_BOTTOM + 4 <= mine
assert mine + 26 <= MINE_ORE_TOP - 4
assert shop > SHOP_CARD_BOTTOM + 8
assert shop > SETTINGS_PANEL_BOTTOM
assert shop + 26 <= 720
assert feature > FEATURE_TITLE_BASELINE
assert feature + 26 <= FEATURE_CONTENT_TOP - 2

W, H = 360, 720
viewports = ((176, 320), (240, 320), (280, 560), (320, 568), (360, 720),
             (393, 873), (720, 1280), (1080, 2400), (1272, 2772),
             (2560, 720), (720, 2560))
checks = 0
for width, height in viewports:
    scale = min(width / W, height / H)
    ox = (width - W * scale) / 2
    oy = (height - H * scale) / 2
    assert scale > 0 and ox >= -1e-9 and oy >= -1e-9
    for page, top in enumerate(TOPS):
        left, right, bottom = 18, 342, top + 26
        assert 0 <= left < right <= W and 136 < top < bottom <= H
        if page == 0:
            assert MINE_TELEMETRY_BOTTOM < top and bottom < MINE_ORE_TOP
        elif page == 1:
            assert top > SETTINGS_PANEL_BOTTOM and top > SHOP_CARD_BOTTOM
        else:
            assert FEATURE_TITLE_BASELINE < top and bottom < FEATURE_CONTENT_TOP
        for x, y in ((left, top), (right, top), (left, bottom),
                     (right, bottom), ((left + right) / 2, (top + bottom) / 2)):
            px, py = ox + x * scale, oy + y * scale
            assert -1e-8 <= px <= width + 1e-8
            assert -1e-8 <= py <= height + 1e-8
            assert abs((px - ox) / scale - x) < 1e-8
            assert abs((py - oy) / scale - y) < 1e-8
            checks += 1

print(f"PASS: {checks} final toast/viewport checks across {len(viewports)} sizes; no APK")
