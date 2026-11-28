using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.GameSettings.Enums;
using Il2CppBrokenArrow.Client.Ecs.GameSettings.Services;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// 0.9.4-dev.1 (Osama 21 Nov 2026 13:1x PST, thread 1572407822849810463: "when people launch our game, we must turn music to the default 70%, people will
// be forced to listen to our music") set the game's Music slider to 70 at every start. Lateralus 24 Nov 2026 09:1x PST, thread 1568104480459722894:
// "It should not be setting it to 70% every time, only the first time someone loads the mod (for new player experience)". So it now runs once per
// game install: the first start with the mod sets 70 (vanilla's default; the saved scale is 0-100) and stores a marker in the game's PlayerPrefs, where
// the game also saves this slider. Later starts keep the player's value. Only VolumeMusic is touched.
// Path: SettingsService.Initialize (loads the saved settings) -> ChangeSettings(VolumeMusic, 70, applyInstantly: true), the game's own call. With
// applyInstantly it writes _newSettings and _settings, then ApplySettingInstantly applies the FMOD Volume_Music value and saves the settings
// (SetSettingsToPlayerPrefs), read in GameAssembly 1.2.2.1 at 0x428C60 / 0x427850.
static class MusicVolumeOnLaunch
{
    const int Music=70;
    const string Marker="FreedomArrow.MusicDefaultApplied";
    const int Night=60;   // HangarEnvironmentType.Night
    const string NightMarker="FreedomArrow.HangarNightDefaultApplied";
    static bool done;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        harmony.Patch(AccessTools.Method(typeof(SettingsService),"Initialize")??throw new MissingMethodException("SettingsService.Initialize"),
            postfix:new HarmonyMethod(typeof(MusicVolumeOnLaunch),nameof(AfterInitialize)));
        MelonLogger.Msg($"FREEDOM_ARROW_MUSIC_ON_LAUNCH installed: the game's Music slider is set to {Music} on the first start with the mod only");
    }
    static void AfterInitialize(SettingsService __instance)
    {
        if(done)return;
        done=true;
        HangarNight(__instance);
        try
        {
            if(PlayerPrefs.GetInt(Marker,0)==1){MelonLogger.Msg("FREEDOM_ARROW_MUSIC_ON_LAUNCH not first start: music slider kept at "+__instance.GetSettingValue(SettingType.VolumeMusic,false));return;}
            int before=__instance.GetSettingValue(SettingType.VolumeMusic,false);
            if(before!=Music)__instance.ChangeSettings(SettingType.VolumeMusic,Music,true);
            PlayerPrefs.SetInt(Marker,1);PlayerPrefs.Save();
            MelonLogger.Msg($"FREEDOM_ARROW_MUSIC_ON_LAUNCH first start: music slider {before} -> {__instance.GetSettingValue(SettingType.VolumeMusic,false)}");
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_MUSIC_ON_LAUNCH_FAILED: the slider keeps the player's value. "+e.Message);}
    }
    static void HangarNight(SettingsService __instance)
    {
        // Hangar time of day (Osama 27 Nov 2026 17:1x PST, thread 1567745029781454889: "make the default hanger night on first install"): game setting
        // HangarEnvironment (SettingType 46; the Arsenal's time button saves HangarEnvironmentType there, Night = 60, read from Osama's saved settings).
        // Set once per install with its own marker, the same call as the music slider; later choices stay.
        try
        {
            if(PlayerPrefs.GetInt(NightMarker,0)==1)return;
            int before=__instance.GetSettingValue(SettingType.HangarEnvironment,false);
            if(before!=Night)__instance.ChangeSettings(SettingType.HangarEnvironment,Night,true);
            PlayerPrefs.SetInt(NightMarker,1);PlayerPrefs.Save();
            MelonLogger.Msg($"FREEDOM_ARROW_HANGAR_NIGHT first start: hangar time {before} -> {__instance.GetSettingValue(SettingType.HangarEnvironment,false)}");
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_HANGAR_NIGHT_FAILED: the hangar keeps the game's time. "+e.Message);}
    }
}
