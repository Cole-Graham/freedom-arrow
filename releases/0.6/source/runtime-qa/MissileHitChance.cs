using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// Flat missile hit chance (Lateralus batch, 8 November 2026). Vanilla BattleSystemHelpers.CalculateMissileHitChance (5-argument,
// RVA 0x7D4130) multiplies accuracy x ECM x ((1 - flare resistance) x flare strength)^flares x stress, and
// SeekerSystem.CalculateMissileDivertion rolls it again for every new flare, so ECM and flares compound across re-rolls.
// FA: chance = accuracy x (1 - (1 - ECM) - flares x (1 - (1 - resistance) x flare strength)) x stress, clamped to 0..1.
// A re-roll inside CalculateMissileDivertion passes with min(1, chance / lowest chance so far), so the chance that the missile
// is still on target equals the flat chance at the worst moment of its flight, however many re-rolls happen. Laser and SEAD
// seekers never reach the roll (vanilla). Calls from outside CalculateMissileDivertion (the AI overkill score) get the flat chance.
static class MissileHitChance
{
    const int MaxLog=60,Prune=4096;
    [ThreadStatic] static bool inDivertion;
    [ThreadStatic] static ulong current;
    static readonly Dictionary<ulong,(float lowest,float time)> missiles=new();
    static bool broken;
    static int logged;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        var chance=AccessTools.Method(typeof(BattleSystemHelpers),nameof(BattleSystemHelpers.CalculateMissileHitChance),new[]{typeof(Ammunitions),typeof(float),typeof(float),typeof(int),typeof(float)})
            ??throw new InvalidOperationException("CalculateMissileHitChance(Ammunitions, float, float, int, float) not found");
        var divertion=AccessTools.Method(typeof(SeekerSystem),"CalculateMissileDivertion")??throw new InvalidOperationException("SeekerSystem.CalculateMissileDivertion not found");
        harmony.Patch(chance,prefix:new HarmonyMethod(typeof(MissileHitChance),nameof(Chance)));
        harmony.Patch(divertion,prefix:new HarmonyMethod(typeof(MissileHitChance),nameof(DivertionBefore)),finalizer:new HarmonyMethod(typeof(MissileHitChance),nameof(DivertionAfter)));
        MelonLogger.Msg("FREEDOM_ARROW_MISSILE_CHANCE installed: flat ECM + flares, re-rolls do not compound");
    }
    public static unsafe void DivertionBefore(ref Entity __0)
    {
        inDivertion=true;
        fixed(Entity* e=&__0)current=*(ulong*)e;  // DefaultEcs Entity: WorldId, Version, EntityId (8 bytes)
    }
    public static Exception DivertionAfter(Exception __exception){inDivertion=false;return __exception;}
    public static bool Chance(Ammunitions ammoInfo,float targetECM,float targetDecoyEffect,int targetActiveDecoys,float stressMultiplier,ref float __result)
    {
        if(broken||!Runtime.IsApplied||ammoInfo==null)return true;
        try
        {
            float accuracy=ammoInfo.DispersionHorizontalRadius,resist=ammoInfo.DispersionVerticalRadius;
            float perFlare=1-(1-resist)*targetDecoyEffect;
            float flat=accuracy*Math.Clamp(1-(1-targetECM)-targetActiveDecoys*perFlare,0f,1f)*stressMultiplier;
            float result=flat;string kind="ai";
            if(inDivertion)
            {
                float now=UnityEngine.Time.time;
                if(missiles.TryGetValue(current,out var seen))
                {
                    result=seen.lowest<=0?0:Math.Min(1f,flat/seen.lowest);
                    missiles[current]=(Math.Min(seen.lowest,flat),now);kind="reroll";
                }
                else
                {
                    if(missiles.Count>=Prune)foreach(var k in missiles.Where(p=>now-p.Value.time>30).Select(p=>p.Key).ToList())missiles.Remove(k);
                    missiles[current]=(flat,now);kind="first";
                }
            }
            __result=result;
            if(kind!="ai"&&++logged<=MaxLog)
                MelonLogger.Msg($"FREEDOM_ARROW_MISSILE_CHANCE {kind} ammo {ammoInfo.Id} ecm {targetECM:0.###} flares {targetActiveDecoys} x {targetDecoyEffect:0.###} stress {stressMultiplier:0.###} flat {flat:0.###} roll {result:0.###}");
            return false;
        }
        catch(Exception x)
        {
            broken=true;
            MelonLogger.Error("FREEDOM_ARROW_MISSILE_CHANCE_FAILED: off for this session; vanilla missile hit chance. "+x.Message);
            return true;
        }
    }
}
