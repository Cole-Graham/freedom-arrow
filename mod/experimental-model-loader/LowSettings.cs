using HarmonyLib;
using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.GameSettings.Enums;
using Il2CppBrokenArrow.Client.Ecs.GameSettings.Services;
namespace FAModels;

// 0.3.28 (Osama 14 Nov 2026 23:3x PST: "FAModels can load battle models for low and potato settings"). The game's Models quality
// setting (SettingType.ModelsQuality, SettingQuality Potato = 1, Low = 2) is read through SettingsService.GetSettingValue; the
// last applied value is kept here. On Potato or Low the armory also uses an entry's battle model (smaller mesh and textures).
public partial class Mod
{
    static int modelsQuality = -1;
    static bool LowModels => modelsQuality == (int)SettingQuality.Potato || modelsQuality == (int)SettingQuality.Low;

    void InstallLowSettings()
    {
        var get = AccessTools.Method(typeof(SettingsService), nameof(SettingsService.GetSettingValue)) ?? throw new InvalidOperationException("SettingsService.GetSettingValue not found");
        HarmonyInstance.Patch(get, postfix: new HarmonyMethod(typeof(Mod), nameof(AfterSetting)));
    }

    public static void AfterSetting(SettingType type, bool newSettings, int __result)
    {
        if (type != SettingType.ModelsQuality || newSettings || __result == modelsQuality) return;
        modelsQuality = __result;
        MelonLogger.Msg($"FAMODELS models quality {(SettingQuality)__result}: armory uses {(LowModels ? "battle models" : "full models")}");
    }
}
