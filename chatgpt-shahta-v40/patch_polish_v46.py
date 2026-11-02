from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
activity=root/"app/src/main/java/com/bezdna/mine/MainActivity.java"
gradle=root/"app/build.gradle"
s=mine.read_text()
def once(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a))
    s=s.replace(a,b,1)
# The visual progress meter must agree with the existing 25-stage biome zones.
once("        int step=(depth-1)%15;","        int step=(depth-1)%25;")
once('"ДО СЛЕДУЮЩЕЙ ЗОНЫ  "+(15-step)+" УР."',
     '"ДО СЛЕДУЮЩЕЙ ЗОНЫ  "+(25-step)+" УР."')
once('bar(c,31,603,298,6,step/15f,bcol);',
     'bar(c,31,603,298,6,step/25f,bcol);')
# Distinct milestone diamonds on the progress rail, independent of input.
once('            bar(c,31,603,298,6,step/25f,bcol);\n',
'''            bar(c,31,603,298,6,step/25f,bcol);
            for(int milestone=1;milestone<5;milestone++){
                float mx=31+298*milestone/5f;
                polygon(c,new float[]{mx,601,mx+3,606,mx,611,mx-3,606},
                    step>=milestone*5?0xfff0dba5:0xff4b6978);
            }
''')
mine.write_text(s)
a=activity.read_text()
assert 'Float.isFinite(f)' in a
a=a.replace('!Float.isFinite(f)','(Float.isNaN(f)||Float.isInfinite(f))',1)
activity.write_text(a)
g=gradle.read_text()
assert "versionCode 22" in g and "versionName '4.5'" in g
assert "signingConfigs" not in g
g=g.replace("    compileOptions {", """    // Debug-only signing key restored from CI cache. Do not use for production.
    signingConfigs {
        shahtaDebug {
            storeFile file(System.getenv('HOME') + '/.android/debug.keystore')
            storePassword 'android'
            keyAlias 'androiddebugkey'
            keyPassword 'android'
        }
    }
    buildTypes {
        debug {
            signingConfig signingConfigs.shahtaDebug
        }
    }
    compileOptions {""")
gradle.write_text(g.replace("versionCode 22","versionCode 23").replace("versionName '4.5'","versionName '4.6'"))
assert "drawV45Guardian" in s and "drawV43AtlasThumbnail" in s
print("v4.6: corrected 25-stage biome rail, milestone diamonds and Android-compatible save import validation")
