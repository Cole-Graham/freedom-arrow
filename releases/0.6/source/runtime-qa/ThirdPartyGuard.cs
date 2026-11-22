using System.Reflection;
using System.Text.Json.Nodes;
using HarmonyLib;
using MelonLoader;
using MelonLoader.Utils;
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
        // 0.9 dev.44 batch (Osama 19 Nov 2026 00:1x PST, Chinese playtester SteelPlate: "Desync when a veh been killed - the infantry it contains
        // some times died normally but usually just left over, and cause the desync"). FlatIncomeMod.CargoDeath polls every 0.1 s and kills the
        // squads of a destroyed transport on each PC itself. 18-19 Nov logs: 41 kills, 25 of them "health 0 didn't kill the squad within 1 s -
        // death mark set (fallback)", a mark that exists on that PC only, so the squad lives on for everyone else. Its Update returns at once while
        // _broken is set (same switch as ForestCover). Passengers still die with the transport through the game's own rule, which DetectionConfig
        // sets to 100% (GameConfig OnTransportDeathCargoKillFloor/HLFloor), so every PC agrees.
        var cargo=asm.GetType("FlatIncomeMod.CargoDeath")?.GetField("_broken",BindingFlags.Static|BindingFlags.NonPublic);
        if(cargo==null){MelonLogger.Error("FREEDOM_ARROW_THIRD_PARTY: FlatIncomeMod CargoDeath not found; its local passenger kill may desync");return;}
        cargo.SetValue(null,true);
        MelonLogger.Msg($"FREEDOM_ARROW_THIRD_PARTY: FlatIncomeMod local passenger kill off (game rule kills them on every PC): {cargo.GetValue(null)}");
    }

    // 0.6 dev.10 (Osama, 7 November 2026): ArrowQueue (unchanged, ActualArrow) runs the Mod game tab against our own
    // matchmaking hub on Sam's deck, not ActualArrow's server. Its match statistics go there too.
    // ArrowQueue keeps these in UserData/ArrowQueue.cfg, which ActualArrow also reads, so the old values are put back
    // when the game closes (MelonLoader runs the quit events before it saves the preferences).
    // 0.9 dev.44 batch (Osama 19 Nov 2026, Chinese playtesters: "can't see others online or other mod lobbies"): mainland China cannot reach the
    // deck's Tailscale address (*.ts.net); SteelPlate's CN sessions timed out every 60 s, his Hong Kong (VPN) session connected. The hub now goes
    // through freedomarrow.app (Cloudflare Worker fa-site, /hubs/* passed through to the same hub, WebSocket included).
    // Ranked test build (Lateralus 22 Nov 2026): RankedMenu.TestHub points ArrowQueue at the ranked test hub (/hubs/test) instead.
    static readonly string Hub=RankedMenu.TestHub?RankedMenu.TestHubRoot+"/game":"https://freedomarrow.app/hubs/game";
    static readonly string Stats=RankedMenu.TestHub?RankedMenu.TestHubRoot+"/stats":"https://freedomarrow.app/hubs/stats";
    static readonly string[] OldHubs={"https://cyberdeck.tailf7ad82.ts.net/hubs/game","https://cyberdeck.tailf7ad82.ts.net/hubs/stats",
        "https://freedomarrow.app/hubs/game","https://freedomarrow.app/hubs/stats","https://freedomarrow.app/hubs/test/game","https://freedomarrow.app/hubs/test/stats"};
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
            changed.Add((e,e.Value==url||Array.IndexOf(OldHubs,e.Value)>=0?"":e.Value));
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
        NoActualArrowLabel(h,game);
        OnlyFaMaps(h,game);
        LobbyMapTabs.Install(h);
        try{MapLabels.Install(h);}catch(Exception x){MelonLogger.Error("FREEDOM_ARROW_MAP_LABELS_FAILED: not installed. "+x.Message);}
    }

    // 0.6 dev.16 (Osama, 7 November 2026): players on the same FA build saw different build codes. ArrowQueue hashes every
    // loaded mod DLL except its Cosmetic list, so the music pack (FAMusic.dll, private, its own version) and the menu logger
    // (FAUiLog.dll, only on test PCs) changed the code. Neither changes the game, so both join the Cosmetic list.
    static void SameBuildCode(Type game)
    {
        if(AccessTools.Field(game,"Cosmetic")?.GetValue(null) is not HashSet<string> cosmetic)
        {MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: ArrowQueue Game.Cosmetic not found; the music pack changes the build code");return;}
        cosmetic.Add("FAMusic.dll");cosmetic.Add("FAUiLog.dll");cosmetic.Add("FAModels.dll");
        // 0.9.1-dev.2: TeamVoice.dll and HudQuick.dll ship as FATeamVoice.dll and FAHudQuick.dll (FA prefix, Lateralus); ArrowQueue lists only the old names.
        cosmetic.Add("FATeamVoice.dll");cosmetic.Add("FAHudQuick.dll");
        AccessTools.Field(game,"_packHash")?.SetValue(null,null);   // in case ArrowQueue already made the code
        MelonLogger.Msg("FREEDOM_ARROW_MATCHMAKING: build code leaves out FAMusic.dll, FAUiLog.dll, FAModels.dll, FATeamVoice.dll and FAHudQuick.dll");
        SameDatabaseCode(game);
    }

    // 0.9 dev.43 batch (Osama, 18 November 2026: "how come some people are on different versions from the same install"): a player's log
    // showed the same 4 DLLs as ours (b90982ef) but "ActualArrow 1.0.8", because an old ActualArrow entry is still switched on in the
    // BAModManager manifest. ArrowQueue then puts "aa1.0.8" instead of "noaa" in front of the DLL hash, so the code was G3XZ, not BRX7.
    // Freedom Arrow never uses ActualArrow, and any ActualArrow DLL that really loads still changes the DLL hash, so only the label goes.
    static FieldInfo packHashField;
    static void NoActualArrowLabel(HarmonyLib.Harmony h,Type game)
    {
        var pack=AccessTools.Method(game,"PackHash");packHashField=AccessTools.Field(game,"_packHash");
        if(pack==null||packHashField==null){MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: ArrowQueue PackHash not found; an old ActualArrow entry still changes the build code");return;}
        h.Patch(pack,postfix:new HarmonyMethod(typeof(ThirdPartyGuard),nameof(DropActualArrowLabel)));
        packHashField.SetValue(null,null);
    }
    static bool labelLogged;
    static void DropActualArrowLabel(ref string __result)
    {
        if(__result==null||!__result.StartsWith("aa",StringComparison.Ordinal))return;
        var dash=__result.IndexOf('-');if(dash<0)return;
        var was=__result;__result="noaa"+__result[dash..];packHashField.SetValue(null,__result);
        if(!labelLogged){labelLogged=true;MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: build code ignores the ActualArrow entry in the Mod Manager ({was} -> {__result}); its DLLs, if loaded, still count");}
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
        // Lateralus 16 Nov 2026: Chernyakhovsky 1v1 and Dead Center 1v1 failed to load into a new lobby. A map author's own editor copy
        // (game folder Scenarios, saved as an editor scenario) can have the same name as our packaged map; the first one found was kept.
        // Our copy is the one InstallScenarios puts in Mods/Scenarios (the game lists it as manually downloaded), so it wins a name clash.
        var dupes=new List<string>();
        // Lateralus 17 Nov 2026: "when I have local copies of a map in my game install, it shows them in this menu, I only want to see the
        // copy that comes with the mod". A local [FA] map that this package does not ship (an old version such as his [1v1] Dead Center
        // 0.1, saved under another GUID so RemoveRetiredScenarios keeps it) stays out. Nothing is deleted from the disk.
        shipped??=Shipped();
        var local=new SortedSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach(var s in all??new object[0])
        {
            var name=(s?.GetType().GetProperty("Name")?.GetValue(s) as string)?.Trim();
            if(name==null||!name.StartsWith("[FA]")||name.Contains("Skirmish"))continue;
            if(shipped.Count>0&&!shipped.Contains(name)){local.Add(name);continue;}
            if(!names.TryGetValue(name,out var had)){names[name]=s;continue;}
            dupes.Add(name);
            if(Ours(s)&&!Ours(had))names[name]=s;
        }
        foreach(var s in names.Values)found.Add(s);
        if(!mapsSaid){mapsSaid=true;MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: lobby maps: {string.Join(", ",names.Keys)}");
            if(dupes.Count>0)MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: same name in two places, the Freedom Arrow copy (Mods/Scenarios) is used: {string.Join(", ",dupes.Distinct())}");
            if(local.Count>0)MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: local [FA] maps not in this package left out: {string.Join(", ",local)}");}
    }
    // Map names this package ships: UserData/FreedomArrow/scenarios/*/meta.json "scenario" (folder name if missing). Empty if the folder
    // cannot be read; then no map is left out. Retired maps (Runtime.RetiredScenarios) never count as shipped.
    static HashSet<string> shipped;
    static HashSet<string> Shipped()
    {
        var names=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        try
        {
            var root=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","scenarios");
            foreach(var folder in Directory.Exists(root)?Directory.GetDirectories(root):new string[0])
            {
                string name=null;
                try{name=JsonNode.Parse(File.ReadAllText(Path.Combine(folder,"meta.json")))?["scenario"]?.GetValue<string>();}catch{}
                names.Add((name??Path.GetFileName(folder)).Trim());
            }
            // A retired map left in UserData by an older package is not shipped.
            foreach(var (folder,_) in Runtime.RetiredScenarios)names.Remove(folder);
            foreach(var folder in Runtime.RetiredScenarioFolders)names.Remove(folder);
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: packaged map names not read, local maps stay in the list. "+e.Message);names.Clear();}
        return names;
    }
    static bool Ours(object s)
    {
        var folder=(s.GetType().GetProperty("Folder")?.GetValue(s) as string??"").Replace('\\','/');
        return folder.Contains("/Mods/Scenarios/",StringComparison.OrdinalIgnoreCase)||s.GetType().GetProperty("ManuallyDownloaded")?.GetValue(s) is true;
    }
    static void ProductName(ref string __result)=>__result="Freedom Arrow";
    static void ProductVer(ref string __result)=>__result=faVersion;
    static void PackName(ref string __result)=>__result=faLabel;

    public static void RestoreArrowQueue()
    {
        // ArrowQueue's settings live in FA's own copy (ThirdPartyCfg): nothing of ActualArrow's to put back.
        if(ThirdPartyCfg.Moved("ArrowQueue")){changed.Clear();guard=null;return;}
        foreach(var (e,old) in changed)e.Value=old;
        if(guard is {} g){g.e.Value=g.old;guard=null;}
        if(changed.Count>0)MelonLogger.Msg("FREEDOM_ARROW_MATCHMAKING: ArrowQueue settings restored for ActualArrow");
        changed.Clear();
    }
}
