using System.Text.Json.Nodes;
namespace FreedomArrow;

public static class WeaponCoverage
{
    public static readonly string[] Tables={"WeaponAmmunitionsJson","TurretUnitsJson","ModificationsJson","OptionsJson","TurretWeaponsJson","SquadWeaponsJson"};
    public static void Validate(Dictionary<string,JsonArray> tables,Dictionary<string,JsonObject> patches)
    {
        HashSet<int> Changed(string table)=>patches.TryGetValue(table,out var p)?p.Where(x=>x.Value!=null&&x.Value.AsObject().ContainsKey("WeaponId")).Select(x=>int.Parse(x.Key)).ToHashSet():new();
        var touched=Changed("TurretWeaponsJson");var squad=Changed("SquadWeaponsJson");
        if(touched.Count+squad.Count==0)return;
        int I(JsonNode r,string k)=>r[k].GetValue<int>();
        var ammo=tables["WeaponAmmunitionsJson"].Select(r=>(I(r,"UnitId"),I(r,"WeaponId"))).ToHashSet();
        // 0.6 dev.61: a helicopter rack turret holds a launcher copy with no rounds, so the game draws the second pod but
        // never fires it. Only our own new weapons named '... rack (no rounds)' may have no ammunition row.
        var modelOnly=patches.TryGetValue("WeaponsJson",out var wp)?wp.Where(x=>x.Value!=null&&int.Parse(x.Key)>=2000000&&(x.Value["Name"]?.GetValue<string>()??"").EndsWith(" rack (no rounds)")).Select(x=>int.Parse(x.Key)).ToHashSet():new();
        var consumers=new Dictionary<int,HashSet<int>>();
        void Add(int turret,int unit){if(!consumers.TryGetValue(turret,out var units))consumers[turret]=units=new();units.Add(unit);}
        foreach(var r in tables["TurretUnitsJson"])Add(I(r,"TurretId"),I(r,"UnitId"));
        var mods=tables["ModificationsJson"].ToDictionary(r=>I(r,"Id"),r=>I(r,"UnitId"));
        foreach(var r in tables["OptionsJson"])
        {
            if(!mods.TryGetValue(I(r,"ModificationId"),out int unit))continue;
            foreach(var f in r.AsObject())
                if(f.Key.StartsWith("Turret")&&f.Key.EndsWith("Id")&&f.Value!=null&&f.Value.GetValue<int>()>0)Add(f.Value.GetValue<int>(),unit);
        }
        foreach(var r in tables["TurretWeaponsJson"])
            if(touched.Contains(I(r,"Id"))&&consumers.TryGetValue(I(r,"TurretId"),out var units))
                foreach(int unit in units)
                    if(!ammo.Contains((unit,I(r,"WeaponId")))&&!modelOnly.Contains(I(r,"WeaponId")))throw new InvalidDataException($"Weapon transfer lacks ammo: unit {unit}, weapon {I(r,"WeaponId")}, turret {I(r,"TurretId")}");
        foreach(var r in tables["SquadWeaponsJson"])
            if(squad.Contains(I(r,"Id"))&&!ammo.Contains((I(r,"UnitId"),I(r,"WeaponId"))))throw new InvalidDataException("Squad weapon transfer lacks ammo");
    }
}
