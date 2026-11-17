using System.Reflection;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// 0.9.0-dev.37 (Osama 17 Nov 2026 14:0x PST: "make sure we're logging that these functions are not breaking when we optimize ... the hooks
// are watched for health and function"). Always on, counters only (no timing). One FREEDOM_ARROW_HOOK_HEALTH line every 60 s, also in the
// diagnostic log:
// - nlos: fog worker calls per second (the hook firing), NLOS shooter units found, units processed per second, enemies added to their
//   shootable set (total), broken. "NOT FIRING" when the hook is installed but no worker call came in 60 s of a battle.
// - overkill: merged-postfix calls per second, modules on, and each module's own counters: AaCooldown corrections (and shadow would-correct),
//   SameUnitClaim blocks, SEAD overkill holds, plus any module error.
static class HookHealth
{
    static float next=-1;static long lastWorker,lastProcessed,lastOverkill;
    static readonly (Type t,string f)[] Fields={(typeof(AaCooldown),"invocations"),(typeof(AaCooldown),"wouldCorrect"),(typeof(AaCooldown),"corrections"),
        (typeof(SameUnitClaim),"blocks"),(typeof(SameUnitClaim),"flips"),(typeof(SeadOverkill),"held")};
    static readonly Dictionary<string,FieldInfo> info=new();
    static EntitySet unitSet;static IntPtr unitWorld;
    // Live units in the battle world (all sides), so runs with different unit counts can be compared.
    static int Units()
    {
        var w=ShootingSystem._gameContext;if(w==null||w._isDisposed)return -1;
        if(unitWorld!=w.Pointer){try{unitSet?.Dispose();}catch{}unitSet=w.GetEntities().With<UnitComponent>().AsSet();unitWorld=w.Pointer;}
        return unitSet.Count;
    }
    static object Read(Type t,string f)
    {
        string k=t.Name+"."+f;
        if(!info.TryGetValue(k,out var fi)){fi=t.GetField(f,BindingFlags.NonPublic|BindingFlags.Static|BindingFlags.Public)!;info[k]=fi;}
        return fi?.GetValue(null);
    }
    public static void LateUpdate()
    {
        float now=Time.realtimeSinceStartup;
        if(next<0){next=now+60;return;}
        if(now<next)return;
        float span=now-next+60;next=now+60;
        try
        {
            bool battle=Runtime.IsApplied&&Conquest.Prototype.DiagnosticSceneActive;
            long w=NlosTrait.WorkerCalls,p=NlosTrait.UnitsProcessed,o=OverkillHooks.Calls;
            double wps=(w-lastWorker)/span,pps=(p-lastProcessed)/span,ops=(o-lastOverkill)/span;lastWorker=w;lastProcessed=p;lastOverkill=o;
            string nlos=!NlosTrait.FireInstalled?"off":NlosTrait.FireBroken?"BROKEN (vanilla line of sight)":battle&&wps==0?"NOT FIRING":"ok";
            var c=new Dictionary<string,string>();foreach(var x in Fields)c[x.t.Name+"."+x.f]=Convert.ToString(Read(x.t,x.f))??"";
            string errs=string.Join("; ",OverkillHooks.Errors.Where(e=>e!=null));
            int units=battle?Units():-1;
            MelonLogger.Msg($"FREEDOM_ARROW_HOOK_HEALTH {span:0} s, battle={battle}, units {units} | nlos {nlos}: fog worker {wps:0.0} calls/s, {NlosTrait.NlosUnits} NLOS units, "
                +$"{pps:0.0} unit updates/s, {NlosTrait.FireAdds} targets added total | overkill {(OverkillHooks.Modules.Length==0?"off":"ok")}: {ops:0} calls/s, modules {OverkillHooks.Modules}, "
                +$"aa corrections {c["AaCooldown.corrections"]} (would {c["AaCooldown.wouldCorrect"]}, seen {c["AaCooldown.invocations"]}), claim blocks {c["SameUnitClaim.blocks"]} flips {c["SameUnitClaim.flips"]}, "
                +$"sead holds {c["SeadOverkill.held"]} | settings-screen scene searches {FreedomArrow.Conquest.Prototype.SettingsSearches} total{(errs.Length>0?" | ERRORS "+errs:"")}");
            DiagnosticLog.Write("hook_health",new{span,battle,units,nlos,workerPerSecond=wps,nlosUnits=NlosTrait.NlosUnits,unitUpdatesPerSecond=pps,nlosTargetsAdded=NlosTrait.FireAdds,
                overkillPerSecond=ops,overkillModules=OverkillHooks.Modules,counters=c,errors=OverkillHooks.Errors});
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HOOK_HEALTH failed: "+e.Message);next=float.MaxValue;}
    }
}
