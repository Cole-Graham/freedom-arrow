using MelonLoader;

namespace FreedomArrow.Conquest;
// 0.6 dev.3 (Osama, 7 November 2026): log the menus too, not only battles. The events-<utc>.jsonl file and Latest.log
// get the list of loaded mods with versions once the game has started, and a line for every scene the game loads.
public sealed partial class Prototype
{
    public void OnLateInitializeMelon()
    {
        try
        {
            var mods=MelonBase.RegisteredMelons.Select(m=>new{name=m.Info.Name,version=m.Info.Version,author=m.Info.Author}).ToArray();
            Log("mods_loaded",new{mods,conquest=status});
            MelonLogger.Msg("FREEDOM_ARROW_MENU mods: "+string.Join(", ",mods.Select(m=>$"{m.name} {m.version}"))+" | conquest: "+status);
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_MENU mods: "+e.Message);}
    }
    public void OnSceneWasLoaded(int buildIndex,string sceneName)
    {
        Log("scene_loaded",new{buildIndex,sceneName});
        MelonLogger.Msg($"FREEDOM_ARROW_MENU scene {buildIndex} '{sceneName}'");
    }
}
