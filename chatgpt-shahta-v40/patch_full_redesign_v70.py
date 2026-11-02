"""Shahta v7.0, complete raster-art gameplay and five-tab UX redesign.

Keeps mining balance, all five feature pages, their real purchasing actions,
SharedPreferences format, JSON import/export, old signing identity and auto-save.
Moves navigation from bottom to the top and rescales every page consistently.
"""
from pathlib import Path
root=Path("chatgpt-shahta-v33/project")
source=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
main=root/"app/src/main/java/com/bezdna/mine/MainActivity.java"
s=source.read_text()

def replace_method(signature, new_code):
    global s
    anchor="    "+signature+"{"
    assert s.count(anchor)==1,(signature,s.count(anchor))
    start=s.index(anchor)
    brace=s.index("{",start)
    level=0
    end=None
    for i in range(brace,len(s)):
        if s[i]=="{":level+=1
        elif s[i]=="}":
            level-=1
            if level==0:
                end=i+1
                break
    assert end is not None,signature
    s=s[:start]+new_code.rstrip()+s[end:]

asset_support=r"""
    // v7.0 raster assets: decode once, reuse each frame, low-memory preview if absent.
    private final java.util.HashMap<String,android.graphics.Bitmap> v70Cache=
        new java.util.HashMap<>();
    private final java.util.HashSet<String> v70Failed=new java.util.HashSet<>();
    private final android.graphics.RectF v70Dst=new android.graphics.RectF();
    private android.graphics.Bitmap v70Asset(String name){
        android.graphics.Bitmap b=v70Cache.get(name);
        if(b!=null&&!b.isRecycled())return b;
        if(v70Failed.contains(name))return null;
        try(java.io.InputStream in=getContext().getAssets().open("shahta_v70/"+name)){
            b=android.graphics.BitmapFactory.decodeStream(in);
            if(b!=null){v70Cache.put(name,b);return b;}
        }catch(java.io.IOException|OutOfMemoryError ex){
            android.util.Log.w("ShahtaV70","Missing asset "+name,ex);
        }
        v70Failed.add(name);
        return null;
    }
    private void v70Draw(Canvas c,String file,float x,float y,float w,float h,int alpha){
        android.graphics.Bitmap b=v70Asset(file);
        if(b==null)return;
        v70Dst.set(x,y,x+w,y+h);
        p.reset();p.setAntiAlias(true);p.setFilterBitmap(true);
        p.setAlpha(Math.max(0,Math.min(255,alpha)));
        c.drawBitmap(b,null,v70Dst,p);
        p.setAlpha(255);
    }
    private static final String[] V70_NAV={"ШАХТА","ЛАВКА","КУЗНЯ","ГИЛЬДИЯ","АТЛАС"};
    private static final String[] V70_ICONS={
      "ore_03.png","ore_01.png","ore_07.png","ore_19.png","ore_22.png"};
"""
anchor="    private void panel(Canvas c,float x,float y,float w,float h,int col){"
assert s.count(anchor)==1
s=s.replace(anchor,asset_support+"\n"+anchor,1)

replace_method("private void panel(Canvas c,float x,float y,float w,float h,int col)",r"""
    private void panel(Canvas c,float x,float y,float w,float h,int col){
        v70Draw(c,"panel.png",x,y,w,h,243);
    }
""")
replace_method("private void button(Canvas c,float x,float y,float w,float h,String title,String sub,boolean enabled)",r"""
    private void button(Canvas c,float x,float y,float w,float h,String title,String sub,boolean enabled){
        v70Draw(c,enabled?"button.png":"button_off.png",x,y,w,h,255);
        text(c,title,x+w/2,y+Math.max(17,h*.36f),12,enabled?0xfff6ebce:0xffc0c6cb,true);
        if(sub!=null&&!sub.isEmpty())
            fittedText(c,sub,x+w/2,y+Math.max(32,h*.72f),10,
                enabled?0xffd9f4ee:0xff9eacb4,w-8);
    }
""")
replace_method("@Override protected void onDraw(Canvas canvas)",r"""
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);
        tick();
        long frame=System.nanoTime();
        if(lastFrameNanos!=0){
            float period=(frame-lastFrameNanos)/1000000000f;
            if(period>.003f&&period<.25f)
                measuredFps=measuredFps*.94f+(1f/period)*.06f;
        }
        lastFrameNanos=frame;
        canvas.save();
        canvas.scale(getWidth()/(float)W,getHeight()/(float)H);
        canvas.drawColor(0xff111d23);
        drawHeader(canvas);
        canvas.save();
        canvas.translate(0,60);
        canvas.scale(1,1.0f);
        canvas.clipRect(0,87,360,653);
        drawPage(canvas,page);
        canvas.restore();
        drawBottom(canvas);
        if(System.currentTimeMillis()<toastUntil){
            panel(canvas,22,139,316,32,0xff405250);
            fittedText(canvas,toast,180,159,12,0xfff6e5c7,290);
        }
        canvas.restore();
        postInvalidateOnAnimation();
    }
""")
replace_method("private void drawPage(Canvas c,int tab)",r"""
    private void drawPage(Canvas c,int tab){
        if(tab==0){
            v70Draw(c,String.format(Locale.US,"biome_%02d.jpg",zone()),
                    0,87,360,566,255);
            drawMine(c);
        }else{
            v70Draw(c,"menu_"+tab+".jpg",0,87,360,566,255);
            if(tab==1)drawShop(c);
            else if(tab==2)drawForge(c);
            else if(tab==3)drawGuild(c);
            else drawCollection(c);
        }
    }
""")
replace_method("private void drawHeader(Canvas c)",r"""
    private void drawHeader(Canvas c){
        v70Draw(c,"header.png",0,0,360,88,255);
        text(c,"D E E P  •  M I N E",180,25,20,0xfff5ddaa,true);
        v70Draw(c,"ore_03.png",10,40,31,31,255);
        v70Draw(c,"ore_07.png",190,40,30,31,255);
        fittedText(c,fmt(coins)+"  МОНЕТ",103,61,14,0xffffdc9a,136);
        fittedText(c,fmt(gems)+"  КРИСТ.",281,61,13,0xffb7ffdb,125);
    }
""")
replace_method("private void drawBottom(Canvas c)",r"""
    // v7.0 top rail; moves all five sections above gameplay, not bottom.
    private void drawBottom(Canvas c){
        v70Draw(c,"nav.png",0,87,360,50,255);
        for(int i=0;i<5;i++){
            float x=4+i*71.1f;
            if(page==i)v70Draw(c,"button.png",x,91,65,40,245);
            else v70Draw(c,"button_off.png",x,91,65,40,196);
            v70Draw(c,V70_ICONS[i],x+22,92,21,22,255);
            text(c,V70_NAV[i],x+32.5f,126,8,
                page==i?0xffffe8ad:0xffc2d0ce,true);
        }
    }
""")
replace_method("private void drawMine(Canvas c)",r"""
    private void drawMine(Canvas c){
        final int biome=zone();
        final int id=ore();
        final int tint=BIOME[biome];
        // New composition: expansive environment and independent fully-textured ore.
        panel(c,18,93,324,66,0xff263c42);
        fittedText(c,"ЭКСПЕДИЦИЯ  •  ГЛУБИНА "+depth,180,115,16,0xfff6dfae,304);
        fittedText(c,ZONES[biome]+"   |   "+ORE_NAMES[id],180,139,11,
            colorBlend(tint,WHITE,.62f),310);
        round(c,28,171,304,5,2,0xff182e34);
        float step=((depth-1)%25+1)/25f;
        rect(c,30,172,300*step,3,colorBlend(tint,0xfff7dfa5,.40f));
        c.save();
        float bob=fxEnabled?(float)Math.sin(time*1.7f)*1.3f:0f;
        c.translate(0,bob);
        // Texture/sprite PNG replaces the original vector silhouette,
        // faceting, vector pickaxe and decorative particle rings.
        v70Draw(c,String.format(Locale.US,"ore_%02d.png",id),
                47,203,266,249,255);
        v70Draw(c,"fractures.png",47,203,266,249,
            (int)(Math.max(0f,Math.min(1f,1-rockHp/(float)Math.max(1,rockMax)))*210));
        if(guardian())v70Draw(c,"ore_09.png",115,247,130,127,110);
        if(treasure())v70Draw(c,"ore_03.png",112,282,140,129,145);
        if(geode())v70Draw(c,"ore_07.png",118,270,125,126,160);
        c.restore();
        if(combo>=2&&comboTimer>0){
            panel(c,24,184,118,27,0xff4b5849);
            text(c,"СЕРИЯ  x"+combo,83,202,12,0xfff7df9c,true);
        }
        if(depthBanner>0&&transition>.2f){
            panel(c,85,405,190,33,0xff4b5849);
            fittedText(c,"НОВАЯ ГЛУБИНА  "+depth,180,426,13,0xfffae5b7,180);
        }
        panel(c,18,457,324,119,0xff223b45);
        fittedText(c,guardian()?"СТРАЖ ГЛУБИНЫ":treasure()?"СОКРОВИЩЕ":geode()?"РЕДКАЯ ГЕОДА":
            modifier()>0?MOD_NAMES[modifier()]:"ПРОЧНОСТЬ РУДЫ",
            180,479,12,guardian()?0xffffac8c:0xffd8f3e6,306);
        fittedText(c,wholeHp(Math.max(0,rockHp))+" / "+wholeHp(rockMax),
            180,500,17,0xfff9f1d8,306);
        bar(c,28,512,304,13,displayedHpRatio,
            guardian()?0xffee865e:colorBlend(tint,0xff8aeab4,.44f));
        fittedText(c,"УРОН "+fmt(damage())+"   •   БУР "+
            String.format(Locale.US,"%.1f",dps())+"/с",
            180,549,12,0xfff4e6c7,314);
        fittedText(c,richVein()?"БОГАТАЯ ЖИЛА • x3 МОНЕТЫ":
            guardian()?"ПОБЕДИ СТРАЖА ДО ИСТЕЧЕНИЯ ВРЕМЕНИ":
            modifier()==4&&volatileSeconds>0?"НЕСТАБИЛЬНАЯ ПОРОДА":
            "ОТКРЫТЫХ БИОМОВ: "+discovered+" / 24",
            180,566,10,0xffbddbd7,316);
        if(guardian()){
            long left=Math.max(0,(bossDeadline-System.currentTimeMillis()+999)/1000);
            fittedText(c,"СТРАЖ:  "+left+" СЕК.  •  БОССОВ: "+bossVictories,
                180,597,11,left<15?0xffff9b88:0xffffdea3,314);
        }else{
            fittedText(c,trialDeadline>0?"ИСПЫТАНИЕ • "+
                Math.max(0,(trialDeadline-System.currentTimeMillis())/1000)+" СЕК.":
                crystalSurgeTime>0?"РЕЗОНАНС • "+(int)crystalSurgeTime+" СЕК.":
                "СЛЕДУЮЩАЯ ЗОНА ЧЕРЕЗ "+(25-(depth-1)%25)+" УР.",
                180,597,11,0xfff5dea9,316);
        }
        powerButton(c,16,610,104,"ФОРСАЖ",
            boostTime>0?"АКТИВНО "+(int)boostTime+"с":
            boostCd>0?"ЖДАТЬ "+(int)boostCd+"с":"x3 АВТОБУР",depth>=5&&boostCd<=0);
        powerButton(c,128,610,104,"ВЗРЫВ",
            blastCd>0?"ЖДАТЬ "+(int)blastCd+"с":"-45% HP",depth>=12&&blastCd<=0);
        powerButton(c,240,610,104,"МАГНИТ",
            magnetTime>0?"АКТИВНО "+(int)magnetTime+"с":
            magnetCd>0?"ЖДАТЬ "+(int)magnetCd+"с":"x2.5 МОНЕТ",depth>=25&&magnetCd<=0);
        for(Popup f:popups){
            if(f.y>205&&f.y<445){
                float a=Math.max(0,Math.min(1,f.life/.95f));
                text(c,f.value,f.x,f.y,14,
                    (f.color&0xffffff)|((int)(a*255)<<24),true);
            }
        }
    }
""")
replace_method("private void powerButton(Canvas c,int x,int y,int w,String title,String sub,boolean enabled)",r"""
    private void powerButton(Canvas c,int x,int y,int w,String title,String sub,boolean enabled){
        v70Draw(c,enabled?"button.png":"button_off.png",x,y,w,35,255);
        text(c,title,x+w/2f,y+15,11,
            enabled?0xffffe4ac:0xffbfc3ca,true);
        fittedText(c,sub,x+w/2f,y+28,9,0xffe0edeb,w-8);
    }
""")
replace_method("private void shopRow(Canvas c,int y,int k,String icon,String title,String detail,int level,int accent)",r"""
    private void shopRow(Canvas c,int y,int k,String icon,String title,String detail,int level,int accent){
        panel(c,13,y,334,73,0xff324555);
        v70Draw(c,String.format(Locale.US,"ore_%02d.png",k%24),
            23,y+11,53,51,255);
        leftFittedText(c,title,81,y+21,12,0xfff7ebd2,148);
        leftFittedText(c,detail,81,y+41,10,0xffc5d2d1,149);
        text(c,"УРОВЕНЬ "+level,81,y+58,10,colorBlend(accent,WHITE,.20f),false);
        drawV63RankTrack(c,81,y+64,133,level,0,accent);
        button(c,236,y+12,102,49,"УЛУЧШИТЬ",fmt(cost(k))+" G",coins>=cost(k));
    }
""")
replace_method("private void drawV43Sigil(Canvas c,float cx,float cy,int kind,int tint)",r"""
    private void drawV43Sigil(Canvas c,float cx,float cy,int kind,int tint){
        v70Draw(c,String.format(Locale.US,"ore_%02d.png",Math.abs(kind)%24),
            cx-21,cy-21,42,42,255);
    }
""")
replace_method("private void drawV43AtlasThumbnail(Canvas c,float cx,float cy,int biome)",r"""
    private void drawV43AtlasThumbnail(Canvas c,float cx,float cy,int biome){
        c.save();
        c.clipRect(cx-23,cy-23,cx+23,cy+23);
        v70Draw(c,String.format(Locale.US,"biome_%02d.jpg",Math.max(0,Math.min(23,biome))),
            cx-26,cy-31,52,75,255);
        c.restore();
    }
""")
assert s.count("    @Override public boolean onTouchEvent(MotionEvent e){")==1
old="        float x=e.getX()*W/Math.max(1,getWidth()),y=e.getY()*H/Math.max(1,getHeight());"
assert s.count(old)==1
new=r"""        float x=e.getX()*W/Math.max(1,getWidth());
        float screenY=e.getY()*H/Math.max(1,getHeight());
        if(screenY>=88&&screenY<=136){
            int next=clamp((int)(x/72f),0,4);
            if(page!=next){
                previousPage=page;page=next;pageSlide=1f;
                toastUntil=0;screenFlash=0;pressPulse=1f;
            }
            invalidate();return true;
        }
        // Every page is moved down 60 units without shrinking; controls remain finger-sized.
        // Map all controls and settings back into their original logical geometry.
        float y=(screenY-60f)/1.0f;"""
s=s.replace(old,new,1)
assert "if(y>=651){" in s
s=s.replace("if(y>=651){","if(y>=900){",1)
oldmine="else if(x>=34&&x<=328&&y>=173&&y<=508){"
assert s.count(oldmine)==1
s=s.replace(oldmine,"else if(x>=52&&x<=308&&y>=201&&y<=455){",1)
# Power controls retain original dimensions / hit targets.
oldpower="if(y>=611&&y<=648){activatePower"
assert s.count(oldpower)==1
s=s.replace(oldpower,"if(y>=609&&y<=648){activatePower",1)
s=s.replace("private static final Typeface GAME_FONT=Typeface.create(\"sans-serif-condensed\",Typeface.BOLD);",
            "private static final Typeface GAME_FONT=Typeface.create(\"sans-serif-medium\",Typeface.BOLD);",1)
# Keep original MainActivity and its imported/exported JSON save protocol intact.
assert 'shahta-save-v1' in main.read_text()
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
assert "getSharedPreferences(\"mine_save_v1\"" in s
assert s.count("private void drawMine(Canvas c)")==1
assert s.count("private void drawBottom(Canvas c)")==1
assert s.count("private void v70Draw(")==1
assert "if(screenY>=88&&screenY<=136)" in s
g=gradle.read_text()
assert "versionCode 46" in g and "versionName '6.9'" in g
assert "applicationId 'com.bezdna.mine'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
source.write_text(s)
gradle.write_text(g.replace("versionCode 46","versionCode 48")
                    .replace("versionName '6.9'","versionName '7.0.1'"))
print("v7.0: entire five-tab UI reskinned, top navigation reflowed with hitboxes, "
      "textured ore/caves, material menus; same saves/balance/signature")