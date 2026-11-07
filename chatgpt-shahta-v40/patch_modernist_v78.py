"""v7.8: keep toast outside the tappable ore sprite (source-only).

The mining hitbox is x=105..330, y=210..440. A notification at y=240
visually obscured ore during play, even though it did not intercept touch.
The 178..204 band is below the depth telemetry (ends at 176) and above
the ore (starts at 210). No gameplay, saves, signing or hitboxes change.
Apply after patch_modernist_v77.py.
"""
from pathlib import Path

source = Path("chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MineView.java")
s = source.read_text(encoding="utf-8")
old = '''            v72NineSlice(canvas,"panel.png",18,240,324,26,252);
            rect(canvas,26,245,3,16,0xff65e1d0);
            leftFittedText(canvas,toast,39,258,12,0xfff0fffb,285);'''
new = '''            v72NineSlice(canvas,"panel.png",18,178,324,26,252);
            rect(canvas,26,183,3,16,0xff65e1d0);
            leftFittedText(canvas,toast,39,196,12,0xfff0fffb,285);'''
assert s.count(old) == 1, "v7.8 toast anchor absent or ambiguous"
s = s.replace(old, new, 1)
assert 'else if(x>=105&&x<=330&&y>=210&&y<=440)' in s
assert 'if(screenY>=88&&screenY<=136)' in s
assert 'getSharedPreferences("mine_save_v1"' in s
source.write_text(s, encoding="utf-8")
print("v7.8: toast moved to non-ore gap; source-only")
