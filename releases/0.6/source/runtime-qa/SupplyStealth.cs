using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components;
using Il2CppBrokenArrow.Client.Ecs.Spawn;
using Il2CppBrokenArrow.Client.Ecs.Transports.Systems;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// Supply caches (Lateralus, 8 November 2026): stealth UI 2.5 (raw 0.4). Vanilla hard-codes AntiVisible 1.0 in
// SpawnService.SpawnSupply (RVA 0x3349F0, constant at 0x677FC04); caches have no unit row, so the tables cannot set it.
// SpawnSupply passes its new entity to SupplySystem.AddActiveSupply, then builds the FogOfWarComponent; the postfix sets
// AntiVisible once the component exists. Remote spawns use the same function, so every client with the mod agrees.
static class SupplyStealth
{
    const float AntiVisible=0.4f;
    const int MaxLog=5;
    static IntPtr hasFog,getFog,getFogCode;
    [ThreadStatic] static bool spawning;
    [ThreadStatic] static Entity spawned;
    [ThreadStatic] static bool haveSpawned;
    static bool broken;
    static int logged;
    public static unsafe void Install(HarmonyLib.Harmony harmony)
    {
        hasFog=SpottingCap.Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(FogOfWarComponent));
        getFog=SpottingCap.Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(FogOfWarComponent));
        getFogCode=*(IntPtr*)getFog;
        if(getFogCode==IntPtr.Zero)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> has no code");
        harmony.Patch(AccessTools.Method(typeof(SpawnService),"SpawnSupply"),prefix:new HarmonyMethod(typeof(SupplyStealth),nameof(SpawnBefore)),postfix:new HarmonyMethod(typeof(SupplyStealth),nameof(SpawnAfter)));
        harmony.Patch(AccessTools.Method(typeof(SupplySystem),"AddActiveSupply"),prefix:new HarmonyMethod(typeof(SupplyStealth),nameof(AddBefore)));
        MelonLogger.Msg($"FREEDOM_ARROW_SUPPLY_STEALTH installed: supply caches AntiVisible {AntiVisible:g} (UI {1/AntiVisible:g})");
    }
    public static void SpawnBefore(){spawning=true;haveSpawned=false;}
    public static void AddBefore(Entity __0){if(spawning){spawned=__0;haveSpawned=true;}}
    public static unsafe void SpawnAfter()
    {
        spawning=false;
        if(broken||!haveSpawned||!Runtime.IsApplied)return;
        haveSpawned=false;
        try
        {
            var e=spawned;
            if(!SpottingCap.Has(hasFog,e))return;
            float* fow=(float*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getFogCode)(&e,getFog);
            float old=fow[3];fow[3]=AntiVisible;  // FogOfWarComponent.AntiVisible at 0xC
            if(++logged<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_SUPPLY_STEALTH cache AntiVisible {old:g} -> {AntiVisible:g}");
        }
        catch(Exception x)
        {
            broken=true;
            MelonLogger.Error("FREEDOM_ARROW_SUPPLY_STEALTH_FAILED: off for this session; caches keep stealth 1.0. "+x.Message);
        }
    }
}
