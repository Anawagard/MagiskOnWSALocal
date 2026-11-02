from pathlib import Path
import re

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()
save_before=s[s.index("    public void save(){"):]
touch_before=s[s.index("    @Override public boolean onTouchEvent("):s.index("    public void save(){")]

def once(old,new):
    global s
    assert s.count(old)==1,("Visual anchor mismatch",old[:110],s.count(old))
    s=s.replace(old,new,1)

def replace_conditional(needle,body,after="    private void drawRock(Canvas c,int id,int theme){"):
    global s
    start=s.index(after)
    i=s.index(needle,start)
    opening=s.index("{",i)
    level=1;end=opening+1
    while level:
        if s[end]=="{":level+=1
        elif s[end]=="}":level-=1
        end+=1
    s=s[:i]+body+s[end:]

# Avoid creating dozens of LinearGradient objects every frame in round().
once("""        p.setColor(col);
        if(a>=235&&h>=14){
            p.setShader(new LinearGradient(x,y,x,y+h,
                colorBlend(col,WHITE,.16f),colorBlend(col,0xff030b16,.24f),Shader.TileMode.CLAMP));
        }
        c.drawRoundRect(x,y,x+w,y+h,r,r,p);
        p.setShader(null);""",
"""        p.setColor(col);
        c.drawRoundRect(x,y,x+w,y+h,r,r,p);
        if(a>=235&&h>=14&&w>=20){
            p.setColor(0x1affffff);
            c.drawRoundRect(x+5,y+3,x+w-5,y+Math.min(h-3,7),2,2,p);
        }""")
# Replace the flat gemstone facets with shared vector primitives.
once("""        if(fxEnabled){
            Paint facets=new Paint(3);
            facets.setColor(0x5579d9ef);
            android.graphics.Path facet=new android.graphics.Path();
            facet.moveTo(-31,-68);
            facet.lineTo(-8,-47);
            facet.lineTo(-23,-12);
            facet.lineTo(-49,-36);
            facet.close();
            c.drawPath(facet,facets);
            facets.setColor(0x77fce8b4);
            facet.reset();
            facet.moveTo(40,-34);
            facet.lineTo(62,-18);
            facet.lineTo(43,12);
            facet.lineTo(29,-7);
            facet.close();
            c.drawPath(facet,facets);
        }""",
"""        if(fxEnabled){
            polygon(c,new float[]{-31,-68,-8,-47,-23,-12,-49,-36},0x5579d9ef);
            polygon(c,new float[]{40,-34,62,-18,43,12,29,-7},0x77fce8b4);
        }""")

art=r"""
    private void drawV45Geode(Canvas c){
        for(int i=0;i<5;i++){
            float x=-45+i*22,y=43+(i%2)*10;
            int col=i%2==0?0xff76e5ed:0xffba9cff;
            polygon(c,new float[]{x-11,y+15,x,y-24,x+11,y+15,x+1,y+24},
                colorBlend(col,0xff142337,.28f));
            polygon(c,new float[]{x,y-24,x+11,y+15,x,y+10},col);
            line(c,x,y-17,x+2,y-6,0xaaffffff,1.4f);
        }
        round(c,-56,69,112,26,7,0xff182c3d);
        text(c,"✦ ГЕОДА ✦",0,87,14,0xffb8f6fa,true);
    }

    private void drawV45Treasure(Canvas c){
        // Sculpted chest, embossed lid, brass corners and faceted lock.
        polygon(c,new float[]{-61,-31,-43,-58,43,-58,61,-31,56,-16,-56,-16},
            0xff6d3f27);
        polygon(c,new float[]{-55,-31,-39,-51,39,-51,55,-31},0xffd99c53);
        polygon(c,new float[]{-39,-49,39,-49,45,-40,-45,-40},0xffffd99a);
        round(c,-58,-17,116,76,8,0xff603c2a);
        round(c,-53,-12,106,67,7,0xff9d6236);
        rect(c,-52,-8,104,8,0xffedbf69);
        rect(c,-52,39,104,7,0xffd5a65d);
        rect(c,-40,-10,8,60,0xfff2c477);
        rect(c,31,-10,8,60,0xfff2c477);
        polygon(c,new float[]{-8,-13,8,-13,15,12,0,27,-15,12},0xffd5a24b);
        polygon(c,new float[]{-6,-10,6,-10,11,11,0,21,-11,11},0xffffe6a5);
        p.reset();p.setAntiAlias(true);p.setColor(0xff2a3840);
        c.drawCircle(0,9,4,p);
        if(fxEnabled){
            float pulse=(float)(.5+.5*Math.sin(time*3.1));
            star(c,-39,-42,4.5f,0xfffff2c8,pulse);
            star(c,41,-38,5.5f,0xfffff2c8,pulse);
            star(c,0,22,3.2f,0xffffffff,pulse);
        }
    }

    private void drawV45Guardian(Canvas c){
        int seconds=bossDeadline>0?
            (int)Math.max(0,(bossDeadline-System.currentTimeMillis())/1000):99;
        if(seconds<12){
            float pulse=fxEnabled?(float)(.11+.10*Math.sin(time*8)):.12f;
            round(c,-118,-112,236,225,23,
                ((int)(Math.max(0,pulse)*255)<<24)|0x00fb6657);
        }
        // Massive crown, dark iron plates, copper edging and an illuminated core.
        polygon(c,new float[]{-97,-69,-89,-129,-54,-105,-21,-118,
            0,-143,24,-117,56,-107,90,-129,97,-68},0xff16263b);
        polygon(c,new float[]{-89,-72,-82,-115,-48,-95,-20,-109,
            0,-128,22,-109,52,-95,83,-115,89,-72},0xff526778);
        polygon(c,new float[]{-76,-76,-56,-102,-28,-90,-6,-107,
            0,-125,8,-107,29,-90,57,-102,77,-76},0xffbd8e60);
        for(int j=0;j<5;j++){
            float x=-68+j*34;
            polygon(c,new float[]{x-18,-60,x,-78,x+18,-60,x+13,-29,x-13,-29},
                j%2==0?0xff273e52:0xff31495c);
            line(c,x-11,-60,x,-72,0x88ffffff,1.3f);
        }
        round(c,-66,-14,53,26,5,0xff2b2028);
        round(c,13,-14,53,26,5,0xff2b2028);
        int eye=seconds<12?0xffff5e57:0xffffa66b;
        round(c,-58,-8,39,12,4,eye);
        round(c,19,-8,39,12,4,eye);
        rect(c,-49,-5,12,5,0xffffedb2);
        rect(c,31,-5,12,5,0xffffedb2);
        polygon(c,new float[]{-26,28,0,18,26,28,18,48,-18,48},0xff132737);
        polygon(c,new float[]{-17,30,0,25,17,30,11,39,-11,39},0xffd3a66e);
        drawOreCrystal(c,0,34,13,seconds<12?0xffff776f:0xff89e9e2,
            fxEnabled?(float)Math.sin(time*3):.6f);
        if(fxEnabled){
            for(int j=0;j<5;j++){
                float a=(float)(time*.7+j*6.283185f/5);
                star(c,(float)Math.cos(a)*96,(float)Math.sin(a)*92,3,
                    seconds<12?0xffff766a:0xff8ad5df,.55f);
            }
        }
    }
"""
anchor="    private void drawRock(Canvas c,int id,int theme){"
once(anchor,art+"\n"+anchor)
replace_conditional("        if(geode()){","        if(geode())drawV45Geode(c);")
replace_conditional("        if(treasure()){","        if(treasure())drawV45Treasure(c);")
replace_conditional("        if(guardian()){","        if(guardian())drawV45Guardian(c);")
# Distinct impact rays make the ore's fracture state readable.
once("""            c.drawCircle(0,0,110+(1-impact)*39,p);p.setStyle(Paint.Style.FILL);
        }
        c.restore();
    }
    private static final String[] PICK_NAMES=""",
"""            c.drawCircle(0,0,110+(1-impact)*39,p);p.setStyle(Paint.Style.FILL);
            if(fxEnabled){
                for(int i=0;i<10;i++){
                    float a=(float)(i*Math.PI/5+time*.2);
                    float r=106+(1-impact)*38;
                    line(c,(float)Math.cos(a)*r,(float)Math.sin(a)*r,
                        (float)Math.cos(a)*(r+12*impact),
                        (float)Math.sin(a)*(r+12*impact),
                        ((int)(impact*180)<<24)|(ORE[id]&0xffffff),1.5f);
                }
            }
        }
        c.restore();
    }
    private static final String[] PICK_NAMES=""")
# Combo meter floats within the cave instead of obscuring HP or controls.
once("""        drawEncounterEffects(c);
        if(depthBanner>0&&transition>.2f){""",
"""        drawEncounterEffects(c);
        if(combo>=2&&comboTimer>0){
            round(c,28,158,96,28,7,0xcc14313c);
            text(c,"СЕРИЯ  x"+combo,76,177,13,combo>=10?0xffffd987:0xff9fece0,true);
        }
        if(depthBanner>0&&transition>.2f){""")

assert s[s.index("    public void save(){"):]==save_before
assert s[s.index("    @Override public boolean onTouchEvent("):s.index("    public void save(){")]==touch_before
for name in ["drawV45Guardian","drawV45Treasure","drawV45Geode"]:
    assert s.count("private void "+name+"(")==1
mine.write_text(s)
g=gradle.read_text()
assert g.count("versionCode 21")==1 and g.count("versionName '4.4'")==1
gradle.write_text(g.replace("versionCode 21","versionCode 22").replace("versionName '4.4'","versionName '4.5'"))
print("v4.5: guardian, chest, geode and impact art rebuilt; shader allocations removed from rounded UI")
