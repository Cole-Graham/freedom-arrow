using System.IO.Compression;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using MelonLoader;
using MelonLoader.Utils;
namespace FreedomArrow;

// 0.9.0-dev.36 game log upload (Osama 16 Nov 2026 20:5x PST and 17 Nov 11:3x PST, thread 1571014792016171120: "the mod automatically should be sending logs
// to our website ... by default it should be on ... If they want to opt out, they'd need to go into the Mod Game settings", "we do want names so we can log
// for cheaters", "whenever someone plays the game, we see the logs uploaded", "It's also an anti cheat purpose").
// The MelonLoader log goes to https://freedomarrow.app/logs/upload with the player's Steam name and ID, the mod version and the SHA-256 of every DLL in
// Mods and Plugins. One file per game session on the site, replaced by each newer copy: after every match, every 5 minutes while the log grows, and at quit.
// MelonLoader stopped keeping old logs on Osama's PC after 9 Nov and the shutdown bundle only appears on a clean quit, so a crash or Alt-F4 still leaves
// the last 5-minute copy. No opt-out (Osama 17 Nov 2026 12:1x PST: "We will just put a warning on the announcement then no opt out. By downloading and
// playing they agree"). Also the SHA-256 of GameAssembly.dll and global-metadata.dat, so a patched game binary shows up next to the mod DLL list.
static class LogUpload
{
    const string Url="https://freedomarrow.app/logs/upload";
    // Not a secret: it ships in this DLL. It only keeps random web traffic off the upload address (Worker secret LOGKEY).
    const string Key="ISX9XIxTlI3LO85gxWK0ePRar6eeQ8eI";
    static readonly string[] MenuScenes={"Hangar_Scene","Void","EntryPoint"};
    static readonly HttpClient http=new(){Timeout=TimeSpan.FromSeconds(60)};
    static string session="",day="",version="",started="",player="",steamId="",lastMap="",scene="";
    static bool identityTried;static long lastLength=-1;static int busy;static DateTime nextPeriodic=DateTime.MaxValue;
    static string[] mods=Array.Empty<string>();
    public static string Session=>session;

    public static void Start(string packageVersion)
    {
        version=packageVersion;var now=DateTime.UtcNow;
        session=$"{now:yyyyMMdd-HHmmss}-{RandomNumberGenerator.GetInt32(0x1000000):x6}";day=$"{now:yyyy-MM-dd}";started=$"{now:yyyy-MM-dd HH:mm}";
        MelonLogger.Msg($"FREEDOM_ARROW_LOG_UPLOAD on, session {session}");
    }

    public static void SceneLoaded(string name)
    {
        string before=scene;scene=name;
        if(Array.IndexOf(MenuScenes,name)<0){lastMap=name;return;}
        if(name!="Hangar_Scene")return;
        if(!identityTried){identityTried=true;ReadIdentity();nextPeriodic=DateTime.UtcNow.AddMinutes(1);}
        if(before.Length>0&&Array.IndexOf(MenuScenes,before)<0)Send("match end");
    }

    public static void Tick()
    {
        if(DateTime.UtcNow<nextPeriodic)return;
        nextPeriodic=DateTime.UtcNow.AddMinutes(5);Send("every 5 min");
    }

    public static void Quit()
    {
        if(!identityTried)return;
        try{Upload("quit",true);}catch{}
    }

    static void Send(string kind)
    {
        if(session.Length==0||Interlocked.CompareExchange(ref busy,1,0)!=0)return;
        Task.Run(()=>{try{Upload(kind,false);}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_LOG_UPLOAD failed: "+e.Message);}finally{busy=0;}});
    }

    // Main thread (Steam's API objects are IL2CPP). Reflection, so the build needs no Steamworks reference.
    static void ReadIdentity()
    {
        try
        {
            var asm=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="Il2Cppcom.rlabrecque.steamworks.net");
            var id=asm?.GetType("Il2CppSteamworks.SteamUser")?.GetMethod("GetSteamID")?.Invoke(null,null);
            var raw=id?.GetType().GetField("m_SteamID")?.GetValue(id)??id?.GetType().GetProperty("m_SteamID")?.GetValue(id);
            steamId=raw?.ToString()??"";
            player=asm?.GetType("Il2CppSteamworks.SteamFriends")?.GetMethod("GetPersonaName")?.Invoke(null,null)?.ToString()??"";
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_LOG_UPLOAD Steam name/ID not read: "+e.Message);}
        if(steamId.Length==0||!steamId.All(char.IsDigit))steamId="unknown";
        MelonLogger.Msg($"FREEDOM_ARROW_LOG_UPLOAD player {player} ({steamId})");
        Task.Run(()=>{try{mods=HashMods();}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_LOG_UPLOAD mod list: "+e.Message);}});
    }

    static string[] HashMods()
    {
        var list=new List<string>();string root=MelonEnvironment.GameRootDirectory;using var sha=SHA256.Create();
        foreach(string dir in new[]{"Mods","Plugins","UserLibs"})
        {
            string d=Path.Combine(root,dir);if(!Directory.Exists(d))continue;
            foreach(string f in Directory.GetFiles(d,"*.dll").OrderBy(f=>f,StringComparer.OrdinalIgnoreCase))
            {
                using var s=new FileStream(f,FileMode.Open,FileAccess.Read,FileShare.ReadWrite|FileShare.Delete);
                list.Add($"{dir}/{Path.GetFileName(f)} {Convert.ToHexString(sha.ComputeHash(s)).ToLowerInvariant()} {new FileInfo(f).Length}");
            }
        }
        foreach(string f in new[]{Path.Combine(root,"GameAssembly.dll")}.Concat(Directory.GetDirectories(root,"*_Data").Select(d=>Path.Combine(d,"il2cpp_data","Metadata","global-metadata.dat"))))
        {
            if(!File.Exists(f))continue;
            using var s=new FileStream(f,FileMode.Open,FileAccess.Read,FileShare.ReadWrite|FileShare.Delete);
            list.Add($"game/{Path.GetFileName(f)} {Convert.ToHexString(sha.ComputeHash(s)).ToLowerInvariant()} {new FileInfo(f).Length}");
        }
        return list.ToArray();
    }

    static void Upload(string kind,bool quit)
    {
        if(session.Length==0)return;
        string log=Path.Combine(MelonEnvironment.GameRootDirectory,"MelonLoader","Latest.log");
        if(!File.Exists(log))return;
        long length=new FileInfo(log).Length;
        long snapLength=MatchLog.File.Length>0&&File.Exists(MatchLog.File)?new FileInfo(MatchLog.File).Length:0;
        if(kind=="every 5 min"&&length+snapLength==lastLength)return;
        var header=new{session,started,version,player,steamId,kind,lastMap,match=MatchLog.FightId,uploadedUtc=DateTime.UtcNow.ToString("u"),mods};
        using var body=new MemoryStream();
        using(var gz=new GZipStream(body,CompressionLevel.Optimal,true))
        {
            var head=Encoding.UTF8.GetBytes("# Freedom Arrow game log upload\n"+JsonSerializer.Serialize(header,new JsonSerializerOptions{WriteIndented=true})+"\n---- MelonLoader/Latest.log ----\n");
            gz.Write(head);
            using var src=new FileStream(log,FileMode.Open,FileAccess.Read,FileShare.ReadWrite|FileShare.Delete);
            src.CopyTo(gz);
            // Unit snapshots of this session (MatchLog), when there was a battle.
            MatchLog.Flush();
            if(MatchLog.File.Length>0&&File.Exists(MatchLog.File))
            {
                gz.Write(Encoding.UTF8.GetBytes("\n---- match snapshots (MatchLog) ----\n"));
                using var snap=new FileStream(MatchLog.File,FileMode.Open,FileAccess.Read,FileShare.ReadWrite|FileShare.Delete);
                snap.CopyTo(gz);
            }
        }
        var req=new HttpRequestMessage(HttpMethod.Post,Url){Content=new ByteArrayContent(body.ToArray())};
        void H(string n,string v)=>req.Headers.TryAddWithoutValidation("X-FA-"+n,Uri.EscapeDataString(v??""));
        req.Headers.TryAddWithoutValidation("X-FA-Key",Key);
        H("SteamId",steamId);H("Session",session);H("Day",day);H("Player",player);H("Version",version);H("Kind",kind);H("Started",started);H("Map",lastMap);
        H("Match",MatchLog.FightId==0?"":MatchLog.FightId.ToString());H("Mods",string.Join(",",mods.Select(m=>m.Split(' ')[0].Split('/')[1])));
        using var cts=new CancellationTokenSource(TimeSpan.FromSeconds(quit?5:60));
        var res=http.Send(req,cts.Token);
        if(!res.IsSuccessStatusCode)throw new HttpRequestException($"HTTP {(int)res.StatusCode}");
        lastLength=length+snapLength;
        if(!quit)MelonLogger.Msg($"FREEDOM_ARROW_LOG_UPLOAD sent ({kind}, {body.Length/1024} KB)");
    }
}
