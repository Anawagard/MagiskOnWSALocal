"""v7.5: compact modernist resource HUD and five-cell navigation.

Source-only transformation applied after v7.4. No Gradle, signing, game
balance, persistence or APK actions. Navigation stays at logical y=88..136
with five 72-unit cells, matching the existing input dispatcher.
"""
from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
source=root/"app/src/main/java/com/bezdna/mine/MineView.java"
s=source.read_text()

def replace_method(signature, replacement):
    global s
    anchor="    "+signature+"{"
    assert s.count(anchor)==1,(signature,s.count(anchor))
    start=s.index(anchor)
    opening=s.index("{",start)
    depth=0
    for pos in range(opening,len(s)):
        if s[pos]=="{":depth+=1
        elif s[pos]=="}":
            depth-=1
            if depth==0:
                s=s[:start]+replacement.strip("\n")+s[pos+1:]
                return
    raise AssertionError(("unclosed method",signature))

replace_method("private void drawHeader(Canvas c)",r"""
    private void drawHeader(Canvas c){
        v70Draw(c,"header.png",0,0,360,88,255);
        leftFittedText(c,"DEEP / MINE",16,27,19,0xffeafffb,200);
        fittedText(c,"СЕКТОР "+(zone()+1)+" / 24",281,26,11,0xff91dace,140);

        // Two equal resource cards; the previous long inline labels could
        // collide with large currency values on narrow phones.
        v72NineSlice(c,"panel.png",10,39,166,40,255);
        v70Draw(c,"ore_03.png",17,46,24,24,255);
        leftFittedText(c,fmt(coins),47,59,15,0xffd9fff5,119);
        leftFittedText(c,"МОНЕТЫ",47,73,9,0xff9bc9c9,119);

        v72NineSlice(c,"panel.png",184,39,166,40,255);
        v70Draw(c,"ore_07.png",191,46,24,24,255);
        leftFittedText(c,fmt(gems),221,59,15,0xffd6f0ff,119);
        leftFittedText(c,"КРИСТАЛЛЫ",221,73,9,0xff9bc9d8,119);
    }
""")

replace_method("private void drawBottom(Canvas c)",r"""
    // Drawn cells and touch cells are both exactly 72 logical pixels wide.
    // The active tab is visible through fill, typography and a bottom marker.
    private void drawBottom(Canvas c){
        v70Draw(c,"nav.png",0,87,360,50,255);
        for(int i=0;i<5;i++){
            float left=i*72f;
            boolean active=page==i;
            v72NineSlice(c,active?"button.png":"button_off.png",
                left+4,90,64,44,active?255:176);
            v70Draw(c,V70_ICONS[i],left+26,93,20,20,255);
            fittedText(c,V70_NAV[i],left+36,126,10,
                active?0xffeafffa:0xffb3c4ce,62);
            if(active)rect(c,left+18,132,36,2,0xff67e6d4);
        }
    }
""")

assert s.count("private void drawHeader(Canvas c)")==1
assert s.count("private void drawBottom(Canvas c)")==1
assert "float left=i*72f;" in s
assert "if(screenY>=88&&screenY<=136)" in s
assert "int next=clamp((int)(x/72f),0,4);" in s
assert 'getSharedPreferences("mine_save_v1"' in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
assert 'shahta-save-v1' in (root/"app/src/main/java/com/bezdna/mine/MainActivity.java").read_text()
gradle=(root/"app/build.gradle").read_text()
assert "applicationId 'com.bezdna.mine'" in gradle
assert "signingConfig signingConfigs.shahtaDebug" in gradle
source.write_text(s)
print("v7.5: compact two-card resource HUD and aligned five-cell top navigation; source-only")
