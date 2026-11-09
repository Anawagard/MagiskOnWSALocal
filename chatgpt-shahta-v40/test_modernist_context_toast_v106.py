"""Source-only regression for v7.9 contextual toast layout.

Run: python3 chatgpt-shahta-v40/test_modernist_context_toast_v106.py
No Android build, emulator or workflow execution required.
"""
from pathlib import Path
import ast

root = Path(__file__).resolve().parent
patch = (root / "patch_modernist_v79.py").read_text(encoding="utf-8")
ast.parse(patch)
assert "int toastY = page==0 ? 178 : 623;" in patch
assert 'v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);' in patch
assert "rect(canvas,26,toastY+5,3,16,0xff65e1d0);" in patch
assert "leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,285);" in patch
assert 'getSharedPreferences("mine_save_v1"' in patch
assert "signingConfig signingConfigs.shahtaDebug" in patch

# Rectangle intervals are half-open: [top, bottom). Notification card
# must not cover the ore hitbox, shop cards, header or bottom navigation.
toast_height = 26
mine_ore = (210, 440)
mine_telemetry_end = 176
feature_cards_end = 615
navigation_top = 653
checks = 0
for page in range(5):
    y = 178 if page == 0 else 623
    end = y + toast_height
    assert y >= 0 and end <= 720
    assert end <= navigation_top
    if page == 0:
        assert y >= mine_telemetry_end
        assert end <= mine_ore[0]
    else:
        assert y >= feature_cards_end
    # Accent bar and baseline must remain inside the toast panel.
    assert y <= y + 5 and y + 5 + 16 <= end
    assert y <= y + 18 <= end
    checks += 1

print(f"PASS: contextual toast bounds on {checks} pages")
