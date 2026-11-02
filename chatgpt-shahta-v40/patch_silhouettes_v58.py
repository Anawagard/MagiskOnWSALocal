from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    n=s.count(old)
    assert n==1,("v5.8 anchor mismatch",old[:120],n)
    s=s.replace(old,new,1)

# Replace the single shared octagonal ore body with twenty-four cached
# irregular silhouettes. Every ore now has its own outer geometry, not
# merely a different tint or engraving. The cached shape is also used for
# texture, fracture and moving-highlight clipping.
old_body="""        polygon(c,new float[]{-85,-91,20,-105,99,-63,109,53,75,96,-31,110,-101,55,-112,-23},0xff0b1320);
        polygon(c,new float[]{-96,-93,15,-108,93,-65,110,39,68,95,-41,100,-107,44,-110,-29},base);
        polygon(c,new float[]{-96,-93,15,-108,83,-74,31,-31,-59,-30,-110,-29},colorBlend(base,WHITE,.18f));
        polygon(c,new float[]{93,-65,110,39,68,95,20,43,38,-29},colorBlend(base,Color.BLACK,.29f));
        polygon(c,new float[]{-107,44,-49,100,68,95,20,43,-50,44},colorBlend(base,Color.BLACK,.15f));
        line(c,-90,-66,-65,-82,0x75ffffff,4);
        line(c,-60,-91,12,-101,0x40ffffff,3);"""
once(old_body,"        drawV58RockBody(c,id,base);")

# The old clip and fracture mask assumed one shared polygon for every ore.
old_clip="""        if(!v52OreClipReady){
            v52OreClip.moveTo(-96,-93);v52OreClip.lineTo(15,-108);
            v52OreClip.lineTo(93,-65);v52OreClip.lineTo(110,39);
            v52OreClip.lineTo(68,95);v52OreClip.lineTo(-41,100);
            v52OreClip.lineTo(-107,44);v52OreClip.lineTo(-110,-29);
            v52OreClip.close();v52OreClipReady=true;
        }"""
once(old_clip,"""        if(!v52OreClipReady||v58TextureOreId!=id){
            v52OreClip.set(v58RockShape(id));
            v58TextureOreId=id;
            v52OreClipReady=true;
        }""")

old_fracture="""        if(!v50FractureMaskReady){
            v50FractureMask.moveTo(-96,-93);v50FractureMask.lineTo(15,-108);
            v50FractureMask.lineTo(93,-65);v50FractureMask.lineTo(110,39);
            v50FractureMask.lineTo(68,95);v50FractureMask.lineTo(-41,100);
            v50FractureMask.lineTo(-107,44);v50FractureMask.lineTo(-110,-29);
            v50FractureMask.close();v50FractureMaskReady=true;
        }"""
once(old_fracture,"""        if(!v50FractureMaskReady||v58FractureOreId!=id){
            v50FractureMask.set(v58RockShape(id));
            v58FractureOreId=id;
            v50FractureMaskReady=true;
        }""")

methods="""
    /** One immutable path per ore. Constructed once, never per animation frame.
     *  Family shape + unique seed give all 24 minerals distinct outlines.
     */
    private final Path[] v58RockShapes=new Path[24];
    private int v58TextureOreId=-1,v58FractureOreId=-1;
    private Path v58RockShape(int id){
        int index=Math.max(0,Math.min(23,id));
        if(v58RockShapes[index]!=null)return v58RockShapes[index];
        Path shape=new Path();
        int family=index==0?0:index<=3?1:
            (index==9||index==14||index==17)?2:index>=20?4:3;
        int corners=family==0?11:family==1?12:family==2?15:
            family==4?16:13;
        for(int i=0;i<corners;i++){
            double angle=-Math.PI/2+2*Math.PI*i/corners;
            double irregular=Math.sin((i+1)*2.37+index*.91)*5.5+
                Math.cos((i+3)*1.67+index*.59)*4.0;
            double radius=91+irregular;
            if(family==0)radius+=Math.sin(i*4.1)*7;
            if(family==1)radius+=(i%3==0?10:-3);
            if(family==2)radius+=(i%2==0?17:-11);
            if(family==3)radius+=(i%4==0?15:-2);
            if(family==4)radius+=(i%2==0?21:-13);
            radius=Math.max(67,Math.min(113,radius));
            float x=(float)(Math.cos(angle)*radius);
            float y=(float)(Math.sin(angle)*radius*.96);
            if(i==0)shape.moveTo(x,y);else shape.lineTo(x,y);
        }
        shape.close();
        v58RockShapes[index]=shape;
        return shape;
    }
    /** Material body, rim, shadow and directional lighting clipped to shape. */
    private void drawV58RockBody(Canvas c,int id,int base){
        Path shape=v58RockShape(id);
        p.reset();p.setAntiAlias(true);p.setColor(0xff09111c);
        c.save();c.translate(0,7);c.drawPath(shape,p);c.restore();
        p.setColor(base);c.drawPath(shape,p);
        c.save();c.clipPath(shape);
        p.setColor(colorBlend(base,WHITE,.20f));
        c.drawOval(-110,-112,70,-20,p);
        p.setColor(colorBlend(base,0xff08101b,.30f));
        c.drawOval(20,-28,125,120,p);
        p.setColor((ORE[id]&0x00ffffff)|0x29000000);
        c.drawOval(-72,30,75,110,p);
        c.restore();
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2.1f);
        p.setColor(colorBlend(base,WHITE,.38f));
        c.drawPath(shape,p);
        p.setStyle(Paint.Style.FILL);
    }
"""
once("    private void drawRock(Canvas c,int id,int theme){",
     methods+"\n    private void drawRock(Canvas c,int id,int theme){")

assert s.count("private Path v58RockShape(")==1
assert s.count("drawV58RockBody(c,id,base);")==1
assert s.count("v52OreClip.set(v58RockShape(id));")==1
assert s.count("v50FractureMask.set(v58RockShape(id));")==1
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 34" in g and "versionName '5.7'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
gradle.write_text(g.replace("versionCode 34","versionCode 35")
                   .replace("versionName '5.7'","versionName '5.8'"))
print("v5.8: 24 cached distinct ore silhouettes; texture, crack and glint masks synchronized")
