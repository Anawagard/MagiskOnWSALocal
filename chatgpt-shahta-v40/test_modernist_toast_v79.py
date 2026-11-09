"""Source-only layout regression for the five-page v7.9 toast overlay.

Checks that notifications avoid the shop purchase hitboxes and fit the
logical 360x720 canvas, including letterboxed narrow devices. No Gradle.
"""
from math import isclose
from pathlib import Path

patch = Path(__file__).with_name('patch_modernist_v79.py').read_text(encoding='utf-8')
assert 'int toastY = page==0 ? 178 : 623;' in patch
assert 'v72NineSlice(canvas,"panel.png",18,toastY,324,26,252)' in patch
assert 'leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,285)' in patch

buttons = [(10 + (i % 2) * 175 + 13, 164 + (i // 2) * 153 + 102,
            10 + (i % 2) * 175 + 152, 164 + (i // 2) * 153 + 138)
           for i in range(6)]
toasts = [(18, 178, 342, 204), (18, 623, 342, 649)]

def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

assert all(not overlaps(toasts[1], button) for button in buttons)
assert toasts[0][3] < 205
assert toasts[1][3] < 653

sizes = [(320, 568), (320, 640), (360, 720), (393, 852),
         (720, 1280), (1080, 2400), (1272, 2772)]
checks = 0
for width, height in sizes:
    scale = min(width / 360, height / 720)
    ox = (width - 360 * scale) / 2
    oy = (height - 720 * scale) / 2
    for box in toasts + buttons:
        screen = (box[0] * scale + ox, box[1] * scale + oy,
                  box[2] * scale + ox, box[3] * scale + oy)
        assert 0 <= screen[0] < screen[2] <= width
        assert 0 <= screen[1] < screen[3] <= height
        assert isclose((screen[0] - ox) / scale, box[0], abs_tol=1e-6)
        assert isclose((screen[3] - oy) / scale, box[3], abs_tol=1e-6)
        checks += 1
print(f'PASS: {checks} toast/purchase geometry checks across {len(sizes)} resolutions')
