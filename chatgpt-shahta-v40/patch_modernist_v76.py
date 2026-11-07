"""v7.6: restrained modernist hierarchy for feature headers and shop cards.

Applied AFTER v7.5. This source-only patch changes presentation only:
no navigation coordinates, hitboxes, costs, persistence or signing.
"""
from pathlib import Path

root = Path("chatgpt-shahta-v33/project")
src = root / "app/src/main/java/com/bezdna/mine/MineView.java"
s = src.read_text()

def replace_method(signature, body):
    global s
    anchor = "    " + signature + "{"
    assert s.count(anchor) == 1, ("missing/ambiguous method", signature, s.count(anchor))
    start = s.index(anchor)
    brace = s.index("{", start)
    depth = 0
    for i in range(brace, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                s = s[:start] + body.strip("\n") + s[i + 1:]
                return
    raise AssertionError("unclosed method: " + signature)

# Keep the 94..143 logical header entirely above the clipped interactive
# content (starts at y=145). This is NOT a floating overlay over buttons.
replace_method("private void v72SectionHeader(Canvas c,String title,String subtitle,int tab)", r"""
    private void v72SectionHeader(Canvas c,String title,String subtitle,int tab){
        v72NineSlice(c,"panel.png",10,94,340,49,255);
        rect(c,17,103,3,30,0xff65e1d0);
        leftFittedText(c,title,28,114,16,0xfff0fffd,253);
        leftFittedText(c,subtitle,28,132,10,0xffb3d2d4,253);
        // Compact, consistent page identity: no medieval frames or
        // effects. The bitmap is an actual ore sprite from the 24-set.
        v72NineSlice(c,"button_off.png",298,98,44,41,214);
        v70Draw(c,String.format(Locale.US,"ore_%02d.png",(tab*5)%24),
            304,102,32,32,255);
    }
""")

# Card structure and purchase hitboxes remain 165x145 and x+13/y+102.
# Use stronger type hierarchy, a restrained accent, and one raster sprite.
replace_method("private void v71ShopTile(Canvas c,int x,int y,int k,\n                             String title,String detail,int level)", r"""
    private void v71ShopTile(Canvas c,int x,int y,int k,
                             String title,String detail,int level){
        v72NineSlice(c,"panel.png",x,y,165,145,255);
        rect(c,x+10,y+9,3,52,0xff59d9c9);
        v70Draw(c,String.format(Locale.US,"ore_%02d.png",k%24),
            x+17,y+12,43,43,255);
        leftFittedText(c,title,x+66,y+29,13,0xffedfffb,91);
        leftFittedText(c,"УР. "+level,x+66,y+48,10,0xff84e1d2,91);
        fittedText(c,detail,x+82,y+80,10,0xffc9e0e2,149);
        drawV63RankTrack(c,x+15,y+91,135,level,0,0xff58dfce);
        button(c,x+13,y+102,139,36,"УЛУЧШИТЬ",
            fmt(cost(k))+" G",coins>=cost(k));
    }
""")

assert "if(screenY>=88&&screenY<=136)" in s
assert "if(screenY<205f||screenY>713f)return true;" in s
assert "v71ShopTile(c,10+(i%2)*175,164+(i/2)*153" in s
assert "if(x>=16&&x<=124){shopPage=0;" in s
assert "if(x>=128&&x<=236){shopPage=1;" in s
assert "if(page==1&&x>=246&&x<=345&&y>=102&&y<=154)" in s
assert 'getSharedPreferences("mine_save_v1"' in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
assert 'shahta-save-v1' in (root / "app/src/main/java/com/bezdna/mine/MainActivity.java").read_text()
gradle = (root / "app/build.gradle").read_text()
assert "applicationId 'com.bezdna.mine'" in gradle
assert "signingConfig signingConfigs.shahtaDebug" in gradle
src.write_text(s)
print("v7.6: feature headers + shop cards restyled; all input geometry unchanged")
