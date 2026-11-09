using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Card icons (Lateralus batch, 8 November 2026). BARS Kornet (unit 721) carries a KPVT, so its card icon shows the KPV
// gun body and barrel where the vanilla icon has the SPG-9 tube. IconsLoader.LoadSprite and LoadSpriteAsync look up
// IconsLoader._sprites by address ("outline\" + address for the outline copy) before they load from the asset
// bundles, so FA puts its own sprites under the vanilla addresses. Only unit 721 uses DLC3_BARS_KORNET-Label in FA
// (BARS FS shows the SPG-9 icon since dev.48). Scouts Stryker (277) and Razvedka Mech (123) use FA-only addresses
// (scouts-contract.json "thumbnails"), so the 3-man Scouts and Razvedka copies keep the vanilla icons; ValidatePath
// treats an unknown address as Vanilla content. The PNGs are embedded in this DLL; icons/*.png in runtime-qa.
static class CardIcons
{
    static readonly (string address,string resource)[] Icons=
    {
        ("DLC3_BARS_KORNET-Label","DLC3_BARS_KORNET-Label.png"),
        ("outline\\DLC3_BARS_KORNET-Label","outline_DLC3_BARS_KORNET-Label.png"),
        ("FA_US_SCOUTS_STRYKER-Label","FA_US_SCOUTS_STRYKER-Label.png"),
        ("outline\\FA_US_SCOUTS_STRYKER-Label","outline_FA_US_SCOUTS_STRYKER-Label.png"),
        ("FA_RU_RAZVEDKA_MECH-Label","FA_RU_RAZVEDKA_MECH-Label.png"),
        ("outline\\FA_RU_RAZVEDKA_MECH-Label","outline_FA_RU_RAZVEDKA_MECH-Label.png"),
    };
    static readonly Dictionary<string,byte[]> png=new();
    static readonly Dictionary<string,Sprite> made=new();
    static bool broken,logged;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        var asm=typeof(CardIcons).Assembly;
        foreach(var (address,resource) in Icons)
        {
            using var s=asm.GetManifestResourceStream("FreedomArrow.icons."+resource)??throw new InvalidOperationException("missing embedded icon "+resource);
            using var m=new MemoryStream();s.CopyTo(m);png[address]=m.ToArray();
        }
        var seed=new HarmonyMethod(typeof(CardIcons),nameof(Seed));
        harmony.Patch(AccessTools.Method(typeof(IconsLoader),nameof(IconsLoader.LoadSprite)),prefix:seed);
        harmony.Patch(AccessTools.Method(typeof(IconsLoader),nameof(IconsLoader.LoadSpriteAsync)),prefix:seed);
        MelonLogger.Msg($"FREEDOM_ARROW_CARD_ICONS installed: {Icons.Length} icons (BARS Kornet with KPV, Scouts Stryker, Razvedka Mech)");
    }
    public static void Seed()
    {
        if(broken||!Runtime.IsApplied)return;
        try
        {
            var cache=IconsLoader._sprites;
            if(cache==null)return;
            foreach(var (address,_) in Icons)
            {
                // IconsLoader.Dispose can destroy cached sprites; make a new one when ours is gone.
                if(!made.TryGetValue(address,out var sprite)||sprite==null)made[address]=sprite=Make(address);
                if(cache.TryGetValue(address,out var have)&&have!=null&&have.Pointer==sprite.Pointer)continue;
                cache[address]=sprite;
            }
            if(!logged){logged=true;MelonLogger.Msg("FREEDOM_ARROW_CARD_ICONS cached: BARS Kornet, Scouts Stryker, Razvedka Mech");}
        }
        catch(Exception x)
        {
            broken=true;
            MelonLogger.Error("FREEDOM_ARROW_CARD_ICONS_FAILED: off for this session; vanilla card icons (Scouts Stryker and Razvedka Mech may show none). "+x.Message);
        }
    }
    static Sprite Make(string address)
    {
        var tex=new Texture2D(2,2,TextureFormat.RGBA32,false){name=address,wrapMode=TextureWrapMode.Clamp};
        if(!ImageConversion.LoadImage(tex,(Il2CppStructArray<byte>)png[address],true))throw new InvalidOperationException("icon did not decode: "+address);
        tex.hideFlags=HideFlags.HideAndDontSave;
        var sprite=Sprite.Create(tex,new Rect(0,0,tex.width,tex.height),new Vector2(0.5f,0.5f),100f);
        sprite.name=address.Substring(address.LastIndexOf('\\')+1);
        sprite.hideFlags=HideFlags.HideAndDontSave;
        return sprite;
    }
}
