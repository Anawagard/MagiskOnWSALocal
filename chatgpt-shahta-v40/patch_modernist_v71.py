"""v7.1 modernist visual layout pass; source-only, never compiles or publishes APK.

Applies after patch_full_redesign_v70.py. Preserves gameplay, persistence,
package ID, signing configuration, JSON import/export and existing balance.
"""
from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
src=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=src.read_text()

def once(old,new):
    global s
    n=s.count(old)
    assert n==1,("layout anchor missing or duplicated",old[:110],n)
    s=s.replace(old,new,1)

def replace_method(signature,body):
    global s
    anchor="    "+signature+"{"
    assert s.count(anchor)==1,(signature,s.count(anchor))
    start=s.index(anchor)
    opening=s.index("{",start)
    depth=0
    end=None
    for i in range(opening,len(s)):
        if s[i]=="{":depth+=1
        elif s[i]=="}":
            depth-=1
            if depth==0:
                end=i+1
                break
    assert end is not None,signature
    s=s[:start]+body.strip("\n")+s[end:]

# Preserve original artwork proportions across tall/narrow Android displays.
# The same inverse transform must be applied to touch coordinates.
geometry=r"""
    private float v71Scale(){
        return Math.max(.01f,Math.min(getWidth()/(float)W,getHeight()/(float)H));
    }
    private float v71OffsetX(){return (getWidth()-W*v71Scale())*.5f;}
    private float v71OffsetY(){return (getHeight()-H*v71Scale())*.5f;}
"""
once("    private void panel(Canvas c,float x,float y,float w,float h,int col){",
     geometry+"\n    private void panel(Canvas c,float x,float y,float w,float h,int col){")
once("        canvas.scale(getWidth()/(float)W,getHeight()/(float)H);",
     "        canvas.translate(v71OffsetX(),v71OffsetY());\n"
     "        canvas.scale(v71Scale(),v71Scale());")
once("""        float x=e.getX()*W/Math.max(1,getWidth());
        float screenY=e.getY()*H/Math.max(1,getHeight());""",
     """        float x=(e.getX()-v71OffsetX())/v71Scale();
        float screenY=(e.getY()-v71OffsetY())/v71Scale();
        if(x<0||x>=W||screenY<0||screenY>=H)return true;""")

# A real textured miner becomes part of the composition; the ore is shifted
# to the right. The interactive rock rectangle follows the new sprite.
once("""        v70Draw(c,String.format(Locale.US,"ore_%02d.png",id),
                47,203,266,249,255);
        v70Draw(c,"fractures.png",47,203,266,249,""",
     """        v70Draw(c,"miner.png",15,293,113,160,255);
        v70Draw(c,String.format(Locale.US,"ore_%02d.png",id),
                105,210,225,230,255);
        v70Draw(c,"fractures.png",105,210,225,230,""")
once("else if(x>=52&&x<=308&&y>=201&&y<=455){",
     "else if(x>=105&&x<=330&&y>=210&&y<=440){")

# Dim textured menu scenes behind content, without blurring the artwork.
once('            v70Draw(c,"menu_"+tab+".jpg",0,87,360,566,255);',
     '            v70Draw(c,"menu_"+tab+".jpg",0,87,360,566,255);\n'
     '            rect(c,0,87,360,566,0x8808111d);')

# Modern two-column shop: each purchase button has its own aligned hitbox.
replace_method("private void drawShop(Canvas c)",r"""
    private void drawShop(Canvas c){
        panel(c,10,95,340,60,0xff142b3c);
        text(c,"ЛАВКА / МОДУЛИ",116,117,17,0xffe4f8f4,true);
        button(c,241,99,104,42,"НАСТРОЙКИ","ЗВУК / FX",true);
        if(settingsOpen){drawAudioSettings(c);return;}
        button(c,13,119,215,35,
            shopPage==0?"ОСНОВНЫЕ  →":"ТЕХНОЛОГИИ  ←","",true);
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
shop_tile=r"""
    private void v71ShopTile(Canvas c,int x,int y,int k,
                             String title,String detail,int level){
        panel(c,x,y,165,145,0xff1c2f41);
        v70Draw(c,String.format(Locale.US,"ore_%02d.png",k%24),
            x+10,y+10,53,53,255);
        leftFittedText(c,title,x+67,y+29,12,0xffe9fbf6,91);
        leftFittedText(c,"УР. "+level,x+67,y+47,11,0xff92e5d9,91);
        fittedText(c,detail,x+82,y+80,10,0xffd0e4e4,149);
        drawV63RankTrack(c,x+15,y+91,135,level,0,0xff58dfce);
        button(c,x+13,y+102,139,36,"УЛУЧШИТЬ",
            fmt(cost(k))+" G",coins>=cost(k));
    }
"""
once("    private void drawShop(Canvas c){",shop_tile+"\n    private void drawShop(Canvas c){")
once("if(page==1&&x>=235&&y>=80&&y<=112)",
     // Match the painted settings button (241,99,104,42) exactly.
     // The previous oversized region accepted invisible edge taps.
     "if(page==1&&x>=241&&x<=345&&y>=99&&y<=141)")
once("""            if(y>=96&&y<144){shopPage=1-shopPage;invalidate();return true;}
            int[] yy={145,226,307,388,469,550};
            for(int i=0;i<6;i++)if(y>=yy[i]&&y<yy[i]+73&&x>225){
                int k=shopPage==1?i+6:i;""",
     """            if(y>=117&&y<157&&x<234){
                shopPage=1-shopPage;invalidate();return true;
            }
            for(int i=0;i<6;i++){
                int xx=10+(i%2)*175, yy=164+(i/2)*153;
                if(x<xx+13||x>xx+152||y<yy+102||y>yy+138)continue;
                int k=shopPage==1?i+6:i;""")

# Remove the old gold visual hierarchy on the remaining three pages while
# retaining all their existing upgrade controls and touch geometry.
for title,baseline in [("КУЗНЯ БЕЗДНЫ",113),
                       ("ГИЛЬДИЯ ИСКАТЕЛЕЙ",112),
                       ("АТЛАС ПОДЗЕМЕЛИЙ",113)]:
    once('text(c,"'+title+'",180,'+str(baseline)+',19,GOLD,true);',
         'text(c,"'+title+'",180,'+str(baseline)+',18,0xffd9f8f3,true);')

assert s.count("private void v71ShopTile(")==1
assert s.count("private float v71Scale(")==1
assert "v70Draw(c,\"miner.png\",15,293,113,160,255)" in s
assert "if(screenY>=88&&screenY<=136)" in s
assert "if(page==1&&x>=241&&x<=345&&y>=99&&y<=141)" in s
assert "getSharedPreferences(\"mine_save_v1\"" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
assert 'shahta-save-v1' in (root/"app/src/main/java/com/bezdna/mine/MainActivity.java").read_text()
assert "applicationId 'com.bezdna.mine'" in gradle.read_text()
assert "signingConfig signingConfigs.shahtaDebug" in gradle.read_text()
src.write_text(s)
print("v7.1 modernist: miner sprite, asymmetrical mine, 2x3 shop grid and "
      "aligned purchases, unified scaling/touch transform, readable menus.")
