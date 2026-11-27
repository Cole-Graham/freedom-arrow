using System.Text.Json;
using MelonLoader;
using MelonLoader.Utils;
namespace FreedomArrow;
// Map sizes from data (Lateralus 23 Nov 2026: "its super important the game can clearly keep track of which version belongs to which game
// size (e.g. we could eventually have a size for every map, e.g. Dam 1v1, Dam 2v2, Dam 3v3, and Dam 4v4)"). Every FA map file has 5 slots
// per team and no size field, so the size comes from UserData/FreedomArrow/maps.json, which the build writes from maps/maps.json with each
// map's exact scenario name, GUID, size ("1v1", "2v2", "3v3", "4v4" or "PvE") and ranked pool. The "[NvN]" tag in a name is display text only.
// Lobby slots, the Create a lobby tabs, the oversized-team warning and the ranked host's map pick read this list. A map that is not in it
// (a vanilla or third-party map) has no size.
static class MapSizes
{
    public sealed class Entry{public string Name,Guid,Size,Base;public bool Ranked,Skirmish;}
    static Dictionary<string,Entry> byName;static bool loaded;
    static Dictionary<string,Entry> All()
    {
        if(loaded)return byName;loaded=true;byName=new(StringComparer.Ordinal);
        var path=Path.Combine(MelonEnvironment.UserDataDirectory,"FreedomArrow","maps.json");
        try
        {
            using var doc=JsonDocument.Parse(File.ReadAllText(path));
            foreach(var m in doc.RootElement.GetProperty("maps").EnumerateArray())
            {
                var e=new Entry{Name=m.GetProperty("name").GetString()??"",Guid=m.GetProperty("guid").GetString()??"",Size=m.GetProperty("size").GetString()??"",
                    Base=m.GetProperty("base").GetString()??"",Ranked=m.GetProperty("ranked").GetBoolean(),Skirmish=m.GetProperty("skirmish").GetBoolean()};
                byName[e.Name]=e;
            }
            MelonLogger.Msg($"FREEDOM_ARROW_MAP_SIZES: {byName.Count} maps from {path}");
        }
        catch(Exception x){MelonLogger.Error($"FREEDOM_ARROW_MAP_SIZES_FAILED: {path}: {x.Message}. FA maps have no size: lobby slots, size tabs, the size warning and ranked map checks are off.");}
        return byName;
    }
    // "1v1" / "2v2" / "3v3" / "4v4" / "PvE", or null for a map that is not in the list.
    public static string SizeOf(string scenario)=>scenario!=null&&All().TryGetValue(scenario,out var e)?e.Size:null;
    // Open slots per team in a new mod lobby, and the team size above which the oversized-team warning shows. [4v4] maps are played as
    // 4v4 or 5v5 (Lateralus 23 Nov 2026: "For mod lobbies the default number of slots open should be 10 for these maps").
    public static int PlayersPerTeam(string size)=>size switch{"1v1"=>1,"2v2"=>2,"3v3"=>3,"4v4"=>5,_=>-1};
    // Base names of the ranked maps of this size, in list order.
    public static IEnumerable<string> RankedBases(string size)=>All().Values.Where(e=>e.Ranked&&!e.Skirmish&&e.Size==size).Select(e=>e.Base);
    // True for a multiplayer map in the ranked pool (the RANKED tag in the Create a lobby map window, MapLabels.cs).
    public static bool IsRanked(string scenario)=>scenario!=null&&All().TryGetValue(scenario.Trim(),out var e)&&e.Ranked&&!e.Skirmish;
    // The installed ranked map of this size and base name (multiplayer version), or null.
    public static Entry Ranked(string size,string baseName)=>All().Values.FirstOrDefault(e=>!e.Skirmish&&e.Size==size&&e.Base.Equals(baseName,StringComparison.OrdinalIgnoreCase));
}
