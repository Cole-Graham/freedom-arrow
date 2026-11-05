using System.Diagnostics;
using System.Text.Json;
using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components.Movement;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Missiles.Components;
using Il2CppBrokenArrow.Client.Ecs.Infantry.Components;

namespace FreedomArrow.Conquest;
// A read-only game state log for F8 and private online matches. It has no combat hooks. Once a second it reads units and
// weapons from the main thread and writes only what changed, so the last line shows the state before a crash.
public sealed partial class Prototype
{
    const float StateSeconds=1,SlowSampleMs=30,StressStep=25;
    const int SlowSamplesForWeaponsOff=3,SlowSamplesForLogOff=6,MaxStateLines=300000;
    sealed class SeenUnit { public int Id;public string Name,Team,Crits;public float Hp,Stress;public int Soldiers; }
    static readonly Dictionary<int,SeenUnit> seenUnits=new();
    static readonly Dictionary<int,(int shots,int magazine)> seenShots=new();
    static readonly HashSet<int> liveUnits=new();
    static StreamWriter stateFile;
    static IntPtr stateMode;
    static bool stateOff,stateWeaponsOff;
    static int stateLines,stateSlow,stateFrames;
    static float stateNext,stateWorst;
    static void StateLine(string kind,object data)
    {
        stateLines++;
        stateFile.WriteLine(JsonSerializer.Serialize(new{kind,data}));
    }
    static void CloseStateLog()
    {
        stateFile?.Dispose();stateFile=null;stateMode=IntPtr.Zero;
        seenUnits.Clear();seenShots.Clear();
    }
    static void StateFrame()
    {
        if(stateOff||!config.StateLog)return;
        try
        {
            if(view==null||!Guarded(view.Service)){if(stateFile!=null)CloseStateLog();return;}
            stateFrames++;stateWorst=Math.Max(stateWorst,Time.unscaledDeltaTime);
            if(Time.unscaledTime<stateNext)return;
            stateNext=Time.unscaledTime+StateSeconds;
            if(stateMode!=view.Pointer)
            {
                CloseStateLog();
                stateMode=view.Pointer;stateLines=0;stateSlow=0;stateWeaponsOff=false;
                stateFile=new StreamWriter(Path.Combine(Root,$"state-{DateTime.UtcNow:yyyyMMdd-HHmmss}.jsonl"));
                MelonLogger.Msg("FREEDOM_ARROW_STATE_LOG started");
            }
            StateSample();
            stateFile.Flush();
            if(stateLines>=MaxStateLines)throw new InvalidOperationException("Line limit reached");
        }
        catch(Exception e)
        {
            stateOff=true;CloseStateLog();
            MelonLogger.Error("FREEDOM_ARROW_STATE_LOG_FAILED: off for this session. "+e.Message);
        }
    }
    static void StateSample()
    {
        var clock=Stopwatch.StartNew();
        var game=GameController.Instance;
        bool paused=game.GameSession.IsPaused;
        int alpha=0,bravo=0,missiles=0,weapons=0;
        // A paused game has no combat, so only the frame data changes.
        if(!paused)
        {
            liveUnits.Clear();
            foreach(var entity in game.GameContext)
            {
                if(entity.Has<MissileGuidanceInfoComponent>())missiles++;
                if(entity.Has<WeaponComponent>()){weapons++;if(!stateWeaponsOff)StateWeapon(entity);}
                if(!entity.Has<UnitComponent>()||!entity.Has<HealthComponent>())continue;
                var unit=StateUnit(entity);
                if(unit.Team=="Alpha")alpha++;else bravo++;
            }
            foreach(var key in seenUnits.Keys.Where(k=>!liveUnits.Contains(k)).ToList())
            {
                var gone=seenUnits[key];
                StateLine("gone",new{e=key,gone.Id,gone.Name,gone.Team,gone.Hp,gone.Soldiers});
                seenUnits.Remove(key);
            }
        }
        var next=ledger.Forecast(zones);
        float ms=clock.ElapsedMilliseconds;
        StateLine("state",new{utc=DateTime.UtcNow.ToString("O"),ledger.Elapsed,paused,game.TimeScale,
            fps=stateFrames/StateSeconds,worstFrameMs=stateWorst*1000,managedMb=GC.GetTotalMemory(false)/1048576,
            alpha,bravo,missiles,weapons,scoreAlpha=ledger.Alpha,scoreBravo=ledger.Bravo,nextAlpha=next.Alpha,nextBravo=next.Bravo,sampleMs=ms});
        stateFrames=0;stateWorst=0;
        stateSlow=ms>SlowSampleMs?stateSlow+1:0;
        if(stateSlow==SlowSamplesForWeaponsOff&&!stateWeaponsOff){stateWeaponsOff=true;StateLine("weapons_off",new{ms});}
        if(stateSlow>=SlowSamplesForLogOff)throw new InvalidOperationException($"Samples too slow: {ms} ms");
    }
    static SeenUnit StateUnit(Entity entity)
    {
        int key=entity.GetHashCode();
        liveUnits.Add(key);
        float hp=NativeEcs.Field<HealthComponent,float>(entity,"_health");
        float stress=entity.Has<StressComponent>()?NativeEcs.Field<StressComponent,float>(entity,"CurrentStressValue"):0;
        int soldiers=entity.Has<InfantryUnitComponent>()?(int)NativeEcs.Field<InfantryUnitComponent,uint>(entity,"AliveSoldierCount"):0;
        if(!seenUnits.TryGetValue(key,out var seen))
        {
            var data=NativeEcs.Read<UnitComponent>(entity);
            seen=new SeenUnit{Crits=StateCrits(entity),Id=data.UnitData?.Id??0,Name=data.UnitData?.Name,Team=data.Owner.TeamSide.ToString(),Hp=hp,Stress=stress,Soldiers=soldiers};
            seenUnits[key]=seen;
            StateLine("unit",new{e=key,seen.Id,seen.Name,seen.Team,hp,max=NativeEcs.Field<HealthComponent,float>(entity,"MaxHealth"),soldiers,infantry=entity.Has<InfantryUnitComponent>()});
            return seen;
        }
        // Crit levels from any source, native or ours: optics, mobility, targeting, loading. 0 none, 1 yellow, 2 red.
        string crits=StateCrits(entity);
        if(crits!=seen.Crits){StateLine("crits",new{e=key,seen.Id,seen.Team,before=seen.Crits,crits});seen.Crits=crits;}
        bool hit=hp!=seen.Hp||soldiers!=seen.Soldiers;
        if(hit)
        {
            var position=NativeEcs.Property<TransformComponent,Vector3>(entity,"Position");
            string terrain=entity.Has<TerrainTypeComponent>()?NativeEcs.Field<TerrainTypeComponent,Il2CppBrokenArrow.Shared.Ecs.Enums.TerrainType>(entity,"Value").ToString():null;
            StateLine("hp",new{e=key,seen.Id,seen.Team,hp,delta=hp-seen.Hp,soldiers,stress,terrain,x=position.x,y=position.y,z=position.z});
        }
        else if(Math.Abs(stress-seen.Stress)>=StressStep)StateLine("stress",new{e=key,seen.Id,seen.Team,stress});
        else return seen;
        seen.Hp=hp;seen.Stress=stress;seen.Soldiers=soldiers;
        return seen;
    }
    static void StateWeapon(Entity entity)
    {
        var weapon=NativeEcs.Read<WeaponComponent>(entity);
        // ShotsMade did not change in a live online match, so a magazine change also counts as a shot.
        int key=entity.GetHashCode(),shots=(int)weapon.ShotsMade.Value,magazine=(int)weapon.AmmoInMagazine.Value;
        bool known=seenShots.TryGetValue(key,out var last);
        if(known&&last==(shots,magazine))return;
        seenShots[key]=(shots,magazine);
        int? owner=entity.Has<ParentComponent>()?NativeEcs.Field<ParentComponent,Entity>(entity,"Root").GetHashCode():null;
        StateLine("shots",new{e=key,owner,weapon=weapon.WeaponInfo?.Id,ammo=weapon.SelectedAmmunitionId,shots,fired=shots-last.shots,magazine,used=known?last.magazine-magazine:0});
    }
    static string StateCrits(Entity entity)
    {
        if(!entity.Has<CriticalEffectComponent>())return null;
        var status=NativeEcs.Read<CriticalEffectComponent>(entity).CriticalEffectStatus;
        if(status==null)return null;
        int Level(Il2CppBrokenArrow.Client.Ecs.BattleSystem.CriticalEffectTypes t)=>status.ContainsKey(t)?status[t]:0;
        return $"O{Level(Il2CppBrokenArrow.Client.Ecs.BattleSystem.CriticalEffectTypes.Optics)} M{Level(Il2CppBrokenArrow.Client.Ecs.BattleSystem.CriticalEffectTypes.Mobility)} T{Level(Il2CppBrokenArrow.Client.Ecs.BattleSystem.CriticalEffectTypes.Targeting)} L{Level(Il2CppBrokenArrow.Client.Ecs.BattleSystem.CriticalEffectTypes.Loading)}";
    }
}
