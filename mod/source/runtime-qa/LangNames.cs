using System.Text.Json;
using HarmonyLib;
using Il2CppBrokenArrow.Shared.Ecs.Localization;
using MelonLoader;

namespace FreedomArrow;

// Osama 23 Nov 2026 13:0x: "you put both names at the same time, it should have been English OR chinese not both" (spec names such as
// "PLARF Rocket Conscript Force 火箭..." and unit names such as "J-5 Drone 歼-5无人机"). Our data keeps one bilingual string per name: English first,
// then the Chinese. The game shows text through LocalizationService.GetLocalizedStringPart; a postfix replaces exactly those bilingual strings with
// the half for the game language (a "zh" or "chin" language code shows Chinese, every other language English), as PartySizeWarning picks its text.
// Only strings that appear as values in our packaged constants (UserData/FreedomArrow/constants/*.json) and contain both Latin letters and CJK are
// split, so vanilla Chinese text that starts with a Latin name (e.g. "M1A2 ...") is never cut.
static class LangNames
{
    static readonly HashSet<string> Bilingual=new();
    static readonly Dictionary<string,(string en,string zh)> Split=new();
    static string lang="\0";static bool chinese;
    public static void Install(HarmonyLib.Harmony h,string root)
    {
        foreach(var f in Directory.GetFiles(Path.Combine(root,"constants"),"*.json"))
            using(var doc=JsonDocument.Parse(File.ReadAllBytes(f)))Collect(doc.RootElement);
        foreach(var s in Bilingual){var p=Halves(s);if(p!=null)Split[s]=p.Value;}
        h.Patch(AccessTools.Method(typeof(LocalizationService),nameof(LocalizationService.GetLocalizedStringPart))??throw new MissingMethodException("LocalizationService.GetLocalizedStringPart"),
            postfix:new HarmonyMethod(typeof(LangNames),nameof(Post)));
        MelonLogger.Msg($"FREEDOM_ARROW_LANG_NAMES installed: {Split.Count} bilingual names shown in the game language");
    }
    static void Collect(JsonElement e)
    {
        switch(e.ValueKind)
        {
            case JsonValueKind.Object:foreach(var p in e.EnumerateObject())Collect(p.Value);break;
            case JsonValueKind.Array:foreach(var v in e.EnumerateArray())Collect(v);break;
            case JsonValueKind.String:var s=e.GetString();if(s!=null&&HasCjk(s)&&s.Any(c=>c<128&&char.IsLetter(c)))Bilingual.Add(s);break;
        }
    }
    static bool Cjk(char c)=>(c>='　'&&c<='鿿')||(c>='＀'&&c<='￯')||(c>='豈'&&c<='﫿');
    static bool HasCjk(string s){foreach(var c in s)if(Cjk(c))return true;return false;}
    // English half = text before the last space/newline that precedes the first CJK character; Chinese half = the rest.
    internal static (string en,string zh)? Halves(string s)
    {
        int i=0;while(i<s.Length&&!Cjk(s[i]))i++;
        if(i==s.Length)return null;
        int j=s.LastIndexOfAny(new[]{' ','\n','\t','　'},i);
        if(j<=0)return null;
        string en=s.Substring(0,j).Trim(),zh=s.Substring(j).Trim();
        if(en.Length==0||zh.Length==0||!en.Any(c=>c<128&&char.IsLetter(c)))return null;
        return (en,zh);
    }
    static void Post(LocalizationService __instance,ref string __result)
    {
        if(__result==null||!Split.TryGetValue(__result,out var p))return;
        string code="";try{code=__instance?.CurrentLanguage??"";}catch{}
        if(code!=lang){lang=code;var c=code.Trim().ToLowerInvariant();chinese=c.StartsWith("zh")||c.Contains("chin");MelonLogger.Msg($"FREEDOM_ARROW_LANG_NAMES language '{code}': {(chinese?"Chinese":"English")}");}
        __result=chinese?p.zh:p.en;
    }
}
