"""Source-only regression: modern shop controls must not overlap or accept ghost taps.

No Android build, Gradle invocation, gameplay changes, or network access.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "patch_modernist_v71.py").read_text(encoding="utf-8")
final = (ROOT / "patch_modernist_v74.py").read_text(encoding="utf-8")
# v7.4 replaces v7.1's broad pagination toggle and settings hitbox.
# Test the final painted geometry and the exact source replacement anchors.
assert 'if(x<xx+13||x>xx+152||y<yy+102||y>yy+138)continue;' in base
assert 'if(page==1&&x>=241&&x<=345&&y>=99&&y<=141)' in base
assert 'if(page==1&&x>=246&&x<=345&&y>=102&&y<=154)' in final
assert 'if(x>=16&&x<=124){shopPage=0;invalidate();return true;}' in final
assert 'if(x>=128&&x<=236){shopPage=1;invalidate();return true;}' in final
assert 'if(y>=130&&y<=158)' in final
assert 'shopPage=1-shopPage' in final  # old anchor, replaced during patch application
assert 'assert "shopPage=1-shopPage" not in s' in final

W, H = 360, 720
settings = (246, 102, 345, 154)
tabs = [(16, 130, 124, 158), (128, 130, 236, 158)]
tiles = []
for i in range(6):
    xx = 10 + (i % 2) * 175
    yy = 164 + (i // 2) * 153
    tiles.append((xx + 13, yy + 102, xx + 152, yy + 138))

def intersects(a, b):
    return max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3])

controls = [settings, *tabs, *tiles]
for i, rect in enumerate(controls):
    assert 0 <= rect[0] < rect[2] < W
    assert 0 <= rect[1] < rect[3] < H
    for other in controls[i + 1:]:
        assert not intersects(rect, other), (rect, other)

def logical(px, py, width, height):
    scale = min(width / W, height / H)
    ox = (width - W * scale) / 2
    oy = (height - H * scale) / 2
    return (px - ox) / scale, (py - oy) / scale

checks = 0
for width, height in ((240, 320), (280, 560), (320, 568), (360, 720),
                      (393, 873), (720, 1280), (1080, 2400), (1272, 2772)):
    scale = min(width / W, height / H)
    ox, oy = (width - W * scale) / 2, (height - H * scale) / 2
    for i, (left, top, right, bottom) in enumerate(controls):
        for x, y in ((left + 0.01, top + 0.01), ((left + right) / 2, (top + bottom) / 2),
                     (right - 0.01, bottom - 0.01)):
            rx, ry = logical(ox + x * scale, oy + y * scale, width, height)
            assert abs(rx - x) < 1e-8 and abs(ry - y) < 1e-8
            assert sum(a <= rx <= c and b <= ry <= d for a, b, c, d in controls) == 1
            checks += 1
    # The gap between page switch and settings is not a hidden hitbox.
    for x, y in ((240, 140), (14, 140), (350, 120), (180, 160), (126, 145)):
        rx, ry = logical(ox + x * scale, oy + y * scale, width, height)
        assert not any(a <= rx <= c and b <= ry <= d for a, b, c, d in controls)
        checks += 1
# Exercise negative space and every control's immediately adjacent exterior.
# These points are deliberately offset by 0.01 logical units to avoid
# rounding ambiguity at inclusive Java hitbox boundaries.
for width, height in ((240, 320), (280, 560), (320, 568), (360, 720),
                      (393, 873), (720, 1280), (1080, 2400), (1272, 2772)):
    scale = min(width / W, height / H)
    ox, oy = (width - W * scale) / 2, (height - H * scale) / 2
    for left, top, right, bottom in controls:
        mx, my = (left + right) / 2, (top + bottom) / 2
        for x, y in ((left - .01, my), (right + .01, my),
                     (mx, top - .01), (mx, bottom + .01)):
            rx, ry = logical(ox + x * scale, oy + y * scale, width, height)
            assert abs(rx - x) < 1e-8 and abs(ry - y) < 1e-8
            # Adjacent controls may legitimately own an exterior point;
            # the specific control being tested must not.
            assert not (left <= rx <= right and top <= ry <= bottom)
            checks += 1
    # Letterboxed margins are not part of the logical canvas.
    if ox > 0:
        for px in (0, ox / 2, ox + W * scale + (width - ox - W * scale) / 2):
            rx, ry = logical(px, height / 2, width, height)
            assert rx < 0 or rx > W
            checks += 1
    if oy > 0:
        for py in (0, oy / 2, oy + H * scale + (height - oy - H * scale) / 2):
            rx, ry = logical(width / 2, py, width, height)
            assert ry < 0 or ry > H
            checks += 1
print(f"PASS: {checks} final v7.4 shop hitbox and exterior checks on 8 viewport sizes; no APK built")
