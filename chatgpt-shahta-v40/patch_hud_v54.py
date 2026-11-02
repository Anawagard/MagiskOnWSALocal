from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    assert s.count(old)==1,("v5.4 source hook mismatch",old[:120],s.count(old))
    s=s.replace(old,new,1)

# Smoke screenshots showed the shop title colliding with the sound button.
# Reposition only the text; preserve the button's existing tap coordinates.
once('        text(c,"ЦЕНТР УЛУЧШЕНИЙ",180,112,19,GOLD,true);',
     '        text(c,"УЛУЧШЕНИЯ",132,112,19,GOLD,true);')

# Atlas discovery must use the same 25-level zone geometry as the actual renderer.
# Keep the existing 15-level reward milestones, but label them correctly.
once("    private int zoneNo(){return (depth-1)/15;}",
     "    private int zoneNo(){return (depth-1)/25;}")
once('else if(old%15==0)message("НОВАЯ ЗОНА! +кристаллы");',
     'else if(old%15==0)message("РУБЕЖ ДОБЫЧИ! +кристаллы");')

# A compact illustrated badge gives each of the 24 biome headers a unique
# identity. This is pure drawing; no hitboxes, save keys, or mechanics change.
once('        text(c,ZONES[biome],180,108,16,colorBlend(bcol,WHITE,.26f),true);',
     '        text(c,ZONES[biome],180,108,16,colorBlend(bcol,WHITE,.26f),true);\n        drawV54BiomeCrest(c,biome,bcol);')
method="""
    private static final String[] V54_BIOME_BADGES={
        "01","02","03","04","05","06","07","08","09","10","11","12",
        "13","14","15","16","17","18","19","20","21","22","23","24"};
    /** Twenty-four numbered metal-and-mineral seals beside the biome title. */
    private void drawV54BiomeCrest(Canvas c,int biome,int tint){
        c.save();c.translate(29,106);
        p.reset();p.setAntiAlias(true);
        p.setColor(0xff0b1a29);c.drawCircle(0,0,14,p);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(1.5f);p.setColor(colorBlend(tint,WHITE,.36f));
        c.drawCircle(0,0,12,p);
        p.setStrokeWidth(.8f);p.setColor(0x99c5aa7b);
        c.drawCircle(0,0,9.7f,p);
        p.setStyle(Paint.Style.FILL);
        int sigil=biome%6;
        int bright=colorBlend(tint,WHITE,.55f);
        if(sigil==0){
            polygon(c,new float[]{-4,-9,0,-13,4,-9,2,-5,-2,-5},bright);
        }else if(sigil==1){
            line(c,-5,-10,0,-13,bright,1.5f);
            line(c,0,-13,5,-10,bright,1.5f);
        }else if(sigil==2){
            polygon(c,new float[]{0,-13,5,-7,0,-5,-5,-7},bright);
        }else if(sigil==3){
            line(c,-6,-10,0,-7,bright,1.3f);
            line(c,0,-7,6,-10,bright,1.3f);
        }else if(sigil==4){
            star(c,0,-9,3,bright,.7f);
        }else{
            polygon(c,new float[]{-6,-10,0,-13,6,-10,0,-6},bright);
        }
        text(c,V54_BIOME_BADGES[biome],0,5,10,WHITE,true);
        c.restore();
    }
"""
once("    private void drawMine(Canvas c){",
     method+"\n    private void drawMine(Canvas c){")

assert "drawV54BiomeCrest(c,biome,bcol);" in s
assert "drawV53LivingOreGlints(c,id,damageRatio);" in s
assert "drawV47BiomeIdentity(c,biome,theme);" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 30" in g and "versionName '5.3'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
gradle.write_text(g.replace("versionCode 30","versionCode 31")
                   .replace("versionName '5.3'","versionName '5.4'"))
print("v5.4: shop heading overlap fixed; 24 biome seals; atlas unlocks at 25-level boundaries")
