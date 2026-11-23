using System.Reflection;
using System.Text.Json;
using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Client.Ecs.Infantry.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;

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
        return new{e=unit.GetHashCode(),id=u.UnitData?.Id??0,name=u.UnitData?.Name,team=u.Owner?.TeamSide.ToString(),unitType=(int)(u.UnitData?.Type??0),infantry=unit.Has<InfantryUnitComponent>()};
    }
    static object Timing(WeaponComponent w)
    {
        try{return new{reload=Math.Round(w.GetMagazineReloadTime(),3),betweenBursts=Math.Round(w.GetTimeBetweenBursts(),3),inBurst=w.TimeBetweenShotsInBurst,shotsPerBurst=w.ShotsPerBurst.Value,inBurstLeft=w.ShotsRemainingInBurst,aim=Math.Round(w.GetAimTime(),3),magazineSize=w.WeaponInfo?.MagazineSize??0};}
        catch{return null;}
    }
    static void LogShot(Entity weapon,WeaponComponent w,string ammo)
    {
        if(shotFile==null)return;
        object shooter=null;Entity unit=default;
        try{unit=w.GetUnitEntity();shooter=UnitInfo(unit);}catch{}
        ShotLine("shot",new{weapon=weapon.GetHashCode(),weaponId=w.WeaponInfo?.Id??0,weaponName=w.WeaponInfo?.Name,weaponType=(int)(w.WeaponInfo?.Type??0),ammo,ammoId=w.SelectedAmmunition?.Id??0,shooter,magazineAfter=w.AmmoInMagazine.Value,shotsMade=w.ShotsMade.Value,timing=Timing(w)});
    }
    static void InstallShotLog()
    {
        // dev.34: the dev.33 reload-roll hook and the native carrier lookup are removed; dev.33 crashed in editor Play.
        MelonLogger.Msg("FREEDOM_ARROW_SHOT_LOG installed: shots and hits in guarded matches and editor tests");
    }
    static void LogHit(Entity target,string ammo,int ammoId,string side,float damage,string armorTargeted,float baseDamage)
    {
        if(shotFile==null)return;
        float hp=0;try{if(target.IsAlive&&target.Has<HealthComponent>())hp=NativeEcs.Field<HealthComponent,float>(target,"_health");}catch{}
        ShotLine("hit",new{ammo,ammoId,armorTargeted,baseDamage,side,damage=Math.Round(damage,3),targetHpBefore=Math.Round(hp,3),target=UnitInfo(target)});
    }
}
