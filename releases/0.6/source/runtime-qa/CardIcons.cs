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
// Aircraft portraits use the supplied PNGs verbatim; numeric card fields remain native.
// Portrait, _BASIC and _HOVER aliases share one Sprite/Texture per resource.
// PLA infantry portraits (Osama, 13 Nov 2026): conscripts and sniper pair are original generated art; the other six are Osama's supplied images.
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
        ("FA_SU75-Portrait","FA_SU75-Portrait.png"),
        ("FA_SU75-Portrait_BASIC","FA_SU75-Portrait.png"),
        ("FA_SU75-Portrait_HOVER","FA_SU75-Portrait.png"),
        ("FA_SU47-Portrait","FA_SU47-Portrait.png"),
        ("FA_SU47-Portrait_BASIC","FA_SU47-Portrait.png"),
        ("FA_SU47-Portrait_HOVER","FA_SU47-Portrait.png"),
        ("FA_SU57D-Portrait","FA_SU57D-Portrait.png"),
        ("FA_SU57D-Portrait_BASIC","FA_SU57D-Portrait.png"),
        ("FA_SU57D-Portrait_HOVER","FA_SU57D-Portrait.png"),
        ("FA_YF23-Portrait","FA_YF23-Portrait.png"),
        ("FA_YF23-Portrait_BASIC","FA_YF23-Portrait.png"),
        ("FA_YF23-Portrait_HOVER","FA_YF23-Portrait.png"),
        ("FA_F14-Portrait","FA_F14-Portrait.png"),
        ("FA_F14-Portrait_BASIC","FA_F14-Portrait.png"),
        ("FA_F14-Portrait_HOVER","FA_F14-Portrait.png"),
        ("FA_SU75-Label","FA_SU75-Label.png"),
        ("outline\\FA_SU75-Label","FA_SU75-Label.png"),
        ("FA_SU47-Label","FA_SU47-Label.png"),
        ("outline\\FA_SU47-Label","FA_SU47-Label.png"),
        ("FA_SU57D-Label","FA_SU57D-Label.png"),
        ("outline\\FA_SU57D-Label","FA_SU57D-Label.png"),
        ("FA_YF23-Label","FA_YF23-Label.png"),
        ("outline\\FA_YF23-Label","FA_YF23-Label.png"),
        ("FA_F14-Label","FA_F14-Label.png"),
        ("outline\\FA_F14-Label","FA_F14-Label.png"),
        ("FA_KARATEL-Portrait","FA_KARATEL-Portrait.png"),
        ("FA_KARATEL-Portrait_BASIC","FA_KARATEL-Portrait.png"),
        ("FA_KARATEL-Portrait_HOVER","FA_KARATEL-Portrait.png"),
        ("FA_KARATEL-Label","FA_KARATEL-Label.png"),
        ("outline\\FA_KARATEL-Label","FA_KARATEL-Label.png"),
        ("FA_XM30-Portrait","FA_XM30-Portrait.png"),
        ("FA_XM30-Portrait_BASIC","FA_XM30-Portrait.png"),
        ("FA_XM30-Portrait_HOVER","FA_XM30-Portrait.png"),
        ("FA_XM30-Label","FA_XM30-Label.png"),
        ("outline\\FA_XM30-Label","FA_XM30-Label.png"),
        ("FA_ABRAMSX-Portrait","FA_ABRAMSX-Portrait.png"),
        ("FA_ABRAMSX-Portrait_BASIC","FA_ABRAMSX-Portrait.png"),
        ("FA_ABRAMSX-Portrait_HOVER","FA_ABRAMSX-Portrait.png"),
        ("FA_ABRAMSX-Label","FA_ABRAMSX-Label.png"),
        ("outline\\FA_ABRAMSX-Label","FA_ABRAMSX-Label.png"),
        ("FA_X47-Portrait","FA_X47-Portrait.png"),
        ("FA_X47-Portrait_BASIC","FA_X47-Portrait.png"),
        ("FA_X47-Portrait_HOVER","FA_X47-Portrait.png"),
        ("FA_X47-Label","FA_X47-Label.png"),
        ("outline\\FA_X47-Label","FA_X47-Label.png"),
        ("FA_LOSAT-Portrait","FA_LOSAT-Portrait.png"),
        ("FA_LOSAT-Portrait_BASIC","FA_LOSAT-Portrait.png"),
        ("FA_LOSAT-Portrait_HOVER","FA_LOSAT-Portrait.png"),
        ("FA_LOSAT-Label","FA_LOSAT-Label.png"),
        ("outline\\FA_LOSAT-Label","FA_LOSAT-Label.png"),
        ("FA_BLACK_EAGLE-Portrait","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE-Portrait_BASIC","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE-Portrait_HOVER","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE_STUDIO-Portrait","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE_STUDIO-Portrait_BASIC","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE_STUDIO-Portrait_HOVER","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE_USER-Portrait","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE_USER-Portrait_BASIC","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE_USER-Portrait_HOVER","FA_BLACK_EAGLE-Portrait.png"),
        ("FA_BLACK_EAGLE-Label","FA_BLACK_EAGLE-Label.png"),
        ("FA_CN_INF_CONSCRIPTS-Portrait","FA_CN_INF_CONSCRIPTS-Portrait.png"),
        ("FA_CN_INF_CONSCRIPTS-Portrait_BASIC","FA_CN_INF_CONSCRIPTS-Portrait.png"),
        ("FA_CN_INF_CONSCRIPTS-Portrait_HOVER","FA_CN_INF_CONSCRIPTS-Portrait.png"),
        ("FA_CN_INF_SNIPER_PAIR-Portrait","FA_CN_INF_SNIPER_PAIR-Portrait.png"),
        ("FA_CN_INF_SNIPER_PAIR-Portrait_BASIC","FA_CN_INF_SNIPER_PAIR-Portrait.png"),
        ("FA_CN_INF_SNIPER_PAIR-Portrait_HOVER","FA_CN_INF_SNIPER_PAIR-Portrait.png"),
        ("FA_CN_INF_SF_HIGH_TECH-Portrait","FA_CN_INF_SF_HIGH_TECH-Portrait.png"),
        ("FA_CN_INF_SF_HIGH_TECH-Portrait_BASIC","FA_CN_INF_SF_HIGH_TECH-Portrait.png"),
        ("FA_CN_INF_SF_HIGH_TECH-Portrait_HOVER","FA_CN_INF_SF_HIGH_TECH-Portrait.png"),
        ("FA_CN_INF_SF_JUNGLE-Portrait","FA_CN_INF_SF_JUNGLE-Portrait.png"),
        ("FA_CN_INF_SF_JUNGLE-Portrait_BASIC","FA_CN_INF_SF_JUNGLE-Portrait.png"),
        ("FA_CN_INF_SF_JUNGLE-Portrait_HOVER","FA_CN_INF_SF_JUNGLE-Portrait.png"),
        ("FA_CN_INF_AIRBORNE-Portrait","FA_CN_INF_AIRBORNE-Portrait.png"),
        ("FA_CN_INF_AIRBORNE-Portrait_BASIC","FA_CN_INF_AIRBORNE-Portrait.png"),
        ("FA_CN_INF_AIRBORNE-Portrait_HOVER","FA_CN_INF_AIRBORNE-Portrait.png"),
        ("FA_CN_INF_MARINES-Portrait","FA_CN_INF_MARINES-Portrait.png"),
        ("FA_CN_INF_MARINES-Portrait_BASIC","FA_CN_INF_MARINES-Portrait.png"),
        ("FA_CN_INF_MARINES-Portrait_HOVER","FA_CN_INF_MARINES-Portrait.png"),
        ("FA_CN_INF_SF_CQC-Portrait","FA_CN_INF_SF_CQC-Portrait.png"),
        ("FA_CN_INF_SF_CQC-Portrait_BASIC","FA_CN_INF_SF_CQC-Portrait.png"),
        ("FA_CN_INF_SF_CQC-Portrait_HOVER","FA_CN_INF_SF_CQC-Portrait.png"),
        ("FA_CN_INF_MOTORIZED-Portrait","FA_CN_INF_MOTORIZED-Portrait.png"),
        ("FA_CN_INF_MOTORIZED-Portrait_BASIC","FA_CN_INF_MOTORIZED-Portrait.png"),
        ("FA_CN_INF_MOTORIZED-Portrait_HOVER","FA_CN_INF_MOTORIZED-Portrait.png"),
        ("outline\\FA_BLACK_EAGLE-Label","FA_BLACK_EAGLE-Label.png"),
        // A distinct address avoids a native UI item retaining the previous gray sprite.
        ("FA_BLACK_EAGLE_WHITE-Label","FA_BLACK_EAGLE-Label.png"),
        ("outline\\FA_BLACK_EAGLE_WHITE-Label","FA_BLACK_EAGLE-Label.png"),
    };
    static readonly Dictionary<string,byte[]> png=new();
    static readonly Dictionary<string,Sprite> made=new();
    static bool broken,logged;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        var asm=typeof(CardIcons).Assembly;
        foreach(var (address,resource) in Icons)
        {
            if(png.ContainsKey(resource))continue;
            using var s=asm.GetManifestResourceStream("FreedomArrow.icons."+resource)??throw new InvalidOperationException("missing embedded icon "+resource);
            using var m=new MemoryStream();s.CopyTo(m);png[resource]=m.ToArray();
        }
        var seed=new HarmonyMethod(typeof(CardIcons),nameof(Seed));
        harmony.Patch(AccessTools.Method(typeof(IconsLoader),nameof(IconsLoader.LoadSprite)),prefix:seed);
        harmony.Patch(AccessTools.Method(typeof(IconsLoader),nameof(IconsLoader.LoadSpriteAsync)),prefix:seed);
        MelonLogger.Msg($"FREEDOM_ARROW_CARD_ICONS installed: {Icons.Length} sprite addresses; 18 portraits, 10 right-facing cutouts, existing ground icons");
    }
    public static void Seed()
    {
        if(broken||!Runtime.IsApplied)return;
        try
        {
            var cache=IconsLoader._sprites;
            if(cache==null)return;
            foreach(var (address,resource) in Icons)
            {
                // IconsLoader.Dispose can destroy cached sprites; make a new one when ours is gone.
                if(!made.TryGetValue(resource,out var sprite)||sprite==null)made[resource]=sprite=Make(resource);
                if(cache.TryGetValue(address,out var have)&&have!=null&&have.Pointer==sprite.Pointer)continue;
                cache[address]=sprite;
            }
            if(!logged){logged=true;MelonLogger.Msg("FREEDOM_ARROW_CARD_ICONS cached: ground icons plus Su-75, Su-47, Su-57D, YF-23, F-21, Karatel, XM30, Abrams X and X-47B portraits, 8 PLA infantry portraits and right-facing cutouts");}
        }
        catch(Exception x)
        {
            broken=true;
            MelonLogger.Error("FREEDOM_ARROW_CARD_ICONS_FAILED: off for this session; custom images unavailable; inspect installation. "+x.Message);
        }
    }
    static Sprite Make(string address)
    {
        bool cutout=address is "FA_SU75-Label.png" or "FA_SU47-Label.png" or "FA_SU57D-Label.png" or "FA_YF23-Label.png" or "FA_F14-Label.png" or "FA_X47-Label.png" or "FA_KARATEL-Label.png" or "FA_XM30-Label.png" or "FA_ABRAMSX-Label.png" or "FA_LOSAT-Label.png" or "FA_BLACK_EAGLE-Label.png";
        var tex=new Texture2D(2,2,TextureFormat.RGBA32,cutout){name=address,wrapMode=TextureWrapMode.Clamp,filterMode=cutout?FilterMode.Trilinear:FilterMode.Bilinear};
        // Preserve the approved source PNGs exactly. Mirror only these aircraft label textures for native right-facing UI.
        bool mirror=address is "FA_SU75-Label.png" or "FA_SU47-Label.png" or "FA_SU57D-Label.png" or "FA_YF23-Label.png" or "FA_F14-Label.png";
        if(!ImageConversion.LoadImage(tex,(Il2CppStructArray<byte>)png[address],!cutout))throw new InvalidOperationException("icon did not decode: "+address);
        if(cutout)
        {
            var source=tex.GetPixels32();var flipped=new Il2CppStructArray<Color32>(source.Length);int w=tex.width,h=tex.height;
            var alpha=new byte[source.Length];for(int i=0;i<alpha.Length;i++)alpha[i]=source[i].a;
            var clean=CutoutMask.Clean(alpha,w,h);
            for(int y=0;y<h;y++)for(int x=0;x<w;x++)
            {
                int from=y*w+(mirror?w-1-x:x);var pixel=source[from];
                // White hidden RGB avoids a dark fringe when mip levels average transparent pixels.
                flipped[y*w+x]=clean[from]==0?new Color32(255,255,255,0):new Color32(pixel.r,pixel.g,pixel.b,255);
            }
            tex.SetPixels32(flipped);tex.Apply(true,true);
        }
        if(address=="FA_BLACK_EAGLE-Label.png")
            MelonLogger.Msg($"FREEDOM_ARROW_BLACK_EAGLE_CARD made: {tex.width}x{tex.height}; cutout={cutout}; png_sha256={Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(png[address])).ToLowerInvariant()}");
        if(address=="FA_BLACK_EAGLE-Portrait.png")
            MelonLogger.Msg($"FREEDOM_ARROW_BLACK_EAGLE_PORTRAIT made: {tex.width}x{tex.height}; png_sha256={Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(png[address])).ToLowerInvariant()}");
        tex.hideFlags=HideFlags.HideAndDontSave;
        // Sam's supplied screenshot is embedded verbatim. Frame the full tank in the UI;
        // these are source-image pixels (Unity's rectangle origin is bottom-left).
        var rect=address=="FA_BLACK_EAGLE-Portrait.png" ? new Rect(220,269,1600,800) : new Rect(0,0,tex.width,tex.height);
        var sprite=Sprite.Create(tex,rect,new Vector2(0.5f,0.5f),100f);
        sprite.name=address.Substring(address.LastIndexOf('\\')+1);
        sprite.hideFlags=HideFlags.HideAndDontSave;
        return sprite;
    }
}
