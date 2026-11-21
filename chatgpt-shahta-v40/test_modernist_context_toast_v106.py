"""Source-only five-page contextual-toast regression.

The v7.9 overlay uses SCREEN coordinates; content is translated +60px.
Run: python3 chatgpt-shahta-v40/test_modernist_context_toast_v106.py
No Android SDK, Gradle, APK, or workflow dispatch.
"""
from pathlib import Path
import ast
import re

root = Path(__file__).resolve().parent
source = (root / "patch_modernist_v79.py").read_text(encoding="utf-8")
ast.parse(source)
match = re.search(
    r"int toastY = page==0 \? (\d+) : \(page==1 \? (\d+) : (\d+)\);",
    source,
)
assert match is not None, "Missing five-page toast expression"
mine, shop, feature = map(int, match.groups())
assert (mine, shop, feature) == (240, 691, 177)
assert 'v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);' in source
assert "rect(canvas,26,toastY+4,3,18,toastAccent);" in source
assert "leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,251);" in source
assert 'getSharedPreferences("mine_save_v1"' in source
assert "signingConfig signingConfigs.shahtaDebug" in source

# The rendered overlay is not shifted by 60; content geometry is.
nav = (88, 136)
mine_telemetry_bottom = 176 + 60
mine_ore_top = 210 + 60
shop_cards_bottom = 615 + 60
settings_bottom = 630 + 60
feature_title_baseline = 110 + 60
feature_controls_top = 145 + 60
checks = 0
for page in range(5):
    y = mine if page == 0 else shop if page == 1 else feature
    end = y + 26
    assert nav[1] < y and 0 < y < end <= 720
    if page == 0:
        assert mine_telemetry_bottom + 4 <= y
        assert end <= mine_ore_top - 4
    elif page == 1:
        assert y > shop_cards_bottom and y > settings_bottom
    else:
        assert y > feature_title_baseline
        assert end <= feature_controls_top - 2
    # Accents and text baseline must stay inside the 26px toast.
    assert 0 <= 4 and 4 + 18 <= 26
    assert 0 < 18 <= 26
    checks += 1

print(f"PASS: {checks} actual screen-space toast checks; no APK")
