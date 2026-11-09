using MelonLoader;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.DataBase.Models;

namespace FreedomArrow.Conquest;
// Lateralus batch, 8 November 2026: napalm and incendiary fire burns REAR armour. Fire ticks reach
// BattleSystemHelpers.CalculateHitDamage(target, damage, ammo, penetration, forceTop, side) through
// ShellHitSystem.DealUnitDamage; without TopArmorAttack (cleared in napalm-contract.json) the side would come
// from the tick's impact vector, so the prefix clears forceTop and sets Back for these rounds only.
// Ids must match napalm-contract.json rear_ammo: Mk77 (300), ZB-500 (322), Grad incendiary (432), MRO-Z (522), M202 (550).
public sealed partial class Prototype
{
    static readonly HashSet<int> fireRearAmmo=new(){300,322,432,522,550};
    static bool fireRearOff;
    static int fireRearLogged;
    static void InstallFireRear()
    {
        Patch(typeof(BattleSystemHelpers),"CalculateHitDamage",nameof(FireRearBefore),null);
        MelonLogger.Msg("FREEDOM_ARROW_FIRE_REAR installed: napalm and incendiary fire hits rear armour");
    }
    public static void FireRearBefore(Entity __0,float __1,Ammunitions __2,float __3,ref bool __4,ref ArmorSides __5)
    {
        if(fireRearOff||__2==null)return;
        try
        {
            if(!fireRearAmmo.Contains(__2.Id))return;
            if(fireRearLogged<10&&++fireRearLogged>0)MelonLogger.Msg($"FREEDOM_ARROW_FIRE_REAR {__2.Name}: side {__5}{(__4?" (forced top)":"")} -> Back");
            __4=false;__5=ArmorSides.Back;
        }
        catch(Exception e)
        {
            fireRearOff=true;
            MelonLogger.Error("FREEDOM_ARROW_FIRE_REAR_FAILED: off for this session; fire uses the game's side. "+e.Message);
        }
    }
}
