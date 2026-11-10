using Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components;
using Il2CppBrokenArrow.Client.Ecs.Transports.Systems;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// Caches have no unit row. Set UI stealth 2.5 (raw 0.4) after native creation.
// Do not intercept SpawnService.SpawnSupply: its by-reference SupplySpawnData value crosses the
// generated IL2CPP callback incorrectly. Both dev.3 dumps read UID/HasValue bytes as an object pointer.
static class SupplyStealth
{
    const float AntiVisible=0.4f;
    const int MaxLog=5;
    static IntPtr hasFog,getFog,getFogCode;
    static bool broken;
    static int logged;
    public static unsafe void Install()
    {
        hasFog=SpottingCap.Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(FogOfWarComponent));
        getFog=SpottingCap.Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(FogOfWarComponent));
        getFogCode=*(IntPtr*)getFog;
        if(getFogCode==IntPtr.Zero)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> has no code");
        MelonLogger.Msg($"FREEDOM_ARROW_SUPPLY_STEALTH installed: late-update active caches, AntiVisible {AntiVisible:g}; no spawn hooks");
    }
    public static unsafe void LateUpdate()
    {
        if(broken||getFogCode==IntPtr.Zero||!Runtime.IsApplied)return;
        try
        {
            var supplies=SupplySystem._activeSupplies;
            if(supplies==null)return;
            foreach(var supply in supplies.Keys)
            {
                var e=supply;
                if(!e.IsAlive||!SpottingCap.Has(hasFog,e))continue;
                float* fow=(float*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getFogCode)(&e,getFog);
                if(fow==null)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> returned null");
                float old=fow[3]; // FogOfWarComponent.AntiVisible at 0xC.
                if(old==AntiVisible)continue;
                fow[3]=AntiVisible;
                if(++logged<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_SUPPLY_STEALTH cache AntiVisible {old:g} -> {AntiVisible:g}");
            }
        }
        catch(Exception x)
        {
            broken=true;
            MelonLogger.Error("FREEDOM_ARROW_SUPPLY_STEALTH_FAILED: off for this session. "+x.Message);
        }
    }
}
