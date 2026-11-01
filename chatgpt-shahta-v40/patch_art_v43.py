from pathlib import Path
import re

root=Path("chatgpt-shahta-v33/project")
src=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=src.read_text()

def replace_once(old,new):
    global s
    n=s.count(old)
    assert n==1, ("expected unique visual hook",old[:110],n)
    s=s.replace(old,new,1)

def java_method(name,visibility="private"):
    m=re.search(r"(?m)^    "+visibility+r"\s+void\s+"+re.escape(name)+r"\s*\(",s)
    assert m is not None,name
    opening=s.index("{",m.end()); level=1;end=opening+1
    while level:
        if s[end]=="{":level+=1
        elif s[end]=="}":level-=1
        end+=1
    return s[m.start():end]

before={n:java_method(n,v) for n,v in [
    ("save","public"),("rebirth","private"),("onTouchEvent","public") ] if n!="onTouchEvent"}
# The touch handler is @Override public boolean; its source remains unchanged by design.
touch_before=s[s.index("    @Override public boolean onTouchEvent("):]

art=r"""
    private void drawV43PageAtmosphere(Canvas c,int tab){
        int[] accents={0xff9cd9d0,0xffe8b97d,0xffb8a0f3,0xff80d2c5,0xff8dc3ed};
        int tint=accents[Math.max(0,Math.min(4,tab))];
        grad(c,0,88,360,563,0xff111f2e,0xff08121f);
        p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
        for(int i=0;i<6;i++){
            p.setStrokeWidth(i%2==0?1.1f:.6f);
            p.setColor(i%2==0?0x2279bdc5:0x226b859b);
            float r=72+i*38;
            c.drawCircle(180,390,r,p);
        }
        p.setStyle(Paint.Style.FILL);
        for(int i=0;i<23;i++){
            float x=(i*73+tab*29)%360,y=96+(i*97+tab*17)%550;
            p.setColor((tint&0xffffff)|0x33000000);
            c.drawCircle(x,y,1.4f+(i%3)*.55f,p);
        }
        // Corner engravings and vertical rule align the whole interface.
        rect(c,8,99,2,533,0x448fbcb4);
        rect(c,350,99,2,533,0x448fbcb4);
        for(int j=0;j<10;j++){
            float y=109+j*53;
            polygon(c,new float[]{8,y,14,y+5,8,y+10},0x5585bdb8);
            polygon(c,new float[]{352,y,346,y+5,352,y+10},0x5585bdb8);
        }
    }

    private void drawV43Sigil(Canvas c,float cx,float cy,int kind,int tint){
        int type=Math.abs(kind)%6;
        p.reset();p.setAntiAlias(true);
        p.setColor(0xff0a1b28);c.drawCircle(cx,cy,20,p);
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.8f);
        p.setColor(tint);c.drawCircle(cx,cy,18,p);
        p.setColor(0x77d4e5dd);p.setStrokeWidth(.7f);
        c.drawCircle(cx,cy,15,p);
        p.setStyle(Paint.Style.FILL);
        if(type==0){
            line(c,cx-9,cy+10,cx+9,cy-10,tint,4);
            polygon(c,new float[]{cx-14,cy-9,cx-3,cy-14,cx+14,cy-9,cx+6,cy-5,cx-7,cy-5},
                colorBlend(tint,WHITE,.38f));
        }else if(type==1){
            for(int j=0;j<8;j++){
                float a=(float)(j*Math.PI/4);
                line(c,cx+(float)Math.cos(a)*8,cy+(float)Math.sin(a)*8,
                    cx+(float)Math.cos(a)*14,cy+(float)Math.sin(a)*14,tint,3);
            }
            p.setColor(tint);c.drawCircle(cx,cy,9,p);
            p.setColor(0xff102332);c.drawCircle(cx,cy,4,p);
        }else if(type==2){
            polygon(c,new float[]{cx,cy-14,cx+5,cy-4,cx+14,cy,cx+5,cy+5,
                cx,cy+14,cx-5,cy+5,cx-14,cy,cx-5,cy-4},tint);
            polygon(c,new float[]{cx,cy-11,cx+4,cy,cx,cy+6,cx-4,cy},
                colorBlend(tint,WHITE,.63f));
        }else if(type==3){
            for(int j=0;j<4;j++){
                float a=(float)(j*Math.PI/2);
                p.setColor(tint);
                c.drawCircle(cx+(float)Math.cos(a)*6,cy+(float)Math.sin(a)*6,5,p);
            }
            p.setColor(0xffffe5b2);c.drawCircle(cx,cy,3,p);
        }else if(type==4){
            p.setColor(tint);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(4);
            c.drawOval(cx-14,cy-6,cx+2,cy+7,p);
            c.drawOval(cx-2,cy-7,cx+14,cy+6,p);
            p.setStyle(Paint.Style.FILL);
        }else{
            polygon(c,new float[]{cx-14,cy+9,cx-10,cy-5,cx-1,cy-13,
                cx+7,cy-3,cx+13,cy+9},tint);
            line(c,cx-12,cy+4,cx+12,cy+4,0xff0d2c3b,2);
            line(c,cx-7,cy-3,cx+6,cy-3,0x88ffffff,1.5f);
        }
        p.reset();p.setAntiAlias(true);p.setColor(0x77ffffff);
        c.drawCircle(cx-12,cy-13,1.6f,p);
    }

    private void drawV43AtlasThumbnail(Canvas c,float cx,float cy,int biome){
        c.save();c.clipRect(cx-24,cy-24,cx+24,cy+24);
        int tint=BIOME[biome%BIOME.length];
        grad(c,cx-24,cy-24,48,48,colorBlend(tint,0xff12273a,.78f),0xff07131d);
        polygon(c,new float[]{cx-24,cy+10,cx-13,cy-9,cx-1,cy+7,cx+13,cy-15,
            cx+24,cy+4,cx+24,cy+24,cx-24,cy+24},0xff1b3540);
        polygon(c,new float[]{cx-24,cy+18,cx-9,cy+2,cx+5,cy+18,
            cx+19,cy+1,cx+24,cy+11,cx+24,cy+24,cx-24,cy+24},
            colorBlend(tint,0xff0b2330,.68f));
        drawOreCrystal(c,cx+1,cy+5,9,tint,fxEnabled?(float)Math.sin(time*2):.5f);
        c.restore();
    }
"""
anchor="    private void drawShop(Canvas c){"
replace_once(anchor,art+"\n"+anchor)
replace_once("""    private void drawPage(Canvas c,int tab){
        if(tab==0)drawMine(c);""",
"""    private void drawPage(Canvas c,int tab){
        if(tab!=0)drawV43PageAtmosphere(c,tab);
        if(tab==0)drawMine(c);""")
# Twelve temporary upgrades and the permanent relics now have real vector sigils.
replace_once('        text(c,icon,47,y+44,23,accent,true);',
             '        drawV43Sigil(c,47,y+37,k,accent);')
replace_once('        text(c,icon,55,y+58,30,tint,true);',
             '        drawV43Sigil(c,55,y+47,k+12,tint);')
replace_once('            text(c,"✦",45,y+43,26,colors[k],true);',
             '            drawV43Sigil(c,45,y+38,k+18,colors[k]);')
replace_once('            text(c,"◆",47,y+43,24,colors[k],true);',
             '            drawV43Sigil(c,47,y+36,k+24,colors[k]);')
# Atlas thumbnails show a miniature scene for each discovered biome.
replace_once('            if(unlocked){drawOreCrystal(c,53,y+39,15,BIOME[bi],(float)Math.sin(time*2+i));}',
             '            if(unlocked){drawV43AtlasThumbnail(c,53,y+38,bi);}')
# Volume slider is now a segmented metal-and-glass bar; interaction is unchanged.
old="""        Paint volumeTrack=new Paint(3);
        volumeTrack.setColor(0xff44566f);
        c.drawRoundRect(55,393,305,400,3.5f,3.5f,volumeTrack);
        volumeTrack.setColor(soundEnabled?0xff81dccc:0xff8192a5);
        if(soundVolume>0)c.drawRoundRect(55,393,55+2.5f*soundVolume,400,3.5f,3.5f,volumeTrack);
        volumeTrack.setColor(0xfff7e7bb);
        float volumeThumb=55+2.5f*soundVolume;
        c.drawCircle(volumeThumb,396.5f,6.5f,volumeTrack);"""
new="""        bar(c,55,393,250,8,soundVolume/100f,
            soundEnabled?0xff77d9d1:0xff7d94a3);
        float volumeThumb=55+2.5f*soundVolume;
        p.reset();p.setAntiAlias(true);p.setColor(0xffffe4a7);
        c.drawCircle(volumeThumb,397,7,p);
        p.setColor(0xff314552);c.drawCircle(volumeThumb,397,3,p);"""
replace_once(old,new)
# Each shop card has an accent notch matching its own mineral class.
replace_once('        panel(c,14,y,332,73,0xff25344e);\n        round(c,23,y+12,47,49,8,0xff172840);',
"""        panel(c,14,y,332,73,0xff25344e);
        rect(c,15,y+12,3,49,accent);
        round(c,23,y+12,47,49,8,0xff172840);""")
# Gold-and-crystal header medallions distinguish the menu sections.
replace_once('        text(c,"КУЗНЯ БЕЗДНЫ",180,113,19,GOLD,true);',
"""        drawV43Sigil(c,28,111,4,0xffe4bd7d);
        text(c,"КУЗНЯ БЕЗДНЫ",180,113,19,GOLD,true);""")
replace_once('        text(c,"ГИЛЬДИЯ ИСКАТЕЛЕЙ",180,112,19,GOLD,true);',
"""        drawV43Sigil(c,28,111,3,0xff78d8c4);
        text(c,"ГИЛЬДИЯ ИСКАТЕЛЕЙ",180,112,19,GOLD,true);""")
replace_once('        text(c,"АТЛАС ПОДЗЕМЕЛИЙ",180,113,19,GOLD,true);',
"""        drawV43Sigil(c,28,111,5,0xffa4c9ec);
        text(c,"АТЛАС ПОДЗЕМЕЛИЙ",180,113,19,GOLD,true);""")

for name,visibility in [("save","public"),("rebirth","private")]:
    assert java_method(name,visibility)==before[name], "Save/gameplay method changed: "+name
assert s[s.index("    @Override public boolean onTouchEvent("):]==touch_before, "Touch input changed"
assert "drawV43PageAtmosphere(c,tab)" in s
src.write_text(s)
g=gradle.read_text()
assert g.count("versionCode 19")==1 and g.count("versionName '4.2'")==1
gradle.write_text(g.replace("versionCode 19","versionCode 20").replace("versionName '4.2'","versionName '4.3'"))
print("v4.3 menu art completed: illustrated shop/forge/mastery icons, page backgrounds, atlas thumbnails, settings and guild")
