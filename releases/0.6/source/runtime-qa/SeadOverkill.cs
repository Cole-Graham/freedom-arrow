using System.Collections.Concurrent;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// SEAD overkill allowance (Lateralus 16 Nov 2026 06:38 PST, thread 1571554273639006392: "implement this proposal A"). Read from GameAssembly
// 6000.3.24f1: OverkillScoringSystem.IsTargetOverkilled is true when the missiles already flying at a target reach its kill-score threshold AND
// a 80% kill chance (BattleSystemSettings.MINIMAL_CHANCE_TO_KILL). CalculateMissileOverkillScore multiplies a Seeker-200 (anti-radiation)
// missile's capped damage score by SEAD_SCORE_MULTIPLIER (vanilla 0.99), so one SEAD missile is never a sure kill and two are: about 2 in
// flight per target, whoever fired them. Enemy SAMs and guns are not counted, so with 5 HP missiles and the SPAAG tiers most of those 2 die
// and every other launcher at that radar is held (RemoveTarget reason 13). sead-overkill.json sets the multiplier (0.33: up to 4 in flight).
// Log: every IsTargetOverkilled == true for a SEAD launcher, with the missile score, kill chance and missile count already on the target
// (GetCurrentMissileScoreOnTarget). The hook only queues keys (it can run off the main thread); LateUpdate reads the game state.
static class SeadOverkill
{
    const int MaxLog=400,QueueMax=512;
    static float value=0.33f,vanilla=float.NaN;static bool on,applied,broken;static int logged,held,lastHeld;static float nextSummary;
    static readonly ConcurrentQueue<(Entity Target,Entity Caller)> Hits=new();
    static readonly Dictionary<ulong,(bool Sead,float At)> sead=new();
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var file=Path.Combine(root,"sead-overkill.json");if(!File.Exists(file))return;
        var c=JsonNode.Parse(File.ReadAllText(file))!;value=c["SeadScoreMultiplier"]?.GetValue<float>()??0.33f;
        if(!(value>0&&value<=1))throw new InvalidDataException("sead-overkill.json: SeadScoreMultiplier must be in (0, 1]");
        var m=AccessTools.Method(typeof(OverkillScoringSystem),"IsTargetOverkilled")??throw new MissingMethodException("IsTargetOverkilled");
        harmony.Patch(m,postfix:new HarmonyMethod(typeof(SeadOverkill),nameof(After)){priority=Priority.Last});
        on=true;
        MelonLogger.Msg($"FREEDOM_ARROW_SEAD_OVERKILL installed: SEAD missile overkill score multiplier {value} (vanilla 0.99)");
        DiagnosticLog.Write("sead_overkill_installed",new{SeadScoreMultiplier=value});
    }
    static void After(ref Entity __0,ref Entity __3,bool __result)
    {
        if(!__result||!on||Hits.Count>=QueueMax)return;
        Hits.Enqueue((__0,__3));
    }
    public static void LateUpdate()
    {
        if(!on||broken)return;
        try
        {
            if(!applied)
            {
                var s=OverkillScoringSystem._battleSettings;
                if(s!=null){vanilla=s.SEAD_SCORE_MULTIPLIER;s.SEAD_SCORE_MULTIPLIER=value;applied=true;
                    DiagnosticLog.Write("sead_overkill_applied",new{vanilla,now=s.SEAD_SCORE_MULTIPLIER,minimalChanceToKill=s.MINIMAL_CHANCE_TO_KILL});
                    MelonLogger.Msg($"FREEDOM_ARROW_SEAD_OVERKILL applied: SEAD_SCORE_MULTIPLIER {vanilla} -> {s.SEAD_SCORE_MULTIPLIER}");}
            }
            else if(OverkillScoringSystem._battleSettings is {} s2&&s2.SEAD_SCORE_MULTIPLIER!=value)
            {   // a scene reload restored the asset: apply again
                DiagnosticLog.Write("sead_overkill_reapplied",new{found=s2.SEAD_SCORE_MULTIPLIER,value});s2.SEAD_SCORE_MULTIPLIER=value;
            }
            float now=Time.time;
            for(int n=0;n<64&&Hits.TryDequeue(out var h);n++)
            {
                var caller=h.Caller;if(!caller.IsAlive||!caller.Has<WeaponComponent>())continue;
                ulong ck=Key(caller);
                if(!sead.TryGetValue(ck,out var r)||now-r.At>5)
                {
                    var w=NativeEcs.Read<WeaponComponent>(caller);
                    r=((int)(w?.SelectedAmmunition?.Seeker??0)==200,now);if(sead.Count>4096)sead.Clear();sead[ck]=r;
                }
                if(!r.Sead)continue;
                held++;
                if(logged>=MaxLog)continue;
                var target=h.Target;if(!target.IsAlive)continue;
                var t=OverkillScoringSystem.GetCurrentMissileScoreOnTarget(ref target,false,false,ref caller,false,false,true,false,false,false);
                string name="";try{name=NativeEcs.Read<UnitComponent>(target).UnitData?.Name??"";}catch{}
                logged++;
                DiagnosticLog.Write("sead_overkill_held",new{t=now,target=name,missileScore=t.Item1,killChance=t.Item2,missilesInFlight=t.Item3,
                    multiplier=OverkillScoringSystem._battleSettings?.SEAD_SCORE_MULTIPLIER});
            }
            if(now>=nextSummary){nextSummary=now+60;if(held!=lastHeld){DiagnosticLog.Write("sead_overkill_summary",new{t=now,heldTotal=held});lastHeld=held;}}
        }
        catch(Exception x)
        {
            broken=true;DiagnosticLog.Write("sead_overkill_failed",new{error=x.ToString()});
            MelonLogger.Error("FREEDOM_ARROW_SEAD_OVERKILL_FAILED: logging stopped; the multiplier set so far stays. "+x.Message);
        }
    }
    public static void SceneChanged(){sead.Clear();while(Hits.TryDequeue(out _)){}}
}
