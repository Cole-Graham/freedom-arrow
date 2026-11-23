using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs.BattleSystem;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// The 12 SPAAG guns of the Lateralus missile-hp batch (15 November 2026, thread 1571554273639006392), listed by weapon ID in
// UserData/FreedomArrow/spaag-weapons.json. No file = vanilla behaviour for both parts.
// 1. Card DPS: "The damage per second should factor in burst cooldowns, but not magazine reloads." Vanilla WeaponHelper.DamagePerSecond
//    (RVA 0x2BD660) = ammoDamage * RateOfFireSecond(weapon, 1, 1, 1); RateOfFireSecond (0x2BD6A0) averages the min/max burst cycle
//    and adds MagazineReloadTime * magazineReloadTimeModifier. The postfix scales the result by RateOfFireSecond(w,1,1,0)/(w,1,1,1),
//    so only the reload term goes. DamagePerSecond has two callers, both Arsenal card UI (AmmoInfoExpansionPanel.SetMainAmmoStats,
//    UnitAmmoCompactInfo.SetPenetrationAndDamage); battle code calls RateOfFireSecond directly and is not touched.
// 2. Burst refill: "it would be nice if the burst would reload on downtime even when there was still a few bullets left in the burst".
//    Native ShotsRemainingInBurst (0x82FA80) = ShotsPerBurst - ShotsMade, and ShotsMade survives idle time (24 of 57 test engagements
//    began with a part-used burst). When a listed gun has not fired for idleSeconds and is not in a burst pause, ShotsMade goes back to 0.
static class SpaagWeapons
{
    const int MaxLog=200;
    static HashSet<int> ids=new();
    static float idle;
    static bool dpsBroken,refillBroken;
    static int dpsLogged,refillLogged,refills;
    static World world;
    static EntitySet weapons;
    static float nextScan,nextPoll;
    static readonly List<Entity> listed=new();
    static readonly Dictionary<ulong,(int made,int ammo,float at)> seen=new();
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var file=Path.Combine(root,"spaag-weapons.json");
        if(!File.Exists(file))return;
        var cfg=JsonNode.Parse(File.ReadAllText(file));
        ids=cfg?["weapons"]?.AsArray().Select(x=>x!.GetValue<int>()).ToHashSet()??new();
        idle=cfg?["burstRefillIdleSeconds"]?.GetValue<float>()??0;
        if(ids.Count==0)return;
        var method=AccessTools.Method(typeof(WeaponHelper),"DamagePerSecond")??throw new MissingMethodException("WeaponHelper.DamagePerSecond");
        harmony.Patch(method,postfix:new HarmonyMethod(typeof(SpaagWeapons),nameof(Dps)));
        MelonLogger.Msg($"FREEDOM_ARROW_SPAAG_WEAPONS installed: {ids.Count} guns, card DPS without magazine reload, burst refill after {idle} s idle");
        DiagnosticLog.Write("spaag_weapons_installed",new{weapons=ids.OrderBy(x=>x).ToArray(),idle});
    }
    static void Dps(Weapons __0,float __1,ref float __result)
    {
        if(dpsBroken||__0==null||!ids.Contains(__0.Id))return;
        try
        {
            float with=WeaponHelper.RateOfFireSecond(__0,1f,1f,1f),without=WeaponHelper.RateOfFireSecond(__0,1f,1f,0f);
            if(!(with>0)||!float.IsFinite(without))return;
            float before=__result;__result*=without/with;
            if(dpsLogged<MaxLog){dpsLogged++;DiagnosticLog.Write("spaag_card_dps",new{weapon=__0.Id,ammoDamage=__1,before,after=__result,with,without});}
        }
        catch(Exception x){dpsBroken=true;DiagnosticLog.Write("spaag_card_dps_failed",new{error=x.ToString()});MelonLogger.Error("FREEDOM_ARROW_SPAAG_DPS_FAILED: vanilla card DPS. "+x.Message);}
    }
    public static void SceneChanged()
    {
        try{if(world!=null&&!world._isDisposed)weapons?.Dispose();}catch{}
        world=null;weapons=null;listed.Clear();seen.Clear();nextScan=nextPoll=0;
    }
    public static void LateUpdate()
    {
        if(refillBroken||idle<=0||ids.Count==0||!Runtime.IsApplied||!Conquest.Prototype.DiagnosticSceneActive)return;
        float now=UnityEngine.Time.time;if(now<nextPoll)return;nextPoll=now+.1f;
        try
        {
            var current=ShootingSystem._gameContext;if(current==null||current._isDisposed)return;
            if(world==null||world.Pointer!=current.Pointer){SceneChanged();world=current;weapons=world.GetEntities().With<WeaponComponent>().AsSet();}
            if(now>=nextScan)
            {
                nextScan=now+2;listed.Clear();var wa=weapons._entities;int n=Math.Min(weapons.Count,wa?.Length??0);
                for(int i=0;i<n&&i<8192;i++)
                {
                    var e=wa[i];if(!e.IsAlive||!e.Has<WeaponComponent>())continue;
                    var info=NativeEcs.Read<WeaponComponent>(e)?.WeaponInfo;if(info!=null&&ids.Contains(info.Id))listed.Add(e);
                }
            }
            foreach(var e in listed)
            {
                if(!e.IsAlive||!e.Has<WeaponComponent>())continue;
                var w=NativeEcs.Read<WeaponComponent>(e);if(w==null)continue;
                int made=w.ShotsMade.Value,ammo=w.AmmoInMagazine.Value;ulong k=Key(e);
                if(!seen.TryGetValue(k,out var s)||s.made!=made||s.ammo!=ammo){seen[k]=(made,ammo,now);continue;}
                if(made<=0||now-s.at<idle||e.Has<BurstCooldownComponent>())continue;
                int leftBefore=w.ShotsRemainingInBurst;
                var g=w.ShotsMade;g.Value=0;w.ShotsMade=g;
                int leftAfter=w.ShotsRemainingInBurst,full=w.ShotsPerBurst.Value;
                if(leftAfter!=full)throw new InvalidOperationException($"burst refill did not take: {leftBefore}->{leftAfter}, burst {full}");
                seen[k]=(0,ammo,now);refills++;
                if(refillLogged<MaxLog){refillLogged++;DiagnosticLog.Write("spaag_burst_refill",new{t=now,weapon=w.WeaponInfo?.Id,leftBefore,leftAfter,idleFor=now-s.at,refills});}
            }
        }
        catch(Exception x){refillBroken=true;DiagnosticLog.Write("spaag_burst_refill_failed",new{error=x.ToString()});MelonLogger.Error("FREEDOM_ARROW_SPAAG_REFILL_FAILED: native bursts. "+x.Message);}
    }
}
