"""Static geometry and integration guard for contextual notifications (v7.9).

Runs with CPython only. No Android build or emulator required.
"""
from pathlib import Path
import ast
import re

root = Path(__file__).parent
patch = (root / "patch_modernist_v79.py").read_text(encoding="utf-8")
ast.parse(patch)
assert "int toastY = page==0 ? 178 : 623;" in patch
assert "toastY+5" in patch and "toastY+18" in patch
assert "s.count(old)==1" in patch

# Mine telemetry ends at 176; ore begins at 210.
mine = (178, 178 + 26)
assert mine[0] >= 176 + 2 and mine[1] <= 210 - 6
# Shop cards: y=164,317,470; each height 145. Last ends at 615.
shop = (623, 623 + 26)
assert shop[0] >= 470 + 145 + 8
assert shop[1] < 653  # content scene bottom

for width,height in ((320,568),(360,720),(393,852),(720,1280),
                     (1080,2400),(1272,2772)):
    scale=min(width/360,height/720)
    offset=(height-720*scale)/2
    for start,end in (mine,shop):
        assert offset+start*scale>=0
        assert offset+end*scale<=height
        assert (end-start)*scale>0

workflow = (root.parent / ".github/workflows/chatgpt-shahta-v40.yml").read_text()
assert "workflow_dispatch:" in workflow
assert "patch_modernist_v78.py" in workflow
assert workflow.index("patch_modernist_v78.py") < workflow.index("patch_modernist_v79.py")
assert workflow.count("patch_modernist_v79.py")==1
print("PASS: v7.9 contextual toast geometry (12 viewport/page combinations)")
