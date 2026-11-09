using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Missiles;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Flat missile hit chance (Lateralus batch, 8 November 2026). Vanilla BattleSystemHelpers.CalculateMissileHitChance (5-argument,
// RVA 0x7D4130) multiplies accuracy x ECM x ((1 - flare resistance) x flare strength)^flares x stress, and
// SeekerSystem.CalculateMissileDivertion rolls it again for every new flare, so ECM and flares compound across re-rolls.
// FA: chance = accuracy x (1 - (1 - ECM) - flares x (1 - (1 - resistance) x flare strength)) x stress, clamped to 0..1.
// A re-roll inside CalculateMissileDivertion passes with min(1, chance / lowest chance so far), so the chance that the missile
// is still on target equals the flat chance at the worst moment of its flight, however many re-rolls happen. Laser and SEAD
// seekers never reach the roll (vanilla). Calls from outside CalculateMissileDivertion (the AI overkill score) get the flat chance.
// Logging (Lateralus batch, 9 November 2026): roll lines name the target and its flares left; MissilesHelper.SetMissileDead
// (a missile stops guiding: hit, lost energy, lost target, launcher lost it...) writes one FREEDOM_ARROW_MISSILE_END line per
// rolled missile with the reason, flight time, distance to the target and the seeker's lock state. Logging only.
static class MissileHitChance
{
    const int MaxLog=3000,Prune=4096;
    [ThreadStatic] static bool inDivertion;
    [ThreadStatic] static Entity current;
    static readonly Dictionary<ulong,(float lowest,float time,float launch,int ammo,int maxFlares,bool ended)> missiles=new();
    static bool broken,endBroken;
    static int logged;
    // Nullable<Entity> as IL2CPP lays it out: bool at 0, Entity at 4, 12 bytes (as HarmSeeker.cs).
    [StructLayout(LayoutKind.Sequential,Pack=4)] struct NullableEntity{public byte HasValue;public byte P1,P2,P3;public int Lo,Hi;}
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    public static void Install(HarmonyLib.Harmony harmony)
    {
        if(Unsafe.SizeOf<Entity>()!=8||Unsafe.SizeOf<NullableEntity>()!=12)throw new InvalidOperationException("Entity layout changed");
        var chance=AccessTools.Method(typeof(BattleSystemHelpers),nameof(BattleSystemHelpers.CalculateMissileHitChance),new[]{typeof(Ammunitions),typeof(float),typeof(float),typeof(int),typeof(float)})
            ??throw new InvalidOperationException("CalculateMissileHitChance(Ammunitions, float, float, int, float) not found");
        var divertion=AccessTools.Method(typeof(SeekerSystem),"CalculateMissileDivertion")??throw new InvalidOperationException("SeekerSystem.CalculateMissileDivertion not found");
        harmony.Patch(chance,prefix:new HarmonyMethod(typeof(MissileHitChance),nameof(Chance)));
        harmony.Patch(divertion,prefix:new HarmonyMethod(typeof(MissileHitChance),nameof(DivertionBefore)),finalizer:new HarmonyMethod(typeof(MissileHitChance),nameof(DivertionAfter)));
        MelonLogger.Msg("FREEDOM_ARROW_MISSILE_CHANCE installed: flat ECM + flares, re-rolls do not compound");
        try
        {
            var dead=AccessTools.Method(typeof(MissilesHelper),nameof(MissilesHelper.SetMissileDead))??throw new InvalidOperationException("MissilesHelper.SetMissileDead not found");
            harmony.Patch(dead,prefix:new HarmonyMethod(typeof(MissileHitChance),nameof(DeadBefore)));
            MelonLogger.Msg("FREEDOM_ARROW_MISSILE_END installed: one line per rolled missile when it stops guiding");
        }
        catch(Exception x){endBroken=true;MelonLogger.Error("FREEDOM_ARROW_MISSILE_END_FAILED: no missile end lines. "+x.Message);}
    }
    public static void DivertionBefore(ref Entity __0){inDivertion=true;current=__0;}
    public static Exception DivertionAfter(Exception __exception){inDivertion=false;return __exception;}
    static bool Target(Entity missile,out Entity target)
    {
        target=default;
        if(!missile.IsAlive||!missile.Has<SeekerComponent>())return false;
        var t=NativeEcs.Field<SeekerComponent,NullableEntity>(missile,"Target");
        if(t.HasValue==0)return false;
        ulong raw=(uint)t.Lo|((ulong)(uint)t.Hi<<32);target=Unsafe.As<ulong,Entity>(ref raw);
        return target.IsAlive;
    }
    static string Id(Entity e)=>e.GetHashCode().ToString();
    static string Flares(Entity target)
    {
        if(!target.IsAlive||!target.Has<CounterMeasuresComponent>())return "cm n/a";
        int left=NativeEcs.EncodedInt<CounterMeasuresComponent>(target,"CounterMeasuresCount");
        bool auto=NativeEcs.Field<CounterMeasuresComponent,bool>(target,"AutomaticCMDispence");
        return $"cm left {left} auto {(auto?"on":"off")}";
    }
    public static bool Chance(Ammunitions ammoInfo,float targetECM,float targetDecoyEffect,int targetActiveDecoys,float stressMultiplier,ref float __result)
    {
        if(broken||!Runtime.IsApplied||ammoInfo==null)return true;
        try
        {
            float accuracy=ammoInfo.DispersionHorizontalRadius,resist=ammoInfo.DispersionVerticalRadius;
            float perFlare=1-(1-resist)*targetDecoyEffect;
            float flat=accuracy*Math.Clamp(1-(1-targetECM)-targetActiveDecoys*perFlare,0f,1f)*stressMultiplier;
            float result=flat,flight=0;string kind="ai";
            if(inDivertion)
            {
                float now=Time.time;ulong key=Key(current);
                if(missiles.TryGetValue(key,out var seen))
                {
                    result=seen.lowest<=0?0:Math.Min(1f,flat/seen.lowest);
                    missiles[key]=(Math.Min(seen.lowest,flat),now,seen.launch,seen.ammo,Math.Max(seen.maxFlares,targetActiveDecoys),seen.ended);kind="reroll";flight=now-seen.launch;
                }
                else
                {
                    if(missiles.Count>=Prune)foreach(var k in missiles.Where(p=>now-p.Value.time>30).Select(p=>p.Key).ToList())missiles.Remove(k);
                    missiles[key]=(flat,now,now,ammoInfo.Id,targetActiveDecoys,false);kind="first";
                }
            }
            __result=result;
            if(kind!="ai"&&++logged<=MaxLog)
            {
                string who="";
                try{who=Target(current,out var t)?$" missile {Id(current)} target {Id(t)} {Flares(t)}":$" missile {Id(current)} target none";}catch{}
                MelonLogger.Msg($"FREEDOM_ARROW_MISSILE_CHANCE {kind} t+{flight:0.00}s ammo {ammoInfo.Id} ecm {targetECM:0.###} flares {targetActiveDecoys} x {targetDecoyEffect:0.###} stress {stressMultiplier:0.###} flat {flat:0.###} roll {result:0.###}{who}");
            }
            return false;
        }
        catch(Exception x)
        {
            broken=true;
            MelonLogger.Error("FREEDOM_ARROW_MISSILE_CHANCE_FAILED: off for this session; vanilla missile hit chance. "+x.Message);
            return true;
        }
    }
    // MissilesHelper.SetMissileDead(in Entity missile, ref SeekerComponent, bool isDestroyed, bool pitbullTerminalGuidance,
    // MissileDeadReqestType): read the seeker before the game clears it. Only missiles that rolled above are logged, once each.
    public static void DeadBefore(in Entity __0,bool __2,MissileDeadReqestType __4)
    {
        if(endBroken||!Runtime.IsApplied)return;
        try
        {
            var missile=__0;ulong key=Key(missile);
            if(!missiles.TryGetValue(key,out var m)||m.ended)return;
            missiles[key]=(m.lowest,m.time,m.launch,m.ammo,m.maxFlares,true);
            if(++logged>MaxLog)return;
            string where="target none";
            if(Target(missile,out var target))
            {
                string dist="?";
                if(missile.Has<ViewComponent>()&&target.Has<ViewComponent>())
                    dist=Vector3.Distance(NativeEcs.Read<ViewComponent>(missile).transform.position,NativeEcs.Read<ViewComponent>(target).transform.position).ToString("0");
                where=$"target {Id(target)} distance {dist} {Flares(target)}";
            }
            bool los=NativeEcs.Field<SeekerComponent,bool>(missile,"HasLOSOnCurrentTarget"),vision=NativeEcs.Field<SeekerComponent,bool>(missile,"HasVisionOnCurrentTarget");
            int miss=NativeEcs.Field<SeekerComponent,int>(missile,"MissType"),seeker=NativeEcs.Field<SeekerComponent,int>(missile,"Type");
            float lost=NativeEcs.EncodedField<SeekerComponent>(missile,"TimeWithoutTarget");
            string missName=miss switch{1=>"on target",2=>"diverted (ECM/miss roll)",3=>"diverted (flare)",_=>"not rolled"};
            MelonLogger.Msg($"FREEDOM_ARROW_MISSILE_END t+{Time.time-m.launch:0.00}s missile {Id(missile)} ammo {m.ammo} reason {__4} destroyed {__2} seeker {seeker} {where} los {los} vision {vision} roll {missName} lowest {m.lowest:0.###} max_flares {m.maxFlares} no_target_s {lost:0.00}");
        }
        catch(Exception x){endBroken=true;MelonLogger.Error("FREEDOM_ARROW_MISSILE_END_FAILED: no more missile end lines this session. "+x.Message);}
    }
}
