using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using MelonLoader;
namespace FreedomArrow;

// Independent, bounded evidence. A logging failure must never disable gameplay or scoring.
static class DiagnosticLog
{
    const long MaxBytes=4*1024*1024;
    const int KeepSessions=8;
    static readonly object Gate=new();
    static StreamWriter writer;
    static long bytes;
    static int sequence;
    static long nextHeartbeat;
    static bool subscribed;
    public static void Start(string root,string version)
    {
        try
        {
            string directory=Path.Combine(root,"diagnostics");
            Directory.CreateDirectory(directory);
            foreach(var old in new DirectoryInfo(directory).GetFiles("runtime-*.jsonl")
                .OrderByDescending(f=>f.LastWriteTimeUtc).Skip(KeepSessions-1))
                try{old.Delete();}catch{ }
            string path=Path.Combine(directory,$"runtime-{DateTime.UtcNow:yyyyMMdd-HHmmssfffffff}-{Environment.ProcessId}.jsonl");
            lock(Gate)
            {
                writer?.Dispose();
                writer=new StreamWriter(new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.ReadWrite),new UTF8Encoding(false)){AutoFlush=true,NewLine="\n"};
                bytes=0;sequence=0;nextHeartbeat=0;
            }
            string gameRoot=Directory.GetParent(Directory.GetParent(root).FullName).FullName;
            string mods=Path.Combine(gameRoot,"Mods");
            var hashes=Directory.Exists(mods)?Directory.GetFiles(mods,"*.dll").OrderBy(f=>f).Take(128)
                .Select(f=>new{file=Path.GetFileName(f),sha256=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(f))).ToLowerInvariant()}).ToArray():null;
            Write("session_start",new{version,clr=Environment.Version.ToString(),pointerBytes=IntPtr.Size,mods=hashes,
                maxBytes=MaxBytes,keepSessions=KeepSessions,nativeDumpRequired=true});
            if(!subscribed)
            {
                subscribed=true;
                AppDomain.CurrentDomain.UnhandledException+=ManagedUnhandled;
            }
            MelonLogger.Msg("FREEDOM_ARROW_DIAGNOSTICS "+path);
        }
        catch(Exception e){StopAfterFailure(e);}
    }
    public static void Write(string kind,object data)
    {
        lock(Gate)
        {
            if(writer==null)return;
            try
            {
                string line=JsonSerializer.Serialize(new{sequence=++sequence,utc=DateTime.UtcNow,pid=Environment.ProcessId,kind,data});
                int size=Encoding.UTF8.GetByteCount(line)+1;
                if(bytes+size>MaxBytes-512)
                {
                    writer.WriteLine(JsonSerializer.Serialize(new{sequence=++sequence,utc=DateTime.UtcNow,pid=Environment.ProcessId,kind="log_limit",data=new{maxBytes=MaxBytes}}));
                    writer.Dispose();writer=null;
                    MelonLogger.Warning("FREEDOM_ARROW_DIAGNOSTICS size limit reached; gameplay continues");
                    return;
                }
                writer.WriteLine(line);bytes+=size;
            }
            catch(Exception e){StopAfterFailure(e);}
        }
    }
    static void ManagedUnhandled(object sender,UnhandledExceptionEventArgs e)
        =>Write("managed_unhandled",new{e.IsTerminating,error=e.ExceptionObject.ToString()});
    public static void Heartbeat()
    {
        long now=Stopwatch.GetTimestamp();
        if(now<nextHeartbeat)return;
        nextHeartbeat=now+10*Stopwatch.Frequency;
        Write("heartbeat",new{applied=Runtime.IsApplied,supply=SupplyStealth.Status()});
    }
    public static void Close(string reason)
    {
        Write("session_close",new{reason});
        lock(Gate){writer?.Dispose();writer=null;}
    }
    static void StopAfterFailure(Exception e)
    {
        try{writer?.Dispose();}catch{ }
        writer=null;
        MelonLogger.Error("FREEDOM_ARROW_DIAGNOSTICS_FAILED: logging off; gameplay continues. "+e);
    }
}
