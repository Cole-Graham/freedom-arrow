using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// Interceptable missile HP (Lateralus, 15 November 2026: "give me three test builds that set the HP of all interceptables to 5, 7, and 9").
// Vanilla ProjectileSpawnerHelper.MakeShellTargetable (RVA 0x7DF1E0, one direct caller in CreateCommonProjectile at 0x7DE682, not inlined)
// gives every CanBeTargeted projectile HealthComponent(1.0, immortal false): _health 0x4 = MaxHealth 0x8 = 1.0, HalfHealth 0xC = 0.5.
// No table holds that HP. The postfix writes projectile-health.json "health" into the three fields of the component the call just set.
// No file or health 0 = vanilla 1 HP.
static class ProjectileHealth
{
    const int MaxLog=200;
    static float health;
    static bool broken;
    static int logged;
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var file=Path.Combine(root,"projectile-health.json");
        if(!File.Exists(file))return;
        health=JsonNode.Parse(File.ReadAllText(file))?["health"]?.GetValue<float>()??0;
        if(health<=0)return;
        var method=AccessTools.Method(typeof(ProjectileSpawnerHelper),"MakeShellTargetable")??throw new MissingMethodException("ProjectileSpawnerHelper.MakeShellTargetable");
        harmony.Patch(method,postfix:new HarmonyMethod(typeof(ProjectileHealth),nameof(After)));
        MelonLogger.Msg($"FREEDOM_ARROW_PROJECTILE_HEALTH installed: every interceptable projectile {health} HP (vanilla 1)");
        DiagnosticLog.Write("projectile_health_installed",new{health});
    }
    public static void After(ref Entity __0,Ammunitions __1)
    {
        if(broken||!Runtime.IsApplied)return;
        try
        {
            var e=__0;
            if(!e.IsAlive||!e.Has<HealthComponent>())return;
            float before=NativeEcs.Field<HealthComponent,float>(e,"MaxHealth");
            NativeEcs.WriteField<HealthComponent,float>(e,"_health",health);
            NativeEcs.WriteField<HealthComponent,float>(e,"MaxHealth",health);
            NativeEcs.WriteField<HealthComponent,float>(e,"HalfHealth",health*0.5f);
            if(logged<MaxLog)
            {
                logged++;
                DiagnosticLog.Write("projectile_health",new{ammo=__1?.Id,name=__1?.HUDName,before,
                    after=NativeEcs.Field<HealthComponent,float>(e,"_health"),max=NativeEcs.Field<HealthComponent,float>(e,"MaxHealth")});
            }
        }
        catch(Exception x)
        {
            broken=true;
            DiagnosticLog.Write("projectile_health_failed",new{error=x.ToString()});
            MelonLogger.Error("FREEDOM_ARROW_PROJECTILE_HEALTH_FAILED: off for this session; projectiles keep 1 HP. "+x.Message);
        }
    }
}
