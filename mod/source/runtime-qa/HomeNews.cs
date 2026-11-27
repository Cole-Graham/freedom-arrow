using System.Net.Http;
using System.Text.Json;
using HarmonyLib;
using Il2CppBrokenArrow.BrokenArrow.Client.Ecs.UI.Menu.News;
using NewsItem = Il2Cpp.NewsItem;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
namespace FreedomArrow;
// Freedom Arrow news in the Home page's News panel (Osama 27 Nov 2026 11:5x PST, #Website thread: "hide the ba news section and replace it
// with our own news ... would not remove the UI element we would just replace it with our own. I wanted to point to guides and other things
// and tools from our website"). Read from GameAssembly 1.2.2.1: NewsService pulls Steam news (ISteamNews/GetNewsForApp, appid 1604270) and
// raises NewsDeliveredEvent; NewsWindow.OnNewsDelivered(NewsItem[]) (0x2B0970) builds one NewsWindowElement per item; Init(NewsItem)
// (0x2B01B0) fills title/description/date and starts the preview download; OnClickNews (0x2B0570) opens the news popup. All three are
// unique methods (no shared stub). This keeps the vanilla panel, prefab, layout and fades: OnNewsDelivered gets our items instead of
// Steam's, each FA element gets its preview picture from our own cache, and a click opens the linked freedomarrow.app page in the browser.
// The list is https://freedomarrow.app/site/data/ingame-news.json (fetched once per game start, cached in UserData/FreedomArrowNews),
// so the news changes without a build; the copy shipped in UserData/FreedomArrow/ingame-news.json is the fallback.
static class HomeNews
{
    const string Url="https://freedomarrow.app/site/data/ingame-news.json";
    const string Tag="fa-news-";
    sealed class Item{public string id="",title="",title_zh="",text="",text_zh="",url="",image="",date="";}
    static List<Item> items=new();
    static readonly Dictionary<string,Sprite> sprites=new();
    static readonly List<(NewsWindowElement el,string id,float until)> pending=new();
    static string cacheDir="";
    public static void Install(HarmonyLib.Harmony h,string root)
    {
        cacheDir=Path.Combine(MelonEnvironment.UserDataDirectory,"FreedomArrowNews");
        Load(Path.Combine(root,"ingame-news.json"));
        Load(Path.Combine(cacheDir,"ingame-news.json"));   // a newer list from the last game start wins
        h.Patch(AccessTools.Method(typeof(NewsWindow),nameof(NewsWindow.OnNewsDelivered)),prefix:new HarmonyMethod(typeof(HomeNews),nameof(BeforeDelivered)));
        h.Patch(AccessTools.Method(typeof(NewsWindowElement),nameof(NewsWindowElement.Init)),postfix:new HarmonyMethod(typeof(HomeNews),nameof(AfterInit)));
        h.Patch(AccessTools.Method(typeof(NewsWindowElement),nameof(NewsWindowElement.OnClickNews)),prefix:new HarmonyMethod(typeof(HomeNews),nameof(BeforeClick)));
        Task.Run(Refresh);
        MelonLogger.Msg($"FREEDOM_ARROW_HOME_NEWS installed: {items.Count} items; Broken Arrow's Steam news replaced in the Home News panel");
    }
    static void Load(string path)
    {
        try{if(!File.Exists(path))return;var l=JsonSerializer.Deserialize<List<Item>>(File.ReadAllText(path),new JsonSerializerOptions{IncludeFields=true});if(l!=null&&l.Count>0)items=l;}
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HOME_NEWS list "+path+": "+e.Message);}
    }
    // Background: new list + pictures into the cache for this and the next start. Never touches Unity objects.
    static async Task Refresh()
    {
        try
        {
            Directory.CreateDirectory(cacheDir);
            using var http=new HttpClient{Timeout=TimeSpan.FromSeconds(15)};
            http.DefaultRequestHeaders.UserAgent.ParseAdd("FreedomArrow-HomeNews");
            var json=await http.GetStringAsync(Url);
            var l=JsonSerializer.Deserialize<List<Item>>(json,new JsonSerializerOptions{IncludeFields=true});
            if(l==null||l.Count==0)return;
            foreach(var it in l)
            {
                if(string.IsNullOrEmpty(it.image))continue;
                var f=Path.Combine(cacheDir,Safe(it.image));if(File.Exists(f))continue;
                var bytes=await http.GetByteArrayAsync(new Uri(new Uri(Url),it.image));
                File.WriteAllBytes(f+".part",bytes);File.Move(f+".part",f,true);
            }
            File.WriteAllText(Path.Combine(cacheDir,"ingame-news.json"),json);
            items=l;
            MelonLogger.Msg($"FREEDOM_ARROW_HOME_NEWS list refreshed: {l.Count} items");
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HOME_NEWS refresh failed (cached list kept): "+e.Message);}
    }
    static string Safe(string s)=>string.Concat(Path.GetFileName(s).Select(c=>char.IsLetterOrDigit(c)||c=='.'||c=='-'||c=='_'?c:'_'));
    static bool Zh(){try{return HeliRangeCard.Chinese();}catch{return false;}}
    static Item Find(NewsItem n){var g=n?.gid;return g!=null&&g.StartsWith(Tag,StringComparison.Ordinal)?items.FirstOrDefault(i=>Tag+i.id==g):null;}
    // A changed `ref` array does not reach the native method (tested on dev.6, 27 Nov: the panel kept Steam's news). So the prefix skips the
    // original and calls OnNewsDelivered again with our array; the flag lets that inner call run the original unchanged.
    static bool inner;
    static Il2CppReferenceArray<NewsItem> Build()
    {
        var l=items;bool zh=Zh();
        var arr=new Il2CppReferenceArray<NewsItem>(l.Count);
        for(int i=0;i<l.Count;i++)
        {
            var it=l[i];var n=new NewsItem();
            n.gid=Tag+it.id;n.title=zh&&it.title_zh!=""?it.title_zh:it.title;n.contents=zh&&it.text_zh!=""?it.text_zh:it.text;
            n.url=it.url;n.is_external_url=true;n.author="Freedom Arrow";n.feedlabel="Freedom Arrow";n.feedname="freedomarrow";
            n.date=DateTime.TryParse(it.date,out var d)?(int)new DateTimeOffset(d,TimeSpan.Zero).ToUnixTimeSeconds():(int)DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            arr[i]=n;
        }
        return arr;
    }
    static bool BeforeDelivered(NewsWindow __instance,Il2CppReferenceArray<NewsItem> news)
    {
        if(inner||items.Count==0)return true;
        try{Fill(__instance,"delivery hook");return false;}
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HOME_NEWS items: "+e);return true;}
    }
    // Tested on dev.6 (27 Nov): the vanilla list is built without passing through the patched OnNewsDelivered, so Tick also checks the
    // live NewsWindow: when its list holds anything that is not ours, the list is emptied and rebuilt through OnNewsDelivered(our items).
    static void Fill(NewsWindow w,string why)
    {
        var box=w._newsItemsContainer;
        if(box!=null)for(int c=box.childCount-1;c>=0;c--){var ch=box.GetChild(c).gameObject;if(ch.GetComponent<NewsWindowElement>()!=null)UnityEngine.Object.DestroyImmediate(ch);}
        inner=true;
        try{w.OnNewsDelivered(Build());}finally{inner=false;}
        if(box!=null)foreach(var el in box.GetComponentsInChildren<NewsWindowElement>(true)){var it=Find(el._newsItem);if(it!=null)pending.Add((el,it.id,float.MaxValue));}
        MelonLogger.Msg($"FREEDOM_ARROW_HOME_NEWS: news list filled with {items.Count} FA items ({why})");
    }
    static float nextScan;
    static void Scan()
    {
        if(items.Count==0||Time.unscaledTime<nextScan)return;
        nextScan=Time.unscaledTime+0.5f;
        foreach(var w in UnityEngine.Object.FindObjectsOfType<NewsWindow>())
        {
            if(w==null||!w.isActiveAndEnabled||w._newsItemsContainer==null)continue;
            var els=w._newsItemsContainer.GetComponentsInChildren<NewsWindowElement>(true);
            if(els.Length==0)continue;   // Steam news not shown yet
            bool foreign=false;foreach(var el in els)if(Find(el._newsItem)==null){foreign=true;break;}
            if(foreign)Fill(w,"panel scan");
        }
    }
    static Sprite Pic(Item it)
    {
        if(string.IsNullOrEmpty(it.image))return null;
        if(sprites.TryGetValue(it.image,out var s)&&s!=null)return s;
        var f=Path.Combine(cacheDir,Safe(it.image));if(!File.Exists(f))return null;
        var t=new Texture2D(2,2,TextureFormat.RGBA32,false);t.hideFlags=HideFlags.DontUnloadUnusedAsset;
        if(!ImageConversion.LoadImage(t,File.ReadAllBytes(f)))return null;
        s=Sprite.Create(t,new Rect(0,0,t.width,t.height),new Vector2(0.5f,0.5f),100f);s.hideFlags=HideFlags.DontUnloadUnusedAsset;
        sprites[it.image]=s;return s;
    }
    static void AfterInit(NewsWindowElement __instance,NewsItem item)
    {
        try{var it=Find(item);if(it!=null){pending.Add((__instance,it.id,float.MaxValue));Apply(__instance,it);}}
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HOME_NEWS element: "+e.Message);}
    }
    // The vanilla preview download runs after Init and finishes later; for 10 s keep our picture on top of whatever it shows.
    static readonly HashSet<string> told=new();
    static void Dump(Transform t,int d)
    {
        if(d>5)return;
        var img=t.GetComponent<Image>();var cg=t.GetComponent<CanvasGroup>();var rt=t.GetComponent<RectTransform>();
        MelonLogger.Msg($"FREEDOM_ARROW_HOME_NEWS tree {new string(' ',d*2)}{t.name} self={t.gameObject.activeSelf} img={(img!=null?$"{(img.sprite!=null?img.sprite.name:"-")} a={img.color.a:0.00} en={img.enabled}":"-")} cg={(cg!=null?cg.alpha.ToString("0.00"):"-")} size={(rt!=null?$"{rt.rect.width:0}x{rt.rect.height:0}":"-")}");
        for(int i=0;i<t.childCount;i++)Dump(t.GetChild(i),d+1);
    }
    static void Apply(NewsWindowElement el,Item it)
    {
        var p=Pic(it);
        if(p==null||el._preview==null){if(told.Add("miss"+it.id))MelonLogger.Warning($"FREEDOM_ARROW_HOME_NEWS: no picture for '{it.id}' (sprite {(p==null?"null":"ok")}, preview {(el._preview==null?"null":"ok")})");return;}
        if(told.Add("ok"+it.id))MelonLogger.Msg($"FREEDOM_ARROW_HOME_NEWS: picture '{it.id}' {p.texture.width}x{p.texture.height} on '{el._preview.gameObject.name}' (active {el._preview.gameObject.activeInHierarchy})");
        el._preview.sprite=p;el._preview.preserveAspect=false;el._preview.color=Color.white;el._preview.enabled=true;
        for(var t=el._preview.transform;t!=null&&t!=el.transform;t=t.parent)if(!t.gameObject.activeSelf)t.gameObject.SetActive(true);   // vanilla keeps the preview's holder off until its own download finishes
        if(el._previewLoader!=null)el._previewLoader.SetActive(false);
        if(el._genericPreview!=null)el._genericPreview.SetActive(false);
    }
    public static void Tick()
    {
        try{Scan();}catch(Exception e){nextScan=Time.unscaledTime+10f;MelonLogger.Warning("FREEDOM_ARROW_HOME_NEWS scan: "+e.Message);}
        if(pending.Count==0)return;
        for(int i=pending.Count-1;i>=0;i--)
        {
            var (el,id,until)=pending[i];
            try{if(el==null||el.WasCollected||Time.unscaledTime>until){pending.RemoveAt(i);continue;}var it=items.FirstOrDefault(x=>x.id==id);if(it!=null)Apply(el,it);}
            catch{pending.RemoveAt(i);}
        }
    }
    static bool BeforeClick(NewsWindowElement __instance)
    {
        try
        {
            var it=Find(__instance._newsItem);if(it==null)return true;
            if(!string.IsNullOrEmpty(it.url)){Application.OpenURL(it.url);MelonLogger.Msg("FREEDOM_ARROW_HOME_NEWS opened "+it.url);}
            return false;
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HOME_NEWS click: "+e.Message);return true;}
    }
}
