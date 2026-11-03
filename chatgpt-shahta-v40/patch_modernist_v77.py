"""v7.7: high-contrast mine telemetry and unified in-game notifications.

Apply AFTER patch_modernist_v76.py. Presentation-only; the mining sprite,
ore tap rectangle, five-tab navigation, economy, saves and signing are untouched.
This patch intentionally does not build an APK.
"""
from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
source=root/"app/src/main/java/com/bezdna/mine/MineView.java"
s=source.read_text()

def once(old,new):
    global s
    count=s.count(old)
    assert count==1,("v7.7 missing or ambiguous anchor",old[:100],count)
    s=s.replace(old,new,1)

# The old center-aligned depth/biome strings competed for the same width.
# Keep the entire telemetry panel above the ore (first pixel y=210).
# The depth progression remains the exact same 25-stage calculation.
once("""        panel(c,18,93,324,66,0xff263c42);
        fittedText(c,"СЕКТОР / ГЛУБИНА "+depth,180,115,16,0xffe7f6f4,304);
        fittedText(c,ZONES[biome]+"   |   "+ORE_NAMES[id],180,139,11,
            colorBlend(tint,WHITE,.62f),310);
        round(c,28,171,304,5,2,0xff182e34);
        float step=((depth-1)%25+1)/25f;
        rect(c,30,172,300*step,3,colorBlend(tint,0xff64e4ce,.40f));""",
"""        v72NineSlice(c,"panel.png",18,93,324,83,255);
        rect(c,27,104,3,45,0xff64ddce);
        leftFittedText(c,"ГЛУБИНА "+depth,40,119,17,0xffeffffc,171);
        fittedText(c,"СЕКТОР "+(biome+1)+" / 24",276,117,11,
            0xffa2e7da,116);
        leftFittedText(c,ZONES[biome]+" / "+ORE_NAMES[id],
            40,144,10,colorBlend(tint,WHITE,.68f),278);
        float step=((depth-1)%25+1)/25f;
        round(c,39,158,282,5,2,0xff263f4a);
        rect(c,39,158,282*step,5,0xff64ddce);""")

# The rock-health telemetry uses the same graphite surface and accent
# language. The original HP numbers, bar, action controls and positions stay.
once("        panel(c,18,457,324,119,0xff223b45);",
     """        v72NineSlice(c,"panel.png",18,457,324,119,255);
        rect(c,27,468,3,37,0xff64ddce);""")

# A legible notification is shared by all five pages. Its box is below
# the navigation rail (ends at 136) and never steals touches.
once("""        if(System.currentTimeMillis()<toastUntil){
            panel(canvas,22,139,316,32,0xff405250);
            fittedText(canvas,toast,180,159,12,0xfff6e5c7,290);
        }""",
"""        if(System.currentTimeMillis()<toastUntil){
            v72NineSlice(canvas,"panel.png",18,240,324,26,252);
            rect(canvas,26,245,3,16,0xff65e1d0);
            leftFittedText(canvas,toast,39,258,12,0xfff0fffb,285);
        }""")

for marker in (
    "if(screenY>=88&&screenY<=136)",
    "else if(x>=105&&x<=330&&y>=210&&y<=440)",
    "if(screenY<205f||screenY>713f)return true;",
    'getSharedPreferences("mine_save_v1"',
    'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);',
    "public void save()",
    "private void rebirth()",
):
    assert marker in s,marker
assert 'shahta-save-v1' in (root/"app/src/main/java/com/bezdna/mine/MainActivity.java").read_text()
gradle=(root/"app/build.gradle").read_text()
assert "applicationId 'com.bezdna.mine'" in gradle
assert "signingConfig signingConfigs.shahtaDebug" in gradle
assert s.count('v72NineSlice(c,"panel.png",18,93,324,83,255);')==1
assert s.count('v72NineSlice(canvas,"panel.png",18,237,324,32,252);')==1
source.write_text(s)
print("v7.7: mine telemetry, health surface and global toast restyled; source-only")
