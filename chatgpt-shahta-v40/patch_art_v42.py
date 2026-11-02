from pathlib import Path
import re

root=Path("chatgpt-shahta-v33/project")
src=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=src.read_text()

def method(name, replacement):
    global s
    match=re.search(r"(?m)^    private void "+re.escape(name)+r"\s*\(",s)
    assert match is not None, "Missing renderer "+name
    start=match.start()
    opening=s.index("{",match.end())
    level=1
    pos=opening+1
    while level and pos<len(s):
        if s[pos]=="{":level+=1
        elif s[pos]=="}":level-=1
        pos+=1
    assert level==0, "Unbalanced method "+name
    s=s[:start]+replacement.strip("\n")+"\n"+s[pos:]
    print("replaced renderer:",name)

# All visual primitives use the same art direction. Cached Paint avoids the
# allocations and GC pauses caused by the previous per-panel bevel pass.
method("round",r"""
    private void round(Canvas c,float x,float y,float w,float h,float radius,int col){
        if(w<=0||h<=0)return;
        float r=Math.max(0,Math.min(radius,Math.min(w,h)*.5f));
        int a=Color.alpha(col);
        p.reset();p.setAntiAlias(true);
        if(a>=180&&w>=24&&h>=12){
            p.setColor(0x55040812);
            c.drawRoundRect(x+1,y+3,x+w+1,y+h+3,r,r,p);
        }
        p.setColor(col);
        if(a>=235&&h>=14){
            p.setShader(new LinearGradient(x,y,x,y+h,
                colorBlend(col,WHITE,.16f),colorBlend(col,0xff030b16,.24f),Shader.TileMode.CLAMP));
        }
        c.drawRoundRect(x,y,x+w,y+h,r,r,p);
        p.setShader(null);
        if(a>=180&&w>=20&&h>=12){
            p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1);
            p.setColor(0x668fd0db);
            c.drawRoundRect(x+.7f,y+.7f,x+w-.7f,y+h-.7f,r,r,p);
            p.setColor(0x44603e28);
            c.drawRoundRect(x+2.5f,y+2.5f,x+w-2.5f,y+h-2.5f,
                Math.max(1,r-2),Math.max(1,r-2),p);
            p.setStyle(Paint.Style.FILL);
            p.setColor(0x36ffffff);
            c.drawRoundRect(x+7,y+3,x+w-7,y+4.6f,1,1,p);
        }
    }
""")
method("text",r"""
    private void text(Canvas c,String s,float x,float y,int size,int col,boolean center){
        p.reset();p.setAntiAlias(true);p.setColor(col);p.setTextSize(size);
        p.setTypeface(Typeface.create("sans-serif-condensed",Typeface.BOLD));
        p.setTextAlign(center?Paint.Align.CENTER:Paint.Align.LEFT);
        if(size>=14)p.setShadowLayer(1.7f,0,1.2f,0xaa030915);
        c.drawText(s,x,y,p);
        p.clearShadowLayer();
    }
""")
method("panel",r"""
    private void panel(Canvas c,float x,float y,float w,float h,int col){
        round(c,x,y,w,h,10,colorBlend(col,0xff07101d,.25f));
        p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(1.3f);p.setColor(0x889bc8c5);
        c.drawRoundRect(x+1.5f,y+1.5f,x+w-1.5f,y+h-1.5f,9,9,p);
        p.setStyle(Paint.Style.FILL);
        rect(c,x+12,y+2,w-24,2,0x66e2bb7b);
        rect(c,x+12,y+h-4,w-24,1,0x6673b7bd);
        polygon(c,new float[]{x+3,y+16,x+3,y+5,x+15,y+3,x+11,y+9},0xffc6a26c);
        polygon(c,new float[]{x+w-3,y+h-16,x+w-3,y+h-5,x+w-15,y+h-3,x+w-11,y+h-9},0xff987852);
        for(int i=0;i<2;i++){
            float bx=i==0?x+8:x+w-8;
            p.setColor(0xffcaa879);
            c.drawCircle(bx,y+h-9,1.8f,p);
        }
    }
""")
method("bar",r"""
    private void bar(Canvas c,float x,float y,float w,float h,float ratio,int active){
        float f=Math.max(0,Math.min(1,ratio));
        round(c,x,y,w,h,h/2,0xff09111c);
        float filled=(w-4)*f;
        if(filled>.5f){
            round(c,x+2,y+2,filled,Math.max(1,h-4),Math.max(1,(h-4)/2),active);
            if(filled>8){
                p.reset();p.setAntiAlias(true);
                p.setColor(0x66ffffff);
                c.drawRoundRect(x+5,y+3,x+Math.max(5,filled-3),y+Math.min(h-2,5),
                    1.5f,1.5f,p);
            }
            if(fxEnabled&&filled>22){
                float gleam=(time*27)%(filled-10);
                rect(c,x+3+gleam,y+3,3,Math.max(1,h-6),0x66ffffff);
            }
        }
        if(h>=9&&w>40){
            p.reset();p.setColor(0x779ab1b5);p.setStrokeWidth(.7f);
            for(int i=1;i<10;i++){
                float tx=x+i*w/10f;
                c.drawLine(tx,y+h-3,tx,y+h-1,p);
            }
        }
    }
""")
method("button",r"""
    private void button(Canvas c,float x,float y,float w,float h,String title,String sub,boolean enabled){
        int base=enabled?0xff276f70:0xff28384a;
        round(c,x,y,w,h,9,base);
        p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(1.4f);p.setColor(enabled?0xff7bd9cb:0xff677b8b);
        c.drawRoundRect(x+2,y+2,x+w-2,y+h-2,8,8,p);
        p.setStyle(Paint.Style.FILL);
        polygon(c,new float[]{x+6,y+4,x+21,y+4,x+6,y+19},
            enabled?0x88f5d9a0:0x447f9db3);
        polygon(c,new float[]{x+w-6,y+h-4,x+w-21,y+h-4,x+w-6,y+h-19},
            enabled?0x88f5d9a0:0x447f9db3);
        rect(c,x+12,y+3,w-24,2,enabled?0xffb8f3e3:0xff637d8b);
        text(c,title,x+w/2,y+17,12,enabled?0xfff9f1df:0xffb6c1cf,true);
        if(sub!=null&&!sub.isEmpty())
            fittedText(c,sub,x+w/2,y+34,10,enabled?0xffe2fff4:0xffb2bfd0,w-8);
    }
""")
method("nav",r"""
    private void nav(Canvas c,int x,int tab,String title,String ico){
        boolean selected=page==tab;
        round(c,x,660,65,49,8,selected?0xff295c62:0xff162839);
        if(selected){
            rect(c,x+9,660,47,3,0xffd7b87c);
            rect(c,x+17,663,31,1,0xff7ffff0);
        }
        p.reset();p.setAntiAlias(true);
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(selected?1.6f:1);
        p.setColor(selected?0xffc4a571:0xff58717d);
        c.drawCircle(x+32.5f,678,11,p);
        p.setStyle(Paint.Style.FILL);
        float bounce=selected&&fxEnabled?(float)Math.sin(time*3)*1.2f:0;
        text(c,ico,x+32.5f,683+bounce,15,selected?0xffffe0a1:0xffa6becb,true);
        text(c,title,x+32.5f,699,9,selected?0xfff2f4e8:0xff9eb3bf,true);
    }
""")
method("powerButton",r"""
    private void powerButton(Canvas c,int x,int y,int w,String title,String sub,boolean enabled){
        int col=enabled?0xff246f6a:0xff243144;
        round(c,x,y,w,34,7,col);
        rect(c,x+7,y+2,w-14,2,enabled?0xffb8efcb:0xff60788d);
        polygon(c,new float[]{x+4,y+4,x+14,y+4,x+4,y+14},
            enabled?0xffdbbd80:0xff53677a);
        text(c,title,x+w/2f,y+15,12,enabled?0xfff5d99c:0xffa4b4c8,true);
        fittedText(c,sub,x+w/2f,y+28,9,0xffe6f4ef,w-8);
    }
""")
method("drawHeader",r"""
    private void drawHeader(Canvas c){
        grad(c,0,0,W,87,0xff182c3b,0xff081622);
        rect(c,0,84,W,3,0xffa8895c);
        rect(c,0,87,W,1,0xff76c8c9);
        for(int i=0;i<9;i++){
            float x=11+i*42;
            polygon(c,new float[]{x,0,x+13,0,x+5,8},0x447ca4ad);
        }
        text(c,"◆ ШАХТА БЕЗ ДНА ◆",180,25,20,0xfff6dca4,true);
        round(c,10,37,174,37,8,0xff102736);
        round(c,190,37,160,37,8,0xff102736);
        polygon(c,new float[]{16,53,22,45,28,53,22,62},0xffffcb6b);
        polygon(c,new float[]{196,53,202,45,208,53,202,62},0xff65e7e3);
        fittedText(c,fmt(coins)+" МОНЕТ",103,60,14,0xfff7dc9f,146);
        fittedText(c,fmt(gems)+" КРИСТ.",272,60,13,0xffa7f8f1,133);
    }
""")
method("drawBottom",r"""
    private void drawBottom(Canvas c){
        grad(c,0,651,360,69,0xff1b3240,0xff07131e);
        rect(c,0,650,360,2,0xffbfa276);
        for(int i=0;i<5;i++){
            float x=3+i*72;
            rect(c,x+66,659,1,47,0x447db9b8);
        }
        nav(c,4,0,"ШАХТА","⛏");
        nav(c,76,1,"УЛУЧШ.","⚙");
        nav(c,148,2,"КУЗНЯ","◆");
        nav(c,220,3,"ГИЛЬДИЯ","✦");
        nav(c,292,4,"АТЛАС","▣");
    }
""")
# The previous v4.0 opaque cave strata were drawn over all biome landmarks.
# Render the new background BEFORE the biomes instead, preserving their unique art.
method("drawV4Scene",r"""
    private void drawV4Scene(Canvas c,int biome,int tint){
        int[] palette={0xffd7ac70,0xff70d5d0,0xffb38be5,0xffef8575,0xffa2dda5};
        int accent=palette[Math.abs(biome)%palette.length];
        grad(c,18,149,324,361,0xff152a38,0xff050c16);
        p.reset();p.setAntiAlias(true);
        for(int layer=0;layer<4;layer++){
            float drift=fxEnabled?(float)Math.sin(time*(.06f+layer*.02f)+biome+layer)*5:0;
            int base=layer%2==0?0xff1d3340:0xff102532;
            float y=181+layer*60;
            Path ridge=new Path();
            ridge.moveTo(18,510);
            ridge.lineTo(18,y);
            for(int x=18;x<=342;x+=22){
                float elevation=(float)Math.sin(x*.045f+layer*2.2f+biome*.4f)*12;
                ridge.lineTo(x,y+elevation+drift);
            }
            ridge.lineTo(342,510);ridge.close();
            p.setColor(base);c.drawPath(ridge,p);
            p.setColor((accent&0xffffff)|0x33000000);
            for(int i=0;i<4;i++){
                float x=40+i*84+layer*7;
                c.drawCircle(x,y+12,2+layer*.5f,p);
            }
        }
        // Architectural arches frame the mining chamber without masking the ore.
        for(int i=0;i<3;i++){
            float x=38+i*120;
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(3.5f);
            p.setColor(0x556c8994);
            c.drawArc(x,190,x+70,430,188,164,false,p);
            p.setStrokeWidth(1.2f);p.setColor(0x6688c8be);
            c.drawArc(x+4,195,x+66,423,188,164,false,p);
            p.setStyle(Paint.Style.FILL);
        }
        for(int i=0;i<23;i++){
            float x=22+(i*97+biome*19)%312;
            float y=163+(i*53+biome*11)%333;
            float pulse=fxEnabled?(float)(.5+.5*Math.sin(time*.6+i)):0.35f;
            p.setColor((accent&0xffffff)|(((int)(20+38*pulse))<<24));
            c.drawCircle(x,y,1.4f+(i%3)*.5f,p);
        }
    }
""")
method("drawV4WorldEngraving",r"""
    private void drawV4WorldEngraving(Canvas c,int biome){
        int accent=BIOME[Math.abs(biome)%BIOME.length];
        for(int side=0;side<2;side++){
            float x=side==0?23:337;
            rect(c,x-3,151,6,357,0xff111f2b);
            rect(c,x-1,151,2,357,0xffb49361);
            for(int i=0;i<13;i++){
                float y=162+i*27;
                rect(c,x-3,y,6,5,i%4==0?accent:0xff486773);
                rect(c,x-2,y+5,4,2,0xff192e3a);
            }
        }
        for(int i=0;i<6;i++){
            float x=43+i*50;
            rect(c,x,502,23,2,0x88bba172);
            rect(c,x+6,505,11,1,0x8876d6cf);
        }
    }
""")
method("drawOreCrystal",r"""
    private void drawOreCrystal(Canvas c,float x,float y,int size,int color,float phase){
        float glow=Math.max(.25f,Math.min(1f,.65f+phase*.3f));
        if(fxEnabled){
            p.reset();p.setAntiAlias(true);
            for(int j=3;j>=1;j--){
                p.setColor(((int)(glow*15/j)<<24)|(color&0xffffff));
                c.drawCircle(x,y,size*(1+.42f*j),p);
            }
        }
        polygon(c,new float[]{x,y-size*1.35f,x+size*.85f,y-size*.4f,
            x+size*.68f,y+size*.9f,x-size*.55f,y+size*.92f,
            x-size*.9f,y-size*.25f},colorBlend(color,0xff0a2130,.28f));
        polygon(c,new float[]{x,y-size*1.35f,x+size*.85f,y-size*.4f,
            x+size*.1f,y+size*.17f,x-size*.9f,y-size*.25f},colorBlend(color,WHITE,.54f));
        polygon(c,new float[]{x+size*.85f,y-size*.4f,x+size*.68f,y+size*.9f,
            x+size*.1f,y+size*.17f},colorBlend(color,0xff071520,.4f));
        polygon(c,new float[]{x-size*.9f,y-size*.25f,x+size*.1f,y+size*.17f,
            x-size*.55f,y+size*.92f},colorBlend(color,0xff081522,.22f));
        line(c,x-size*.12f,y-size*.95f,x+size*.3f,y-size*.6f,0x99ffffff,1.1f);
        if(fxEnabled&&size>=9&&phase>.25f)star(c,x+size*.47f,y-size*.56f,2.5f,WHITE,glow);
    }
""")
# Add a different silhouette and specular language to the ore without altering
# health, collision areas, stage modifiers or saved progression.
ore=r"""
    private void drawV42OreHighlights(Canvas c,int id,int base){
        int mineral=ORE[id];
        float shimmer=fxEnabled?(float)(.7+.3*Math.sin(time*2.4+id)):1f;
        for(int i=0;i<7;i++){
            int seed=seeded(i+211,id+7,depth/5+3);
            float x=-75+(seed%150),y=-64+(seed/163)%129;
            float h=11+(seed/379)%16;
            float w=5+(seed/719)%8;
            int dark=colorBlend(mineral,0xff07151d,.55f);
            polygon(c,new float[]{x-w,y+3,x,y-h,x+w,y+2,x,y+h*.7f},dark);
            polygon(c,new float[]{x,y-h,x+w,y+2,x,y+h*.7f},mineral);
            polygon(c,new float[]{x-w,y+3,x,y-h,x,y+h*.7f},colorBlend(mineral,WHITE,.47f));
            line(c,x,y-h+2,x+1,y-h*.2f,0x88ffffff,1.2f);
            if(i%3==0&&fxEnabled)
                star(c,x+w*.5f,y-h*.3f,2.3f,mineral,shimmer);
        }
        // Faceted metallic rim, separate from ore fracture mechanics.
        line(c,-94,-69,-66,-88,0x88ffffff,2);
        line(c,-67,-89,8,-99,0x44ffffff,2);
        line(c,89,-50,104,30,0x447fe5e5,2);
    }
"""
anchor="    private void drawRock(Canvas c,int id,int theme){"
assert s.count(anchor)==1
s=s.replace(anchor,ore+"\n"+anchor,1)
old="""        if(id!=0)drawMineralTexture(c,id);
        c.restore();
        float damageRatio="""
assert s.count(old)==1
s=s.replace(old,"""        if(id!=0)drawMineralTexture(c,id);
        drawV42OreHighlights(c,id,base);
        c.restore();
        float damageRatio=""",1)
# Reposition background: the new cave strata sit below landmarks and lights.
old="        drawV4Scene(c,biome,tint);\n"
assert s.count(old)==1
s=s.replace(old,"",1)
old="        grad(c,18,149,324,361,colorBlend(theme,DARK,.83f),0xff060c1b);\n"
assert s.count(old)==1
s=s.replace(old,old+"        drawV4Scene(c,biome,theme);\n",1)
# Fragment particles become gemstone chips with a glint, rather than squares.
old="            rect(c,a.x,a.y,a.size,a.size,color);\n"
assert s.count(old)==1
s=s.replace(old,"""            polygon(c,new float[]{a.x,a.y-a.size*.9f,a.x+a.size*.7f,a.y,
                a.x,a.y+a.size*.9f,a.x-a.size*.7f,a.y},color);
            if(a.size>=3)line(c,a.x,a.y-a.size*.6f,a.x+a.size*.25f,a.y,
                0x88ffffff,1);
""",1)
# The pickaxe now carries an illuminated forged arc on every strike.
old="        c.rotate(angle);\n        if(swing>.2f){"
assert s.count(old)==1
s=s.replace(old,"""        c.rotate(angle);
        if(fxEnabled&&swing>.15f){
            for(int j=3;j>=1;j--){
                p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(j*2.5f);
                p.setColor(((int)(28/j)<<24)|(metal&0xffffff));
                c.drawArc(-90-j*3,-65-j*3,91+j*3,53+j*3,208,104,false,p);
            }
            p.setStyle(Paint.Style.FILL);
        }
        if(swing>.2f){""",1)

src.write_text(s)
g=gradle.read_text()
assert g.count("versionCode 18")==1 and g.count("versionName '4.1'")==1
gradle.write_text(g.replace("versionCode 18","versionCode 19").replace("versionName '4.1'","versionName '4.2'"))
assert "drawV4Scene(c,biome,theme)" in s
assert "drawV4Scene(c,biome,tint)" not in s
assert "drawV42OreHighlights(c,id,base)" in s
print("v4.2 complete: material system, HUD, navigation, shop cards, bars, buttons, ore, pickaxe, particles and cave layering")
