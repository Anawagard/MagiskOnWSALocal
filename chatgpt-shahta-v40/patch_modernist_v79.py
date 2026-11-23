"""v7.9: context-aware toast placement for all five modernist pages.

Coordinates are in SCREEN space, whereas page content is rendered +60px down.
Mine: telemetry ends at screen y=236, rock begins at 270; toast y=240..266.
Shop: last shop card ends at y=675, settings sheet at y=690;
toast y=691..717 (inside the 720px canvas, clear of shop actions).
Forge/guild/atlas: toast y=177..203 temporarily replaces the non-interactive
section-header subtitle, below the title and above active content (starts at 205).
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
            // Screen-space: mine rock gap, shop footer, feature header subtitle strip.
            // This overlay never changes onTouchEvent geometry.
            int toastY = page==0 ? 240 : (page==1 ? 691 : 177);
            // Page-aware rail: mine cyan, shop amber, forge orange,
            // guild violet, atlas blue. Presentation only; touch bounds stay unchanged.
            int toastAccent = page==0 ? 0xff65e1d0 :
                (page==1 ? 0xffffcf82 : (page==2 ? 0xffffa77a :
                (page==3 ? 0xffc4a7ff : 0xff82bfff)));
            // Dedicated notification surface: accent rail + quiet baseline.
            // Preserve the original 324x26 panel and all touch geometry.
            v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);
            rect(canvas,26,toastY+4,3,18,toastAccent);
            // A slim illuminated top edge adds depth without obscuring the toast text.
            rect(canvas,36,toastY+2,76,1,toastAccent);
            rect(canvas,112,toastY+2,220,1,0xff315d60);
            rect(canvas,36,toastY+22,296,1,0xff315d60);
            // Keep the text inside the 251px safe zone, with a separate ore badge.
            leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,251);
            rect(canvas,301,toastY+3,25,20,0xff18383c);
            rect(canvas,301,toastY+3,25,1,toastAccent);
            rect(canvas,301,toastY+22,25,1,0xff315d60);
            v70Draw(canvas,String.format(Locale.US,"ore_%02d.png",(page*5)%24),
                305,toastY+4,18,18,225);
        }'''
# The five destinations now carry their own accent in the *active* bottom
# navigation state, matching the existing page-specific toast/header palette.
# These are paint-only rails within the old 64x44 button. No input or
# navigation dispatcher code changes.
nav_old = '            if(active)rect(c,left+18,132,36,2,0xff67e6d4);'
nav_new = '''            if(active){
                int tabAccent=i==0 ? 0xff65e1d0 : (i==1 ? 0xffffcf82 :
                    (i==2 ? 0xffffa77a : (i==3 ? 0xffc4a7ff : 0xff82bfff)));
                rect(c,left+18,90,36,2,tabAccent);
                rect(c,left+18,132,36,2,tabAccent);
                rect(c,left+9,94,2,12,tabAccent);
            }'''

# Geometry contract: the notification must fit the 360x720 logical canvas,
# clear the fixed top navigation, and not cover the mine's ore hitbox.
# Keep this source-only and independent of Android/Gradle.
TOAST_HEIGHT = 26
TOAST_WIDTH = 324
TOAST_X = 18
TOAST_Y = {0: 240, 1: 691, 2: 177, 3: 177, 4: 177}
def validate_toast_geometry():
    """Enforce the five-page visual contract even under Python -O."""
    # Constants used by the verifier must match the actual Java expression.
    # Otherwise a safe TOAST_Y table could mask unsafe rendered positions.
    import re
    expression = re.search(
        r"int toastY = page==0 \? (\d+) : \(page==1 \? (\d+) : (\d+)\);",
        new,
    )
    if expression is None:
        raise RuntimeError("v7.9: Java toast coordinates cannot be verified")
    mine, shop, feature = map(int, expression.groups())
    rendered = {0: mine, 1: shop, 2: feature, 3: feature, 4: feature}
    if rendered != TOAST_Y:
        raise RuntimeError("v7.9: Java toast coordinates differ from validated geometry")
    # Five opaque, distinct tab accents, verified against the actual Java source.
    palette = re.search(r"int toastAccent = (.*?);", new, re.S)
    if palette is None:
        raise RuntimeError("v7.9: missing page-aware toast palette")
    accents = re.findall(r"0xff[0-9a-fA-F]{6}", palette.group(1))
    if len(accents) != 5 or len(set(accents)) != 5:
        raise RuntimeError("v7.9: expected five unique opaque toast accents")
    if new.count("rect(canvas,26,toastY+4,3,18,toastAccent)") != 1:
        raise RuntimeError("v7.9: accent rail is not bound to page palette")
    if set(TOAST_Y) != set(range(5)):
        raise RuntimeError("v7.9: toast coordinates must cover exactly five pages")
    if not (39 + 251 < 301 and 301 + 25 <= TOAST_X + TOAST_WIDTH):
        raise RuntimeError("v7.9: toast text overlaps the ore badge")
    if not (305 >= 301 and 305 + 18 <= 301 + 25):
        raise RuntimeError("v7.9: toast badge sprite exceeds its container")
    for page_index, top in TOAST_Y.items():
        if not (0 <= TOAST_X and TOAST_X + TOAST_WIDTH <= 360
                and 137 < top and top + TOAST_HEIGHT <= 720):
            raise RuntimeError(f"v7.9: toast outside safe screen area on page {page_index}")
        # Translated page content is +60px below the old page-local tests.
        if page_index == 0 and not (top >= 240 and top + TOAST_HEIGHT <= 266):
            raise RuntimeError("v7.9: mine toast overlaps shifted telemetry or ore")
        if page_index == 1 and not (top > 690 and top + TOAST_HEIGHT <= 720):
            raise RuntimeError("v7.9: shop toast overlaps shifted cards/settings")
        if page_index >= 2 and not (top >= 175 and top + TOAST_HEIGHT <= 203):
            raise RuntimeError(f"v7.9: feature toast overlaps title or live content on page {page_index}")
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
    # Draw state is changed strictly after verifying the v7.5 navigation rail.
    # The menu's painted 64x44 area and touch dispatch remain untouched.
    if current.count(nav_old) != 1 or nav_new in current:
        raise RuntimeError("v7.9: expected exactly one v7.5 nav accent anchor; source unchanged")
    result = current.replace(old, new, 1).replace(nav_old, nav_new, 1)
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
