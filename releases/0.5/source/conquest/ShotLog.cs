using System.Reflection;
using System.Text.Json;
using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components;

namespace FreedomArrow.Conquest;
// 0.5 dev.32 (Lateralus): scenario editor tests. A scenario started with the editor Play button runs our combat
// rules (crits, front arc) and fire statistics, as a guarded match does. While combat rules are active, every shot
// and every real hit goes to UserData/FAConquestPrototype/shots-<utc>.jsonl. Logging only; it changes nothing.
public sealed partial class Prototype
{
    const int MaxShotLines=500000;
    static StreamWriter shotFile;
    static int shotLines;
    static bool shotOff,editorBound;
    static PropertyInfo editorInstance,editorLaunched,editorMode;
    // Editor Play, offline: ISceneLoadManager says the scenario came from the editor and the editor is not open.
    static bool EditorTest()
    {
        if(!ready||faulted||!config.Enabled)return false;
        try
        {
            if(!editorBound)
            {
                editorBound=true;
                var t=typeof(Il2CppBrokenArrow.Client.Ecs.Utils.ISceneLoadManager);
                editorInstance=t.GetProperty("Instance",BindingFlags.Public|BindingFlags.Static);
                editorLaunched=t.GetProperty("ScenarioLaunchedFromEditor");editorMode=t.GetProperty("IsEditorMode");
            }
            var manager=editorInstance?.GetValue(null);
            if(manager==null||editorLaunched?.GetValue(manager) is not true||editorMode?.GetValue(manager) is not false)return false;
            if(view!=null&&view.Service._isOnline)return false;
            var runtime=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="FreedomArrow.Runtime");
            return runtime?.GetType("FreedomArrow.Runtime")?.GetProperty("IsApplied")?.GetValue(null) is true;
        }
        catch(Exception e){editorInstance=null;MelonLogger.Warning("FREEDOM_ARROW_EDITOR_TEST check failed: "+e.Message);return false;}
    }
    static void ShotFrame(bool active)
    {
        if(active&&shotFile==null&&!shotOff)
        {
            try
            {
                Directory.CreateDirectory(Root);shotLines=0;
                shotFile=new StreamWriter(Path.Combine(Root,$"shots-{DateTime.UtcNow:yyyyMMdd-HHmmss}.jsonl"));
                ShotLine("start",new{editor=EditorTest(),version=typeof(Prototype).Assembly.GetName().Version?.ToString()});
                MelonLogger.Msg("FREEDOM_ARROW_SHOT_LOG started");
            }
            catch(Exception e){shotOff=true;MelonLogger.Error("FREEDOM_ARROW_SHOT_LOG_FAILED: "+e.Message);}
        }
        else if(!active&&shotFile!=null){ShotLine("stop",new{lines=shotLines});shotFile.Dispose();shotFile=null;MelonLogger.Msg("FREEDOM_ARROW_SHOT_LOG closed");}
        else shotFile?.Flush();
    }
    static void ShotLine(string kind,object data)
    {
        if(shotFile==null||shotOff)return;
        try
        {
            shotFile.WriteLine(JsonSerializer.Serialize(new{t=Math.Round(Time.time,2),kind,data}));
            if(++shotLines>=MaxShotLines){shotOff=true;shotFile.Dispose();shotFile=null;MelonLogger.Warning("FREEDOM_ARROW_SHOT_LOG line limit reached");}
        }
        catch(Exception e){shotOff=true;MelonLogger.Error("FREEDOM_ARROW_SHOT_LOG_FAILED: "+e.Message);}
    }
    static object UnitInfo(Entity unit)
    {
        if(!unit.IsAlive||!unit.Has<UnitComponent>())return null;
        var u=NativeEcs.Read<UnitComponent>(unit);
        return new{e=unit.GetHashCode(),id=u.UnitData?.Id??0,name=u.UnitData?.Name,team=u.Owner?.TeamSide.ToString()};
    }
    static void LogShot(Entity weapon,WeaponComponent w,string ammo)
    {
        if(shotFile==null)return;
        object shooter=null;
        try{shooter=UnitInfo(w.GetUnitEntity());}catch{}
        ShotLine("shot",new{weapon=weapon.GetHashCode(),weaponId=w.WeaponInfo?.Id??0,weaponName=w.WeaponInfo?.Name,ammo,ammoId=w.SelectedAmmunition?.Id??0,shooter,magazine=w.AmmoInMagazine.Value});
    }
    static void LogHit(Entity target,string ammo,int ammoId,string side,float damage)
    {
        if(shotFile==null)return;
        ShotLine("hit",new{ammo,ammoId,side,damage=Math.Round(damage,3),target=UnitInfo(target)});
    }
}
