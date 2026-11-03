"""Source-only affine hitbox regression for the modernist 360x720 canvas.

Run: python3 test_modernist_affine_hitboxes_v80.py
No Android tools, builds, or repository writes.
"""
from math import isclose

WIDTH, HEIGHT = 360.0, 720.0
# v7.2 applies translate then scale to the content canvas.
TX, TY, SX, SY = 13.0, 18.0, 0.93, 0.94
RESOLUTIONS = (
    (320, 568), (360, 720), (393, 852), (720, 1280),
    (1080, 2400), (1272, 2772), (1440, 3200),
)
# Rectangles are in the untransformed canvas's logical coordinates.
# These are sampling fixtures, not assertions about the runtime's exact layout.
TARGETS = {
    "mine_ore": (105, 210, 330, 440),
    "mine_health": (18, 457, 342, 576),
    "top_navigation": (18, 88, 342, 136),
}
def forward(x, y, width, height):
    scale = min(width / WIDTH, height / HEIGHT)
    ox = (width - WIDTH * scale) / 2
    oy = (height - HEIGHT * scale) / 2
    return (ox + scale * (TX + SX * x),
            oy + scale * (TY + SY * y))

def inverse(px, py, width, height):
    scale = min(width / WIDTH, height / HEIGHT)
    ox = (width - WIDTH * scale) / 2
    oy = (height - HEIGHT * scale) / 2
    return ((px - ox - scale * TX) / (scale * SX),
            (py - oy - scale * TY) / (scale * SY))

checks = 0
for width, height in RESOLUTIONS:
    for name, (left, top, right, bottom) in TARGETS.items():
        for x, y in ((left, top), (right, bottom),
                     ((left + right) / 2, (top + bottom) / 2)):
            px, py = forward(x, y, width, height)
            rx, ry = inverse(px, py, width, height)
            assert isclose(rx, x, abs_tol=1e-8), (name, width, height, x, rx)
            assert isclose(ry, y, abs_tol=1e-8), (name, width, height, y, ry)
            checks += 2
    # Letterboxed areas must not be interpreted as canvas touches.
    scale = min(width / WIDTH, height / HEIGHT)
    ox = (width - WIDTH * scale) / 2
    oy = (height - HEIGHT * scale) / 2
    if ox > 0:
        assert inverse(ox / 2, height / 2, width, height)[0] < 0
        checks += 1
    if oy > 0:
        assert inverse(width / 2, oy / 2, width, height)[1] < 0
        checks += 1
print(f"PASS: {checks} affine forward/inverse and letterbox checks on {len(RESOLUTIONS)} resolutions")
