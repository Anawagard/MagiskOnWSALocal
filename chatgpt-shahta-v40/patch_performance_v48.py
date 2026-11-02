from pathlib import Path
root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()
def once(a,b):
    global s
    assert s.count(a)==1,(a[:100],s.count(a))
    s=s.replace(a,b,1)
# Reuse the frequently drawn polygon path instead of allocating dozens of
# Path instances each frame, and cache the font used by every UI label.
once('    private final Paint p=new Paint();', '''    private final Paint p=new Paint();
    private final Path reusablePolygon=new Path();
    private final Path reusableRidge=new Path();
    private static final Typeface GAME_FONT=Typeface.create("sans-serif-condensed",Typeface.BOLD);''')
once('''        Path path=new Path();path.moveTo(coords[0],coords[1]);
        for(int i=2;i<coords.length;i+=2)path.lineTo(coords[i],coords[i+1]);path.close();
        p.reset();p.setAntiAlias(false);p.setColor(color);c.drawPath(path,p);''', '''        reusablePolygon.reset();reusablePolygon.moveTo(coords[0],coords[1]);
        for(int i=2;i<coords.length;i+=2)reusablePolygon.lineTo(coords[i],coords[i+1]);
        reusablePolygon.close();
        p.reset();p.setAntiAlias(false);p.setColor(color);c.drawPath(reusablePolygon,p);''')
old='Typeface.create("sans-serif-condensed",Typeface.BOLD)'
assert s.count(old)==4,s.count(old)
s=s.replace(old,'GAME_FONT')
once('private static final Typeface GAME_FONT=GAME_FONT;',
     'private static final Typeface GAME_FONT=Typeface.create("sans-serif-condensed",Typeface.BOLD);')
once('            Path ridge=new Path();\n            ridge.moveTo(18,510);',
     '            reusableRidge.reset();\n            reusableRidge.moveTo(18,510);')
once('            ridge.lineTo(18,y);','            reusableRidge.lineTo(18,y);')
once('                ridge.lineTo(x,y+elevation+drift);','                reusableRidge.lineTo(x,y+elevation+drift);')
once('            ridge.lineTo(342,510);ridge.close();','            reusableRidge.lineTo(342,510);reusableRidge.close();')
once('            p.setColor(base);c.drawPath(ridge,p);','            p.setColor(base);c.drawPath(reusableRidge,p);')
# Adaptive ambient effects, not simulation or static artwork.
once('        for(int i=0;i<28;i++){\n            double wave=time*',
     '        int dustCount=measuredFps<43f?14:28;\n        for(int i=0;i<dustCount;i++){\n            double wave=time*')
once('            for(int i=0;i<9;i++){\n                double phase=i*2.399',
     '            int glowCount=measuredFps<43f?5:9;\n            for(int i=0;i<glowCount;i++){\n                double phase=i*2.399')
assert 'private void drawV47BiomeIdentity(' in s
assert 'private void rebirth()' in s and 'public void save()' in s
mine.write_text(s)
b=gradle.read_text()
assert "versionCode 24" in b and "versionName '4.7'" in b
gradle.write_text(b.replace("versionCode 24","versionCode 25").replace("versionName '4.7'","versionName '4.8'"))
print("v4.8: cached font, reusable polygon/ridge paths, adaptive ambient FX")
