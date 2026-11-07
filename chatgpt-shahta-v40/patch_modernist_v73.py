"""v7.3: modernist audio/settings sheet and exact interaction geometry.

Run AFTER patch_modernist_v72.py. Source-only: no build, network, Gradle,
APK publication, version bump or change to saves/gameplay/signing.
"""
from pathlib import Path

root = Path("chatgpt-shahta-v33/project")
src = root / "app/src/main/java/com/bezdna/mine/MineView.java"
s = src.read_text()

def once(old, new):
    global s
    count = s.count(old)
    assert count == 1, ("v7.3 missing or ambiguous source anchor", old[:100], count)
    s = s.replace(old, new, 1)

def replace_method(signature, replacement):
    global s
    anchor = "    " + signature + "{"
    assert s.count(anchor) == 1, (signature, s.count(anchor))
    start = s.index(anchor)
    opening = s.index("{", start)
    level = 0
    end = None
    for i in range(opening, len(s)):
        if s[i] == "{":
            level += 1
        elif s[i] == "}":
            level -= 1
            if level == 0:
                end = i + 1
                break
    assert end is not None, signature
    s = s[:start] + replacement.strip("\n") + s[end:]

# Replace the legacy gold, vertically-stretched settings modal with distinct
# graphite cards. The positions are shared with the hitbox regression test.
replace_method("private void drawAudioSettings(Canvas c)", r"""
    private void drawAudioSettings(Canvas c){
        v72NineSlice(c,"panel.png",14,153,332,477,255);
        leftFittedText(c,"НАСТРОЙКИ / ИГРА",30,179,18,0xffeafffa,289);
        leftFittedText(c,"ЗВУК  •  ВИЗУАЛИЗАЦИЯ",30,201,11,0xff9cc8c8,289);
        rect(c,30,214,300,2,0xff51b9b4);

        v72NineSlice(c,"panel.png",18,235,324,85,255);
        leftFittedText(c,"ЗВУК",34,264,15,0xffe5fbf8,174);
        leftFittedText(c,"Удары и находки",34,286,11,0xffa6c3cb,174);
        button(c,218,251,105,50,soundEnabled?"ВКЛ":"ВЫКЛ","",true);

        v72NineSlice(c,"panel.png",18,327,324,112,255);
        leftFittedText(c,"ГРОМКОСТЬ",34,355,15,0xffe5fbf8,190);
        fittedText(c,soundVolume+"%",284,355,13,0xffa7f1df,64);
        leftFittedText(c,"0",42,422,10,0xff9ebac5,26);
        fittedText(c,"100",318,422,10,0xff9ebac5,36);
        p.reset();p.setAntiAlias(true);p.setColor(0xff405669);
        c.drawRoundRect(42,393,318,401,4,4,p);
        p.setColor(soundEnabled?0xff63ddcb:0xff879aa6);
        float end=42+2.76f*soundVolume;
        if(end>42)c.drawRoundRect(42,393,end,401,4,4,p);
        p.setColor(soundEnabled?0xffe5fffa:0xffb3c5cd);
        c.drawCircle(end,397,7,p);

        v72NineSlice(c,"panel.png",18,445,324,85,255);
        leftFittedText(c,"ЭФФЕКТЫ",34,474,15,0xffe5fbf8,174);
        leftFittedText(c,"Анимации и частицы",34,496,11,0xffa6c3cb,174);
        button(c,218,461,105,50,fxEnabled?"ВКЛ":"ВЫКЛ","",true);

        button(c,18,548,324,61,"НАЗАД В ЛАВКУ",
            "Изменения сохраняются автоматически",true);
    }
""")

# The old full-row click areas caused accidental toggles while scrolling.
# Hitboxes now match the visible controls, not the surrounding card.
once("if(y>=245&&y<=307){soundEnabled=!soundEnabled;",
     "if(x>=218&&x<=323&&y>=251&&y<=301){soundEnabled=!soundEnabled;")
once("else if(y>=326&&y<=402){soundVolume=Math.max(0,Math.min(100,Math.round((x-55f)/250f*20f)*5));",
     "else if(x>=35&&x<=325&&y>=383&&y<=414){soundVolume=Math.max(0,Math.min(100,Math.round((x-42f)/276f*20f)*5));")
once("else if(y>=407&&y<=469){fxEnabled=!fxEnabled;",
     "else if(x>=218&&x<=323&&y>=461&&y<=511){fxEnabled=!fxEnabled;")
once("else if(y>=520&&y<=585){settingsOpen=false;",
     "else if(x>=18&&x<=342&&y>=548&&y<=609){settingsOpen=false;")
once("if(page==1&&x>=235&&y>=95&&y<=144){settingsOpen=true;",
     "if(page==1&&x>=241&&x<=345&&y>=99&&y<=141){settingsOpen=true;")
# Returning to the shop from another tab must not resurrect a stale modal.
once("previousPage=page;page=next;pageSlide=1f;",
     "previousPage=page;page=next;pageSlide=1f;settingsOpen=false;")

assert s.count("private void drawAudioSettings(Canvas c)")==1
assert "if(x>=218&&x<=323&&y>=251&&y<=301)" in s
assert "if(x>=35&&x<=325&&y>=383&&y<=414)" in s
assert "if(x>=218&&x<=323&&y>=461&&y<=511)" in s
assert "if(x>=18&&x<=342&&y>=548&&y<=609)" in s
assert "settingsOpen=false;" in s
assert 'getSharedPreferences("mine_save_v1"' in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
assert "signingConfig signingConfigs.shahtaDebug" in (root/"app/build.gradle").read_text()
assert "applicationId 'com.bezdna.mine'" in (root/"app/build.gradle").read_text()
assert 'shahta-save-v1' in (root/"app/src/main/java/com/bezdna/mine/MainActivity.java").read_text()
src.write_text(s)
print("v7.3: modernist settings, aligned controls and touch zones; no APK built")
