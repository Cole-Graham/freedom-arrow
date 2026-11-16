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
        // Unit card: RefundSystem.GetAmmoResupplyTime walks unit.Turrets -> Weapons -> Ammunitions / WeaponAmmunitions[ammo.Id] -> ChildTurrets
        // (AddTurretWeaponsAmmoTime). Log every null on that walk (16 Nov 2026: NullReferenceException there on the China tank cards).
        harmony.Patch(AccessTools.Method(typeof(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitInfoCard),"SetUnitStatistic"),prefix:new HarmonyMethod(typeof(TurretDiag),nameof(CardStats)));
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
    static void Walk(Il2CppSystem.Collections.Generic.List<Turrets> ts,string path,List<string> faults,int depth)
    {
        if(ts==null){faults.Add(path+": turret list null");return;}
        if(depth>4)return;
        for(int i=0;i<ts.Count;i++)
        {
            var t=ts[i];if(t==null){faults.Add($"{path}[{i}]: turret null");continue;}
            var p=$"{path}/{t.Id}";var w=t.Weapons;
            if(w==null){faults.Add(p+": Weapons null");continue;}
            for(int j=0;j<w.Count;j++)
            {
                var x=w[j];if(x==null){faults.Add($"{p}: Weapons[{j}] null (count {w.Count})");continue;}
                var a=x.Ammunitions;var d=x.WeaponAmmunitions;
                if(a==null)faults.Add($"{p}/w{x.Id}: Ammunitions null");
                if(d==null)faults.Add($"{p}/w{x.Id}: WeaponAmmunitions null");
                if(a!=null)for(int k=0;k<a.Count;k++){var m=a[k];if(m==null)faults.Add($"{p}/w{x.Id}: Ammunitions[{k}] null");else if(d!=null&&!d.ContainsKey(m.Id))faults.Add($"{p}/w{x.Id}: no WeaponAmmunitions key {m.Id}");}
            }
            Walk(t.ChildTurrets,p,faults,depth+1);
        }
    }
    static void CardStats(Units __0)
    {
        try
        {
            if(__0==null)return;var faults=new List<string>();Walk(__0.Turrets,"u"+__0.Id,faults,0);
            if(faults.Count==0&&!watch.Contains(__0.Id))return;
            lock(seen){if(!seen.Add("card:"+__0.Id+":"+faults.Count)||logs++>300)return;}
            DiagnosticLog.Write("turret_diag_card",new{unit=__0.Id,name=__0.HUDName,faults=faults.Take(40).ToArray()});
        }
        catch(Exception x){lock(seen){if(logs++<5)DiagnosticLog.Write("turret_diag_failed",new{where="card",error=x.ToString()});}}
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
