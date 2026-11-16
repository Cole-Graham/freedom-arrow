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
    static bool shotOff,editorBound,shotRunActive;
    static int shotRun;
    static float nextShotFlush;
    static PropertyInfo editorInstance,editorLaunched,editorMode;
    // Editor Play, offline: ISceneLoadManager says the scenario came from the editor and the editor is not open.
    internal static bool DiagnosticSceneActive=>combatActive;
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
            return FreedomArrow.Runtime.IsApplied;
        }
        catch(Exception e){editorInstance=null;MelonLogger.Warning("FREEDOM_ARROW_EDITOR_TEST check failed: "+e.Message);return false;}
    }
    static void ShotFrame(bool active)
    {
        if(active&&!shotRunActive&&!shotOff)
        {
            try
            {
                if(shotFile==null)
                {
                    Directory.CreateDirectory(Root);shotLines=0;
                    shotFile=new StreamWriter(Path.Combine(Root,$"shots-{DateTime.UtcNow:yyyyMMdd-HHmmssfffffff}-{Environment.ProcessId}.jsonl"));
                }
                shotRun++;shotRunActive=true;shotRepeat.Clear();penTotals.Clear();
                ShotLine("start",new{run=shotRun,editor=EditorTest(),packageVersion=Runtime.DiagnosticPackageVersion});
                MelonLogger.Msg("FREEDOM_ARROW_SHOT_LOG started run "+shotRun+" (one session file)");
            }
            catch(Exception e){shotOff=true;MelonLogger.Error("FREEDOM_ARROW_SHOT_LOG_FAILED: "+e.Message);}
        }
        else if(!active&&shotRunActive)
        {
            WritePenSummary();
            ShotLine("stop",new{run=shotRun,lines=shotLines});shotRunActive=false;
            shotFile?.Flush();MelonLogger.Msg("FREEDOM_ARROW_SHOT_LOG run stopped; session file retained");
        }
        else if(Time.unscaledTime>=nextShotFlush){nextShotFlush=Time.unscaledTime+1f;shotFile?.Flush();}
    }
    static void CloseShotSession()
    {
        try
        {
            if(shotRunActive){WritePenSummary();ShotLine("stop",new{run=shotRun,reason="shutdown",lines=shotLines});}
            shotFile?.Flush();shotFile?.Dispose();
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_SHOT_LOG close failed: "+e.Message);}
        finally{shotFile=null;shotRunActive=false;}
    }
    static void ShotLine(string kind,object data)
    {
        if(shotFile==null||shotOff)return;
        try
        {
            shotFile.WriteLine(JsonSerializer.Serialize(new{t=Math.Round(Time.time,2),run=shotRun,kind,data}));
            if(++shotLines>=MaxShotLines){shotOff=true;shotFile.Dispose();shotFile=null;MelonLogger.Warning("FREEDOM_ARROW_SHOT_LOG line limit reached");}
        }
        catch(Exception e){shotOff=true;MelonLogger.Error("FREEDOM_ARROW_SHOT_LOG_FAILED: "+e.Message);}
    }
    static object UnitInfo(Entity unit)
    {
        if(!unit.IsAlive||!unit.Has<UnitComponent>())return null;
        var u=NativeEcs.Read<UnitComponent>(unit);
        return new{e=unit.GetHashCode(),identity=System.Runtime.CompilerServices.Unsafe.As<Entity,ulong>(ref unit).ToString("X16"),id=u.UnitData?.Id??0,name=u.UnitData?.Name,team=u.Owner?.TeamSide.ToString(),unitType=(int)(u.UnitData?.Type??0),infantry=unit.Has<InfantryUnitComponent>()};
    }
    static object Timing(WeaponComponent w)
    {
        try{return new{reload=Math.Round(w.GetMagazineReloadTime(),3),betweenBursts=Math.Round(w.GetTimeBetweenBursts(),3),inBurst=w.TimeBetweenShotsInBurst,shotsPerBurst=w.ShotsPerBurst.Value,inBurstLeft=w.ShotsRemainingInBurst,aim=Math.Round(w.GetAimTime(),3),magazineSize=w.WeaponInfo?.MagazineSize??0};}
        catch{return null;}
    }
    static readonly Dictionary<int,(int mag,float t)> shotRepeat=new();
    static void LogShot(Entity weapon,WeaponComponent w,string ammo)
    {
        GroundAaLog.Fired(weapon);
        if(shotFile==null)return;
        // Lateralus batch, 9 November 2026: the Patriot repeats the shot callback every frame with an unchanged magazine
        // (185 lines in 6 s, shotsMade 0). Skip a repeat of the same weapon and magazine count within 0.25 s.
        int key=weapon.GetHashCode(),mag=w.AmmoInMagazine.Value;float now=Time.time;
        if(shotRepeat.TryGetValue(key,out var last)&&last.mag==mag&&now-last.t<0.25f){shotRepeat[key]=(mag,now);return;}
        shotRepeat[key]=(mag,now);
        object shooter=null;Entity unit=default;
        try{unit=w.GetUnitEntity();shooter=UnitInfo(unit);}catch{}
        ShotLine("shot",new{weapon=weapon.GetHashCode(),weaponId=w.WeaponInfo?.Id??0,weaponName=w.WeaponInfo?.Name,weaponType=(int)(w.WeaponInfo?.Type??0),ammo,ammoId=w.SelectedAmmunition?.Id??0,shooter,magazineAfter=w.AmmoInMagazine.Value,shotsMade=w.ShotsMade.Value,timing=Timing(w)});
    }
    static void InstallShotLog()
    {
        // dev.34: the dev.33 reload-roll hook and the native carrier lookup are removed; dev.33 crashed in editor Play.
        MelonLogger.Msg("FREEDOM_ARROW_SHOT_LOG installed: shots and hits in guarded matches and editor tests");
    }
    // 0.9.0-dev.12 (Osama 15 Nov 2026: "can you log penetration"): each hit line also has the penetration the game used, the target's
    // armour on the hit side (BattleSystemHelpers.GetArmorBySideAndType, the armour type the round attacks), whether penetration reached
    // that armour, the top-attack flag and the shell's distance travelled (-1 when the shell has no trajectory). The run's stop line is
    // preceded by one pen_summary line per ammunition, target unit and side. In a multiplayer match each game logs the hits its own
    // units' shells make; the other player's file has the hits on this player's units.
    sealed class PenTotal{public int Hits,Through;public double Pen,Damage;public int Armor;}
    static readonly System.Collections.Concurrent.ConcurrentDictionary<(int ammo,int unit,int side),PenTotal> penTotals=new();
    static void LogHit(Entity target,Il2CppBrokenArrow.DataBase.Models.Ammunitions a,Il2CppBrokenArrow.Client.Ecs.BattleSystem.ArmorSides side,float damage,float penetration,bool forceTop,float distance)
    {
        if(shotFile==null)return;
        float hp=0;try{if(target.IsAlive&&target.Has<HealthComponent>())hp=NativeEcs.Field<HealthComponent,float>(target,"_health");}catch{}
        int armor=-1,unit=0;
        try
        {
            var data=target.IsAlive&&target.Has<UnitComponent>()?NativeEcs.Read<UnitComponent>(target).UnitData:null;
            if(data!=null){unit=data.Id;armor=Il2CppBrokenArrow.Client.Ecs.BattleSystem.BattleSystemHelpers.GetArmorBySideAndType(data,a.ArmorTargeted,side);}
        }
        catch{}
        bool through=armor>=0&&penetration>=armor;
        ShotLine("hit",new{ammo=a.Name,ammoId=a.Id,armorTargeted=a.ArmorTargeted.ToString(),baseDamage=a.Damage,side=side.ToString(),damage=Math.Round(damage,3),targetHpBefore=Math.Round(hp,3),
            penetration=Math.Round(penetration,2),armor,penetrated=armor>=0?(bool?)through:null,forceTop,distance=distance<0?(double?)null:Math.Round(distance,1),target=UnitInfo(target)});
        var total=penTotals.GetOrAdd((a.Id,unit,(int)side),_=>new PenTotal{Armor=armor});
        lock(total){total.Hits++;if(through)total.Through++;total.Pen+=penetration;total.Damage+=damage;}
    }
    static void WritePenSummary()
    {
        foreach(var (k,v) in penTotals.OrderBy(x=>x.Key.ammo).ThenBy(x=>x.Key.unit))
            ShotLine("pen_summary",new{ammoId=k.ammo,targetUnit=k.unit,side=((Il2CppBrokenArrow.Client.Ecs.BattleSystem.ArmorSides)k.side).ToString(),hits=v.Hits,penetrated=v.Through,armor=v.Armor,
                meanPenetration=Math.Round(v.Pen/v.Hits,2),damage=Math.Round(v.Damage,2)});
        if(penTotals.Count>0)MelonLogger.Msg($"FREEDOM_ARROW_SHOT_LOG penetration summary: {penTotals.Count} ammunition/target/side rows, {penTotals.Values.Sum(x=>x.Hits)} hits");
        penTotals.Clear();
    }
}
