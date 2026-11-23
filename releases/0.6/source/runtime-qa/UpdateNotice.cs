using System.Text.Json.Nodes;
using MelonLoader;
namespace FreedomArrow;
// Out-of-date notice (Osama 21 Nov 2026: "in game we should have a notification in the main menu that alerts the player their version is out
// of date" / "Yes, let the launcher update them"). One request at startup to the live manifest; if its "current" release is newer than the
// installed package_version, the main menu shows Text above the version label (conquest/VersionLabel.cs). Offline, a failed request or a
// dev/test build (version with a suffix) shows nothing.
public static class UpdateNotice
{
    const string Manifest="https://freedomarrow.app/manifest/live.json";
    public static string Text { get; private set; }
    public static void Start(string installed)
    {
        var have=Parse(installed);if(have==null)return;
        _=Check(installed,have);
    }
    static async Task Check(string installed,int[] have)
    {
        {
            try
            {
                using var http=new HttpClient{Timeout=TimeSpan.FromSeconds(15)};
                var current=JsonNode.Parse(await http.GetStringAsync(Manifest))?["current"]?.GetValue<string>();
                var live=Parse(current);
                if(live!=null&&Newer(live,have))
                {
                    Text=$"Freedom Arrow {current} is available. Close the game and press PLAY in the launcher to update.\nFreedom Arrow {current} 已发布。请关闭游戏，在启动器中点击 PLAY 更新。";
                    MelonLogger.Msg($"FREEDOM_ARROW_UPDATE_NOTICE installed {installed}, live {current}: notice shown in the main menu");
                }
                else MelonLogger.Msg($"FREEDOM_ARROW_UPDATE_NOTICE installed {installed}, live {current}: up to date");
            }
            catch(Exception e){MelonLogger.Msg("FREEDOM_ARROW_UPDATE_NOTICE live version not read: "+e.GetType().Name);}
        }
    }
    // "0.9.4", "0.9.4.1" or a lettered hotfix "0.9.4b" (Lateralus 22 Nov 2026: hotfixes are 0.9.4b, 0.9.4c, ...; the letter is compared as
    // one more number, b = 1, c = 2, so 0.9.4 < 0.9.4b < 0.9.4c < 0.9.5). Anything else (0.9.4-dev.3, -test10) is not compared.
    static int[] Parse(string v)
    {
        if(string.IsNullOrEmpty(v))return null;
        var parts=v.Split('.');int letter=0;
        var last=parts[^1];
        if(last.Length>1&&last[^1]>='b'&&last[^1]<='z'&&char.IsDigit(last[^2])){letter=last[^1]-'a';parts[^1]=last[..^1];}
        var n=new int[parts.Length+(letter>0?1:0)];
        for(int i=0;i<parts.Length;i++)if(!int.TryParse(parts[i],out n[i]))return null;
        if(letter>0)n[^1]=letter;
        return n;
    }
    static bool Newer(int[] a,int[] b)
    {
        for(int i=0;i<Math.Max(a.Length,b.Length);i++)
        {
            int x=i<a.Length?a[i]:0,y=i<b.Length?b[i]:0;
            if(x!=y)return x>y;
        }
        return false;
    }
}
