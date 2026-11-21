"""Source-only regression for the v7.8 mining notification clearance.

Run without Gradle/Android: python3 chatgpt-shahta-v40/test_modernist_toast_clearance_v85.py
The toast must not occlude the ore hit target at any supported aspect ratio.
"""
from pathlib import Path
import ast
import re

HERE = Path(__file__).resolve().parent
patch = (HERE / "patch_modernist_v78.py").read_text(encoding="utf-8")
ast.parse(patch)

# Read actual patch replacement, rather than duplicating expected coordinates.
new = re.search(r"new = '''(.*?)'''", patch, re.S)
assert new, "Missing replacement for toast layout"
body = new.group(1)
panel = re.search(r'v72NineSlice\(canvas,"panel.png",(\d+),(\d+),(\d+),(\d+),', body)
assert panel, "Toast panel not found"
x, y, w, h = map(int, panel.groups())
assert x >= 0 and x+w <= 360 and y >= 0 and y+h <= 720

# Mine sprite and depth readout in the same logical 360x720 viewport.
ore = (105, 210, 330, 440)
depth_bottom = 176
assert y >= depth_bottom + 2, "Toast collides with depth telemetry"
assert y+h <= ore[1]-6, "Toast collides with tappable ore"
assert x+w > ore[0] and x < ore[2], "Unexpected horizontal layout"

# The text and accent must remain inside the notification panel.
accent = re.search(r'rect\(canvas,(\d+),(\d+),(\d+),(\d+),', body)
label = re.search(r'leftFittedText\(canvas,toast,(\d+),(\d+),', body)
assert accent and label
ax, ay, aw, ah = map(int, accent.groups())
tx, ty = map(int, label.groups())
assert x <= ax and ax+aw <= x+w and y <= ay and ay+ah <= y+h
assert x <= tx <= x+w and y < ty <= y+h

# Verify uniform letterboxing preserves separation on narrow and tall displays.
checks = 0
for width, height in ((320,568),(360,720),(393,852),(720,1280),
                      (1080,2400),(1272,2772),(1440,3200)):
    scale = min(width/360, height/720)
    ox, oy = (width-360*scale)/2, (height-720*scale)/2
    panel_bottom = oy + (y+h)*scale
    ore_top = oy + ore[1]*scale
    depth_end = oy + depth_bottom*scale
    assert depth_end < oy+y*scale < panel_bottom < ore_top
    assert ore_top-panel_bottom >= 6*scale - 1e-6
    checks += 1
print(f"PASS: toast/depth/ore clearance across {checks} viewports; source-only")
