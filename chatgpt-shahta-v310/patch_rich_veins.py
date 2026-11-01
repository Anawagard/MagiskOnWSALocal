from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    count=s.count(old)
    assert count==1, f"v3.10 source hook mismatch ({count}): {old[:110]}"
    s=s.replace(old,new,1)

# Deterministic rare ore: no new save keys and no random reroll after restarting.
# Depths 5, 24, 43, 62... are eligible, excluding boss and chest stages.
once('    private int hpFor(int d){',
'''    private boolean richVein(int d){
        return d>=5&&d%19==5&&d%10!=0&&d%17!=0;
    }
    private boolean richVein(){return richVein(depth);}
    private int hpFor(int d){''')

# The vein is tougher than ordinary rock; existing prestige scaling remains intact.
once('return (int)Math.min(1500000000,Math.ceil(hp*rebirthScale*earlyScale*hardened));',
     'return (int)Math.min(1500000000,Math.ceil(hp*rebirthScale*earlyScale*hardened*(richVein(d)?1.75:1.0)));')

# Higher-value find, plus an optional skill bonus for at least five manual strikes.
once('reward=(long)Math.min(8000000000000000.0,reward*(1+tech[2]*.10));',
'''reward=(long)Math.min(8000000000000000.0,reward*(1+tech[2]*.10));
        if(richVein(old)){
            reward=(long)Math.min(8000000000000000.0,reward*3.0);
            gems+=2+Math.min(5,old/100);
            dust+=2+old/120;
            if(oreStrikes>=5){
                gems+=2;
                if(popups.size()<14)popups.add(new Popup(180,237,"МАСТЕРСКАЯ ДОБЫЧА +2 ◆",0xff9afce5));
            }
        }''')

# Visual seams follow the rock as it bobs and shakes; low-cost primitives only.
once('''        if(geode()){
            round(c,-39,50,78,28,8,0xff273a58);''',
'''        if(richVein()){
            float veinPulse=fxEnabled?(float)(.65+.35*Math.sin(time*3.0)):.8f;
            line(c,-79,-55,-20,-15,0xff5de8d8,6);
            line(c,-20,-15,24,30,0xffb8fff1,5);
            line(c,24,30,76,58,0xff5de8d8,6);
            line(c,-32,62,12,22,0xff7bd9ff,4);
            star(c,-79,-55,5,0xffbafff0,veinPulse);
            star(c,24,30,6,0xffbafff0,veinPulse);
            star(c,76,58,5,0xffbafff0,veinPulse);
        }
        if(geode()){
            round(c,-39,50,78,28,8,0xff273a58);''')

# On-screen identification and clear manual-mining incentive.
once('''if(modifier()==1&&oreStrikes<4)text(c,"ПРОБЕЙ БРОНЮ: "+(4-oreStrikes)+" УД.",180,473,12,0xffc4e9ff,true);''',
'''if(richVein())text(c,"✦ БОГАТАЯ ЖИЛА: x3 МОНЕТЫ",180,473,12,0xffb0f7f1,true);
        else if(modifier()==1&&oreStrikes<4)text(c,"ПРОБЕЙ БРОНЮ: "+(4-oreStrikes)+" УД.",180,473,12,0xffc4e9ff,true);''')
once('''if(old%25==0)message("СВЕРХЗАРЯД! x2 НА 12 СЕК.");''',
'''if(richVein())message("БОГАТАЯ ЖИЛА! x3 МОНЕТЫ И КРИСТАЛЛЫ");
        else if(old%25==0)message("СВЕРХЗАРЯД! x2 НА 12 СЕК.");''')

# No new preference keys, no migration, no modifications to the rebirth reset.
assert s.count('private boolean richVein(int d)')==1
assert s.count('if(richVein(old))')==1
assert 'private void destroyRock(){' in s
assert 'c.drawText("⛏  ШАХТА БЕЗ ДНА",180,25,versionPaint);' in s
mine.write_text(s)
g=gradle.read_text()
assert g.count("versionCode 14")==1 and g.count("versionName '3.9'")==1
gradle.write_text(g.replace("versionCode 14","versionCode 15")
                   .replace("versionName '3.9'","versionName '3.10'"))
print("v3.10 rich ore veins: 1.75x HP, 3x coins, crystals/dust, manual mastery bonus, glowing ore")
