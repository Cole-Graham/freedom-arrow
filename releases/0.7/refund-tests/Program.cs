using System.Reflection;
using FreedomArrow;
namespace HarmonyLib
{
 public class Harmony {public void Patch(MethodInfo m,HarmonyMethod prefix=null,HarmonyMethod postfix=null,HarmonyMethod finalizer=null){}}
 public class HarmonyMethod {public int priority;public HarmonyMethod(Type t,string n){}}
 public static class Priority {public const int First=800;}
 public static class AccessTools {public static MethodInfo Method(Type t,string n)=>t.GetMethod(n);}
}
namespace MelonLoader {public static class MelonLogger {public static void Msg(string s){}}}
namespace Il2CppBrokenArrow.Client.Ecs.Configs
{public class GameConfig {public static GameConfig Instance=new();public float HealthCostMultiplier=.5f;public int MaximumRefundPercent=90,MinimumRefundPercent=20;}}
namespace Il2CppBrokenArrow.Shared.Ecs.Components
{public class Data {public int Id=297,CategoryType=6;public float Cost=385;} public struct UnitComponent {public Data UnitData;}}
namespace Il2CppDefaultEcs
{public struct Entity {public bool IsAlive;public Il2CppBrokenArrow.Shared.Ecs.Components.Data Data;public bool Has<T>()=>Data!=null;}}
namespace Il2CppBrokenArrow.Client.Ecs.Economy.Systems {public static class RefundSystem {public static float RefundUnit(in Il2CppDefaultEcs.Entity e,bool count)=>0;}}
namespace FreedomArrow
{
 public static class Runtime {public static bool IsApplied=true;}
 public static class DiagnosticLog {public static void Write(string s,object o){}}
 public static class NativeEcs {public static T Read<T>(Il2CppDefaultEcs.Entity e)=>(T)(object)new Il2CppBrokenArrow.Shared.Ecs.Components.UnitComponent{UnitData=e.Data};}
}
static class Program
{
 static int checks;
 static void Check(bool b,string message){if(!b)throw new Exception(message);checks++;}
 static object Before(Il2CppDefaultEcs.Entity e)
 {var args=new object[]{e,null};typeof(PlaneRefund).GetMethod("Before",BindingFlags.Static|BindingFlags.NonPublic)!.Invoke(null,args);return args[1];}
 static Exception End(object state,Exception error=null)=>(Exception)typeof(PlaneRefund).GetMethod("Finally",BindingFlags.Static|BindingFlags.NonPublic)!.Invoke(null,new[]{error,state});
 static void Main()
 {
  using var fixture=new Fixture();
  PlaneRefund.Install(new HarmonyLib.Harmony(),fixture.Path);
  var cfg=Il2CppBrokenArrow.Client.Ecs.Configs.GameConfig.Instance;
  var plane=new Il2CppDefaultEcs.Entity{IsAlive=true,Data=new(){CategoryType=6}};
  var ground=new Il2CppDefaultEcs.Entity{IsAlive=true,Data=new(){CategoryType=3}};
  var drone=new Il2CppDefaultEcs.Entity{IsAlive=true,Data=new(){CategoryType=2}};
  var s=Before(plane);Check(Math.Abs(cfg.HealthCostMultiplier-2f/9)<1e-7,"Plane reads its new coefficient");
  Check(cfg.MaximumRefundPercent==90&&cfg.MinimumRefundPercent==20,"Cap and floor untouched");
  var error=new InvalidOperationException("original failed");Check(ReferenceEquals(End(s,error),error),"Original exception preserved");
  Check(cfg.HealthCostMultiplier==.5f,"Exception finalizer restores original");
  cfg.HealthCostMultiplier=.37f;s=Before(plane);End(s);Check(cfg.HealthCostMultiplier==.37f,"Restore exact original rather than hardcoded .5");
  foreach(var e in new[]{ground,drone,new Il2CppDefaultEcs.Entity()}){s=Before(e);Check(cfg.HealthCostMultiplier==.37f,"Non-air-category or dead entity unchanged");End(s);}
  Runtime.IsApplied=false;s=Before(plane);Check(cfg.HealthCostMultiplier==.37f,"Unapplied database unchanged");End(s);Runtime.IsApplied=true;
  cfg.HealthCostMultiplier=.5f;s=Before(plane);
  using var attempting=new ManualResetEventSlim();using var entered=new ManualResetEventSlim();
  var task=Task.Run(()=>{attempting.Set();var other=Before(ground);entered.Set();Check(cfg.HealthCostMultiplier==.5f,"Concurrent ground refund sees restored original");End(other);});
  Check(attempting.Wait(2000),"Concurrent refund started");Check(!entered.Wait(50),"Concurrent refund blocked while plane override active");
  End(s);Check(task.Wait(2000),"Refund lock released by finalizer");
  // Reentrant previews restore the outer coefficient, then the outer call restores the original.
  s=Before(plane);var nested=Before(plane);End(nested);Check(Math.Abs(cfg.HealthCostMultiplier-2f/9)<1e-7,"Nested plane restores outer value");End(s);Check(cfg.HealthCostMultiplier==.5f,"Outer restores original");
  Console.WriteLine($"PASS: {checks} actual PlaneRefund hook tests with native-access fixtures; IL2CPP invocation still untested.");
 }
 sealed class Fixture:IDisposable
 {
  public string Path=System.IO.Path.Combine(System.IO.Path.GetTempPath(),"fa-refund-"+Guid.NewGuid());
  public Fixture(){Directory.CreateDirectory(Path);File.WriteAllText(System.IO.Path.Combine(Path,"game-config.json"),"{\"PlaneRefundHealthMultiplier\":0.2222222222222222}");}
  public void Dispose()=>Directory.Delete(Path,true);
 }
}
