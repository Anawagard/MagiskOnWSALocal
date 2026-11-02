from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
activity=root/"app/src/main/java/com/bezdna/mine/MainActivity.java"
gradle=root/"app/build.gradle"

s=mine.read_text()
def once(old,new):
    global s
    assert s.count(old)==1,("Missing unique save/UI hook",old[:100],s.count(old))
    s=s.replace(old,new,1)

# Preserve all six resettable upgrades, not just the first four.
once('            ed.putInt("tech_"+i,tech[i]);\n','')
once('        ed.apply();\n    }\n}',
     '        for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);\n        ed.apply();\n    }\n}')
# Backup controls live inside existing settings: no gameplay or touch coordinates move.
once('        button(c,37,520,286,61,"НАЗАД В МАГАЗИН","Все настройки сохраняются",true);',
'''        button(c,37,476,136,51,"ЭКСПОРТ","Сохранить JSON",true);
        button(c,187,476,136,51,"ИМПОРТ","Загрузить JSON",true);
        button(c,37,544,286,57,"НАЗАД В МАГАЗИН","Все настройки сохраняются",true);
        fittedText(c,"РЕЗЕРВНАЯ КОПИЯ ЗАЩИЩАЕТ ПРОГРЕСС",180,618,10,MUTED,304);''')
once('            else if(y>=520&&y<=585){settingsOpen=false;playSound(2);}',
'''            else if(y>=476&&y<=531){
                playSound(2);
                if(getContext() instanceof MainActivity){
                    if(x<180)((MainActivity)getContext()).exportSave();
                    else ((MainActivity)getContext()).importSave();
                }
            }
            else if(y>=544&&y<=605){settingsOpen=false;playSound(2);}''')
mine.write_text(s)

a=activity.read_text()
assert "private void requestHighRefreshRate()" in a
assert "    @Override protected void onPause()" in a
assert "exportSave()" not in a
a=a.replace("import android.app.Activity;",
"""import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.widget.Toast;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;""",1)
extra=r"""
    private static final int EXPORT_SAVE=71,IMPORT_SAVE=72;

    public void exportSave(){
        if(game!=null)game.save();
        Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/json");
        intent.putExtra(Intent.EXTRA_TITLE,"shahta-save.json");
        startActivityForResult(intent,EXPORT_SAVE);
    }
    public void importSave(){
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/json");
        startActivityForResult(intent,IMPORT_SAVE);
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(result!=RESULT_OK||data==null||data.getData()==null)return;
        try{
            Uri uri=data.getData();
            if(request==EXPORT_SAVE){
                SharedPreferences prefs=getSharedPreferences("mine_save_v1",MODE_PRIVATE);
                JSONObject values=new JSONObject();
                for(Map.Entry<String,?> e:prefs.getAll().entrySet()){
                    Object value=e.getValue();
                    String type=value instanceof Long?"long":value instanceof Integer?"int":
                        value instanceof Float?"float":value instanceof Boolean?"bool":"string";
                    JSONObject item=new JSONObject();
                    item.put("t",type);
                    item.put("v",String.valueOf(value));
                    values.put(e.getKey(),item);
                }
                JSONObject document=new JSONObject();
                document.put("format","shahta-save-v1");
                document.put("values",values);
                OutputStream stream=getContentResolver().openOutputStream(uri);
                if(stream==null)throw new IOException("Не удалось открыть файл");
                try(OutputStream out=stream;OutputStreamWriter writer=
                    new OutputStreamWriter(out,"UTF-8")){
                    writer.write(document.toString(2));
                }
                Toast.makeText(this,"Копия сохранения создана",Toast.LENGTH_LONG).show();
            }else if(request==IMPORT_SAVE){
                InputStream stream=getContentResolver().openInputStream(uri);
                if(stream==null)throw new IOException("Не удалось прочитать файл");
                StringBuilder content=new StringBuilder();
                try(InputStream in=stream;BufferedReader reader=
                    new BufferedReader(new InputStreamReader(in,"UTF-8"))){
                    char[] buffer=new char[4096];
                    int n;
                    while((n=reader.read(buffer))!=-1){
                        content.append(buffer,0,n);
                        if(content.length()>262144)throw new IOException("Слишком большой файл");
                    }
                }
                JSONObject document=new JSONObject(content.toString());
                if(!"shahta-save-v1".equals(document.optString("format")))
                    throw new IOException("Неверный формат сохранения");
                JSONObject values=document.getJSONObject("values");
                if(values.length()>400)throw new IOException("Слишком много записей");
                HashMap<String,Object> restored=new HashMap<>();
                Iterator<String> keys=values.keys();
                while(keys.hasNext()){
                    String key=keys.next();
                    if(!key.matches("[A-Za-z0-9_]{1,80}"))
                        throw new IOException("Недопустимый ключ");
                    JSONObject item=values.getJSONObject(key);
                    String type=item.getString("t");
                    String value=item.getString("v");
                    if(value.length()>1024)throw new IOException("Слишком длинное значение");
                    Object parsed;
                    switch(type){
                        case "long":parsed=Long.parseLong(value);break;
                        case "int":parsed=Integer.parseInt(value);break;
                        case "float":
                            float f=Float.parseFloat(value);
                            if(!Float.isFinite(f))throw new IOException("Недопустимое число");
                            parsed=f;break;
                        case "bool":
                            if(!value.equals("true")&&!value.equals("false"))
                                throw new IOException("Недопустимый флаг");
                            parsed=Boolean.parseBoolean(value);break;
                        case "string":parsed=value;break;
                        default:throw new IOException("Неизвестный тип");
                    }
                    restored.put(key,parsed);
                }
                SharedPreferences.Editor edit=getSharedPreferences(
                    "mine_save_v1",MODE_PRIVATE).edit().clear();
                for(Map.Entry<String,Object> e:restored.entrySet()){
                    Object v=e.getValue();
                    if(v instanceof Long)edit.putLong(e.getKey(),(Long)v);
                    else if(v instanceof Integer)edit.putInt(e.getKey(),(Integer)v);
                    else if(v instanceof Float)edit.putFloat(e.getKey(),(Float)v);
                    else if(v instanceof Boolean)edit.putBoolean(e.getKey(),(Boolean)v);
                    else edit.putString(e.getKey(),String.valueOf(v));
                }
                if(!edit.commit())throw new IOException("Не удалось записать сохранение");
                game=new MineView(this);
                setContentView(game);
                Toast.makeText(this,"Прогресс восстановлен",Toast.LENGTH_LONG).show();
            }
        }catch(Exception ex){
            Toast.makeText(this,"Ошибка сохранения: "+ex.getMessage(),Toast.LENGTH_LONG).show();
        }
    }
"""
a=a.replace("    @Override protected void onPause()",extra+"\n    @Override protected void onPause()",1)
activity.write_text(a)

g=gradle.read_text()
assert g.count("versionCode 20")==1 and g.count("versionName '4.3'")==1
gradle.write_text(g.replace("versionCode 20","versionCode 21").replace("versionName '4.3'","versionName '4.4'"))
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert 'private static final int EXPORT_SAVE=71,IMPORT_SAVE=72' in a
assert 'startActivityForResult(intent,IMPORT_SAVE)' in a
print("v4.4: fixed six-upgrade persistence and added Android document backup/import UI")
