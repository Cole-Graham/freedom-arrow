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
    static long passes,changes;
    static int active,lastChanged=-1;
    static bool firstPass;
    public static object Status()=>new{bound=getFogCode!=IntPtr.Zero,broken,passes,active,changes,lastChanged};
    public static unsafe void Install()
    {
        hasFog=SpottingCap.Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(FogOfWarComponent));
        getFog=SpottingCap.Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(FogOfWarComponent));
        getFogCode=*(IntPtr*)getFog;
        if(getFogCode==IntPtr.Zero)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> has no code");
        DiagnosticLog.Write("supply_bound",new{mode="LateUpdate; no native spawn hooks",antiVisible=AntiVisible});
        MelonLogger.Msg($"FREEDOM_ARROW_SUPPLY_STEALTH installed: late-update active caches, AntiVisible {AntiVisible:g}; no spawn hooks");
    }
    public static unsafe void LateUpdate()
    {
        if(broken||getFogCode==IntPtr.Zero||!Runtime.IsApplied)return;
        try
        {
            var supplies=SupplySystem._activeSupplies;
            if(supplies==null)return;
            passes++;active=supplies.Count;
            if(!firstPass)
            {
                firstPass=true;
                DiagnosticLog.Write("supply_first_scan",new{active});
            }
            foreach(var supply in supplies.Keys)
            {
                var e=supply;
                if(!e.IsAlive||!SpottingCap.Has(hasFog,e))continue;
                float* fow=(float*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getFogCode)(&e,getFog);
                if(fow==null)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> returned null");
                float old=fow[3]; // FogOfWarComponent.AntiVisible at 0xC.
                if(old==AntiVisible)continue;
                lastChanged=e.GetHashCode();
                DiagnosticLog.Write("supply_write_begin",new{entity=lastChanged,before=old,target=AntiVisible});
                fow[3]=AntiVisible;
                if(fow[3]!=AntiVisible)throw new InvalidOperationException("Supply AntiVisible readback mismatch");
                changes++;
                DiagnosticLog.Write("supply_write_verified",new{entity=lastChanged,before=old,after=fow[3],changes});
                if(++logged<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_SUPPLY_STEALTH cache AntiVisible {old:g} -> {AntiVisible:g}");
            }
        }
        catch(Exception x)
        {
            broken=true;
            DiagnosticLog.Write("supply_failed",new{error=x.ToString(),passes,active,changes,lastChanged});
            MelonLogger.Error("FREEDOM_ARROW_SUPPLY_STEALTH_FAILED: off for this session. "+x);
        }
    }
}
