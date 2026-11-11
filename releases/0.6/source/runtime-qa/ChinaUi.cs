using HarmonyLib;
using System.Text.Json;
using MelonLoader.Utils;
using Il2CppBrokenArrow.Client.Ecs.Decks_v2.UI;
using Il2CppBrokenArrow.Client.Ecs.UI;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.ArmyBuilder;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using MelonLoader;
using UnityEngine;

namespace FreedomArrow;

// PLA only. Let the game create its real buttons and callbacks; change capacity, ordering and sprites.
static class ChinaUi
{
    static readonly string[] Addresses=new[]{"FA_CHINA_FLAG","FA_CHINA_AIR_SF","FA_CHINA_ARMORED","FA_CHINA_ROCKET","FA_CHINA_NAVAL","FA_CHINA_MOTORIZED"}
        .Concat(typeof(ChinaUi).Assembly.GetManifestResourceNames()
            .Where(n=>n.StartsWith("FreedomArrow.icons.FA_PLA_")&&n.EndsWith(".png"))
            .Select(n=>n.Substring("FreedomArrow.icons.".Length,n.Length-"FreedomArrow.icons.".Length-4)))
        .Distinct().ToArray();
    static readonly Dictionary<string,byte[]> png=new();
    static readonly Dictionary<string,Sprite> made=new();
    static bool failed,plaOnly;
    static bool Ready=>!failed&&Runtime.IsApplied;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        var config=Path.Combine(MelonEnvironment.UserDataDirectory,"FreedomArrow","pla-specializations.json");
        if(File.Exists(config))plaOnly=JsonDocument.Parse(File.ReadAllText(config)).RootElement.GetProperty("pla_only").GetBoolean();
        foreach(var address in Addresses)
        {
            using var s=typeof(ChinaUi).Assembly.GetManifestResourceStream("FreedomArrow.icons."+address+".png")??throw new InvalidDataException("Missing China UI sprite "+address);
            using var m=new MemoryStream();s.CopyTo(m);png[address]=m.ToArray();
        }
        var seed=new HarmonyMethod(typeof(ChinaUi),nameof(Seed));
        harmony.Patch(AccessTools.Method(typeof(IconsLoader),nameof(IconsLoader.LoadSprite)),prefix:seed);
        harmony.Patch(AccessTools.Method(typeof(IconsLoader),nameof(IconsLoader.LoadSpriteAsync)),prefix:seed);
        harmony.Patch(AccessTools.Method(typeof(IconsLoader),nameof(IconsLoader.LoadSpecIcon)),prefix:seed);
        harmony.Patch(AccessTools.Method(typeof(HangarUnitFilter),"Initialize"),prefix:new HarmonyMethod(typeof(ChinaUi),nameof(Capacity)),postfix:new HarmonyMethod(typeof(ChinaUi),nameof(FilterReady)));
        harmony.Patch(AccessTools.Method(typeof(CountryFilterButtonsGroup),"Initialize"),postfix:new HarmonyMethod(typeof(ChinaUi),nameof(CountryRow)));
        harmony.Patch(AccessTools.Method(typeof(DeckCreationPopup),"RenderCountries"),postfix:new HarmonyMethod(typeof(ChinaUi),nameof(DeckCountries)));
        MelonLogger.Msg("PLA_CHINA_UI hooks installed; native layout/click validation pending");
    }
    public static void Seed()
    {
        if(!Ready)return;
        try
        {
            var cache=IconsLoader._sprites;if(cache==null)return;
            foreach(var address in Addresses)
            {
                if(!made.TryGetValue(address,out var sprite)||sprite==null)
                {
                    var t=new Texture2D(2,2,TextureFormat.RGBA32,false){name=address,wrapMode=TextureWrapMode.Clamp,hideFlags=HideFlags.HideAndDontSave};
                    if(!ImageConversion.LoadImage(t,(Il2CppStructArray<byte>)png[address],true))throw new InvalidDataException(address);
                    sprite=Sprite.Create(t,new Rect(0,0,t.width,t.height),new Vector2(.5f,.5f),100);sprite.name=address;sprite.hideFlags=HideFlags.HideAndDontSave;made[address]=sprite;
                }
                // Native flag and specialization callers use both plain and prefixed cache addresses.
                foreach(var prefix in new[]{"","outline\\","small\\"})cache[prefix+address]=sprite;
            }
        }
        catch(Exception e){failed=true;MelonLogger.Error("PLA_CHINA_UI_FAILED: "+e);}
    }
    public static void Capacity(HangarUnitFilter __instance)
    {
        if(Ready)__instance._maxCountryGroupsCount=Math.Max(3,__instance._maxCountryGroupsCount);
    }
    public static void FilterReady(HangarUnitFilter __instance)
    {
        if(Ready)MelonLogger.Msg($"PLA_CHINA_UI_FILTER_READY initialized={__instance._isInitialized} countryGroups={__instance._countryFilterButtonsGroups?.Count} flags={__instance._filterFlagsMapping?.Count} buttons={__instance._flagToButtonMapping?.Count} reset={__instance._unitFilterResetFlag}");
    }
    public static void CountryRow(CountryFilterButtonsGroup __instance,Countries country)
    {
        if(!Ready)return;
        if(country.Id!=4)return;
        __instance.transform.SetAsFirstSibling();
        MelonLogger.Msg("PLA_CHINA_UI Arsenal China row initialized above other countries; next filter bit="+__instance.NextBitIndex);
    }
    public static void DeckCountries(DeckCreationPopup __instance)
    {
        if(!Ready)return;
        var countries=__instance._countries;var buttons=__instance._countryButtons;
        if(countries==null||buttons==null)return;
        int china=-1;
        for(int i=0;i<countries.Length&&i<buttons.Length;i++)
        {
            buttons[i].gameObject.SetActive(true);
            if(countries[i].Id==4){china=i;buttons[i].transform.SetAsFirstSibling();}
        }
        if(plaOnly&&china>=0&&__instance._selectedCountryIdx!=china)__instance.OnCountrySelected(buttons[china].gameObject);
        MelonLogger.Msg($"PLA_CHINA_UI deck countries rendered; PLA-units-only={plaOnly}; China index={china}; native callbacks retained");
    }
}
