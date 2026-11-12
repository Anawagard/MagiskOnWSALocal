"""v7.4: explicit two-tab shop navigation and balanced modernist header.

Apply AFTER patch_modernist_v73.py. Source-only: no Gradle, APK, CI or
persistence/balance/signing changes. The visible controls and touch zones
share one documented coordinate contract.
"""
from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
source=root/"app/src/main/java/com/bezdna/mine/MineView.java"
s=source.read_text()

def once(old,new):
    global s
    n=s.count(old)
    assert n==1,("v7.4 missing/ambiguous anchor",old[:130],n)
    s=s.replace(old,new,1)

def replace_method(signature,body):
    global s
    anchor="    "+signature+"{"
    assert s.count(anchor)==1,(signature,s.count(anchor))
    start=s.index(anchor)
    opening=s.index("{",start)
    level=0
    for i in range(opening,len(s)):
        if s[i]=="{":level+=1
        elif s[i]=="}":
            level-=1
            if level==0:
                s=s[:start]+body.strip("\n")+s[i+1:]
                return
    raise AssertionError(("unclosed method",signature))

# A single 65-unit toolbar: title, two selectable pages and settings.
# Cards start at y=164, leaving a 6-unit gap below the controls.
# No old full-width, invisible toggle area survives.
replace_method("private void drawShop(Canvas c)",r"""
    private void drawShop(Canvas c){
        v72NineSlice(c,"panel.png",10,93,340,65,255);
        leftFittedText(c,"ЛАВКА / МОДУЛИ",22,117,16,0xffedfffc,217);
        v72NineSlice(c,"button.png",246,102,99,52,255);
        fittedText(c,"НАСТРОЙКИ",295.5f,124,10,0xffe6fffa,91);
        fittedText(c,"ЗВУК / FX",295.5f,140,9,0xffb1e4dd,91);

        v72NineSlice(c,shopPage==0?"button.png":"button_off.png",
            16,130,108,28,shopPage==0?255:190);
        fittedText(c,"БАЗОВЫЕ",70,148,11,
            shopPage==0?0xffe7fffa:0xffa9bbc5,101);
        v72NineSlice(c,shopPage==1?"button.png":"button_off.png",
            128,130,108,28,shopPage==1?255:190);
        fittedText(c,"ТЕХНОЛОГИИ",182,148,10,
            shopPage==1?0xffe7fffa:0xffa9bbc5,101);

        if(settingsOpen){drawAudioSettings(c);return;}
        String[] titles={"КИРКА","АВТОБУР","КРИТ. УДАР","УДАЧА","ЦЕПНАЯ РЕАКЦИЯ","ГЕОЛОГИЯ",
            "ЗАКАЛКА","ТУРБОПРИВОД","ОБОГАЩЕНИЕ","ЗАТОЧКА","КРИСТАЛЛЫ","СЕПАРАТОР"};
        String[] details={"Урон: "+fmt(damage()),"Бур: "+String.format(Locale.US,"%.1f",dps()),
            "Шанс x3: "+Math.min(50,critLevel*3)+"%","Награда +"+(fortuneLevel*12)+"%",
            "Шанс x2: "+Math.min(50,chainLevel*5)+"%","Монеты +"+(geologyLevel*7)+"%",
            "+9% к урону","+11% к бурению","+10% к награде","+4.5% к урону",
            "Бонусные кристаллы","Больше рудной пыли"};
        int[] levels={powerLevel,drillLevel,critLevel,fortuneLevel,chainLevel,geologyLevel,
            tech[0],tech[1],tech[2],tech[3],tech[4],tech[5]};
        for(int i=0;i<6;i++){
            int k=i+(shopPage==1?6:0);
            v71ShopTile(c,10+(i%2)*175,164+(i/2)*153,k,titles[k],details[k],levels[k]);
        }
    }
""")

# v7.3 has already narrowed the settings entry to the old 99..141 rect.
# The new header uses an exact 246..345 x 102..154 rectangle.
once("if(page==1&&x>=241&&x<=345&&y>=99&&y<=141){settingsOpen=true;",
     "if(page==1&&x>=246&&x<=345&&y>=102&&y<=154){settingsOpen=true;")

# Replace the legacy page-toggle with two independently selectable tabs.
# This prevents a tap on the already selected tab from switching pages.
once("""            if(y>=117&&y<157&&x<234){
                shopPage=1-shopPage;invalidate();return true;
            }""",
     """            if(y>=130&&y<=158){
                if(x>=16&&x<=124){shopPage=0;invalidate();return true;}
                if(x>=128&&x<=236){shopPage=1;invalidate();return true;}
            }""")

assert "if(x>=16&&x<=124){shopPage=0;" in s
assert "if(x>=128&&x<=236){shopPage=1;" in s
assert "if(page==1&&x>=246&&x<=345&&y>=102&&y<=154)" in s
assert "shopPage=1-shopPage" not in s
assert s.count("private void drawShop(Canvas c)")==1
assert s.count("v71ShopTile(c,10+(i%2)*175,164+(i/2)*153")==1
assert 'getSharedPreferences("mine_save_v1"' in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
assert 'shahta-save-v1' in (root/"app/src/main/java/com/bezdna/mine/MainActivity.java").read_text()
gradle=(root/"app/build.gradle").read_text()
assert "applicationId 'com.bezdna.mine'" in gradle
assert "signingConfig signingConfigs.shahtaDebug" in gradle
# Geometry contract: painted tabs and settings must remain disjoint; six
# purchase buttons must stay inside separate cards and above the toast.
shop_tabs=[(16,130,124,158),(128,130,236,158)]
settings_rect=(246,102,345,154)
assert shop_tabs[0][2]<shop_tabs[1][0]<settings_rect[0]
assert all(tab[2]<settings_rect[0] for tab in shop_tabs)
shop_cards=[]
for i in range(6):
    x,y=10+(i%2)*175,164+(i//2)*153
    card=(x,y,x+165,y+145)
    buy=(x+13,y+102,x+152,y+138)
    assert card[0]<=buy[0]<buy[2]<=card[2]
    assert card[1]<=buy[1]<buy[3]<=card[3]
    assert buy[3]<623,('purchase overlaps shop toast',i)
    shop_cards.append(card)
for i,a in enumerate(shop_cards):
    for b in shop_cards[i+1:]:
        assert a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1], ('overlapping shop cards',a,b)

source.write_text(s)
print("v7.4: independent shop tabs, no invisible toggle, aligned toolbar and settings; source-only")
