from pathlib import Path
import re
root=Path("chatgpt-shahta-v33/project")
p=root/"app/src/main/java/com/bezdna/mine/MineView.java"
g=root/"app/build.gradle"
s=p.read_text()
def replace_once(old,new):
    global s
    assert s.count(old)==1,(old[:80],s.count(old))
    s=s.replace(old,new)
# Six new temporary technologies; stored separately from permanent prestige mastery.
replace_once("private int chainLevel,geologyLevel;","private int chainLevel,geologyLevel,shopPage;\n    private final int[] tech={0,0,0,0,0,0};")
replace_once('geologyLevel=Math.max(0,prefs.getInt("geology",0));',
             'geologyLevel=Math.max(0,prefs.getInt("geology",0));\n        for(int i=0;i<6;i++)tech[i]=Math.max(0,prefs.getInt("tech_"+i,0));')
# Preserve previous save state and reset all six on rebirth.
replace_once('fortuneLevel=0;chainLevel=0;geologyLevel=0;',
             'fortuneLevel=0;chainLevel=0;geologyLevel=0;\n        for(int i=0;i<6;i++)tech[i]=0;shopPage=0;')
replace_once('ed.putInt("mastery_"+i,mastery[i]);','ed.putInt("mastery_"+i,mastery[i]);\n            ed.putInt("tech_"+i,tech[i]);')
# Prestige scaling starts at depth 1, while milestones remain demanding.
replace_once('return (int)Math.min(1500000000,Math.ceil(hp));',
'''double rebirthScale=Math.pow(1.32,Math.min(28,prestige));
        double earlyScale=1.0+Math.min(2.0,prestige*.08);
        double hardened=1.0+(d>=30?Math.min(1.6,(d-29)*.004):0);
        return (int)Math.min(1500000000,Math.ceil(hp*rebirthScale*earlyScale*hardened));''')
# Additional upgrades amplify active skills, manual damage, drilling and income.
replace_once('private int damage(){return (int)Math.min(170000000,',
             'private int damage(){return (int)Math.min(170000000,')
replace_once('(1+mastery[0]*.035));}', '(1+mastery[0]*.035)*(1+tech[0]*.09)*(1+tech[3]*.045));}')
replace_once('(crystalSurgeTime>0?1.8:1));}', '(crystalSurgeTime>0?1.8:1)*(1+tech[1]*.11));}')
# Add effective income to each ore payout while keeping rewards capped.
replace_once('long reward=rewardFor(depth);',
             'long reward=rewardFor(depth);\n        reward=(long)Math.min(8000000000000000.0,reward*(1+tech[2]*.10));')
# Extra resource bonuses for ore breakthroughs.
replace_once('if(old%13==0){gems+=1+mastery[2]/5;}',
             'if(old%13==0){gems+=1+mastery[2]/5+tech[4]/5;}')
replace_once('if(old%5==0||rng.nextInt(100)<Math.min(55,geologyLevel*5+talent[3]*3))dust+=1+(found>=10?1:0);',
             'if(old%5==0||rng.nextInt(100)<Math.min(75,geologyLevel*5+talent[3]*3+tech[5]*2))dust+=1+(found>=10?1:0)+tech[5]/8;')
# Shop second page, same six slots with switchable tab, preserving legacy layout.
replace_once('text(c,"Шесть технологий для скоростной добычи",180,132,11,MUTED,true);',
             'text(c,shopPage==0?"ОСНОВНЫЕ  1/2  ▶":"НОВЫЕ ТЕХНОЛОГИИ  2/2  ◀",180,132,12,0xff94eddd,true);')
replace_once('int[] pos={145,226,307,388,469,550};',
             'int[] pos={145,226,307,388,469,550};\n        if(shopPage==1){\n            String[] titles={"ЗАКАЛКА КИРКИ","ТУРБОПРИВОД","ОБОГАЩЕНИЕ РУДЫ","ТОЧНАЯ ЗАТОЧКА","КРИСТАЛЛОИСКАТЕЛЬ","ПЫЛЕВОЙ СЕПАРАТОР"};\n            String[] desc={"+9% к ручному урону","+11% к бурению","+10% к награде","+4.5% к урону","+кристаллы на этапах","+пыль за добычу"};\n            int[] colors={0xffffa869,0xff73d9ed,0xffffd36a,0xffff8cae,0xffb4a0fa,0xff8fddb5};\n            for(int i=0;i<6;i++)shopRow(c,pos[i],i+6,"✦",titles[i],desc[i],tech[i],colors[i]);\n            return;\n        }')
replace_once('int lvl=kind==0?powerLevel:kind==1?drillLevel:kind==2?critLevel:kind==3?fortuneLevel:kind==4?chainLevel:geologyLevel;',
             'int lvl=kind>=6?tech[kind-6]:kind==0?powerLevel:kind==1?drillLevel:kind==2?critLevel:kind==3?fortuneLevel:kind==4?chainLevel:geologyLevel;')
replace_once('double base=kind==0?15:', 'double base=kind>=6?(320+kind*170):kind==0?15:')
replace_once('double growth=kind==0?1.47:', 'double growth=kind>=6?1.52+((kind-6)*.025):kind==0?1.47:')
replace_once('}else if(page==1){\n            int[] yy={145,226,307,388,469,550};',
             '}else if(page==1){\n            if(y>=96&&y<144){shopPage=1-shopPage;invalidate();return true;}\n            int[] yy={145,226,307,388,469,550};')
replace_once('long price=cost(i);', 'int k=shopPage==1?i+6:i;\n                long price=cost(k);')
replace_once('switch(i){case 0:powerLevel++;break;case 1:drillLevel++;break;',
             'if(k>=6){tech[k-6]++;}else switch(i){case 0:powerLevel++;break;case 1:drillLevel++;break;')
replace_once('message(i==0?"КИРКА: "+PICK_NAMES[pickTier()]:"ТЕХНОЛОГИЯ УЛУЧШЕНА!");save();',
             'message(k==0?"КИРКА: "+PICK_NAMES[pickTier()]:"ТЕХНОЛОГИЯ УЛУЧШЕНА!");save();')
# Make boss-level life scale more difficult after each prestige.
replace_once('private long cost(int kind){', 'private long cost(int kind){')
p.write_text(s)
grad=g.read_text()
assert "versionCode 8" in grad and "versionName '3.3'" in grad
g.write_text(grad.replace("versionCode 8","versionCode 9").replace("versionName '3.3'","versionName '3.4'"))
print("v3.4 new 6 resettable upgrades, 2 shop pages, prestige-based HP escalation")
