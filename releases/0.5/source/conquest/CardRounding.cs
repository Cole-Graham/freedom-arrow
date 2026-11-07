using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.Utils;

namespace FreedomArrow.Conquest;
// 0.5 dev.18: the detailed unit card rounds rate of fire to the nearest 5 (UnitInfoCard.OnWeaponButtonSelected
// calls UtilsClass.RoundToNearestMultiple(value, 5)). Every other caller uses 0.05. Under 100 rounds per minute
// a step of 5 hides real values (12.5 shows as 10), so values under 100 round to 1 instead. Display only.
public sealed partial class Prototype
{
    static void InstallCardRounding()
    {
        Patch(typeof(UtilsClass),"RoundToNearestMultiple",nameof(CardRoundingBefore),null);
        MelonLogger.Msg("FREEDOM_ARROW_CARD_ROF installed: card rate of fire under 100 rounds to 1 (was 5)");
    }
    public static bool CardRoundingBefore(float __0,float __1,ref float __result)
    {
        if(__1!=5f||__0>=100f)return true;
        __result=MathF.Round(__0,MidpointRounding.ToEven);
        return false;
    }
}
