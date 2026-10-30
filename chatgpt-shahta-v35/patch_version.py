from pathlib import Path
p=Path("chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MineView.java")
s=p.read_text()
old='text(c,"⛏  ШАХТА БЕЗ ДНА 3.2",180,25,20,GOLD,true);'
assert s.count(old)==1, "Version label not found"
new='''Paint versionPaint=new Paint(3);
        versionPaint.setTypeface(android.graphics.Typeface.create("sans-serif-condensed",android.graphics.Typeface.BOLD));
        versionPaint.setTextSize(19);
        versionPaint.setTextAlign(Paint.Align.CENTER);
        versionPaint.setColor(0xfff5d794);
        versionPaint.setShadowLayer(3,0,1,0xff3e6384);
        c.drawText("⛏  ШАХТА БЕЗ ДНА  •  v3.5",180,25,versionPaint);'''
p.write_text(s.replace(old,new))
g=Path("chatgpt-shahta-v33/project/app/build.gradle")
s=g.read_text()
assert "versionCode 9" in s and "versionName '3.4'" in s
g.write_text(s.replace("versionCode 9","versionCode 10").replace("versionName '3.4'","versionName '3.5'"))
print("Version badge uses condensed bold typeface, warm gold, subtle glow; release 3.5")
