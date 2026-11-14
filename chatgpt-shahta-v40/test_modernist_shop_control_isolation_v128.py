"""Source-only regression: modern shop controls must not overlap or accept ghost taps.

No Android build, Gradle invocation, gameplay changes, or network access.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
patch = (ROOT / "patch_modernist_v71.py").read_text(encoding="utf-8")
assert "if(page==1&&x>=241&&x<=345&&y>=99&&y<=141)" in patch
assert "if(x>=13&&x<=228&&y>=119&&y<=154)" in patch
assert "if(x<xx+13||x>xx+152||y<yy+102||y>yy+138)continue;" in patch

W, H = 360, 720
settings = (241, 99, 345, 141)
pagination = (13, 119, 228, 154)
tiles = []
for i in range(6):
    xx = 10 + (i % 2) * 175
    yy = 164 + (i // 2) * 153
    tiles.append((xx + 13, yy + 102, xx + 152, yy + 138))

def intersects(a, b):
    return max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3])

controls = [settings, pagination, *tiles]
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
        for x, y in ((left, top), ((left + right) / 2, (top + bottom) / 2),
                     (right, bottom)):
            rx, ry = logical(ox + x * scale, oy + y * scale, width, height)
            assert abs(rx - x) < 1e-8 and abs(ry - y) < 1e-8
            assert sum(a <= rx <= c and b <= ry <= d for a, b, c, d in controls) == 1
            checks += 1
    # The gap between page switch and settings is not a hidden hitbox.
    for x, y in ((234, 130), (8, 140), (350, 120), (180, 160)):
        rx, ry = logical(ox + x * scale, oy + y * scale, width, height)
        assert not any(a <= rx <= c and b <= ry <= d for a, b, c, d in controls)
        checks += 1
print(f"PASS: {checks} shop hitbox checks on 8 viewport sizes; no APK built")
