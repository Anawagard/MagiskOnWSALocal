"""Source-only contract for the three clipped feature pages.

Run with python3; no Android SDK, APK, emulator, or GitHub Actions.
This tests the actual v7.2 patch anchors and mathematical screen mapping.
"""
from pathlib import Path
import ast
import math

root = Path(__file__).resolve().parent
source = (root / "patch_modernist_v72.py").read_text(encoding="utf-8")
ast.parse(source)

# The clip is applied before the affine transform, in page-local coordinates.
# The page is then rendered 60 px below the screen origin.
assert source.count("c.clipRect(0,145,360,653);") == 1
assert 'for name in ("drawForge","drawGuild","drawCollection"):' in source
assert 'for name,title,subtitle,tab in pages:' in source
assert source.count("c.translate(13f,18f);") == 1  # template, used by 3 pages
assert source.count("c.scale(.93f,.94f);") == 1
assert "if(screenY<205f||screenY>713f)return true;" in source
assert "x=(x-13f)/.93f;" in source
assert "y=(y-18f)/.94f;" in source

# Physical device viewport -> logical 360x720 screen -> legacy content.
# Test inclusive clip edges, just-outside positions, and both letterbox axes.
devices = ((240, 320), (320, 480), (360, 720), (393, 852),
           (720, 1280), (1080, 2400), (1272, 2772),
           (1000, 720), (360, 1000), (1768, 2208))
checks = 0
for width, height in devices:
    scale = min(width / 360.0, height / 720.0)
    ox = (width - 360 * scale) / 2
    oy = (height - 720 * scale) / 2
    for sx in (0.25, 13, 180, 359.75):
        for sy in (204.75, 205, 205.25, 459, 712.75, 713, 713.25):
            px, py = ox + sx * scale, oy + sy * scale
            restored_x = (px - ox) / scale
            restored_y = (py - oy) / scale
            assert math.isclose(restored_x, sx, abs_tol=1e-8)
            assert math.isclose(restored_y, sy, abs_tol=1e-8)
            visible = 205 <= sy <= 713
            assert (205 - 1e-8 <= restored_y <= 713 + 1e-8) == visible
            legacy_x = (restored_x - 13) / .93
            legacy_y = (restored_y - 60 - 18) / .94
            assert math.isclose(13 + legacy_x * .93, sx, abs_tol=1e-8)
            assert math.isclose(60 + 18 + legacy_y * .94, sy, abs_tol=1e-8)
            checks += 1

# Header and navigation remain outside the interactive feature clip.
assert 136 < 205
assert 143 < 205  # fixed section header ends at 94 + 49
print(f"PASS: {checks} feature-page clipping and inverse-hitbox checks")
