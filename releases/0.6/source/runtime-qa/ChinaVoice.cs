using HarmonyLib;
using Il2CppBrokenArrow.AudioSystem.AudioCommand;
using Il2CppBrokenArrow.Client.Ecs.Audio;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;

// 0.9.0-dev.10 (Osama 14 Nov 2026 23:3x PST: "for dev 10 also, remove all the voice lines for China"). China units (CountryId 4)
// borrow Russian and US sound presets, so they spoke Russian or C&C lines. AudioCommandSystem.PlayCommand(Entity) plays one
// unit's line through AudioCommandsCollection.GetEventByCommand, and plays nothing when that returns "". While PlayCommand runs
// for a China unit, GetEventByCommand returns "". Runs before FAMusic's postfix, so no custom clip plays either.
// PlayCommand itself still runs, so the game's own command bookkeeping is unchanged.
internal static class ChinaVoice
{
    const int China=4;
    [ThreadStatic] static bool chinaSpeaking;
    static bool broken;static int muted;

    public static void Install(HarmonyLib.Harmony harmony)
    {
        var play=AccessTools.Method(typeof(AudioCommandSystem),"PlayCommand")??throw new InvalidOperationException("AudioCommandSystem.PlayCommand not found");
        var pick=AccessTools.Method(typeof(AudioCommandsCollection),nameof(AudioCommandsCollection.GetEventByCommand))??throw new InvalidOperationException("GetEventByCommand not found");
        harmony.Patch(play,prefix:new HarmonyMethod(typeof(ChinaVoice),nameof(PlayBefore)),finalizer:new HarmonyMethod(typeof(ChinaVoice),nameof(PlayDone)));
        harmony.Patch(pick,postfix:new HarmonyMethod(typeof(ChinaVoice),nameof(PickAfter)){priority=Priority.First});
        MelonLogger.Msg("FREEDOM_ARROW_CHINA_VOICE installed: China units play no command voice lines");
    }

    public static void PlayBefore(in Entity __0)
    {
        chinaSpeaking=false;
        if(broken||!Runtime.IsApplied)return;
        try
        {
            var unit=__0;
            if(!unit.IsAlive||!unit.Has<UnitComponent>())return;
            chinaSpeaking=NativeEcs.Read<UnitComponent>(unit).UnitData?.CountryId==China;
        }
        catch(Exception e){broken=true;MelonLogger.Warning("FREEDOM_ARROW_CHINA_VOICE disabled, China units use their preset voices: "+e.Message);}
    }

    public static Exception PlayDone(Exception __exception){chinaSpeaking=false;return __exception;}

    public static void PickAfter(ref string __result)
    {
        if(!chinaSpeaking||string.IsNullOrEmpty(__result))return;
        if(muted++==0)MelonLogger.Msg("FREEDOM_ARROW_CHINA_VOICE first China line muted: "+__result);
        __result="";
    }
}
