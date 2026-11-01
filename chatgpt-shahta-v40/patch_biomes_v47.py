from pathlib import Path
root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()
anchor="        drawBiomeLandmark(c,biome,theme);"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n        drawV47BiomeIdentity(c,biome,theme);",1)
method=r'''    /** Distinctive background-only art for each of the 24 zones. No save/input changes. */
    private void drawV47BiomeIdentity(Canvas c,int biome,int theme){
        c.save();c.clipRect(19,155,341,506);
        float drift=fxEnabled?(float)Math.sin(time*.72f+biome)*3f:0f;
        float pulse=fxEnabled?(float)(.55+.45*Math.sin(time*1.7f+biome)):1f;
        int lit=colorBlend(theme,WHITE,.40f);
        switch(biome){
case 0: // fossils and stratified stone
for(int i=0;i<5;i++){float x=32+i*68,y=214+(i%3)*105;line(c,x-15,y,x+17,y-8,0xff6f8790,2);line(c,x-12,y+7,x+20,y-1,0xff455a68,2);for(int j=0;j<4;j++)line(c,x+j*6-9,y-4,x+j*6-13,y+5,0xffa4b5b6,1);}break;
case 1: // copper pipes and oxidized valves
for(int i=0;i<4;i++){float x=37+i*91,y=184+(i%2)*212;line(c,x,y,x,y+75,0xffaf8051,5);line(c,x,y+40,x+21,y+40,0xff69b89c,4);p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(3);p.setColor(0xffd4aa7e);c.drawCircle(x,y+40,9,p);p.setStyle(Paint.Style.FILL);rect(c,x-3,y+37,6,6,0xff77d9b6);}break;
case 2: // emerald roots and seed pods
for(int i=0;i<7;i++){float x=26+i*49,y=210+(i%3)*98;line(c,x,y,x+drift+12,y+47,0xff3b9367,3);polygon(c,new float[]{x+8+drift,y+25,x+23+drift,y+13,x+20+drift,y+39},0xff65dc9e);star(c,x+12+drift,y+48,3,lit,pulse);}break;
case 3: // gold temple inlay
for(int i=0;i<4;i++){float x=47+i*85,y=190+(i%2)*215;rect(c,x-18,y-15,37,48,0xff624829);rect(c,x-15,y-12,31,42,0xffac894a);polygon(c,new float[]{x,y-6,x+12,y+8,x,y+23,x-12,y+8},0xfff6d57d);star(c,x,y+8,4,WHITE,pulse);}break;
case 4: // frost snowflakes
for(int i=0;i<6;i++){float x=38+i*54,y=191+(i%3)*114;for(int j=0;j<3;j++){float a=(float)(j*Math.PI/3),dx=(float)Math.cos(a)*15,dy=(float)Math.sin(a)*15;line(c,x-dx,y-dy,x+dx,y+dy,0xffb8f7ff,2);}star(c,x,y,3,WHITE,pulse);}break;
case 5: // crimson tectonic fault
for(int i=0;i<4;i++){float x=27+i*96,y=162+(i%2)*130;line(c,x,y,x+15,y+38,0xffac354b,6);line(c,x+15,y+38,x-4,y+79,0xffff746d,3);line(c,x+9,y+27,x+34,y+42,0xffffb088,2);star(c,x+15,y+38,4,0xffffb69a,pulse);}break;
case 6: // amethyst runic obelisks
for(int i=0;i<5;i++){float x=39+i*69,y=192+(i%2)*216;polygon(c,new float[]{x-12,y+42,x-9,y-17,x,y-31,x+10,y-17,x+12,y+42},0xff543575);polygon(c,new float[]{x,y-31,x+10,y-17,x+12,y+42,x,y+29},0xff9e77e1);line(c,x-5,y+7,x+5,y+7,0xffedc8ff,2);star(c,x,y-11,3,lit,pulse);}break;
case 7: // molten catacomb chains
for(int i=0;i<5;i++){float x=26+i*77;for(int j=0;j<4;j++){float y=163+j*13;line(c,x,y,x+(j%2==0?3:-3),y+10,0xff8e5138,3);}polygon(c,new float[]{x-11,482,x+14,482,x+20,506,x-17,506},0xffa94326);line(c,x-7,487,x+10,487,0xffffb45b,3);}break;
case 8: // shipwreck timber and air bells
for(int i=0;i<4;i++){float x=38+i*88,y=222+(i%2)*193;line(c,x-15,y,x+17,y+21,0xff806c56,6);line(c,x+12,y-13,x+12,y+31,0xffa58e6f,4);p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2);p.setColor(0x996bdafa);c.drawCircle(x+drift,y-28,6,p);p.setStyle(Paint.Style.FILL);}break;
case 9: // obsidian spikes
for(int i=0;i<7;i++){float x=22+i*51,y=410+(i%3)*24;polygon(c,new float[]{x-16,506,x,y-62,x+17,506},0xff161626);polygon(c,new float[]{x,y-62,x+17,506,x+3,484},0xff50455d);line(c,x,y-44,x+3,y-11,0xffba526d,2);}break;
case 10: // astral constellations
for(int i=0;i<9;i++){float x=34+(i*79)%290,y=182+(i*67)%285;float xx=34+((i+1)*79)%290,yy=182+((i+1)*67)%285;line(c,x,y,xx,yy,0x5571d8e9,1);star(c,x,y,3+i%3,0xffc5ffff,pulse);}break;
case 11: // ancient rail carts
for(int i=0;i<4;i++){float x=25+i*94,y=430+(i%2)*18;rect(c,x,y,66,6,0xff97734d);polygon(c,new float[]{x+5,y-34,x+61,y-34,x+54,y,x+12,y},0xff4b4a47);rect(c,x+12,y-29,43,5,0xffd6b16c);for(int j=0;j<2;j++){p.reset();p.setColor(0xffc2a27a);c.drawCircle(x+17+j*32,y+7,7,p);}}break;
case 12: // bioluminescent fungi
for(int i=0;i<7;i++){float x=30+i*47,y=461-(i%3)*35;line(c,x,y,x+drift,y-31,0xff91b8a3,5);polygon(c,new float[]{x-20+drift,y-31,x-13+drift,y-48,x+drift,y-55,x+17+drift,y-46,x+22+drift,y-31},0xffcf77c8);for(int j=0;j<3;j++)rect(c,x-10+j*9+drift,y-38,3,4,0xfffbe5b5);}break;
case 13: // lightning and copper rods
for(int i=0;i<5;i++){float x=31+i*74,y=168+(i%2)*178;line(c,x,y,x,y+62,0xff768ca1,4);polygon(c,new float[]{x-5,y+8,x+8,y+8,x-2,y+33,x+12,y+33,x-13,y+66,x-4,y+38},0xff8bdfff);star(c,x+1,y+32,3,WHITE,pulse);}break;
case 14: // refractive glass prisms
for(int i=0;i<6;i++){float x=29+i*56,y=205+(i%3)*99;polygon(c,new float[]{x,y-36,x+23,y+7,x,y+49,x-23,y+7},0x6670d6e9);polygon(c,new float[]{x,y-36,x+23,y+7,x,y+11},0x99d1ffff);line(c,x,y-32,x-19,y+7,0xfff0ffff,1);}break;
case 15: // shadow-gate eyes
for(int i=0;i<5;i++){float x=35+i*71,y=215+(i%2)*196;polygon(c,new float[]{x-21,y+29,x-21,y-11,x,y-35,x+21,y-11,x+21,y+29},0xff211b39);polygon(c,new float[]{x-12,y,x,y-7,x+12,y,x,y+7},0xff74538d);p.reset();p.setColor(0xfff1c8ff);c.drawCircle(x+drift*.3f,y,2.6f,p);}break;
case 16: // meteor anvils
for(int i=0;i<5;i++){float x=30+i*73,y=458-(i%2)*45;polygon(c,new float[]{x-22,y-12,x+21,y-12,x+12,y+4,x+12,y+18,x-13,y+18,x-13,y+4},0xff64717a);rect(c,x-18,y-15,36,4,0xffc6a57e);line(c,x-6,y-28,x+drift+4,y-18,0xffffae69,2);star(c,x+drift+6,y-33,4,0xffffd69b,pulse);}break;
case 17: // cathedral stained-glass rosettes
for(int i=0;i<3;i++){float x=74+i*105,y=203+(i%2)*210;p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(5);p.setColor(0xffa98bbd);c.drawCircle(x,y,31,p);p.setStrokeWidth(2);p.setColor(0xffe4c5f5);c.drawCircle(x,y,20,p);p.setStyle(Paint.Style.FILL);for(int j=0;j<8;j++){float a=(float)(j*Math.PI/4),dx=(float)Math.cos(a)*22,dy=(float)Math.sin(a)*22;line(c,x,y,x+dx,y+dy,0xffe9b8f6,2);}star(c,x,y,5,WHITE,pulse);}break;
case 18: // oasis palms
for(int i=0;i<5;i++){float x=36+i*70,y=456+(i%2)*20;line(c,x,y,x+drift,y-65,0xff8a784a,6);for(int j=-2;j<=2;j++)line(c,x+drift,y-65,x+drift+j*15,y-75+Math.abs(j)*8,0xff83c97c,4);line(c,x-18,y+10,x+20,y+10,0xff4caaac,3);}break;
case 19: // ash citadel crenellations
for(int i=0;i<5;i++){float x=20+i*73,y=200+(i%2)*215;rect(c,x,y,57,51,0xff423b42);for(int j=0;j<4;j++)rect(c,x+j*16,y-14,10,15,0xff6b4b47);rect(c,x+18,y+18,18,33,0xff201e29);star(c,x+42,y+12,3,0xfff9a274,pulse);}break;
case 20: // submarine coral and pearls
for(int i=0;i<8;i++){float x=25+i*43,y=503-(i%3)*14;line(c,x,y,x+drift,y-48,0xff5eb3b1,4);line(c,x+drift,y-32,x+drift+14,y-48,0xff8be4d5,3);line(c,x+drift,y-20,x+drift-11,y-36,0xff8be4d5,3);p.reset();p.setColor(0xffc8faff);c.drawCircle(x+drift,y-62,3,p);}break;
case 21: // firefly flower garden
for(int i=0;i<10;i++){float x=25+i*34,y=480-(i%3)*19;line(c,x,y,x+drift,y-42,0xff4d9266,3);star(c,x+drift,y-44,6,0xffd6fc86,pulse);star(c,x+drift+8,y-64,2,0xfff6ffbc,pulse);}break;
case 22: // clockwork time gates
for(int i=0;i<4;i++){float x=44+i*88,y=210+(i%2)*199;p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(4);p.setColor(0xffbca4d2);c.drawCircle(x,y,26,p);p.setStyle(Paint.Style.FILL);line(c,x,y,x+drift+12,y-15,0xfff0d3f4,3);line(c,x,y,x-8,y-14,0xfff0d3f4,2);polygon(c,new float[]{x-6,y+13,x+6,y+13,x,y+24},0xff9bd9ee);}break;
case 23: // zenith crowns and aurora rays
for(int i=0;i<5;i++){float x=33+i*74,y=195+(i%2)*221;polygon(c,new float[]{x-24,y+16,x-23,y-6,x-11,y+1,x,y-20,x+11,y+1,x+23,y-6,x+24,y+16},0xffbca071);rect(c,x-22,y+16,44,6,0xfff9dca4);star(c,x,y-18,5,WHITE,pulse);line(c,x,y-29,x+drift,y-53,0x88f8d5a2,2);}break;
            default:break;
        }
        c.restore();
    }'''
marker="    private void drawBiomeLandmark(Canvas c,int biome,int theme){"
assert s.count(marker)==1
assert all(("case %d:"%i) in method for i in range(24))
s=s.replace(marker,method+"\n"+marker,1)
assert s.count("drawV47BiomeIdentity(c,biome,theme);")==1
mine.write_text(s)
b=gradle.read_text()
assert "versionCode 23" in b and "versionName '4.6'" in b
gradle.write_text(b.replace("versionCode 23","versionCode 24").replace("versionName '4.6'","versionName '4.7'"))
print("v4.7: 24 unique biome illustrations, no save or touch changes")
