using MelonLoader;
using UnityEngine;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.DataBase.Enums;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;

namespace FreedomArrow.Conquest;
// 0.5 dev.38 (Lateralus): infantry launcher cards show "Rate of fire" like rifles, not "Reload time".
// UnitInfoCard.OnWeaponButtonSelected (native) shows rate of fire for weapon type 60 (grenade launcher) or a magazine
// over 1; single-shot launchers (62, 63) get the reload line. While the card draws one of these, its type reads 60,
// and it is put back right after. The rate is WeaponHelper.RateOfFire x carriers; disposables get the squad formula
// (SquadReload.cs) and the rounding hook (CardRounding.cs) rounds to the nearest whole shot per minute. Display only.
public sealed partial class Prototype
{
    static readonly int[] cardLauncherTypes={62,63};
    [ThreadStatic] static Weapons cardWeapon;
    [ThreadStatic] static int cardRealType;
    static void InstallCardLauncherRof()
    {
        Patch(typeof(UnitInfoCard),"OnWeaponButtonSelected",nameof(CardLauncherBefore),nameof(CardLauncherAfter));
        MelonLogger.Msg("FREEDOM_ARROW_CARD_LAUNCHER_ROF installed: infantry launcher cards show rate of fire");
    }
    public static void CardLauncherBefore(GameObject __0)
    {
        CardLauncherAfter();
        var w=__0==null?null:__0.GetComponent<WeaponListButton>()?.Weapon;
        if(w==null||w.MagazineSize!=1||Array.IndexOf(cardLauncherTypes,(int)w.Type)<0)return;
        cardWeapon=w;cardRealType=(int)w.Type;w.Type=(WeaponType)60;
    }
    public static void CardLauncherAfter()
    {
        var w=cardWeapon;cardWeapon=null;
        if(w!=null)w.Type=(WeaponType)cardRealType;
    }
    // The real type of a weapon, also while the card shows it as type 60.
    static int CardType(Weapons w)=>cardWeapon!=null&&w.Pointer==cardWeapon.Pointer?cardRealType:(int)w.Type;
}
