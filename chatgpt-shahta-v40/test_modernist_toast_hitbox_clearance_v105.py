"""Source-only regression: contextual toast must not cover mine ore or feature buttons.

This test intentionally requires no Android SDK or APK build.
"""
from pathlib import Path
import ast

root = Path(__file__).resolve().parent
patch = (root / "patch_modernist_v79.py").read_text(encoding="utf-8")
ast.parse(patch)
assert "int toastY = page==0 ? 178 : 623;" in patch
assert 'v72NineSlice(canvas,"panel.png",18,toastY,324,26,252)' in patch
assert 'leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,285)' in patch

def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

mine_toast = (18,178,342,204)
mine_ore = (105,210,330,440)
feature_toast = (18,623,342,649)
feature_clip = (0,145,360,653)
feature_buttons = [
    (10+(i%2)*175+13,164+(i//2)*153+102,
     10+(i%2)*175+152,164+(i//2)*153+138)
    for i in range(6)
]
assert not intersects(mine_toast, mine_ore)
assert feature_clip[0] <= feature_toast[0] < feature_toast[2] <= feature_clip[2]
assert feature_clip[1] <= feature_toast[1] < feature_toast[3] <= feature_clip[3]
for i, button in enumerate(feature_buttons):
    assert not intersects(feature_toast, button), (i, button)

# Verify that the last row ends before the notification starts.
assert max(button[3] for button in feature_buttons) == 608
assert feature_toast[1] - max(button[3] for button in feature_buttons) >= 15
print("PASS: mine and feature toast placement avoids all 7 critical hitboxes")
