from pathlib import Path
root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(a,b):
    global s
    n=s.count(a)
    assert n==1, f"Visual patch hook mismatch: {a[:80]!r}, found {n}"
    s=s.replace(a,b,1)

# Procedural graphics: no new textures to load, no changes to save format.
# Three parallax-like layers, depth-sensitive palette and restrained light blooms.
once("    private void drawCaveWeather(Canvas c,int biome,int tint){", """    private void drawLuxuryCaveLighting(Canvas c,int biome,int tint){
        if(!fxEnabled)return;
        Paint glow=new Paint(3);
        final int[] colors={0xff72d4e5,0xffffc46e,0xffad8cff,0xff76e5b7};
        int hue=colors[Math.abs(biome)%colors.length];
        for(int layer=2;layer>=0;layer--){
            float speed=.11f+layer*.08f;
            for(int i=0;i<9;i++){
                double phase=i*2.399+biome*.77+time*speed;
                float x=18+(float)((i*83+layer*59+Math.sin(phase)*19+720)%325);
                float y=148+(float)((i*67+layer*109+time*(2+layer))%400);
                int alpha=layer==0?45:layer==1?25:13;
                glow.setColor((hue&0x00ffffff)|(alpha<<24));
                c.drawCircle(x,y,layer==0?5:layer==1?11:18,glow);
                if(layer==0){
                    glow.setColor(0x99ffffff);
                    c.drawCircle(x,y,1.2f,glow);
                }
            }
        }
    }
    private void drawCaveWeather(Canvas c,int biome,int tint){
        drawLuxuryCaveLighting(c,biome,tint);""")

# Jewel glints stay aligned with the rock and use the existing time-based animation.
once("        if(richVein()){", """        if(richVein()){
            if(fxEnabled){
                float shimmer=(float)(.5+.5*Math.sin(time*4.2));
                star(c,-53,-32,3,0xffe8fff7,shimmer);
                star(c,44,43,4,0xffe8fff7,shimmer);
            }""")

assert "drawLuxuryCaveLighting" in s
mine.write_text(s)
g=gradle.read_text()
assert g.count("versionCode 15")==1 and g.count("versionName '3.10'")==1
gradle.write_text(g.replace("versionCode 15","versionCode 16").replace("versionName '3.10'","versionName '3.11'"))
print("Shahta 3.11 visual patch: depth-colored layered cave lights and mineral glints")
