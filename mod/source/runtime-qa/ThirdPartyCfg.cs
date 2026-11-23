using MelonLoader;
using MelonLoader.Utils;
namespace FreedomArrow;
// Lateralus 22 Nov 2026 (thread 1568104480459722894): "I'm worried that some of these config file names might overlap with Actual Arrow"
// / "ok proceed with the fix to the collisions". FA ships unchanged ActualArrow mods (ArrowQueue, HudQuick, TeamVoice, FlatIncomeMod,
// SteamAvatars inside FlatIncomeMod). They keep their settings in UserData/ArrowQueue.cfg, HudQuick.cfg, TeamVoice.cfg, SteamAvatars.cfg
// and the FlatIncomeMod section of MelonPreferences.cfg - the same files an ActualArrow install reads, and FA writes some of them
// (ArrowQueue's Server/StatsServer/BlockUnsafeModes, FlatIncomeMod's missile alarm volume).
// While Freedom Arrow runs, those categories are moved to UserData/FreedomArrow/ThirdParty/<category>.cfg with MelonLoader's own
// per-category file switch, so ActualArrow's files are never written by FA. First run: the current values (read from the AA file) are
// saved into the FA copy. Later runs: the FA copy is loaded. The AA DLLs are unchanged.
static class ThirdPartyCfg
{
    static readonly string[] Categories={"ArrowQueue","HudQuick","TeamVoice","SteamAvatars","FlatIncomeMod"};
    static readonly HashSet<string> done=new();
    public static bool Moved(string category)=>done.Contains(category);

    // Called at the start of OnInitializeMelon (categories of mods that loaded before FA) and of OnLateInitializeMelon (all the rest),
    // before any FA code changes a third-party value.
    public static void Redirect()
    {
        var dir=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","ThirdParty");
        foreach(var id in Categories)
        {
            if(done.Contains(id))continue;
            var cat=MelonPreferences.GetCategory(id);
            if(cat==null)continue;
            try
            {
                Directory.CreateDirectory(dir);
                var file=Path.Combine(dir,id+".cfg");
                bool first=!File.Exists(file);
                cat.SetFilePath(file,!first,false);    // later runs: load the FA copy over the values read from the AA file
                if(first)cat.SaveToFile(false);        // first run: keep the player's current values
                done.Add(id);
                MelonLogger.Msg($"FREEDOM_ARROW_THIRD_PARTY_CFG {id} -> UserData/FreedomArrow/ThirdParty/{id}.cfg ({(first?"copied current values":"loaded")})");
            }
            catch(Exception e){MelonLogger.Error($"FREEDOM_ARROW_THIRD_PARTY_CFG {id} stays in its ActualArrow file: {e.Message}");}
        }
    }
}
