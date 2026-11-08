using System.Collections.Concurrent;
using MelonLoader;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.DataBase.Models;

namespace FreedomArrow.Conquest;
// 0.6 dev.54 (Osama): only guided bombs hit the roof. dev.49 set OverpressureRadius 0 on unguided bombs,
// but the game can still pick the roof from a steep impact vector (GetArmorSideFromShotVector, over 30 degrees)
// or a runtime ForceTopAttack. CalculateHitDamage(target, damage, ammo, penetration, forceTop, side) is where
// both arrive. For an unguided HE bomb (name "Bomb", OverpressureRadius 0, no top-attack flag) a roof hit uses
// rear armor instead. Cluster and napalm bombs keep their top-attack flag; guided bombs keep overpressure.
// Every bomb and MLRS hit is written to the shot log as "bomb_roof".
public sealed partial class Prototype
{
    const int MaxRoofLog=300,MaxRoofMsg=20;
    static bool roofOff;
    static int roofLogged,roofMoved;
    static readonly ConcurrentDictionary<int,bool> unguidedBomb=new();
    static void InstallBombRoof()
    {
        Patch(typeof(BattleSystemHelpers),"CalculateHitDamage",nameof(BombRoofBefore),null);
        MelonLogger.Msg("FREEDOM_ARROW_BOMB_ROOF installed: unguided bombs use rear armor instead of roof");
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
            bool moved=unguided&&(forceTop||side==ArmorSides.Top);
            if(moved){__4=false;__5=ArmorSides.Back;}
            if(moved&&Interlocked.Increment(ref roofMoved)<=MaxRoofMsg)MelonLogger.Msg($"FREEDOM_ARROW_BOMB_ROOF {name}: forceTop {forceTop} side {side} -> Back");
            if(Interlocked.Increment(ref roofLogged)<=MaxRoofLog)
                ShotLine("bomb_roof",new{ammo=name,ammoId=ammo.Id,realHit,overpressureRadius=ammo.OverpressureRadius,topArmorAttack=ammo.TopArmorAttack,unguided,forceTop,side=side.ToString(),usedSide=__5.ToString(),movedToBack=moved,baseDamage=Math.Round(__1,3),penetration=__3,target=UnitInfo(__0)});
        }
        catch(Exception e)
        {
            roofOff=true;
            MelonLogger.Error("FREEDOM_ARROW_BOMB_ROOF_FAILED: off for this session. "+e.Message);
        }
    }
}
