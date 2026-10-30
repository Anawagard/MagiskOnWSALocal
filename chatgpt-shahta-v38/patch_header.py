from pathlib import Path
p=Path("chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MineView.java")
s=p.read_text()
old='c.drawText("⛏  ШАХТА БЕЗ ДНА  •  v3.5",180,25,versionPaint);'
assert s.count(old)==1, "Header title hook missing"
s=s.replace(old,'c.drawText("⛏  ШАХТА БЕЗ ДНА",180,25,versionPaint);')
p.write_text(s)
g=Path("chatgpt-shahta-v33/project/app/build.gradle")
v=g.read_text()
assert "versionCode 12" in v and "versionName '3.7'" in v
g.write_text(v.replace("versionCode 12","versionCode 13").replace("versionName '3.7'","versionName '3.8'"))
print("Static game header without hardcoded version")
