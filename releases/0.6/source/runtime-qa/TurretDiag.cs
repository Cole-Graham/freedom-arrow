using HarmonyLib;
using Il2CppBrokenArrow.DataBase.Models;
using MelonLoader;
namespace FreedomArrow;
// Diagnostic (16 Nov 2026, dev.23 editor crash "NullReferenceException at Turrets.CloneWithClonedWeaponsAndTurrets" on the ZTZ-99A/99 LSDW
// loadout): before the game copies a loadout turret, log its weapon and child-turret lists when one is missing or holds a null, and always
// for the turrets in turret-diag.json. Logging only; it changes nothing.
static class TurretDiag
{
    static HashSet<int> watch=new();static readonly HashSet<string> seen=new();static int logs;
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var file=Path.Combine(root,"turret-diag.json");if(!File.Exists(file))return;
        watch=System.Text.Json.Nodes.JsonNode.Parse(File.ReadAllText(file))!["turrets"]!.AsArray().Select(x=>x!.GetValue<int>()).ToHashSet();
        harmony.Patch(AccessTools.Method(typeof(Turrets),"CloneWithClonedWeaponsAndTurrets"),prefix:new HarmonyMethod(typeof(TurretDiag),nameof(Before)));
        DiagnosticLog.Write("turret_diag_installed",new{watch=watch.ToArray()});MelonLogger.Msg("FREEDOM_ARROW_TURRET_DIAG installed");
    }
    static object Describe(Turrets t)
    {
        if(t==null)return null;
        var w=t.Weapons;var c=t.ChildTurrets;
        var ws=new List<object>();if(w!=null)for(int i=0;i<w.Count;i++){var x=w[i];ws.Add(x==null?null:new{x.Id,x.HUDName});}
        var cs=new List<int?>();if(c!=null)for(int i=0;i<c.Count;i++)cs.Add(c[i]?.Id);
        return new{t.Id,t.Name,t.IsDefault,order=t.Order,weaponsNull=w==null,weapons=ws,childrenNull=c==null,children=cs};
    }
    static void Before(Turrets __instance)
    {
        try
        {
            var t=__instance;if(t==null)return;var w=t.Weapons;var c=t.ChildTurrets;
            bool bad=w==null||c==null;
            if(w!=null)for(int i=0;i<w.Count;i++)if(w[i]==null)bad=true;
            var kids=new List<object>();
            if(c!=null)for(int i=0;i<c.Count;i++){var k=c[i];if(k==null||k.Weapons==null||k.ChildTurrets==null)bad=true;kids.Add(Describe(k));}
            if(!bad&&!watch.Contains(t.Id))return;
            string key=t.Id+":"+bad+":"+(w?.Count??-1)+":"+(c?.Count??-1);
            lock(seen){if(!seen.Add(key)||logs++>300)return;}
            DiagnosticLog.Write("turret_diag_clone",new{bad,turret=Describe(t),childDetail=kids});
        }
        catch(Exception x){lock(seen){if(logs++<5)DiagnosticLog.Write("turret_diag_failed",new{error=x.ToString()});}}
    }
}
