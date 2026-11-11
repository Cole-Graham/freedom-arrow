using System.IO.Compression;
using System.Text.Json;
namespace FreedomArrow;

// Managed file work at normal shutdown only. Never called from native combat callbacks.
static class TestLogBundle
{
    const long MaxFileBytes=32L*1024*1024,MaxTotalBytes=128L*1024*1024;
    public static string Create(string gameRoot,DateTime startedUtc,string version)
    {
        string diagnostics=Path.Combine(gameRoot,"UserData","FreedomArrow","diagnostics");
        Directory.CreateDirectory(diagnostics);
        var candidates=new List<string>();
        void Add(string folder,string pattern)
        {
            if(Directory.Exists(folder))candidates.AddRange(Directory.GetFiles(folder,pattern)
                .Where(f=>File.GetLastWriteTimeUtc(f)>=startedUtc.AddSeconds(-10)));
        }
        Add(diagnostics,"aa-targeting-*.jsonl");Add(diagnostics,"runtime-*.jsonl");
        string conquest=Path.Combine(gameRoot,"UserData","FAConquestPrototype");
        Add(conquest,"shots-*.jsonl");Add(conquest,"events-*.jsonl");
        string latest=Path.Combine(gameRoot,"MelonLoader","Latest.log");
        if(File.Exists(latest))candidates.Add(latest);
        string safeVersion=new string(version.Where(c=>(c>='A'&&c<='Z'||c>='a'&&c<='z'||c>='0'&&c<='9')||c=='.'||c=='-').ToArray());
        string path=Path.Combine(diagnostics,$"test-logs-{safeVersion}-{DateTime.UtcNow:yyyyMMdd-HHmmssfffffff}-{Environment.ProcessId}.zip");
        var copied=new List<object>();var skipped=new List<object>();long total=0;
        using(var zip=new ZipArchive(new FileStream(path,FileMode.CreateNew,FileAccess.Write),ZipArchiveMode.Create))
        {
            foreach(string file in candidates.Distinct().OrderBy(f=>f))
            {
                string relative=Path.GetRelativePath(gameRoot,file).Replace('\\','/');
                try
                {
                    var info=new FileInfo(file);
                    if(info.Attributes.HasFlag(FileAttributes.ReparsePoint)||info.Length>MaxFileBytes||total+info.Length>MaxTotalBytes)
                    {skipped.Add(new{file=relative,reason="symlink or size limit"});continue;}
                    using var input=new FileStream(file,FileMode.Open,FileAccess.Read,FileShare.ReadWrite|FileShare.Delete);
                    long length=input.Length,remaining=length;
                    using(var output=zip.CreateEntry(relative,CompressionLevel.Fastest).Open())
                    {
                        byte[] buffer=new byte[65536];
                        while(remaining>0)
                        {
                            int n=input.Read(buffer,0,(int)Math.Min(buffer.Length,remaining));
                            if(n==0)break;output.Write(buffer,0,n);remaining-=n;
                        }
                    }
                    total+=length-remaining;copied.Add(new{file=relative,bytes=length-remaining});
                }
                catch(Exception e){skipped.Add(new{file=relative,reason=e.GetType().Name});}
            }
            using var writer=new StreamWriter(zip.CreateEntry("bundle.json").Open());
            writer.Write(JsonSerializer.Serialize(new{version,startedUtc,createdUtc=DateTime.UtcNow,
                scope="BA test logs from this session plus MelonLoader Latest.log; no gameplay changes",copied,skipped,totalBytes=total},new JsonSerializerOptions{WriteIndented=true}));
        }
        return path;
    }
}
