"""Source-only layout regression for the five-page v7.9 toast overlay.

Checks that notifications avoid the shop purchase hitboxes and fit the
logical 360x720 canvas, including letterboxed narrow devices. No Gradle.
"""
from math import isclose
from pathlib import Path

patch = Path(__file__).with_name('patch_modernist_v79.py').read_text(encoding='utf-8')
assert 'int toastY = page==0 ? 178 : (page==1 ? 623 : 655);' in patch
assert 'v72NineSlice(canvas,"panel.png",18,toastY,324,26,252)' in patch
assert 'leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,285)' in patch
assert 'rect(canvas,26,toastY+4,3,18,0xff65e1d0)' in patch
assert 'rect(canvas,36,toastY+22,296,1,0xff315d60)' in patch
# Rail and baseline must stay inside the toast panel at both anchors.
for toast_y in (178, 623, 655):
    assert toast_y <= toast_y+4 < toast_y+22 <= toast_y+26
    assert 18 <= 26 and 26+3 <= 342
    assert 18 <= 36 and 36+296 <= 342

buttons = [(10 + (i % 2) * 175 + 13, 164 + (i // 2) * 153 + 102,
            10 + (i % 2) * 175 + 152, 164 + (i // 2) * 153 + 138)
           for i in range(6)]
toasts = [(18, 178, 342, 204), (18, 623, 342, 649),
          (18, 655, 342, 681)]

def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

assert all(not overlaps(toasts[1], button) for button in buttons)
assert toasts[0][3] < 205
assert toasts[1][3] < 653
assert toasts[2][1] > 18 + .94 * 653  # feature page content ends here
assert toasts[2][3] <= 720

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

# A screen-space tap must round-trip to the same logical hitbox after
# letterboxing. This guards against invisible shifted purchase controls.
for width, height in sizes:
    scale = min(width / 360, height / 720)
    ox = (width - 360 * scale) / 2
    oy = (height - 720 * scale) / 2
    for left, top, right, bottom in buttons:
        for x, y in ((left, top), (right, bottom),
                     ((left + right) / 2, (top + bottom) / 2)):
            sx, sy = ox + x * scale, oy + y * scale
            lx, ly = (sx - ox) / scale, (sy - oy) / scale
            assert isclose(lx, x, abs_tol=1e-6)
            assert isclose(ly, y, abs_tol=1e-6)
            assert left - 1e-6 <= lx <= right + 1e-6
            assert top - 1e-6 <= ly <= bottom + 1e-6
    # The toast on feature pages must never visually cover purchase controls.
    toast_screen = tuple((v * scale + (ox if i % 2 == 0 else oy))
                         for i, v in enumerate(toasts[1]))
    for box in buttons:
        button_screen = tuple((v * scale + (ox if i % 2 == 0 else oy))
                              for i, v in enumerate(box))
        assert not overlaps(toast_screen, button_screen)
print('PASS: 126 purchase-hitbox round trips and 42 toast exclusions')

# Verify tap classification, not only coordinate round-tripping. The
# letterbox transform must reject the one-pixel exterior of each button.
# Test actual integer screen-pixel centres to catch rounding near edges.
def in_button(x, y, box):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]

pixel_checks = 0
for width, height in sizes:
    scale = min(width / 360, height / 720)
    ox = (width - 360 * scale) / 2
    oy = (height - 720 * scale) / 2
    for button in buttons:
        l, t, r, b = button
        samples = [(l-1, (t+b)/2), (r+1, (t+b)/2),
                   ((l+r)/2, t-1), ((l+r)/2, b+1),
                   ((l+r)/2, (t+b)/2)]
        for lx, ly in samples:
            sx, sy = ox + lx*scale, oy + ly*scale
            recovered_x = (sx-ox)/scale
            recovered_y = (sy-oy)/scale
            expected = in_button(lx, ly, button)
            # Small float tolerance applies to the inverse transform,
            # never to the hitbox itself.
            assert isclose(recovered_x, lx, abs_tol=1e-6)
            assert isclose(recovered_y, ly, abs_tol=1e-6)
            assert expected == (0 <= lx-l <= r-l and 0 <= ly-t <= b-t)
            pixel_checks += 1

# A toast must never intersect another page's fixed navigation region.
# Check both the mine's notification slot and the feature-page slot.
nav = (0, 686, 360, 720)
for toast in toasts:
    assert not overlaps(toast, nav), (toast, nav)
print(f'PASS: {pixel_checks} exterior/centre hitbox samples; toast clear of navigation')
