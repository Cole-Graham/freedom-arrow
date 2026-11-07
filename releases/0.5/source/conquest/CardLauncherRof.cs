using MelonLoader;
using UnityEngine;
using Il2CppTMPro;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.DataBase.Enums;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;

namespace FreedomArrow.Conquest;
// 0.5 dev.38 (Lateralus): infantry launcher cards show "Rate of fire" like rifles, not "Reload time".
// UnitInfoCard.OnWeaponButtonSelected (native) shows rate of fire for weapon type 60 (grenade launcher) or a magazine
// over 1; single-shot launchers (62, 63) get the reload line. While the card draws one of these, its type reads 60,
// and it is put back right after. The rate is WeaponHelper.RateOfFire x carriers; disposables get the squad formula
// (SquadReload.cs) and the rounding hook (CardRounding.cs) rounds to the nearest whole shot per minute. Display only.
// dev.40: the dev.39 card showed one launcher's rate (Shturmoviki 8, Mech. Riflemen MMG AT4 12) and the header
// "Grenade launcher". The launcher count now comes from the weapon button, and the header gets the real type name back.
public sealed partial class Prototype
{
    static readonly int[] cardLauncherTypes={62,63};
    [ThreadStatic] static Weapons cardWeapon;
    [ThreadStatic] static int cardRealType;
    [ThreadStatic] static int cardCount;
    static void InstallCardLauncherRof()
    {
        Patch(typeof(UnitInfoCard),"OnWeaponButtonSelected",nameof(CardLauncherBefore),nameof(CardLauncherAfter));
        MelonLogger.Msg("FREEDOM_ARROW_CARD_LAUNCHER_ROF installed: infantry launcher cards show rate of fire");
    }
    public static void CardLauncherBefore(GameObject __0)
    {
        RestoreCardType();
        var button=__0==null?null:__0.GetComponent<WeaponListButton>();
        var w=button?.Weapon;
        if(w==null||w.MagazineSize!=1||Array.IndexOf(cardLauncherTypes,(int)w.Type)<0)return;
        cardWeapon=w;cardRealType=(int)w.Type;cardCount=Math.Max(1,button.WeaponsCount);w.Type=(WeaponType)60;
    }
    public static void CardLauncherAfter(UnitInfoCard __instance)
    {
        int real=cardRealType;bool swapped=cardWeapon!=null;
        RestoreCardType();
        if(!swapped||__instance==null)return;
        try
        {
            string shown=InfoCardLocalization.ToLocalizedString((WeaponType)60),name=InfoCardLocalization.ToLocalizedString((WeaponType)real);
            foreach(var t in __instance.GetComponentsInChildren<TextMeshProUGUI>(true))if(t.text==shown)t.text=name;
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_CARD_LAUNCHER_ROF header: "+e.Message);}
    }
    static void RestoreCardType()
    {
        var w=cardWeapon;cardWeapon=null;cardCount=0;
        if(w!=null)w.Type=(WeaponType)cardRealType;
    }
    // Rate for the card's launcher: disposables the squad formula, reusable launchers one launcher's rate x launchers.
    static bool CardLauncherRate(float per,out float rate)
    {
        rate=0;
        if(cardWeapon==null||cardCount<1)return false;
        int n=cardCount;cardCount=0;
        if(cardRealType==rofType){rate=rofK*MathF.Pow(n,rofExp);return true;}
        if(per<=0)return false;
        rate=per*n;return true;
    }
    // The real type of a weapon, also while the card shows it as type 60.
    static int CardType(Weapons w)=>cardWeapon!=null&&w.Pointer==cardWeapon.Pointer?cardRealType:(int)w.Type;
}
