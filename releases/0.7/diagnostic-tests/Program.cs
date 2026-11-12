using System.Text.Json;
using FreedomArrow;
namespace MelonLoader
{
    public static class MelonLogger
    {
        public static readonly List<string> Errors=new();
        public static void Msg(string text) { }
        public static void Warning(string text) { }
        public static void Error(string text)=>Errors.Add(text);
    }
}
namespace FreedomArrow
{
    public static class Runtime { public static bool IsApplied=>true; }
    public static class SupplyStealth { public static object Status()=>new{passes=7,changes=2}; }
}
static class Program
{
    static int checks;
    static void Check(bool value,string label){if(!value)throw new Exception(label);checks++;}
    static void Main()
    {
        string fixture=Path.Combine(Path.GetTempPath(),"fa-diagnostic-test-"+Guid.NewGuid());
        string root=Path.Combine(fixture,"Game","UserData","FreedomArrow");
        string mods=Path.Combine(fixture,"Game","Mods");Directory.CreateDirectory(mods);
        File.WriteAllBytes(Path.Combine(mods,"Fixture.dll"),new byte[]{1,2,3});
        try
        {
            DiagnosticLog.Start(root,"fixture-version");
            var path=Directory.GetFiles(Path.Combine(root,"diagnostics"),"*.jsonl").Single();
            DiagnosticLog.Write("fixture",new{value=42});
            var live=File.ReadAllLines(path).Select(s=>JsonDocument.Parse(s)).ToArray();
            Check(live.Length==2,"Records are flushed while the process is still alive");
            var start=live[0].RootElement;
            Check(start.GetProperty("data").GetProperty("version").GetString()=="fixture-version","Version ties evidence to a build");
            Check(start.GetProperty("pid").GetInt32()==Environment.ProcessId,"PID ties evidence to a dump");
            Check(start.GetProperty("data").GetProperty("mods")[0].GetProperty("sha256").GetString()==
                  "039058c6f2c0cb492c533b0a4d14ef77cc0f78abccced5287d84a1a2011cfb81","DLL hash is correct");
            DiagnosticLog.Heartbeat();DiagnosticLog.Heartbeat();
            Check(File.ReadAllLines(path).Count(x=>x.Contains("\"heartbeat\""))==1,"Repeated frames do not spam heartbeat");
            Exception fixtureError;
            try{throw new InvalidOperationException("managed exception fixture");}
            catch(Exception e){fixtureError=e;}
            typeof(DiagnosticLog).GetMethod("ManagedUnhandled",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic)
                .Invoke(null,new object[]{null,new UnhandledExceptionEventArgs(fixtureError,false)});
            var error=JsonDocument.Parse(File.ReadAllLines(path).Last()).RootElement;
            Check(error.GetProperty("kind").GetString()=="managed_unhandled"&&
                  error.GetProperty("data").GetProperty("error").GetString().Contains("Program.Main"),
                  "Managed exception callback preserves the error and stack");
            DiagnosticLog.Close("fixture");
            Check(File.ReadAllLines(path).Last().Contains("session_close"),"Normal stop has an end record");
            for(int i=0;i<10;i++){DiagnosticLog.Start(root,"retention");DiagnosticLog.Close("retention");}
            Check(Directory.GetFiles(Path.Combine(root,"diagnostics"),"*.jsonl").Length==8,"Only eight sessions retained");
            DiagnosticLog.Start(root,"size-limit");
            path=Directory.GetFiles(Path.Combine(root,"diagnostics"),"*.jsonl").OrderByDescending(File.GetLastWriteTimeUtc).First();
            string payload=new('x',200_000);for(int i=0;i<30;i++)DiagnosticLog.Write("large",new{payload});
            Check(new FileInfo(path).Length<=4*1024*1024,"File size stays bounded");
            Check(File.ReadAllLines(path).Last().Contains("log_limit"),"An intentional size stop is distinguishable from a crash");
            long length=new FileInfo(path).Length;DiagnosticLog.Write("after_limit",new{});
            Check(new FileInfo(path).Length==length,"Size limit stops further writes");
            DiagnosticLog.Close("done");
            string bad=Path.Combine(fixture,"not-a-directory");File.WriteAllText(bad,"fixture");
            DiagnosticLog.Start(bad,"io-failure");DiagnosticLog.Write("ignored",new{});
            Check(MelonLoader.MelonLogger.Errors.Count==1,"IO failure is contained and reported");
            Console.WriteLine($"Diagnostic tests: {checks} passed. Native-crash handling is not exercised.");
        }
        finally{DiagnosticLog.Close("cleanup");Directory.Delete(fixture,true);}
    }
}
