"""Source-only regression for untranslated toast overlays and shifted controls.

The page Canvas is translated down 60 logical pixels; toast is painted after
canvas.restore() in screen-space. This test checks actual screen rectangles.
No SDK, Gradle, emulator, Actions, or APK build.
"""
from pathlib import Path
import ast

root = Path(__file__).resolve().parent
v70 = (root / "patch_full_redesign_v70.py").read_text(encoding="utf-8")
v72 = (root / "patch_modernist_v72.py").read_text(encoding="utf-8")
v74 = (root / "patch_modernist_v74.py").read_text(encoding="utf-8")
v79 = (root / "patch_modernist_v79.py").read_text(encoding="utf-8")
for file in (v70, v72, v74, v79):
    ast.parse(file)
assert "canvas.translate(0,60);" in v70
assert "c.clipRect(0,145,360,653);" in v72
assert "int toastY = page==0 ? 240 : (page==1 ? 691 : 177);" in v79
assert 'v72NineSlice(canvas,"panel.png",18,toastY,324,26,252)' in v79
assert 'leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,251)' in v79
assert 'v71ShopTile(c,10+(i%2)*175,164+(i/2)*153' in v74

def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

mine = (18, 240, 342, 266)
shop = (18, 691, 342, 717)
feature = (18, 177, 342, 203)
nav = (0, 88, 360, 136)
mine_telemetry = (18, 153, 342, 236)  # 93..176 + 60
mine_ore = (105, 270, 330, 500)  # 210..440 + 60
shop_buttons = [
    (10+(i%2)*175+13, 164+(i//2)*153+102+60,
     10+(i%2)*175+152, 164+(i//2)*153+138+60)
    for i in range(6)
]
settings_close = (18, 548+60, 342, 609+60)
feature_content = (0, 205, 360, 713)
for box in (mine, shop, feature):
    assert not intersects(box, nav)
    assert 0 <= box[0] < box[2] <= 360
    assert 0 <= box[1] < box[3] <= 720
assert not intersects(mine, mine_telemetry)
assert not intersects(mine, mine_ore)
assert all(not intersects(shop, button) for button in shop_buttons)
assert not intersects(shop, settings_close)
assert shop[1] > 690  # Settings panel bottom, not just its close button.
assert not intersects(feature, feature_content)
assert feature[1] > 114 + 60  # Header title baseline.
print("PASS: five-page screen-space toast bounds clear interactive controls")
