using System.Reflection;
using MelonLoader;
namespace FreedomArrow;
// 0.6 dev.1 (Osama, 7 November 2026): FlatIncomeMod (Speer) ships with Freedom Arrow, but its forest cover stays off.
// Its ForestCover.Post cuts infantry damage in woods by 30%, the same rule as our CoverDamage, so both would cut it twice.
// Post returns at once while its private _broken flag is set (FlatIncomeMod sets it only after an error).
static class ThirdPartyGuard
{
    static bool done;
    public static void Ensure()
    {
        if(done)return;
        var asm=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="FlatIncomeMod");
        if(asm==null)return;
        done=true;
        var field=asm.GetType("FlatIncomeMod.ForestCover")?.GetField("_broken",BindingFlags.Static|BindingFlags.NonPublic);
        if(field==null){MelonLogger.Error("FREEDOM_ARROW_THIRD_PARTY: FlatIncomeMod forest cover not found; it may double the forest cut");return;}
        field.SetValue(null,true);
        MelonLogger.Msg($"FREEDOM_ARROW_THIRD_PARTY: FlatIncomeMod forest cover off (FA forest rule only): {field.GetValue(null)}");
    }
}
