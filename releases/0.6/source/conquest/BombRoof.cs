using System.Collections.Concurrent;
using MelonLoader;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.DataBase.Models;

namespace FreedomArrow.Conquest;
// 0.6 dev.54/57 (Osama): an unguided bomb that lands next to a tank must not hit the roof; one that lands on
// the tank may. dev.49 set OverpressureRadius 0 on unguided bombs. CalculateHitDamage(target, damage, ammo,
// penetration, forceTop, side) receives two roof routes: forceTop (overpressure or a runtime ForceTopAttack,
// independent of where the bomb landed) and side Top, which GetArmorSideFromShotVector picks only when the
// impact vector is steeper than 30 degrees, i.e. the bomb came down on the tank. dev.57: for an unguided HE bomb
// (name "Bomb", OverpressureRadius 0, no top-attack flag) forceTop is cleared and the geometric side is kept;
// dev.54 had also moved geometric Top hits to rear armor. Guided, cluster and napalm bombs are unchanged.
// Every bomb and MLRS hit is written to the shot log as "bomb_roof", with the impact vector.
public sealed partial class Prototype
{
    const int MaxRoofLog=300,MaxRoofMsg=20;
    static bool roofOff;
    static int roofLogged,roofMoved;
    static readonly ConcurrentDictionary<int,bool> unguidedBomb=new();
    [ThreadStatic] static UnityEngine.Vector3 roofVector;
    [ThreadStatic] static bool roofVectorSet;
    static void InstallBombRoof()
    {
        Patch(typeof(BattleSystemHelpers),"GetArmorSideFromShotVector",nameof(BombRoofVector),null);
        Patch(typeof(BattleSystemHelpers),"CalculateHitDamage",nameof(BombRoofBefore),null);
        MelonLogger.Msg("FREEDOM_ARROW_BOMB_ROOF installed: unguided bombs lose forced roof hits; landing on the tank keeps the roof");
    }
    public static void BombRoofVector(UnityEngine.Vector3 __2) { roofVector=__2; roofVectorSet=true; }
    static object VectorInfo(UnityEngine.Vector3 v)
    {
        float h=MathF.Sqrt(v.x*v.x+v.z*v.z);
        return new{x=Math.Round(v.x,2),y=Math.Round(v.y,2),z=Math.Round(v.z,2),degreesFromHorizontal=Math.Round(MathF.Atan2(MathF.Abs(v.y),h)*180/MathF.PI,1)};
    }
    public static void BombRoofBefore(Entity __0,float __1,Ammunitions __2,float __3,ref bool __4,ref ArmorSides __5)
    {
        if(roofOff||__2==null)return;
        try
        {
            string name=__2.Name??"";
            if(!name.StartsWith("Bomb")&&!name.StartsWith("MLRS"))return;
            var ammo=__2;
            bool unguided=unguidedBomb.GetOrAdd(ammo.Id,_=>name.StartsWith("Bomb")&&ammo.OverpressureRadius<=0&&!ammo.TopArmorAttack&&!ammo.IsTopArmorArmorAttack);
            bool forceTop=__4;var side=__5;
            bool vectorSet=roofVectorSet;var vector=roofVector;roofVectorSet=false;
            bool moved=unguided&&forceTop;
            if(moved)__4=false;
            if(moved&&Interlocked.Increment(ref roofMoved)<=MaxRoofMsg)MelonLogger.Msg($"FREEDOM_ARROW_BOMB_ROOF {name}: forced roof removed, side {side} kept");
            if(Interlocked.Increment(ref roofLogged)<=MaxRoofLog)
                ShotLine("bomb_roof",new{ammo=name,ammoId=ammo.Id,realHit,overpressureRadius=ammo.OverpressureRadius,topArmorAttack=ammo.TopArmorAttack,unguided,forceTop,side=side.ToString(),roofUsed=__4||__5==ArmorSides.Top,forcedRoofRemoved=moved,impactVector=vectorSet?VectorInfo(vector):null,baseDamage=Math.Round(__1,3),penetration=__3,target=UnitInfo(__0)});
        }
        catch(Exception e)
        {
            roofOff=true;
            MelonLogger.Error("FREEDOM_ARROW_BOMB_ROOF_FAILED: off for this session. "+e.Message);
        }
    }
}
