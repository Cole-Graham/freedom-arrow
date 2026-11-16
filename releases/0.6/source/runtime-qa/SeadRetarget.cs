using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Missiles;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// SEAD missiles re-target when their radar dies (Lateralus 16 Nov 2026 07:3x PST, thread 1571554273639006392: "when a radar unit dies the SEAD
// missiles still in flight don't switch targets ... Can we replicate the same target switching behavior for when a radar target dies?").
// Read from GameAssembly 6000.3.24f1, SeekerSystem.InternalUpdate (0x8284C0): for seeker types 10 and 200 (SEAD) the seeker scans nearby units
// (UnitsPositionsTree.GetNearbyUnits) and, for SEAD, keeps only units whose RadarAbilityComponent.Active is true, then switches with
// MissilesHelper.SetNewTargetToMissile. That scan runs while the current radar is alive (radar switched off). A dead target goes to
// DropCurrentTarget, and every SEAD round has CanReaquire = false, so the missile flies on to where the radar was.
// This prefix runs before the seeker update. For a SEAD missile whose target is dead, it looks for an enemy unit with its radar on, inside the
// seeker's range (SeekerComponent.MaxRange) and field of view (MissilesHelper.IsTargetWithinSeekerFOV), takes the one nearest the nose and
// sets it as the new target, as the radar-off switch does. No candidate: the game's own drop, as before.
static class SeadRetarget
{
    const int SeadSeeker=200,MaxLog=200;
    [StructLayout(LayoutKind.Sequential,Pack=4)] struct NullableEntity{public byte HasValue;public byte P1,P2,P3;public int Lo,Hi;}
    static EntitySet radars;static IntPtr radarsWorld;static bool on,off;static int logged,switched,none;static float nextSummary;
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    public static void Install(HarmonyLib.Harmony harmony)
    {
        if(Unsafe.SizeOf<NullableEntity>()!=12)throw new InvalidOperationException("Nullable<Entity> layout changed");
        var m=AccessTools.Method(typeof(SeekerSystem),"InternalUpdate")??throw new MissingMethodException("SeekerSystem.InternalUpdate");
        harmony.Patch(m,prefix:new HarmonyMethod(typeof(SeadRetarget),nameof(Before)){priority=Priority.First});
        on=true;
        MelonLogger.Msg("FREEDOM_ARROW_SEAD_RETARGET installed: a SEAD missile whose radar dies switches to another enemy radar that is on, inside its seeker cone and range");
        DiagnosticLog.Write("sead_retarget_installed",new{hook="SeekerSystem.InternalUpdate prefix"});
    }
    static bool Dead(Entity e)=>!e.IsAlive||e.Has<DeadComponent>()||e.Has<DeathComponent>();
    static void Before(in Entity __0)
    {
        if(!on||off)return;
        try
        {
            var missile=__0;
            if(!missile.IsAlive||!missile.Has<SeekerComponent>())return;
            if(NativeEcs.Field<SeekerComponent,int>(missile,"Type")!=SeadSeeker)return;
            var t=NativeEcs.Field<SeekerComponent,NullableEntity>(missile,"Target");if(t.HasValue==0)return;
            long raw=(uint)t.Lo|((long)t.Hi<<32);var old=Unsafe.As<long,Entity>(ref raw);
            if(!Dead(old))return;
            var world=Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems.ShootingSystem._gameContext;if(world==null||world._isDisposed)return;
            if(radarsWorld!=world.Pointer){try{radars?.Dispose();}catch{}radars=world.GetEntities().With<RadarAbilityComponent>().With<UnitComponent>().AsSet();radarsWorld=world.Pointer;}
            var seeker=NativeEcs.Read<SeekerComponent>(missile);
            var mine=seeker.PlayerInfo;if(mine==null)return;var side=mine.TeamSide;
            float range=NativeEcs.Field<SeekerComponent,float>(missile,"MaxRange");
            var at=NativeEcs.Read<ViewComponent>(missile).transform.position;
            Entity best=default;float bestAngle=float.MaxValue,bestDist=0;int seen=0;
            var list=radars._entities;int count=Math.Min(radars.Count,list?.Length??0);
            for(int i=0;i<count;i++)
            {
                var r=list[i];if(Dead(r)||!r.Has<ViewComponent>())continue;
                if(!NativeEcs.Field<RadarAbilityComponent,bool>(r,"<Active>k__BackingField"))continue;
                var owner=NativeEcs.Read<UnitComponent>(r).Owner;if(owner==null||owner.TeamSide==side)continue;
                float d=Vector3.Distance(at,NativeEcs.Read<ViewComponent>(r).transform.position);if(range>0&&d>range)continue;
                seen++;
                if(!MissilesHelper.IsTargetWithinSeekerFOV(ref missile,ref r,out float angle))continue;
                if(angle<bestAngle){bestAngle=angle;best=r;bestDist=d;}
            }
            if(bestAngle==float.MaxValue)
            {
                none++;if(logged<MaxLog){logged++;DiagnosticLog.Write("sead_retarget_none",new{t=Time.time,deadTarget=Name(old),radarsOnInRange=seen,range});}
                return;   // the game's own drop
            }
            MissilesHelper.SetNewTargetToMissile(ref missile,ref best,true,true);
            FreedomArrow.Conquest.Prototype.HarmForget(missile);   // else the dark-radar lock (HarmSeeker) would pull it back to the old spot
            switched++;
            if(logged<MaxLog){logged++;DiagnosticLog.Write("sead_retarget",new{t=Time.time,deadTarget=Name(old),newTarget=Name(best),angle=bestAngle,distance=bestDist,range,candidates=seen});}
            float now=Time.time;if(now>=nextSummary){nextSummary=now+60;DiagnosticLog.Write("sead_retarget_summary",new{t=now,switched,none});}
        }
        catch(Exception x)
        {
            off=true;DiagnosticLog.Write("sead_retarget_failed",new{error=x.ToString()});
            MelonLogger.Error("FREEDOM_ARROW_SEAD_RETARGET_FAILED: vanilla behaviour for this session. "+x.Message);
        }
    }
    static string Name(Entity e){try{return e.IsAlive&&e.Has<UnitComponent>()?NativeEcs.Read<UnitComponent>(e).UnitData?.Name??"":"(gone)";}catch{return "";}}
    public static void SceneChanged(){try{radars?.Dispose();}catch{}radars=null;radarsWorld=IntPtr.Zero;}
}
