from pathlib import Path
import re
root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def inject_method(name,body):
    global s
    # Insert directly inside the existing renderer method; keep gameplay and touch hitboxes intact.
    pattern=r'(private\s+(?:void|boolean|int|float|long)\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{)'
    matches=list(re.finditer(pattern,s))
    assert len(matches)==1,(name,len(matches))
    m=matches[0]
    s=s[:m.end()]+'\n'+body+'\n'+s[m.end():]

# A new, unified dark-fantasy art direction: inset panels, warm metal trim,
# deep parallax cave strata, glowing ore flecks and dynamic cave dust.
art=r"""
    private void drawV4Scene(Canvas c,int biome,int tint){
        Paint p=new Paint(3);
        int[] palette={0xffdba65c,0xff63d8d0,0xffb78cff,0xffef7477,0xff8cd8a5};
        int accent=palette[Math.abs(biome)%palette.length];
        // Cave strata: offset silhouettes and engraved mineral seams.
        for(int layer=0;layer<4;layer++){
            float offset=(float)Math.sin(time*(.07+layer*.03)+biome+layer)*9;
            int shade=layer%2==0?0xff152332:0xff1d2a3a;
            p.setColor(shade);
            android.graphics.Path wall=new android.graphics.Path();
            wall.moveTo(-30,128+layer*29);
            for(int x=0;x<=390;x+=22){
                float y=128+layer*29+(float)Math.sin(x*.052+layer*1.8+biome*.2)*12+offset;
                wall.lineTo(x,y);
            }
            wall.lineTo(390,550);
            wall.lineTo(-30,550);
            wall.close();
            c.drawPath(wall,p);
        }
        // Golden structural framing: independent of touch areas and save data.
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(2);
        p.setColor(0x88cba56b);
        c.drawRoundRect(12,118,348,540,18,18,p);
        p.setStrokeWidth(1);
        p.setColor(0x5586a7b6);
        c.drawRoundRect(17,123,343,535,15,15,p);
        p.setStyle(Paint.Style.FILL);
        for(int i=0;i<34;i++){
            float x=24+(i*97+biome*11)%315;
            float y=136+(i*71+biome*17)%383;
            float phase=(float)Math.sin(time*(.45+(i%5)*.12)+i*2.2);
            int a=fxEnabled?(int)(45+35*(phase+1)) : 30;
            p.setColor((accent&0x00ffffff)|(a<<24));
            c.drawCircle(x,y,(i%4==0)?2.4f:1.1f,p);
        }
        // Distinct illuminated corners and etched divider.
        p.setColor(0xffd4b17c);
        for(int x:new int[]{18,342}){
            c.drawCircle(x,125,3.5f,p);
            c.drawCircle(x,534,3.5f,p);
        }
        p.setColor(0x779cb0c0);
        c.drawRect(26,132,334,133,p);
    }
"""
anchor="    private void drawCaveWeather(Canvas c,int biome,int tint){"
assert s.count(anchor)==1
s=s.replace(anchor,art+"\n"+anchor+"\n        drawV4Scene(c,biome,tint);",1)

# Replace generic rounded panels with beveled, highlighted materials while preserving
# original coordinates, interaction and text.
def enhance_primitive(name,helper):
    global s
    pat=r'(private\s+void\s+'+name+r'\s*\(([^)]*)\)\s*\{)'
    matches=list(re.finditer(pat,s))
    if len(matches)!=1:
        print("Skipping optional UI primitive",name,"matches",len(matches))
        return
    m=matches[0]
    args=m.group(2)
    if name=="round":
        # Read actual argument names rather than assuming their spelling.
        parts=[v.strip().split()[-1] for v in args.split(",")]
        if len(parts)<7:return
        cv,x,y,w,h,r,color=parts[:7]
        overlay=f'''
        Paint bevel=new Paint(3);
        bevel.setColor(0x22ffffff);
        bevel.setStyle(Paint.Style.STROKE);
        bevel.setStrokeWidth(1.2f);
        {cv}.drawRoundRect({x}+1,{y}+1,{x}+{w}-1,{y}+{h}-1,{r},{r},bevel);
        bevel.setStyle(Paint.Style.FILL);
        bevel.setColor(0x18ffffff);
        {cv}.drawRoundRect({x}+4,{y}+3,{x}+{w}-4,{y}+5,2,2,bevel);
'''
    else:return
    # append after method's original first draw to preserve layering? before works for bevel
    s=s[:m.end()]+overlay+s[m.end():]
enhance_primitive("round","bevel")

# New ore crystal artwork: independently overlaid on the existing ore mesh.
# The prior version's mineral positions are preserved, preventing hitbox changes.
needle="        if(richVein()){"
assert s.count(needle)==1
s=s.replace(needle,'''        if(fxEnabled){
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
        }
        if(richVein()){''',1)
assert "drawV4Scene" in s and "facet.moveTo" in s
mine.write_text(s)
g=gradle.read_text()
assert g.count("versionCode 16")==1 and g.count("versionName '3.11'")==1
gradle.write_text(g.replace("versionCode 16","versionCode 17").replace("versionName '3.11'","versionName '4.0'"))
print("v4.0: redesigned cave strata, framing, mineral facets, decorative UI bevels")
