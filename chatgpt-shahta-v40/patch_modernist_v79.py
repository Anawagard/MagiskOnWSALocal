"""v7.9: context-aware toast placement for all five modernist pages.

Mine has a reserved gap at y=178..204. Shop notifications sit below the content viewport (ends at 653), at y=655..681; this also avoids the settings modal ending at 630.
Forge/guild/atlas notifications occupy y=145..171, below the fixed
navigation (ends at 137) and above transformed feature content (starts at 205).
The toast is drawn in screen-space outside the translated page canvas. Presentation-only: no hitboxes, balance, persistence,
package identifier or signing changes. Apply after v7.8.
"""
from pathlib import Path
import os
import tempfile

root = Path("chatgpt-shahta-v33/project")
source = root / "app/src/main/java/com/bezdna/mine/MineView.java"
old = '''        if(System.currentTimeMillis()<toastUntil){
            v72NineSlice(canvas,"panel.png",18,178,324,26,252);
            rect(canvas,26,183,3,16,0xff65e1d0);
            leftFittedText(canvas,toast,39,196,12,0xfff0fffb,285);
        }'''
new = '''        if(System.currentTimeMillis()<toastUntil){
            // Mine: telemetry gap; shop: below cards and settings; feature pages: reserved upper gap.
            // This overlay never changes onTouchEvent geometry.
            int toastY = page==0 ? 178 : (page==1 ? 655 : 145);
            // Dedicated notification surface: accent rail + quiet baseline.
            // Preserve the original 324x26 panel and all touch geometry.
            v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);
            rect(canvas,26,toastY+4,3,18,0xff65e1d0);
            // A slim illuminated top edge adds depth without obscuring the toast text.
            rect(canvas,36,toastY+2,76,1,0xff65e1d0);
            rect(canvas,112,toastY+2,220,1,0xff315d60);
            rect(canvas,36,toastY+22,296,1,0xff315d60);
            // Keep the text inside the 251px safe zone, with a separate ore badge.
            leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,251);
            rect(canvas,301,toastY+3,25,20,0xff18383c);
            rect(canvas,301,toastY+3,25,1,0xff65e1d0);
            rect(canvas,301,toastY+22,25,1,0xff315d60);
            v70Draw(canvas,String.format(Locale.US,"ore_%02d.png",(page*5)%24),
                305,toastY+4,18,18,225);
        }'''
# Geometry contract: the notification must fit the 360x720 logical canvas,
# clear the fixed top navigation, and not cover the mine's ore hitbox.
# Keep this source-only and independent of Android/Gradle.
TOAST_HEIGHT = 26
TOAST_WIDTH = 324
TOAST_X = 18
TOAST_Y = {0: 178, 1: 655, 2: 145, 3: 145, 4: 145}
def validate_toast_geometry():
    """Enforce the five-page visual contract even under Python -O."""
    # Constants used by the verifier must match the actual Java expression.
    # Otherwise a safe TOAST_Y table could mask unsafe rendered positions.
    import re
    expression = re.search(
        r"int toastY = page==0 \\? (\\d+) : \\(page==1 \\? (\\d+) : (\\d+)\\);",
        new,
    )
    if expression is None:
        raise RuntimeError("v7.9: Java toast coordinates cannot be verified")
    mine, shop, feature = map(int, expression.groups())
    rendered = {0: mine, 1: shop, 2: feature, 3: feature, 4: feature}
    if rendered != TOAST_Y:
        raise RuntimeError("v7.9: Java toast coordinates differ from validated geometry")
    if set(TOAST_Y) != set(range(5)):
        raise RuntimeError("v7.9: toast coordinates must cover exactly five pages")
    if not (39 + 251 < 301 and 301 + 25 <= TOAST_X + TOAST_WIDTH):
        raise RuntimeError("v7.9: toast text overlaps the ore badge")
    if not (305 >= 301 and 305 + 18 <= 301 + 25):
        raise RuntimeError("v7.9: toast badge sprite exceeds its container")
    for page_index, top in TOAST_Y.items():
        if not (0 <= TOAST_X and TOAST_X + TOAST_WIDTH <= 360
                and 137 < top and top + TOAST_HEIGHT <= 682):
            raise RuntimeError(f"v7.9: toast outside safe screen area on page {page_index}")
        if page_index == 0 and not top + TOAST_HEIGHT < 210:
            raise RuntimeError("v7.9: mine toast overlaps ore hitbox")
        if page_index == 1 and not (top > 653 and top > 630):
            raise RuntimeError("v7.9: shop toast overlaps content or settings")
        if page_index >= 2 and not top + TOAST_HEIGHT < 205:
            raise RuntimeError(f"v7.9: feature toast overlaps content on page {page_index}")
        if not 0 <= (page_index * 5) % 24 < 24:
            raise RuntimeError("v7.9: invalid ore badge index")

def apply():
    validate_toast_geometry()
    # Fail closed even with python -O; never write partially patched Java.
    current = source.read_text(encoding="utf-8")
    if current.count(old) != 1 or new in current:
        raise RuntimeError("v7.9: expected exactly one v7.8 toast anchor; source unchanged")
    gradle = (root / "app/build.gradle").read_text(encoding="utf-8")
    required = (
        "v71Scale()",
        "else if(x>=105&&x<=330&&y>=210&&y<=440)",
        'getSharedPreferences("mine_save_v1"',
        "public void save()",
        "private void rebirth()",
    )
    missing = [marker for marker in required if marker not in current]
    if missing:
        raise RuntimeError(f"v7.9: missing source contracts {missing}; source unchanged")
    gradle_required = ("applicationId 'com.bezdna.mine'",
                       "signingConfig signingConfigs.shahtaDebug")
    missing_gradle = [marker for marker in gradle_required if marker not in gradle]
    if missing_gradle:
        raise RuntimeError(f"v7.9: missing build contracts {missing_gradle}; source unchanged")
    result = current.replace(old, new, 1)
    fd, tmp = tempfile.mkstemp(prefix=".mineview-v79-", suffix=".tmp", dir=source.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(result)
        os.chmod(tmp, source.stat().st_mode)
        os.replace(tmp, source)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print("v7.9: contextual toast position; source-only")


if __name__ == "__main__":
    apply()
