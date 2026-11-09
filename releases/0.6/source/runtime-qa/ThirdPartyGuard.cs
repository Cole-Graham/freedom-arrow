using System.Reflection;
using HarmonyLib;
using MelonLoader;
namespace FreedomArrow;
// 0.6 dev.1 (Osama, 7 November 2026): FlatIncomeMod (Speer) ships with Freedom Arrow, but its forest cover stays off.
// Its ForestCover.Post cuts infantry damage in woods by 30%, the same rule as our CoverDamage, so both would cut it twice.
// Post returns at once while its private _broken flag is set (FlatIncomeMod sets it only after an error).
static class ThirdPartyGuard
{
    static bool done;
    public static void Ensure()
    {
        if(done)return;
        var asm=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="FlatIncomeMod");
        if(asm==null)return;
        done=true;
        var field=asm.GetType("FlatIncomeMod.ForestCover")?.GetField("_broken",BindingFlags.Static|BindingFlags.NonPublic);
        if(field==null){MelonLogger.Error("FREEDOM_ARROW_THIRD_PARTY: FlatIncomeMod forest cover not found; it may double the forest cut");return;}
        field.SetValue(null,true);
        MelonLogger.Msg($"FREEDOM_ARROW_THIRD_PARTY: FlatIncomeMod forest cover off (FA forest rule only): {field.GetValue(null)}");
    }

    // 0.6 dev.10 (Osama, 7 November 2026): ArrowQueue (unchanged, ActualArrow) runs the Mod game tab against our own
    // matchmaking hub on Sam's deck, not ActualArrow's server. Its match statistics go there too.
    // ArrowQueue keeps these in UserData/ArrowQueue.cfg, which ActualArrow also reads, so the old values are put back
    // when the game closes (MelonLoader runs the quit events before it saves the preferences).
    const string Hub="https://cyberdeck.tailf7ad82.ts.net/hubs/game";
    const string Stats="https://cyberdeck.tailf7ad82.ts.net/hubs/stats";
    // ArrowQueue's own ban guard blocks the game's Skirmish button, which is how Freedom Arrow opens its offline Local AI
    // Skirmish. BALocalSkirmish already refuses every non-scenario online lobby (create, list, invite, quick search),
    // so ArrowQueue's guard is off while Freedom Arrow runs.
    static readonly List<(MelonPreferences_Entry<string> e,string old)> changed=new();
    static (MelonPreferences_Entry<bool> e,bool old)? guard;
    public static void PointArrowQueue()
    {
        if(changed.Count>0||MelonPreferences.GetCategory("ArrowQueue")==null)return;
        var g=MelonPreferences.GetEntry<bool>("ArrowQueue","BlockUnsafeModes");
        if(g==null)MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: ArrowQueue setting BlockUnsafeModes not found; its guard may block Local AI Skirmish");
        else{guard=(g,g.Value);g.Value=false;}
        foreach(var (id,url) in new[]{("Server",Hub),("StatsServer",Stats)})
        {
            var e=MelonPreferences.GetEntry<string>("ArrowQueue",id);
            if(e==null){MelonLogger.Error($"FREEDOM_ARROW_MATCHMAKING: ArrowQueue setting {id} not found");continue;}
            // A value that is already ours (left by a crash) goes back to ArrowQueue's own default ("").
            changed.Add((e,e.Value==url?"":e.Value));
            e.Value=url;
        }
        MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: ArrowQueue uses {Hub}; its ban guard is off (Freedom Arrow's lobby rules apply)");
    }
    // 0.6 dev.11 (Osama, 7 November 2026): ArrowQueue names itself and ActualArrow in the menu ("Mod server · ArrowQueue",
    // "MODS ARE ON · ARROWQUEUE", "no ActualArrow" under each online player). Its Game.Product, ProductVersion and
    // PackLabel now read Freedom Arrow and our version. PackLabel is also what ArrowQueue sends to the hub, which shows
    // "FA <version>" as each player's version (FAQueue).
    static string faLabel="",faVersion="";
    public static void NameArrowQueue(HarmonyLib.Harmony h,string version)
    {
        var game=AccessTools.TypeByName("ArrowQueue.Game");
        if(game==null){MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: ArrowQueue.Game not found; menu keeps ArrowQueue's names");return;}
        faVersion=version;faLabel="FA "+version;
        foreach(var (prop,post) in new[]{("Product",nameof(ProductName)),("ProductVersion",nameof(ProductVer)),("PackLabel",nameof(PackName))})
        {
            var getter=AccessTools.PropertyGetter(game,prop);
            if(getter==null){MelonLogger.Error($"FREEDOM_ARROW_MATCHMAKING: ArrowQueue Game.{prop} not found");continue;}
            h.Patch(getter,postfix:new HarmonyMethod(typeof(ThirdPartyGuard),post));
        }
        MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: ArrowQueue menu names Freedom Arrow {version}");
        SameBuildCode(game);
        OnlyFaMaps(h,game);
    }

    // 0.6 dev.16 (Osama, 7 November 2026): players on the same FA build saw different build codes. ArrowQueue hashes every
    // loaded mod DLL except its Cosmetic list, so the music pack (FAMusic.dll, private, its own version) and the menu logger
    // (FAUiLog.dll, only on test PCs) changed the code. Neither changes the game, so both join the Cosmetic list.
    static void SameBuildCode(Type game)
    {
        if(AccessTools.Field(game,"Cosmetic")?.GetValue(null) is not HashSet<string> cosmetic)
        {MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: ArrowQueue Game.Cosmetic not found; the music pack changes the build code");return;}
        cosmetic.Add("FAMusic.dll");cosmetic.Add("FAUiLog.dll");
        AccessTools.Field(game,"_packHash")?.SetValue(null,null);   // in case ArrowQueue already made the code
        MelonLogger.Msg("FREEDOM_ARROW_MATCHMAKING: build code leaves out FAMusic.dll and FAUiLog.dll");
        SameDatabaseCode(game);
    }

    // Batch (Lateralus, 8 November 2026): players on the same FA build still saw different codes. ArrowQueue's database part
    // hashes UserData/MLDatabaseMod: "nodb" with no folder, "0f-..." with only the disabled ActualArrow files left over.
    // Freedom Arrow never reads that folder. The part is now the hash of our payload manifest, which lists every packaged
    // file's SHA-256, so the code tracks FA's own data and no longer depends on ActualArrow leftovers.
    static void SameDatabaseCode(Type game)
    {
        var field=AccessTools.Field(game,"_dbHash");
        if(field==null){MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: ArrowQueue Game._dbHash not found; leftover MLDatabaseMod folders change the build code");return;}
        var manifest=Path.Combine(MelonLoader.Utils.MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","payload-manifest.json");
        var code="fa-"+Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(manifest)))[..12].ToLowerInvariant();
        field.SetValue(null,code);
        AccessTools.Field(game,"_packHash")?.SetValue(null,null);
        MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: build code database part {code} (payload manifest; MLDatabaseMod not read)");
    }

    // 0.6 dev.16 (Osama, 7 November 2026): Create a lobby offers only our online maps. ArrowQueue offers Steam Workshop
    // maps only; the [FA] scenarios come in the Freedom Arrow package, so every player has them. The Skirmish copies
    // are for Local AI Skirmish and stay out.
    static MethodInfo allScenarios;
    static void OnlyFaMaps(HarmonyLib.Harmony h,Type game)
    {
        var supported=AccessTools.Method(game,"SupportedScenarios");
        allScenarios=AccessTools.Method(game,"AllScenarios");
        if(supported==null||allScenarios==null){MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: ArrowQueue map list not found; Create a lobby keeps Workshop maps");return;}
        h.Patch(supported,postfix:new HarmonyMethod(typeof(ThirdPartyGuard),nameof(FaMaps)));
        MelonLogger.Msg("FREEDOM_ARROW_MATCHMAKING: Create a lobby offers [FA] maps only");
    }
    static bool mapsSaid;
    static void FaMaps(object __result)
    {
        if(__result is not System.Collections.IList found)return;
        var all=allScenarios.Invoke(null,null) as System.Collections.IList;
        found.Clear();
        var names=new SortedDictionary<string,object>(StringComparer.OrdinalIgnoreCase);
        foreach(var s in all??new object[0])
        {
            var name=s?.GetType().GetProperty("Name")?.GetValue(s) as string;
            if(name!=null&&name.StartsWith("[FA]")&&!name.Contains("Skirmish"))names.TryAdd(name,s);
        }
        foreach(var s in names.Values)found.Add(s);
        if(!mapsSaid){mapsSaid=true;MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: lobby maps: {string.Join(", ",names.Keys)}");}
    }
    static void ProductName(ref string __result)=>__result="Freedom Arrow";
    static void ProductVer(ref string __result)=>__result=faVersion;
    static void PackName(ref string __result)=>__result=faLabel;

    public static void RestoreArrowQueue()
    {
        foreach(var (e,old) in changed)e.Value=old;
        if(guard is {} g){g.e.Value=g.old;guard=null;}
        if(changed.Count>0)MelonLogger.Msg("FREEDOM_ARROW_MATCHMAKING: ArrowQueue settings restored for ActualArrow");
        changed.Clear();
    }
}
