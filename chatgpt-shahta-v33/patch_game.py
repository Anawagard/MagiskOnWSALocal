from pathlib import Path
import re
root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
activity=root/"app/src/main/java/com/bezdna/mine/MainActivity.java"
gradle=root/"app/build.gradle"
s=mine.read_text()
def append_array(src,name,items):
    pattern=r'(\b'+name+r'\s*=\s*\{)(.*?)(\};)'
    m=re.search(pattern,src,re.S)
    if not m: raise RuntimeError("Array missing: "+name)
    current=m.group(2).rstrip()
    if not current.rstrip().endswith(","): current+=","
    repl=m.group(1)+current+"\n        "+",".join(items)+m.group(3)
    return src[:m.start()]+repl+src[m.end():]
# Stretch the existing 24 handcrafted biomes to 25 levels each: 600 stages.
s=s.replace("(depth-1)/15","(depth-1)/25")
s=s.replace("(bi*15+1)","(bi*25+1)").replace("(bi*15+15)","(bi*25+25)")
# New upgrade ceiling, including saved progress and mastery shop.
repls={"clamp(prefs.getInt(\"mastery_\"+i,0),0,30)":"clamp(prefs.getInt(\"mastery_\"+i,0),0,60)",
       "mastery[k]>=30":"mastery[k]>=60","mastery[k]==30":"mastery[k]==60",
       "mastery[k]<30":"mastery[k]<60","mastery[k]+\" / 30\"":"mastery[k]+\" / 60\""}
for a,b in repls.items(): s=s.replace(a,b)
# Expand the animated atmospheric layer while using existing in-game renderer.
needle="    private void drawCaveWeather(Canvas c,int biome,int tint){"
assert needle in s
extra="""    private void drawDeepAtmosphere(Canvas c,int biome,int tint){
        for(int i=0;i<28;i++){
            double wave=time*(.34+(i%4)*.08)+i*1.79+biome*.8;
            int x=12+(int)((i*83+Math.sin(wave)*25+720)%335);
            int y=160+(int)((i*61+time*(5+i%5))%365);
            float glow=(float)(.13+.19*(.5+.5*Math.sin(wave)));
            star(c,x,y,1+i%3,tint,glow);
        }
    }
"""
s=s.replace(needle,extra+needle+"\n        drawDeepAtmosphere(c,biome,tint);")
mine.write_text(s)
a=activity.read_text()
a,n=re.subn(r'getWindow\(\)\.setFlags\(WindowManager\.LayoutParams\.FLAG_FULLSCREEN,\s*WindowManager\.LayoutParams\.FLAG_FULLSCREEN\);','getWindow().clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);\n        getWindow().setStatusBarColor(0xff0d1625);',a)
assert n==1,n
activity.write_text(a)
g=gradle.read_text()
assert "versionCode 7" in g and "versionName '3.2'" in g
gradle.write_text(g.replace("versionCode 7","versionCode 8").replace("versionName '3.2'","versionName '3.3'"))
print("v3.3 PATCH: 600 level progression, 60 mastery ranks, ambient particles, visible status bar")
