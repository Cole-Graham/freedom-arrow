using System.Runtime.InteropServices;
using FreedomArrow;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.Transports.Systems;

namespace Il2CppDefaultEcs
{
    public struct Entity
    {
        public int Id;
        public bool IsAlive => Id > 0;
    }
}
namespace Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components { public struct FogOfWarComponent { } }
namespace Il2CppBrokenArrow.Client.Ecs.Transports.Systems
{
    public static class SupplySystem { public static Dictionary<Entity,int> _activeSupplies; }
}
namespace MelonLoader
{
    public static class MelonLogger
    {
        public static readonly List<string> Errors=new();
        public static void Msg(string text) { }
        public static void Error(string text) => Errors.Add(text);
    }
}
namespace FreedomArrow
{
    public static class Runtime { public static bool IsApplied; }
    public static class DiagnosticLog
    {
        public static readonly List<(string kind,object data)> Events=new();
        public static void Write(string kind,object data)=>Events.Add((kind,data));
    }
    public static unsafe class SpottingCap
    {
        public static readonly Dictionary<int,IntPtr> Fields=new();
        static readonly IntPtr StorePointer=Marshal.AllocHGlobal(IntPtr.Size);
        public static bool Throw;
        public static IntPtr Store(string name,Type component)
        {
            Marshal.WriteIntPtr(StorePointer,(IntPtr)(delegate* unmanaged<Entity*,IntPtr,IntPtr>)&Get);
            return StorePointer;
        }
        public static bool Has(IntPtr store,Entity e)
        {
            if(Throw)throw new InvalidOperationException("fixture read failure");
            return Fields.ContainsKey(e.Id);
        }
        [UnmanagedCallersOnly]
        static IntPtr Get(Entity* e,IntPtr method) => Fields[e->Id];
    }
}
static unsafe class Program
{
    static int checks;
    static void Check(bool value,string label)
    {
        if(!value)throw new Exception(label);
        checks++;
    }
    static float* Fog(int id,float value)
    {
        float* f=(float*)NativeMemory.Alloc(16);
        f[0]=91;f[1]=92;f[2]=93;f[3]=value;
        SpottingCap.Fields[id]=(IntPtr)f;
        return f;
    }
    static void Main()
    {
        SupplyStealth.LateUpdate(); // Startup before binding must be harmless.
        SupplyStealth.Install();
        SupplySystem._activeSupplies=null;
        Runtime.IsApplied=true;
        SupplyStealth.LateUpdate();
        var ready=new Entity{Id=1};var delayed=new Entity{Id=2};var dead=new Entity{Id=-3};
        SupplySystem._activeSupplies=new(){{ready,0},{delayed,0},{dead,0}};
        var a=Fog(1,1);var c=Fog(-3,1);
        Runtime.IsApplied=false;SupplyStealth.LateUpdate();
        Check(a[3]==1,"No mutation before database application");
        Runtime.IsApplied=true;SupplyStealth.LateUpdate();
        Check(a[3]==0.4f,"Live cache gets requested stealth");
        Check(DiagnosticLog.Events.Count(x=>x.kind=="supply_first_scan")==1,"Invocation evidence is recorded");
        Check(DiagnosticLog.Events.Count(x=>x.kind=="supply_write_begin")==1&&DiagnosticLog.Events.Count(x=>x.kind=="supply_write_verified")==1,
              "Mutation has before and verified-after evidence");
        Check(a[0]==91&&a[1]==92&&a[2]==93,"Adjacent fog fields remain intact");
        Check(c[3]==1,"Dead entity is ignored");
        var b=Fog(2,1);SupplyStealth.LateUpdate();
        Check(b[3]==0.4f,"Cache missing fog on first frame is processed when ready");
        SupplyStealth.LateUpdate();Check(a[3]==0.4f&&b[3]==0.4f,"Repeated frame is idempotent");
        a[3]=1;SupplySystem._activeSupplies.Remove(ready);SupplyStealth.LateUpdate();
        Check(a[3]==1,"Removed cache is no longer touched");
        SpottingCap.Throw=true;SupplyStealth.LateUpdate();
        Check(MelonLoader.MelonLogger.Errors.Count==1,"Read failure is reported once");
        Check(DiagnosticLog.Events.Count(x=>x.kind=="supply_failed")==1,"Failure has a diagnostic event");
        SpottingCap.Throw=false;b[3]=1;SupplyStealth.LateUpdate();
        Check(b[3]==1,"Read failure disables later writes for this session");
        Check(typeof(SupplyStealth).GetMethod("SpawnBefore")==null&&typeof(SupplyStealth).GetMethod("SpawnAfter")==null,
              "Removed native spawn callbacks do not exist");
        NativeMemory.Free(a);NativeMemory.Free(b);NativeMemory.Free(c);
        Console.WriteLine($"Supply stealth tests: {checks} passed. Native IL2CPP bridge/gameplay not exercised.");
    }
}
