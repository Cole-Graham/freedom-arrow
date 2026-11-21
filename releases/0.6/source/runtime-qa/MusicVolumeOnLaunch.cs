using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.GameSettings.Enums;
using Il2CppBrokenArrow.Client.Ecs.GameSettings.Services;
using MelonLoader;
namespace FreedomArrow;

// 0.9.4-dev.1 (Osama 21 Nov 2026 13:1x PST, thread 1572407822849810463: "when people launch our game, we must turn music to the default 70%, people will
// be forced to listen to our music"). Every game start sets the game's Music slider to 70 (vanilla's default; the saved scale is 0-100). A player can
// still move it during the session; the next launch sets it back. Only VolumeMusic is touched.
// Path: SettingsService.Initialize (loads the saved settings) -> ChangeSettings(VolumeMusic, 70, applyInstantly: true), the game's own call. With
// applyInstantly it writes _newSettings and _settings, then ApplySettingInstantly applies the FMOD Volume_Music value and saves the settings
// (SetSettingsToPlayerPrefs), read in GameAssembly 1.2.2.1 at 0x428C60 / 0x427850.
static class MusicVolumeOnLaunch
{
    const int Music=70;
    static bool done;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        harmony.Patch(AccessTools.Method(typeof(SettingsService),"Initialize")??throw new MissingMethodException("SettingsService.Initialize"),
            postfix:new HarmonyMethod(typeof(MusicVolumeOnLaunch),nameof(AfterInitialize)));
        MelonLogger.Msg($"FREEDOM_ARROW_MUSIC_ON_LAUNCH installed: the game's Music slider is set to {Music} at every start");
    }
    static void AfterInitialize(SettingsService __instance)
    {
        if(done)return;
        done=true;
        try
        {
            int before=__instance.GetSettingValue(SettingType.VolumeMusic,false);
            if(before!=Music)__instance.ChangeSettings(SettingType.VolumeMusic,Music,true);
            MelonLogger.Msg($"FREEDOM_ARROW_MUSIC_ON_LAUNCH music slider {before} -> {__instance.GetSettingValue(SettingType.VolumeMusic,false)}");
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_MUSIC_ON_LAUNCH_FAILED: the slider keeps the player's value. "+e.Message);}
    }
}
