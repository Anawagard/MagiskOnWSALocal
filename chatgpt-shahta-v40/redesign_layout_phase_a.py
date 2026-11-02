"""Full redesign phase A: textured scene, asymmetrical ore/miner, new shop grid and HUD.
No APK compilation, version bump, gameplay or save-schema change.
"""
from pathlib import Path
import re
p=Path("chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MineView.java")
s=p.read_text()
def method(name,body):
    global s
    m=re.search(r"(?m)^    private void "+re.escape(name)+r"\s*\(",s)
    assert m is not None,name
    start=m.start();opening=s.index("{",m.end());level=1;end=opening+1
    while level:
        if s[end]=="{":level+=1
        elif s[end]=="}":level-=1
        end+=1
    s=s[:start]+body.strip("\n")+"\n"+s[end:]
def once(a,b):
    global s
    assert s.count(a)==1,(a[:100],s.count(a))
    s=s.replace(a,b,1)
art=r"""
    private final android.graphics.Bitmap[] v70Caves=new android.graphics.Bitmap[24];
    private final android.graphics.Bitmap[] v70Ores=new android.graphics.Bitmap[24];
    private final boolean[] v70CaveLoaded=new boolean[24],v70OreLoaded=new boolean[24];
    private android.graphics.Bitmap v70Miner,v70Plate;
    private boolean v70MinerLoaded,v70PlateLoaded;
    private final android.graphics.Rect v70Src=new android.graphics.Rect();
    private final android.graphics.RectF v70Dst=new android.graphics.RectF();
    private android.graphics.Bitmap v70Decode(String name){
        try(java.io.InputStream input=getContext().getAssets().open("shahta_redesign/"+name)){
            return android.graphics.BitmapFactory.decodeStream(input);
        }catch(java.io.IOException ex){
            android.util.Log.w("ShahtaArt","Missing raster artwork: "+name,ex);
            return null;
        }
    }
    private void v70Bitmap(Canvas c,android.graphics.Bitmap bitmap,float x,float y,float w,float h,int alpha){
        if(bitmap==null||bitmap.isRecycled())return;
        v70Src.set(0,0,bitmap.getWidth(),bitmap.getHeight());
        v70Dst.set(x,y,x+w,y+h);
        p.reset();p.setAntiAlias(true);p.setFilterBitmap(true);
        p.setAlpha(alpha);c.drawBitmap(bitmap,v70Src,v70Dst,p);p.setAlpha(255);
    }
    private void v70Cave(Canvas c,int biome){
        final int id=Math.max(0,Math.min(23,biome));
        if(!v70CaveLoaded[id]){v70CaveLoaded[id]=true;
            v70Caves[id]=v70Decode(String.format(Locale.US,"cave_%02d.png",id));}
        if(v70Caves[id]!=null)v70Bitmap(c,v70Caves[id],0,88,360,563,255);
        else rect(c,0,88,360,563,colorBlend(BIOME[id],0xff102030,.83f));
    }
    private void v70Ore(Canvas c,int ore,float x,float y,float w,float h){
        final int id=Math.max(0,Math.min(23,ore));
        if(!v70OreLoaded[id]){v70OreLoaded[id]=true;
            v70Ores[id]=v70Decode(String.format(Locale.US,"ore_%02d.png",id));}
        if(v70Ores[id]!=null)v70Bitmap(c,v70Ores[id],x,y,w,h,255);
        else {p.reset();p.setAntiAlias(true);p.setColor(ORE[id]);
            c.drawOval(x+15,y+15,x+w-15,y+h-15,p);}
    }
    private void v70Miner(Canvas c,float x,float y,float w,float h){
        if(!v70MinerLoaded){v70MinerLoaded=true;v70Miner=v70Decode("miner.png");}
        v70Bitmap(c,v70Miner,x,y,w,h,255);
    }
    private void v70Plate(Canvas c,float x,float y,float w,float h){
        if(!v70PlateLoaded){v70PlateLoaded=true;v70Plate=v70Decode("plate.png");}
        if(v70Plate!=null)v70Bitmap(c,v70Plate,x,y,w,h,255);
        else round(c,x,y,w,h,12,0xff263947);
    }
"""
once("    private void drawPage(Canvas c,int tab){",art+"\n    private void drawPage(Canvas c,int tab){")
method("drawPage",r"""
    private void drawPage(Canvas c,int tab){
        if(tab!=0){v70Cave(c,(zone()+tab*4)%24);rect(c,0,88,360,563,0x9907131e);}
        if(tab==0)drawMine(c);else if(tab==1)drawShop(c);
        else if(tab==2)drawForge(c);else if(tab==3)drawGuild(c);else drawCollection(c);
    }
""")
method("drawHeader",r"""
    private void drawHeader(Canvas c){
        rect(c,0,0,360,88,0xff101c28);
        v70Plate(c,6,4,348,80);
        text(c,"ШАХТА / ЭКСПЕДИЦИЯ",180,26,18,0xfff7e8c9,true);
        v70Plate(c,12,34,166,43);v70Plate(c,182,34,166,43);
        fittedText(c,"●  "+fmt(coins)+" МОНЕТ",95,60,13,0xfff5cf7b,153);
        fittedText(c,"◆  "+fmt(gems)+" КРИСТ.",264,60,13,0xff95f4e1,151);
    }
""")
method("drawBottom",r"""
    private void drawBottom(Canvas c){
        rect(c,0,650,360,70,0xff101c28);
        v70Plate(c,3,651,354,66);
        nav(c,5,61,0,"ШАХТА","⛏");
        nav(c,67,65,1,"РОСТ","✚");
        nav(c,136,78,2,"КУЗНЯ","◆");
        nav(c,218,66,3,"ГИЛЬДИЯ","✦");
        nav(c,287,68,4,"МИР","▣");
    }
""")
method("nav",r"""
    private void nav(Canvas c,int x,int w,int tab,String title,String ico){
        boolean selected=page==tab;
        if(selected){v70Plate(c,x,655,w,57);rect(c,x+8,656,w-16,3,0xffefb85e);}
        text(c,ico,x+w/2f,679,20,selected?0xffffd78e:0xff90b3bb,true);
        text(c,title,x+w/2f,702,10,selected?0xfffff2d4:0xff9cb6bf,true);
    }
""")
method("panel",r"""
    private void panel(Canvas c,float x,float y,float w,float h,int col){
        v70Plate(c,x,y,w,h);
    }
""")
method("button",r"""
    private void button(Canvas c,float x,float y,float w,float h,String title,String sub,boolean enabled){
        v70Plate(c,x,y,w,h);
        if(enabled)rect(c,x+9,y+2,Math.max(0,w-18),2,0xffd8ad66);
        fittedText(c,title,x+w/2f,y+(sub.isEmpty()?h*.62f:h*.40f),
            h<31?11:12,enabled?0xfff8e3b7:0xff899aa6,Math.max(12,w-9));
        if(!sub.isEmpty())fittedText(c,sub,x+w/2f,y+h*.78f,
            h<35?9:10,enabled?0xffd3e2d8:0xff7c929e,Math.max(12,w-8));
    }
""")
method("drawMine",r"""
    private void drawMine(Canvas c){
        final int biome=zone();final int tint=BIOME[biome];
        v70Cave(c,biome);
        v70Plate(c,10,96,340,78);
        fittedText(c,ZONES[biome],180,121,18,0xfff9ead0,315);
        fittedText(c,"ГЛУБИНА "+depth+"  ·  "+ORE_NAMES[ore()],180,143,12,0xffc6e6df,316);
        drawV55BiomeProgress(c,biome);
        v70Plate(c,12,183,336,311);
        c.save();c.clipRect(17,188,343,488);
        v70Cave(c,biome);
        v70Miner(c,17,285,126,198);
        c.save();
        if(shake>0)c.translate((float)Math.sin(time*83)*shake*.35f,0);
        drawRock(c,ore(),tint);
        c.restore();
        if(combo>=2&&comboTimer>0)fittedText(c,"СЕРИЯ x"+combo,231,215,15,0xffffd488,180);
        if(richVein())fittedText(c,"БОГАТАЯ ЖИЛА x3",222,467,12,0xffbaf7dc,190);
        for(Popup f:popups)if(f.y>=190&&f.y<470)
            fittedText(c,f.value,Math.max(40,Math.min(320,f.x)),f.y,13,f.color,170);
        c.restore();
        v70Plate(c,10,502,340,89);
        fittedText(c,guardian()?"СТРАЖ ГЛУБИНЫ":treasure()?"СУНДУК СОКРОВИЩ":
            geode()?"РЕДКАЯ ГЕОДА":"ПРОЧНОСТЬ РУДЫ",180,523,13,
            guardian()?0xffff9d86:0xfff1dba7,325);
        fittedText(c,wholeHp(Math.max(0,rockHp))+" / "+wholeHp(rockMax),180,544,14,WHITE,320);
        bar(c,29,551,302,13,displayedHpRatio,guardian()?0xfff27d72:tint);
        fittedText(c,"УРОН "+fmt(damage())+"   ·   БУР "+String.format(Locale.US,"%.1f",dps())+"/с",
            180,581,12,0xffe2eceb,317);
        powerButton(c,9,600,109,"ФОРСАЖ",boostTime>0?"АКТИВНО":boostCd>0?"ЖДАТЬ":"x3 АВТОБУР",depth>=5&&boostCd<=0);
        powerButton(c,126,600,109,"ВЗРЫВ",blastCd>0?"ЖДАТЬ":"-45% HP",depth>=12&&blastCd<=0);
        powerButton(c,243,600,109,"МАГНИТ",magnetTime>0?"АКТИВНО":magnetCd>0?"ЖДАТЬ":"x2.5 МОНЕТ",depth>=25&&magnetCd<=0);
    }
""")
method("drawRock",r"""
    private void drawRock(Canvas c,int id,int theme){
        final float bob=fxEnabled?(float)Math.sin(time*1.1f)*2f:0f;
        v70Ore(c,id,109,221+bob,229,237);
        if(guardian())fittedText(c,"СТРАЖ",221,244,14,0xffffb5a0,160);
    }
""")
method("powerButton",r"""
    private void powerButton(Canvas c,int x,int y,int w,String title,String sub,boolean enabled){
        button(c,x,y,w,43,title,sub,enabled);
    }
""")
method("drawShop",r"""
    private void drawShop(Canvas c){
        v70Plate(c,10,95,340,57);
        text(c,"МАСТЕРСКАЯ",114,119,19,0xfff9dfac,true);
        button(c,241,99,104,41,"НАСТРОЙКИ","ЗВУК / FX",true);
        if(settingsOpen){drawAudioSettings(c);return;}
        button(c,13,119,215,35,shopPage==0?"ОСНОВНЫЕ  →":"ТЕХНОЛОГИИ  ←","",true);
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
            v70ShopTile(c,10+(i%2)*175,165+(i/2)*153,k,titles[k],details[k],levels[k]);
        }
    }
    private void v70ShopTile(Canvas c,int x,int y,int k,String title,String detail,int level){
        v70Plate(c,x,y,165,145);
        v70Ore(c,k,x+10,y+11,51,51);
        leftFittedText(c,title,x+67,y+29,12,0xfff9e3b8,91);
        leftFittedText(c,"УР. "+level,x+67,y+47,11,0xff9de7d5,91);
        fittedText(c,detail,x+82,y+81,11,0xffd0dedb,149);
        drawV63RankTrack(c,x+15,y+91,135,level,0,BIOME[k%24]);
        button(c,x+13,y+102,139,36,"УЛУЧШИТЬ",fmt(cost(k))+" G",coins>=cost(k));
    }
""")
once("if(page==1&&x>=235&&y>=80&&y<=112)","if(page==1&&x>=235&&y>=95&&y<=144)")
once("        if(y>=651){\n            int next=clamp((int)(x/72),0,4);",
     "        if(y>=651){\n            int next=x<66?0:x<135?1:x<216?2:x<286?3:4;")
once("if(y>=611&&y<=648){activatePower(x<124?0:x<236?1:2);}",
     "if(y>=600&&y<=646){activatePower(x<122?0:x<240?1:2);}")
once("else if(x>=34&&x<=328&&y>=173&&y<=508){",
     "else if(x>=110&&x<=340&&y>=217&&y<=480){")
once("""            if(y>=96&&y<144){shopPage=1-shopPage;invalidate();return true;}
            int[] yy={145,226,307,388,469,550};
            for(int i=0;i<6;i++)if(y>=yy[i]&&y<yy[i]+73&&x>225){
                int k=shopPage==1?i+6:i;""",
     """            if(y>=117&&y<157&&x<234){shopPage=1-shopPage;invalidate();return true;}
            for(int i=0;i<6;i++){
                int xx=10+(i%2)*175, yy=165+(i/2)*153;
                if(x<xx+13||x>xx+152||y<yy+101||y>yy+142)continue;
                int k=shopPage==1?i+6:i;""")
assert s.count("private void v70ShopTile(")==1
assert s.count("private void drawRock(")==1
assert "public void save()" in s and "private void rebirth()" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "private int zoneNo(){return (depth-1)/25;}" in s
p.write_text(s)
print("New mine/shop composition and touch geometry applied without save changes")
