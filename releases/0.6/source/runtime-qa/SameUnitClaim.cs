using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Missiles.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// One unit, one weapon per SEAD missile (Lateralus, 15 November 2026, thread 1571554273639006392: "there should be an exception when its
// weapons from the same unit. For SeaRAM it should wait until the next missile is in range to fire the second missile. For Pantsir it
// should hold its gun burst for the second missile"). In his tier3-sam run the SeaRAM fired 3 RAMs per 2-missile salvo and the Pantsir gun
// and SAM hit the same missile 3 times; our AaCooldown hook made 0 corrections, so this is native: ShootingSystem.InternalUpdate calls
// OverkillScoringSystem.IsTargetOverkilled with excludeShooter = the calling weapon, so a launcher ignores its own missile in flight.
// A unit claims a SEAD missile when one of its listed SAMs has a missile flying at it (ShootPriorityComponent.Shooters entry with
// MissileLaunched, or, as seen in his tier3-sam-claim run where that flag was almost never set, the flying missile's own
// SeekerComponent.ShooterWeapon + Target) or one of its listed guns has it as target and fired in the last GunClaimSeconds. Every listed weapon of that unit
// then gets "overkilled" for that missile (the claiming gun itself excepted), so it takes another missile or holds fire.
// Weapons: sameUnitClaimWeapons in spaag-weapons.json. Same pattern as AaCooldown: LateUpdate builds an immutable snapshot, the native
// callback only reads it. Other units are not affected.
// Second hook (claim3, after Lateralus 12:57 PST "still seems the same": 3 blocks in the claim2 run although 286 SAM-in-flight claims were
// seen): ShootingSystem.InternalUpdate(weapon, shooterUnit) first calls BattleSystemHelpers.IsTargetSEADProjectileTargetingMe(target,
// shooterUnit) (call 0x80DF3F) and, if the SEAD missile is aimed at this unit, fires without asking IsTargetOverkilled at all. Lateralus's
// SeaRAM and Pantsir were the SEAD targets. Postfix: when this unit already claims that missile, answer "not aimed at me", so the normal
// overkill check (and the rule above) runs. Other callers: TargetMaintenanceSystem.LocalTargetUpdate (target keeping), ShellHitSystem ctor.
static class SameUnitClaim
{
    const float GunClaimSeconds=0.5f,Period=0.05f,MaxAge=0.25f;
    sealed class Frame
    {
        public readonly long At;public readonly Dictionary<ulong,ulong> WeaponUnit;public readonly Dictionary<ulong,(ulong Unit,ulong Weapon,bool Missile)[]> Claims;
        public Frame(long at,Dictionary<ulong,ulong> wu,Dictionary<ulong,(ulong,ulong,bool)[]> c){At=at;WeaponUnit=wu;Claims=c;}
    }
    static Frame frame=new(0,new(),new());
    static HashSet<int> ids=new();
    static bool enabled,failed;
    static World world;static EntitySet weaponSet,missileSet,seekerSet;
    [StructLayout(LayoutKind.Sequential,Pack=4)] struct NullableEntity{public byte HasValue;public byte P1,P2,P3;public int Lo,Hi;}
    static ulong Raw(NullableEntity n)=>n.HasValue==0?0:(uint)n.Lo|((ulong)(uint)n.Hi<<32);
    static float next,nextScan,nextMetrics;
    static readonly List<(Entity E,ulong Key,ulong Unit,bool Gun)> listed=new();
    static readonly Dictionary<ulong,(int made,int ammo,float at)> fired=new();
    static bool guidanceOk;
    static int drops,dropLogs,flips,blocks,blockLogs,claimsSeen,guidanceClaims,seekerClaims,shooterClaims,gunClaims;
    static readonly Dictionary<(ulong,ulong),float> lastBlockLog=new();
    static readonly Dictionary<ulong,float> lastDrop=new();
    static readonly System.Collections.Concurrent.ConcurrentQueue<(ulong Target,ulong Caller,bool Missile)> Blocked=new();
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var file=Path.Combine(root,"spaag-weapons.json");if(!File.Exists(file))return;
        ids=JsonNode.Parse(File.ReadAllText(file))?["sameUnitClaimWeapons"]?.AsArray().Select(x=>x!.GetValue<int>()).ToHashSet()??new();
        if(ids.Count==0)return;
        if(Unsafe.SizeOf<Entity>()!=8||Unsafe.SizeOf<NullableEntity>()!=12)throw new InvalidOperationException("Entity layout changed");
        if(!NativeEcs.Compiled<SeekerComponent>())throw new InvalidOperationException("SeekerComponent getter not compiled");
        guidanceOk=NativeEcs.Compiled<ActiveGuidanceComponent>();
        var method=AccessTools.Method(typeof(OverkillScoringSystem),"IsTargetOverkilled")??throw new MissingMethodException("IsTargetOverkilled");
        var p=method.GetParameters();
        if(method.ReturnType!=typeof(bool)||p.Length!=10||p[0].ParameterType!=typeof(Entity).MakeByRefType()||p[3].ParameterType!=typeof(Entity).MakeByRefType())
            throw new InvalidOperationException("Overkill hook signature changed");
        // Runs after AaCooldown's postfix so a claim is the final word for these weapons.
        harmony.Patch(method,postfix:new HarmonyMethod(typeof(SameUnitClaim),nameof(After)){priority=Priority.Last});
        var me=AccessTools.Method(typeof(BattleSystemHelpers),"IsTargetSEADProjectileTargetingMe")??throw new MissingMethodException("IsTargetSEADProjectileTargetingMe");
        var mp=me.GetParameters();
        if(me.ReturnType!=typeof(bool)||mp.Length!=2||mp.Any(x=>x.ParameterType!=typeof(Entity).MakeByRefType()))throw new InvalidOperationException("TargetingMe hook signature changed");
        harmony.Patch(me,postfix:new HarmonyMethod(typeof(SameUnitClaim),nameof(TargetingMe)));
        enabled=true;
        DiagnosticLog.Write("same_unit_claim_installed",new{weapons=ids.Count,gunClaimSeconds=GunClaimSeconds,launcherGuidance=guidanceOk});
        MelonLogger.Msg($"FREEDOM_ARROW_SAME_UNIT_CLAIM installed: {ids.Count} interceptor weapons take one SEAD missile per unit");
    }
    // Native callback: reads the snapshot only.
    static void After(ref Entity __0,ref Entity __3,ref bool __result)
    {
        if(__result||!enabled||failed)return;
        var f=Volatile.Read(ref frame);
        if((Stopwatch.GetTimestamp()-f.At)/(double)Stopwatch.Frequency>MaxAge)return;   // stale snapshot: native behaviour
        ulong caller=Key(__3);
        if(!f.WeaponUnit.TryGetValue(caller,out var unit))return;
        if(!f.Claims.TryGetValue(Key(__0),out var claims))return;
        foreach(var c in claims)
            if(c.Unit==unit&&(c.Missile||c.Weapon!=caller))
            {
                __result=true;Interlocked.Increment(ref blocks);
                if(Blocked.Count<256)Blocked.Enqueue((Key(__0),caller,c.Missile));
                return;
            }
    }
    // Native callback: reads the snapshot only. A claimed SEAD missile aimed at this unit no longer skips the overkill check.
    static void TargetingMe(ref Entity __0,ref Entity __1,ref bool __result)
    {
        if(!__result||!enabled||failed)return;
        var f=Volatile.Read(ref frame);
        if((Stopwatch.GetTimestamp()-f.At)/(double)Stopwatch.Frequency>MaxAge)return;
        if(!f.Claims.TryGetValue(Key(__0),out var claims))return;
        ulong unit=Key(__1);
        foreach(var c in claims)if(c.Unit==unit){__result=false;Interlocked.Increment(ref flips);return;}
    }
    public static void SceneChanged()
    {
        Volatile.Write(ref frame,new(0,new(),new()));
        try{if(world!=null&&!world._isDisposed){weaponSet?.Dispose();missileSet?.Dispose();seekerSet?.Dispose();}}catch{}
        world=null;weaponSet=missileSet=seekerSet=null;listed.Clear();fired.Clear();lastBlockLog.Clear();lastDrop.Clear();next=nextScan=0;
    }
    static Entity Target(Entity w)=>w.IsAlive&&w.Has<TargetComponent>()?NativeEcs.Field<TargetComponent,Entity>(w,"Target"):default;
    public static void LateUpdate()
    {
        if(!enabled||failed)return;
        if(!Runtime.IsApplied||!Conquest.Prototype.DiagnosticSceneActive){Volatile.Write(ref frame,new(0,new(),new()));return;}
        float now=UnityEngine.Time.time;if(now<next)return;next=now+Period;
        try
        {
            var current=ShootingSystem._gameContext;if(current==null||current._isDisposed)return;
            if(world==null||world.Pointer!=current.Pointer)
            {
                SceneChanged();world=current;
                weaponSet=world.GetEntities().With<WeaponComponent>().AsSet();
                missileSet=world.GetEntities().With<UnitComponent>().With<WarheadComponent>().With<ShootPriorityComponent>().AsSet();
                seekerSet=world.GetEntities().With<SeekerComponent>().AsSet();
            }
            if(now>=nextScan)
            {
                nextScan=now+2;listed.Clear();var wa=weaponSet._entities;int n=Math.Min(weaponSet.Count,wa?.Length??0);
                for(int i=0;i<n&&i<8192;i++)
                {
                    var e=wa[i];if(!e.IsAlive||!e.Has<WeaponComponent>())continue;
                    var w=NativeEcs.Read<WeaponComponent>(e);var info=w?.WeaponInfo;if(info==null||!ids.Contains(info.Id))continue;
                    var u=w.GetUnitEntity();if(!u.IsAlive)continue;
                    listed.Add((e,Key(e),Key(u),(int)info.Type!=86));
                }
            }
            var weaponUnit=new Dictionary<ulong,ulong>();var claims=new Dictionary<ulong,List<(ulong,ulong,bool)>>();
            foreach(var l in listed)
            {
                if(!l.E.IsAlive||!l.E.Has<WeaponComponent>())continue;
                weaponUnit[l.Key]=l.Unit;
                if(!l.Gun)continue;
                var w=NativeEcs.Read<WeaponComponent>(l.E);int made=w.ShotsMade.Value,ammo=w.AmmoInMagazine.Value;
                if(!fired.TryGetValue(l.Key,out var s))fired[l.Key]=s=(made,ammo,-99f);
                else if(s.made!=made||s.ammo!=ammo)fired[l.Key]=s=(made,ammo,now);
                if(now-s.at>GunClaimSeconds)continue;
                var t=Target(l.E);if(!t.IsAlive||!t.Has<UnitComponent>())continue;
                if(!AaCooldownPolicy.ProjectileType((int)NativeEcs.Read<UnitComponent>(t).UnitData.Type))continue;
                ulong tk=Key(t);if(!claims.TryGetValue(tk,out var list))claims[tk]=list=new();list.Add((l.Unit,l.Key,false));gunClaims++;
            }
            var ma=missileSet._entities;int mc=Math.Min(missileSet.Count,ma?.Length??0);
            for(int i=0;i<mc&&i<512;i++)
            {
                var e=ma[i];if(!e.IsAlive||!e.Has<ShootPriorityComponent>()||!e.Has<UnitComponent>())continue;
                if(!AaCooldownPolicy.ProjectileType((int)NativeEcs.Read<UnitComponent>(e).UnitData.Type))continue;
                var pr=NativeEcs.Read<ShootPriorityComponent>(e);if(pr.Shooters==null||pr.Shooters.Count==0)continue;
                var it=pr.Shooters.GetEnumerator();
                try
                {
                    while(it.MoveNext())
                    {
                        var kv=it.Current;if(kv.Value==null||!kv.Value.MissileLaunched)continue;
                        ulong wk=Key(kv.Key);if(!weaponUnit.TryGetValue(wk,out var u))continue;
                        ulong tk=Key(e);if(!claims.TryGetValue(tk,out var list))claims[tk]=list=new();list.Add((u,wk,true));shooterClaims++;
                    }
                }
                finally{it.Dispose();}
            }
            // Launcher-steered SAMs (claim4, Lateralus 13:07 PST "the mixed weapons still fire at the same target on the Pantsir"; Pantsir 57E6E
            // and Tor are seeker type 100, SeaRAM 10): the missile does not hold the target, the launcher's ActiveGuidanceComponent does.
            if(guidanceOk)
                foreach(var l in listed)
                {
                    if(l.Gun||!l.E.IsAlive||!l.E.Has<ActiveGuidanceComponent>())continue;
                    var g=NativeEcs.Read<ActiveGuidanceComponent>(l.E);var all=g?.GetAllMissiles();if(all==null)continue;
                    foreach(var m in all)
                    {
                        var mm=m;if(!mm.IsAlive||!g.DoesMissileHaveTarget(ref mm))continue;
                        var t=g.GetMissileTarget(ref mm);ulong tk=Key(t);if(tk==0)continue;
                        if(!claims.TryGetValue(tk,out var list))claims[tk]=list=new();
                        if(!list.Exists(c=>c.Item2==l.Key&&c.Item3))list.Add((l.Unit,l.Key,true));
                        guidanceClaims++;
                    }
                }
            // Each flying missile names the launcher that fired it and what it is chasing.
            var sa=seekerSet._entities;int sc=Math.Min(seekerSet.Count,sa?.Length??0);
            for(int i=0;i<sc&&i<1024;i++)
            {
                var e=sa[i];if(!e.IsAlive||!e.Has<SeekerComponent>())continue;
                ulong wk=Raw(NativeEcs.Field<SeekerComponent,NullableEntity>(e,"ShooterWeapon"));if(wk==0||!weaponUnit.TryGetValue(wk,out var u))continue;
                ulong tk=Raw(NativeEcs.Field<SeekerComponent,NullableEntity>(e,"Target"));if(tk==0)continue;
                if(!claims.TryGetValue(tk,out var list))claims[tk]=list=new();
                if(!list.Exists(c=>c.Item2==wk&&c.Item3))list.Add((u,wk,true));
                seekerClaims++;
            }
            // Guns (claim5, Lateralus 13:17 PST "no improvement"): ShootingSystem.InternalUpdate only asks IsTargetOverkilled when the
            // selected round has a seeker (Ammunitions.Seeker at 0x108 > 0, check at 0x80DEF0), so gun rounds never reach the hooks above.
            // A listed gun whose current target is a SEAD missile that another weapon of its unit has a missile flying at drops that
            // target the way the game drops an overkilled one: RemoveTarget(weapon, false, false, TargetOverkilled). At most every 0.25 s.
            foreach(var l in listed)
            {
                if(!l.Gun||!l.E.IsAlive)continue;
                var t=Target(l.E);if(!t.IsAlive)continue;ulong tk=Key(t);
                if(!claims.TryGetValue(tk,out var cl)||!cl.Exists(c=>c.Item1==l.Unit&&c.Item3&&c.Item2!=l.Key))continue;
                if(lastDrop.TryGetValue(l.Key,out var at)&&now-at<0.25f)continue;
                lastDrop[l.Key]=now;var w=l.E;
                BattleSystemHelpers.RemoveTarget(ref w,false,false,TargetRemoveReason.TargetOverkilled);drops++;
                if(dropLogs++<500)DiagnosticLog.Write("same_unit_claim_gun_drop",new{t=now,weapon=l.Key.ToString("X16"),target=tk.ToString("X16"),after=Key(Target(l.E)).ToString("X16")});
            }
            claimsSeen+=claims.Count;
            Volatile.Write(ref frame,new(Stopwatch.GetTimestamp(),weaponUnit,claims.ToDictionary(p=>p.Key,p=>p.Value.ToArray())));
            int flushed=0;
            while(flushed++<32&&Blocked.TryDequeue(out var b))
            {
                if(lastBlockLog.TryGetValue((b.Target,b.Caller),out var at)&&now-at<1)continue;
                lastBlockLog[(b.Target,b.Caller)]=now;
                if(blockLogs++<2000)DiagnosticLog.Write("same_unit_claim_block",new{t=now,target=b.Target.ToString("X16"),weapon=b.Caller.ToString("X16"),claimBy=b.Missile?"missile_in_flight":"gun_firing"});
            }
            if(now>=nextMetrics){nextMetrics=now+5;DiagnosticLog.Write("same_unit_claim_metrics",new{t=now,weapons=listed.Count,claims=claims.Count,claimsSeen,guidanceClaims,seekerClaims,shooterClaims,gunClaims,targetingMeFlips=Volatile.Read(ref flips),gunDrops=drops,blocks=Volatile.Read(ref blocks)});}
        }
        catch(Exception x){failed=true;Volatile.Write(ref frame,new(0,new(),new()));DiagnosticLog.Write("same_unit_claim_failed",new{error=x.ToString()});MelonLogger.Error("FREEDOM_ARROW_SAME_UNIT_CLAIM_FAILED: native targeting. "+x.Message);}
    }
}
