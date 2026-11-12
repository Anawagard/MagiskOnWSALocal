"""v7.9: context-aware toast placement for all five modernist pages.

Mine has a reserved gap at y=178..204. Shop notifications sit below the content viewport (ends at 653), at y=655..681; this also avoids the settings modal ending at 630.
Forge/guild/atlas notifications occupy y=145..171, below the fixed
navigation (ends at 137) and above transformed feature content (starts at 205).
The toast is drawn in screen-space outside the translated page canvas. Presentation-only: no hitboxes, balance, persistence,
package identifier or signing changes. Apply after v7.8.
"""
from pathlib import Path

root = Path("chatgpt-shahta-v33/project")
source = root / "app/src/main/java/com/bezdna/mine/MineView.java"
s = source.read_text(encoding="utf-8")
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
            leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,285);
        }'''
assert s.count(old)==1, "v7.9 toast anchor missing or ambiguous"
assert "v71Scale()" in s
assert "else if(x>=105&&x<=330&&y>=210&&y<=440)" in s
assert 'getSharedPreferences("mine_save_v1"' in s
assert "public void save()" in s
assert "private void rebirth()" in s
assert "applicationId 'com.bezdna.mine'" in (root/"app/build.gradle").read_text()
assert "signingConfig signingConfigs.shahtaDebug" in (root/"app/build.gradle").read_text()
s=s.replace(old,new,1)
source.write_text(s,encoding="utf-8")
print("v7.9: contextual toast position; source-only")
