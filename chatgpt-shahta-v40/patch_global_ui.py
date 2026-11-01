from pathlib import Path
import re
p=Path("chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MineView.java")
g=Path("chatgpt-shahta-v33/project/app/build.gradle")
s=p.read_text()

# Retheme all existing interface surfaces through the shared drawing primitives.
# This deliberately leaves input geometry, gameplay, save keys, and progression intact.
def hook(name,callback):
    global s
    pattern=r'(private\\s+void\\s+'+name+r'\\s*\\(([^)]*)\\)\\s*\\{)'
    found=list(re.finditer(pattern,s))
    if len(found)!=1:
        print("optional primitive not found:",name,len(found));return False
    m=found[0]
    params=[x.strip().split()[-1] for x in m.group(2).split(",")]
    addition=callback(params)
    if not addition:return False
    s=s[:m.end()]+"\\n"+addition+"\\n"+s[m.end():]
    print("redesigned primitive",name)
    return True

# Color transformation across every rounded button, shop tile, settings panel and HUD card.
# Render highlights AFTER the original primitive by hooking at the method end.
def posthook(name,callback):
    global s
    pattern=r'(private\\s+void\\s+'+name+r'\\s*\\(([^)]*)\\)\\s*\\{)'
    found=list(re.finditer(pattern,s))
    if len(found)!=1:return False
    m=found[0];params=[x.strip().split()[-1] for x in m.group(2).split(",")]
    level=1;idx=m.end()
    while level and idx<len(s):
        if s[idx]=='{':level+=1
        elif s[idx]=='}':level-=1
        idx+=1
    assert level==0
    addition=callback(params)
    if not addition:return False
    s=s[:idx-1]+"\\n"+addition+"\\n"+s[idx-1:]
    print("post-redesigned",name)
    return True

def panel(a):
    if len(a)<7:return ""
    c,x,y,w,h,r,color=a[:7]
    return f"""
        Paint material=new Paint(3);
        material.setStyle(Paint.Style.STROKE);
        material.setStrokeWidth(1.3f);
        material.setColor(0x88c6a476);
        {c}.drawRoundRect({x}+1,{y}+1,{x}+{w}-1,{y}+{h}-1,{r},{r},material);
        material.setStrokeWidth(.6f);
        material.setColor(0x8870a2ac);
        {c}.drawRoundRect({x}+3,{y}+3,{x}+{w}-3,{y}+{h}-3,{r},{r},material);
        material.setStyle(Paint.Style.FILL);
        material.setColor(0x28f6e2b8);
        {c}.drawRoundRect({x}+8,{y}+3,{x}+{w}-8,{y}+5,2,2,material);
        material.setColor(0x66e9c990);
        {c}.drawCircle({x}+7,{y}+7,1.4f,material);
        {c}.drawCircle({x}+{w}-7,{y}+{h}-7,1.4f,material);
"""
assert posthook("round",panel),"round() renderer not found"

# Give all interface labels a subtle engraved dark shadow, preserving original glyph and position.
def letterpress(a):
    if len(a)<7:return ""
    c,label,x,y,size,color,center=a[:7]
    return f"""
        Paint ink=new Paint(3);
        ink.setTypeface(android.graphics.Typeface.create("sans-serif-condensed",android.graphics.Typeface.BOLD));
        ink.setTextSize({size});
        ink.setTextAlign({center}?Paint.Align.CENTER:Paint.Align.LEFT);
        ink.setColor(0x334ce5dc);
        {c}.drawText({label},{x},{y}-.65f,ink);
"""
# Text overlays may be skipped if the source uses another signature.
posthook("text",letterpress)

# Animated depth markers and side wall etching added to the game scene.
anchor="    private void drawCaveWeather(Canvas c,int biome,int tint){"
assert s.count(anchor)==1
scene=r"""
    private void drawV4WorldEngraving(Canvas c,int biome){
        Paint p=new Paint(3);
        int[] glow={0xffdfb778,0xff67cbd2,0xffa98cda,0xfff58c80,0xff8bd9b1};
        int metal=glow[Math.abs(biome)%glow.length];
        for(int side=0;side<2;side++){
            float x=side==0?8:352;
            p.setColor(0xff09131d);
            c.drawRect(x-5,113,x+5,552,p);
            p.setColor(0xffa7875a);
            c.drawRect(x-1,118,x+1,546,p);
            for(int i=0;i<18;i++){
                float y=125+i*23;
                p.setColor(i%4==0?metal:0xff344b5a);
                c.drawRect(x-2,y,x+2,y+7,p);
            }
        }
        for(int i=0;i<6;i++){
            float x=35+i*57;
            p.setColor(0x66c9a774);
            c.drawRect(x,546,x+24,548,p);
            p.setColor(0x5574d9d2);
            c.drawRect(x+7,549,x+18,550,p);
        }
    }
"""
s=s.replace(anchor,scene+"\\n"+anchor+"\\n        drawV4WorldEngraving(c,biome);",1)
p.write_text(s)
b=g.read_text()
assert "versionName '4.0'" in b
b=b.replace("versionName '4.0'","versionName '4.1'").replace("versionCode 17","versionCode 18")
g.write_text(b)
print("v4.1 global UI material and world engraving pass completed")
