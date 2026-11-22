using System.Collections;
using System.Reflection;
using System.Text.Json;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI;
using Il2CppBrokenArrow.Client.Ecs.UI.MainMenu;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
namespace FreedomArrow;
// Ranked menus (Lateralus 22 Nov 2026, thread 1568104480459722894: "implement the test server, and build the in-game ranked screens";
// design docs/ranked/RANKED-PROPOSAL.md, mock-ups docs/ranked/mock-*.jpg).
// - Play tab: a 5th card "Ranked" (UserData/FreedomArrow/ranked/card.png) right of the game's own cards, placed from PlayTab._buttonsContainer.
// - Ranked menu (IMGUI, full screen, the game's UI input is off while it is open): tabs Ranked / Leaderboard / Rank ladder.
//   Ranked: two queues (Lateralus 22 Nov: "1v1 should be a completely different queue"): 1v1 (solo) and Team (3v3 or 5v5, solo or party);
//   your rank in the selected ladder, recent results, the epaulet set picker and the rank ladder strip.
// - Searches go through ArrowQueue (unchanged): Flow.Begin(compat, now, null, "r1v1"|"rteam"). The hub picks the map; for the host,
//   Flow.PickMap is answered with the hub's map from GetRanked (ArrowQueue normally lets the host choose).
// - Data comes from the FA lobby server over ArrowQueue's own connection: GetRanked, GetRankedLeaderboard.
// - Epaulets are the game's own sprites (Epaulet_USA_base_N US Army, Epaulet_USA_N US Marines, Epaulet_RUS_base_N Russian Army,
//   Epaulet_RUS_N Russian VDV), found by name at run time. Default set = the player's vanilla pick, read from the sprite the game's
//   ProfileUtils.GetEpauletData returns for the local player. The PLA set is not drawn yet.
static class RankedMenu
{
    // TEST BUILD: ranked runs on the test hub (faqueue-test.service, /hubs/test). ThirdPartyGuard points ArrowQueue here while this is set.
    public const bool TestHub=true;
    // ArrowQueue only uses its SignalR hub when the address ends in /hubs/game (Signal.On); otherwise it falls back to its old REST API.
    public const string TestHubRoot="https://freedomarrow.app/hubs/test/hubs";

    static readonly int[] BandStart={0,1001,1028,1059,1093,1132,1175,1223,1277,1337,1405,1481,1566,1661,1767,1887,2020,2170};
    static readonly string[] UsNames={"Private","Private first class","Sergeant","Staff sergeant","Sergeant first class","Master sergeant","First sergeant","Sergeant major",
        "Second lieutenant","First lieutenant","Captain","Major","Lieutenant colonel","Colonel","Brigadier general","Major general","Lieutenant general","General","General of the army","General of the armies"};
    static readonly string[] RuNames={"Ryadovoj","Efrejtor","Mladshij serzhant","Serzhant","Starshij serzhant","Starshina","Praporshhik","Starshij praporshhik",
        "Mladshij lejtenant","Lejtenant","Kapitan","Major","Podpolkovnik","Polkovnik","General-major","General-lejtenant","General-polkovnik","General armii","Marshal","Marshal"};
    static readonly string[] SetNames={"US Army","US Marines","Russian Army","Russian VDV","PLA"};
    static readonly string[] SetPrefix={"Epaulet_USA_base_","Epaulet_USA_","Epaulet_RUS_base_","Epaulet_RUS_",""};
    static readonly Dictionary<string,string> Pools=new(){["r1v1"]="Dead Center · Kadaga · Jelgava · Klaipeda · Chernyakhovsky",
        ["rteam"]="3v3: Baltiisk · Bay of Winds · Dam\n5v5: Airport · Oil Rush · Cold Harbor"};

    static string dir="",settingsFile="";
    static Texture2D card;
    static int set=-1;              // chosen set; -1 = follow the vanilla pick
    static int vanillaSet=-1;       // from the game's profile epaulet
    static string mySteam="";

    // ArrowQueue (reflection; it is a separate unchanged mod)
    static Type tFlow,tUi,tApi,tGame,tSignal;
    static MethodInfo mBegin,mCanStart,mStop,mPicked,mSupported;
    static PropertyInfo pActive,pCurrent,pMySteam,pInLobby;
    static FieldInfo fLink,fPartyNews;

    public static void Install(HarmonyLib.Harmony h)
    {
        dir=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","ranked");
        settingsFile=Path.Combine(dir,"settings.json");
        card=Load(Path.Combine(dir,"card.png"),"FA_ranked_card");
        try{var s=JsonDocument.Parse(File.ReadAllText(settingsFile)).RootElement;if(s.TryGetProperty("set",out var v))set=Array.IndexOf(SetNames,v.GetString());}catch{}
        tFlow=AccessTools.TypeByName("ArrowQueue.Flow");tUi=AccessTools.TypeByName("ArrowQueue.Ui");tApi=AccessTools.TypeByName("ArrowQueue.Api");
        tGame=AccessTools.TypeByName("ArrowQueue.Game");tSignal=AccessTools.TypeByName("ArrowQueue.Signal");
        if(tFlow==null||tUi==null||tApi==null||tGame==null||tSignal==null)throw new InvalidOperationException("ArrowQueue types not found");
        mBegin=AccessTools.Method(tFlow,"Begin");mPicked=AccessTools.Method(tFlow,"Picked");mCanStart=AccessTools.Method(tUi,"CanStart");
        mStop=AccessTools.Method(tApi,"Stop");mSupported=AccessTools.Method(tGame,"SupportedScenarios");
        pActive=AccessTools.Property(tApi,"Active");pCurrent=AccessTools.Property(tApi,"Current");
        pMySteam=AccessTools.Property(tGame,"MySteamId");pInLobby=AccessTools.Property(tGame,"InLobby");
        fLink=AccessTools.Field(tSignal,"_link");fPartyNews=AccessTools.Field(tApi,"PartyNews");
        foreach(var (n,o) in new (string,object)[]{("Flow.Begin",mBegin),("Flow.Picked",mPicked),("Ui.CanStart",mCanStart),("Api.Stop",mStop),("Game.SupportedScenarios",mSupported),
            ("Api.Active",pActive),("Api.Current",pCurrent),("Game.MySteamId",pMySteam),("Game.InLobby",pInLobby),("Signal._link",fLink)})
            if(o==null)throw new InvalidOperationException("ArrowQueue "+n+" not found");
        h.Patch(AccessTools.Method(tFlow,"PickMap"),prefix:new HarmonyMethod(typeof(RankedMenu),nameof(PickMap)));
        var mode=AccessTools.Method(AccessTools.TypeByName("ArrowQueue.Text"),"Mode");
        if(mode!=null)h.Patch(mode,postfix:new HarmonyMethod(typeof(RankedMenu),nameof(ModeName)));
        try
        {
            var gep=AccessTools.Method(typeof(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Profile.Other.ProfileUtils),"GetEpauletData",new[]{typeof(Il2CppNetworkCommon.RestApi.Models.RestUserInfo)});
            h.Patch(gep,postfix:new HarmonyMethod(typeof(RankedMenu),nameof(Epaulet)));
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED: vanilla epaulet pick not read ("+e.Message+"); default set US Army");}
        MelonLogger.Msg($"FREEDOM_ARROW_RANKED installed: card {(card!=null?$"{card.width}x{card.height}":"missing")}, saved set {(set<0?"vanilla pick":SetNames[set])}, hub {(TestHub?TestHubRoot:"live")}");
    }
    static Texture2D Load(string file,string name)
    {
        if(!File.Exists(file))return null;
        var t=new Texture2D(2,2,TextureFormat.RGBA32,false){name=name,hideFlags=HideFlags.DontUnloadUnusedAsset};
        return ImageConversion.LoadImage(t,File.ReadAllBytes(file),true)?t:null;
    }
    static void SaveSettings(){try{Directory.CreateDirectory(dir);File.WriteAllText(settingsFile,JsonSerializer.Serialize(new{set=set<0?"":SetNames[set]}));}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED settings: "+e.Message);}}

    // ---------- hooks ----------
    static void ModeName(string m,ref string __result){if(m=="r1v1")__result="Ranked 1v1";else if(m=="rteam")__result="Ranked team";}
    static void Epaulet(Il2CppNetworkCommon.RestApi.Models.RestUserInfo __0,Il2CppBrokenArrow.Client.Ecs.Configs.UserProgress.EpauletData __result)
    {
        try
        {
            if(__0==null||__result?.Sprite==null)return;
            var me=MySteam();if(me.Length==0||(__0.MarketId!=me&&__0.SteamId!=me))return;
            var n=__result.Sprite.name;int s=-1;
            for(int i=0;i<4;i++)if(n.StartsWith(SetPrefix[i])&&int.TryParse(n[SetPrefix[i].Length..],out _)){s=i;break;}
            if(s<0&&n.StartsWith("Epaulet_RUS"))s=2;   // RusVMF (unused) -> Russian Army
            if(s>=0&&s!=vanillaSet){vanillaSet=s;MelonLogger.Msg($"FREEDOM_ARROW_RANKED vanilla epaulet {n} -> {SetNames[s]}");}
        }
        catch{}
    }
    static string rankedMap="",rankedLobby="";static float pickWaitFrom=-1f,lastAsk;
    // Host of a ranked match: load the hub's map. Ranked lobbies have mode r1v1/rteam (the hub sends the queue as the lobby mode).
    static bool PickMap(object v,float now,ref bool __result)
    {
        try
        {
            var mode=Traverse.Create(v).Property("mode").GetValue<string>();
            if(mode is not ("r1v1" or "rteam"))return true;
            var lobby=Traverse.Create(v).Property("lobbyId").GetValue<string>();
            if(pickWaitFrom<0f)pickWaitFrom=now;
            if(rankedLobby==lobby&&rankedMap.Length>0)
            {
                object best=null;string bestName="";
                foreach(var s in (IEnumerable)mSupported.Invoke(null,null))
                {
                    var name=Traverse.Create(s).Property("Name").GetValue<string>()??"";
                    if(!MapName(name).Equals(rankedMap,StringComparison.OrdinalIgnoreCase))continue;
                    if(best==null||string.CompareOrdinal(name,bestName)>0){best=s;bestName=name;}
                }
                if(best!=null)
                {
                    mPicked.Invoke(null,new[]{lobby,best});pickWaitFrom=-1f;__result=true;
                    MelonLogger.Msg($"FREEDOM_ARROW_RANKED host map {bestName} (hub pick {rankedMap}, lobby {lobby})");
                    return false;
                }
                MelonLogger.Warning($"FREEDOM_ARROW_RANKED hub map {rankedMap} is not installed; the normal map choice opens (the match will be unrated)");
                pickWaitFrom=-1f;return true;
            }
            if(now-pickWaitFrom>20f){MelonLogger.Warning("FREEDOM_ARROW_RANKED no hub map after 20 s; the normal map choice opens");pickWaitFrom=-1f;return true;}
            if(now-lastAsk>2f){lastAsk=now;Ask();}
            __result=false;return false;
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED map pick: "+e.Message);return true;}
    }
    // "[FA] [1v1] Dead Center 0.2" -> "Dead Center" (same rule as the hub's Ranked.MapName)
    static string MapName(string s)
    {
        s=System.Text.RegularExpressions.Regex.Replace(s??"",@"^\[FA\]\s*","");
        s=System.Text.RegularExpressions.Regex.Replace(s,@"^\[\dv\d\]\s*","");
        return System.Text.RegularExpressions.Regex.Replace(s,@"\s+\d+(\.\d+)+$","").Trim();
    }

    // ---------- hub data (ArrowQueue's connection) ----------
    static volatile string meJson="",board1="",boardT="",error="";
    static float nextAsk=-100f,nextBoard=-100f;
    static string MySteam(){if(mySteam.Length==0)try{var id=(ulong)pMySteam.GetValue(null);if(id!=0)mySteam=id.ToString();}catch{}return mySteam;}
    static void Call(string method,Action<string> done,params object[] args)
    {
        var link=fLink.GetValue(null);
        if(link==null||!Traverse.Create(link).Property("Open").GetValue<bool>()){error="Not connected to the Freedom Arrow lobby server yet.";return;}
        var inv=AccessTools.Method(link.GetType(),"Invoke");
        Task<JsonElement> t;
        try{t=(Task<JsonElement>)inv.Invoke(link,new object[]{method,args});}catch(Exception e){error=e.InnerException?.Message??e.Message;return;}
        t.ContinueWith(new Action<Task<JsonElement>>(r=>Finish(r,done)));
    }
    static void Finish(Task<JsonElement> r,Action<string> done)
    {
        if(r.IsFaulted){var ex=r.Exception;error=ex==null||ex.InnerException==null?"error":ex.InnerException.Message;return;}
        error="";done(r.Result.GetRawText());
    }
    static void Ask()
    {
        Call("GetRanked",j=>
        {
            meJson=j;
            try{var m=JsonDocument.Parse(j).RootElement.GetProperty("match");if(m.ValueKind==JsonValueKind.Object){rankedLobby=m.GetProperty("lobbyId").GetString();rankedMap=m.GetProperty("map").GetString();}}catch{}
        });
    }
    static void AskBoards(){Call("GetRankedLeaderboard",j=>board1=j,"1v1");Call("GetRankedLeaderboard",j=>boardT=j,"team");}

    // ---------- menu state ----------
    static bool open;
    static int tab;                // 0 Ranked, 1 Leaderboard, 2 Rank ladder
    static string queue="r1v1";
    static string boardLadder="1v1";
    static int selRow=-1;
    static string note="";static float noteUntil;
    static Vector2 boardScroll;
    static Il2CppSystem.Object esWas;
    static UnityEngine.EventSystems.EventSystem es;
    static PlayTab play;static float nextPlayScan;

    static int Set=>set>=0?set:vanillaSet>=0?vanillaSet:0;
    static string Ladder(string q)=>q=="r1v1"?"1v1":"team";
    static int Level(double rating,int place){if(rating>=2170&&place==1)return 20;if(rating>=2170&&place is 2 or 3)return 19;int lv=1;for(int i=0;i<BandStart.Length;i++)if(Math.Floor(rating)>=BandStart[i])lv=i+1;return lv;}
    static string RankName(int lv,int s)=>s>=2&&s<=3?RuNames[lv-1]:UsNames[lv-1];

    static void Open()
    {
        open=true;tab=0;selRow=-1;nextAsk=nextBoard=-100f;
        es=UnityEngine.EventSystems.EventSystem.current;
        if(es!=null)es.enabled=false;   // the game's menu must not take the clicks meant for this one
        MelonLogger.Msg("FREEDOM_ARROW_RANKED menu opened");
    }
    static void Close(string why)
    {
        if(!open)return;
        open=false;
        if(es!=null&&!es.WasCollected)es.enabled=true;es=null;
        MelonLogger.Msg("FREEDOM_ARROW_RANKED menu closed: "+why);
    }

    // The Play tab's cards are showing: PlayTab active, its buttons visible and the Scenarios sub-tab closed.
    static string why="";
    static bool No(string reason){if(reason!=why){why=reason;MelonLogger.Msg("FREEDOM_ARROW_RANKED card hidden: "+reason);}return false;}
    static bool PlayCards(out Rect last,out float pitch)
    {
        last=default;pitch=0;
        if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name!="Hangar_Scene"){play=null;return No("not the menu scene");}
        if(play==null||play.WasCollected)
        {
            play=null;
            if(Time.unscaledTime<nextPlayScan)return false;
            nextPlayScan=Time.unscaledTime+1f;
            play=UnityEngine.Object.FindObjectOfType<PlayTab>();
            if(play==null)return No("no active PlayTab");
        }
        if(!play.isActiveAndEnabled)return No("PlayTab not active");
        if(play.IsScenarioTabActive)return No("Scenarios sub-tab open");
        var c=play._buttonsContainer;if(c==null||!c.activeInHierarchy)return No("Play buttons hidden");
        // The game's cards: active children of the buttons container (or of its first level, if the cards sit one level deeper), left to right.
        var rects=Cards(c.transform);
        if(rects.Count<2&&c.transform.childCount>0)for(int i=0;i<c.transform.childCount&&rects.Count<2;i++)rects=Cards(c.transform.GetChild(i));
        if(rects.Count<2)return No($"found {rects.Count} card rects under {c.name} ({c.transform.childCount} children)");
        rects.Sort((a,b)=>a.x.CompareTo(b.x));
        last=rects[^1];pitch=rects[^1].x-rects[^2].x;
        if(!(last.width>20f&&pitch>last.width*0.5f))return No($"odd card layout: last {last}, pitch {pitch}");
        if(why!="shown"){why="shown";MelonLogger.Msg($"FREEDOM_ARROW_RANKED cards: {string.Join(" ",rects)}");}
        return true;
    }
    static List<Rect> Cards(Transform t)
    {
        var l=new List<Rect>();
        for(int i=0;i<t.childCount;i++)
        {
            var ch=t.GetChild(i);if(!ch.gameObject.activeInHierarchy)continue;
            var rt=ch.GetComponent<RectTransform>();if(rt==null)continue;
            var r=ScreenRect(rt);if(r.width>20f&&r.height>20f)l.Add(r);
        }
        return l;
    }
    static Rect ScreenRect(RectTransform rt)
    {
        var corners=new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppStructArray<Vector3>(4);
        rt.GetWorldCorners(corners);
        var canvas=rt.GetComponentInParent<Canvas>();
        Camera cam=canvas!=null&&canvas.rootCanvas.renderMode!=RenderMode.ScreenSpaceOverlay?canvas.rootCanvas.worldCamera:null;
        var a=RectTransformUtility.WorldToScreenPoint(cam,corners[0]);var b=RectTransformUtility.WorldToScreenPoint(cam,corners[2]);
        return new Rect(a.x,Screen.height-b.y,b.x-a.x,b.y-a.y);
    }

    public static void Tick()
    {
        if(open&&(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name!="Hangar_Scene"))Close("menu scene left");
        if(open)try{if(pInLobby.GetValue(null) is true)Close("joined a lobby");}catch{}
    }

    static bool loggedCard;
    public static void OnGUI()
    {
        try
        {
            if(open){Menu();return;}
            if(card==null||!PlayCards(out var last,out var pitch))return;
            var r=new Rect(last.x+pitch,last.y,last.width,last.height);
            if(!loggedCard){loggedCard=true;MelonLogger.Msg($"FREEDOM_ARROW_RANKED card at {r} (last game card {last}, screen {Screen.width}x{Screen.height})");}
            GUI.DrawTexture(r,card,ScaleMode.ScaleAndCrop);
            var e=Event.current;
            if(r.Contains(e.mousePosition)){Fill(r,new Color(1,1,1,0.10f));Fill(new Rect(r.x,r.yMax-4,r.width,4),Red);}
            if(GUI.Button(r,GUIContent.none,GUIStyle.none))Open();
        }
        catch(Exception ex){MelonLogger.Warning("FREEDOM_ARROW_RANKED: "+ex.Message);Close("error");play=null;}
    }

    // ---------- drawing ----------
    static readonly Color Red=new(0.886f,0.212f,0.243f),Green=new(0.42f,0.8f,0.38f),Dim=new(0.75f,0.75f,0.75f),Panel=new(0,0,0,0.45f);
    static float S,X0;   // scale (design height 900) and left offset (design width 1600, centred)
    static Rect R(float x,float y,float w,float h)=>new(X0+x*S,y*S,w*S,h*S);
    static void Fill(Rect r,Color c){var o=GUI.color;GUI.color=c;GUI.DrawTexture(r,Texture2D.whiteTexture);GUI.color=o;}
    static GUIStyle St(int size,Color c,FontStyle f=FontStyle.Normal,TextAnchor a=TextAnchor.MiddleLeft)
    {
        var s=new GUIStyle(GUI.skin.label){fontSize=Mathf.Max(8,Mathf.RoundToInt(size*S)),fontStyle=f,alignment=a,wordWrap=true,richText=false};
        s.normal.textColor=c;return s;
    }
    static void T(float x,float y,float w,float h,string s,int size,Color c,FontStyle f=FontStyle.Normal,TextAnchor a=TextAnchor.MiddleLeft)=>GUI.Label(R(x,y,w,h),s,St(size,c,f,a));
    static bool Btn(float x,float y,float w,float h,string label,bool on,int size=17,Color? fill=null)
    {
        var r=R(x,y,w,h);bool hover=r.Contains(Event.current.mousePosition);
        Fill(r,fill??(on?new Color(0.45f,0.08f,0.1f,0.9f):new Color(0,0,0,hover?0.75f:0.55f)));
        if(on||hover){Fill(new Rect(r.x,r.y,r.width,1),on?Red:Dim);Fill(new Rect(r.x,r.yMax-1,r.width,1),on?Red:Dim);Fill(new Rect(r.x,r.y,1,r.height),on?Red:Dim);Fill(new Rect(r.xMax-1,r.y,1,r.height),on?Red:Dim);}
        GUI.Label(r,label,St(size,Color.white,FontStyle.Bold,TextAnchor.MiddleCenter));
        return GUI.Button(r,GUIContent.none,GUIStyle.none);
    }
    // Epaulets: UserData/FreedomArrow/ranked/ep/<Epaulet_...>_<rank>.png (the game's own 72x128 icons, exported once). Drawing the game's
    // atlas sprites directly (GUI.DrawTextureWithTexCoords on Sprite.texture) is the likely reason the game closed right after the first sprite lookup (Vengeance 22 Nov 09:09).
    static readonly Dictionary<string,Texture2D> eps=new();
    static Texture2D Ep(int s,int lv)
    {
        if(s<0||s>3)return null;
        var name=SetPrefix[s]+lv;
        if(!eps.TryGetValue(name,out var t)){t=Load(Path.Combine(dir,"ep",name+".png"),"FA_ranked_"+name);eps[name]=t;if(t==null)MelonLogger.Warning("FREEDOM_ARROW_RANKED missing epaulet "+name);}
        return t;
    }
    static void DrawEp(Rect r,int s,int lv)
    {
        var t=Ep(s,lv);
        if(t==null){if(s==4)GUI.Label(r,"★",St(18,new Color(1f,0.8f,0.2f),FontStyle.Bold,TextAnchor.MiddleCenter));return;}
        GUI.DrawTexture(r,t,ScaleMode.ScaleToFit);
    }

    static void Menu()
    {
        S=Screen.height/900f;X0=(Screen.width-1600*S)/2f;
        var now=Time.unscaledTime;
        if(now>=nextAsk){nextAsk=now+5f;Ask();}
        if(tab==1&&now>=nextBoard){nextBoard=now+30f;AskBoards();}
        Fill(new Rect(0,0,Screen.width,Screen.height),new Color(0.02f,0.03f,0.04f,0.97f));
        var e=Event.current;
        if(e.type==EventType.KeyDown&&e.keyCode==KeyCode.Escape){Close("Esc");e.Use();return;}
        string[] tabs={"Ranked","Leaderboard","Rank ladder"};
        float tx=58;
        for(int i=0;i<3;i++)
        {
            var w=i==0?150:i==1?230:215;
            T(tx,18,w,52,tabs[i],34,i==tab?Color.white:Dim,i==tab?FontStyle.Bold:FontStyle.Normal);
            Fill(R(tx,72,w-25,i==tab?4:2),i==tab?Color.white:new Color(1,1,1,0.25f));
            if(GUI.Button(R(tx,18,w,58),GUIContent.none,GUIStyle.none)){tab=i;selRow=-1;nextBoard=-100f;}
            tx+=w+20;
        }
        if(TestHub)T(1180,22,380,24,"TEST SERVER · ratings here are test ratings",13,new Color(1f,0.75f,0.3f),FontStyle.Bold,TextAnchor.MiddleRight);
        JsonElement me=default;bool haveMe=false;
        try{if(meJson.Length>0){me=JsonDocument.Parse(meJson).RootElement;haveMe=true;}}catch{}
        if(tab==0)RankedTab(me,haveMe,now);else if(tab==1)BoardTab(me,haveMe);else LadderTab();
        if(error.Length>0)T(58,820,900,24,error,14,new Color(1f,0.55f,0.5f));
        if(Btn(740,850,120,36,"BACK",false,16))Close("Back");
        T(560,880,480,18,"Freedom Arrow ranked · Esc to go back",12,Dim,FontStyle.Normal,TextAnchor.MiddleCenter);
        if(!drawnOnce&&e.type==EventType.Repaint){drawnOnce=true;MelonLogger.Msg($"FREEDOM_ARROW_RANKED menu drawn (tab {tab}, {Screen.width}x{Screen.height})");}
    }
    static bool drawnOnce;

    static (double rating,int level,int place,int wins,int losses,double best,JsonElement recent) Mine(JsonElement me,bool have,string ladder)
    {
        if(!have)return (1000,1,0,0,0,1000,default);
        try
        {
            var l=me.GetProperty("me").GetProperty(ladder);
            return (l.GetProperty("rating").GetDouble(),l.GetProperty("level").GetInt32(),l.GetProperty("place").GetInt32(),l.GetProperty("wins").GetInt32(),l.GetProperty("losses").GetInt32(),
                l.GetProperty("best").GetDouble(),l.TryGetProperty("recent",out var r)?r:default);
        }
        catch{return (1000,1,0,0,0,1000,default);}
    }

    static void RankedTab(JsonElement me,bool have,float now)
    {
        // left: find a match
        T(58,110,470,30,"FIND A RANKED MATCH",17,Color.white,FontStyle.Bold);
        bool active=false;string state="";
        try{active=pActive.GetValue(null) is true;var v=pCurrent.GetValue(null);if(v!=null)state=Traverse.Create(v).Property("state").GetValue<string>()??"";}catch{}
        if(Btn(58,150,230,46,"1v1",queue=="r1v1")&&!active)queue="r1v1";
        if(Btn(298,150,230,46,"Team · 3v3 / 5v5",queue=="rteam")&&!active)queue="rteam";
        T(58,204,470,40,queue=="r1v1"?"Solo only. Its own ladder.":"Solo or with your party. You get a 3v3 or a 5v5, never a 1v1. A party of 4-5 plays 5v5.",13,Dim);
        T(58,246,90,44,"Map pool",15,Dim);T(150,246,378,56,Pools[queue],14,Color.white);
        Fill(R(58,306,470,1),new Color(1,1,1,0.12f));
        T(58,310,140,32,"Rules",15,Dim);T(200,310,328,32,"Freedom Arrow "+Runtime.DiagnosticPackageVersion+" · conquest 300",14,Color.white,FontStyle.Normal,TextAnchor.MiddleRight);
        Fill(R(58,344,470,1),new Color(1,1,1,0.12f));
        T(58,348,140,32,"Map",15,Dim);T(200,348,328,32,"picked by the server",14,Color.white,FontStyle.Normal,TextAnchor.MiddleRight);
        int party=1;string leader="";
        try{var pr=fPartyNews?.GetValue(null);var pv=pr==null?null:Traverse.Create(pr).Property("party").GetValue();if(pv!=null){party=Math.Max(1,(Traverse.Create(pv).Property("members").GetValue() as Array)?.Length??1);leader=Traverse.Create(pv).Property("leader").GetValue<string>()??"";}}catch{}
        if(party>1){Fill(R(58,382,470,1),new Color(1,1,1,0.12f));T(58,386,470,30,$"Party of {party}"+(leader==MySteam()?" · you lead":" · the leader starts the search"),14,new Color(0.6f,0.85f,1f));}
        if(active)
        {
            if(Btn(58,430,470,64,"SEARCHING… CANCEL",true,24,new Color(0.3f,0.3f,0.3f,0.9f))){try{mStop.Invoke(null,new object[]{true,false});}catch(Exception ex){error=ex.Message;}}
            T(58,498,470,24,"Status: "+(state.Length>0?state:"searching"),13,Dim,FontStyle.Normal,TextAnchor.MiddleCenter);
        }
        else if(Btn(58,430,470,64,"FIND MATCH",false,26,Red))Find(party,leader,now);
        int searching=0;
        try{if(have)searching=me.GetProperty("searching").GetProperty(queue).GetInt32();}catch{}
        T(58,520,470,24,$"{searching} players searching {(queue=="r1v1"?"1v1":"team games")}",13,Dim,FontStyle.Normal,TextAnchor.MiddleCenter);
        if(now<noteUntil)T(58,546,470,44,note,13,new Color(1f,0.75f,0.3f),FontStyle.Normal,TextAnchor.MiddleCenter);

        // middle: your rank
        var lad=Ladder(queue);var m=Mine(me,have,lad);int s=Set;
        int season=1;try{if(have)season=me.GetProperty("season").GetInt32();}catch{}
        T(590,110,440,30,$"YOUR RANK · {(lad=="1v1"?"1V1":"TEAM")} · SEASON {season}",17,Color.white,FontStyle.Bold);
        Fill(R(590,150,440,190),Panel);
        DrawEp(R(605,160,100,170),s,m.level);
        T(720,175,300,46,RankName(m.level,s),32,Color.white,FontStyle.Bold);
        T(720,222,300,32,$"Elo {m.rating:0}",22,Green);
        T(720,258,300,40,$"Rank {m.level} of 20"+(m.place>0?$" · {Ord(m.place)} on the leaderboard":" · not placed yet (play a match)"),13,Dim);
        int nextLv=Math.Min(18,m.level+1);double from=BandStart[Math.Min(17,m.level-1)],to=m.level>=18?from:BandStart[nextLv-1];
        float frac=m.level>=18?1f:(float)Math.Clamp((m.rating-from)/Math.Max(1,to-from),0,1);
        Fill(R(590,352,440,8),new Color(1,1,1,0.15f));Fill(R(590,352,440*frac,8),Color.white);
        T(590,364,220,22,$"{RankName(m.level,s)} {from:0}",12,Dim);
        T(810,364,220,22,m.level>=18?"top band":$"{to-m.rating:0} to {RankName(nextLv,s)} ({to:0})",12,Dim,FontStyle.Normal,TextAnchor.MiddleRight);
        int games=m.wins+m.losses;
        Stat(590,398,"Ranked matches",games.ToString());Stat(740,398,"Win rate",games>0?$"{100.0*m.wins/games:0}%":"-");Stat(890,398,"Best Elo",$"{m.best:0}");
        // epaulet set picker
        for(int i=0;i<5;i++)
        {
            var r=R(590+i*89,480,82,90);bool on=i==s;
            Fill(r,new Color(0,0,0,on?0.7f:0.45f));
            if(on){Fill(new Rect(r.x,r.y,r.width,2),Green);Fill(new Rect(r.x,r.yMax-2,r.width,2),Green);}
            DrawEp(new Rect(r.x+r.width*0.3f,r.y+6*S,r.width*0.4f,50*S),i,Math.Max(1,m.level));
            GUI.Label(new Rect(r.x,r.yMax-30*S,r.width,26*S),SetNames[i]+(i==4?" (soon)":""),St(11,i==4?Dim:Color.white,FontStyle.Normal,TextAnchor.MiddleCenter));
            if(i<4&&GUI.Button(r,GUIContent.none,GUIStyle.none)){set=i;SaveSettings();MelonLogger.Msg("FREEDOM_ARROW_RANKED set "+SetNames[i]);}
        }
        T(590,574,440,40,(set<0?$"Following your vanilla epaulet ({SetNames[s]}). ":"")+"The set only changes how your rank looks.",12,Dim);

        // right: recent matches
        T(1090,110,460,30,"RECENT RANKED MATCHES",17,Color.white,FontStyle.Bold);
        int row=0;
        if(m.recent.ValueKind==JsonValueKind.Array)
            foreach(var x in m.recent.EnumerateArray())
            {
                if(row>=8)break;
                float y=150+row*40;bool win=x.GetProperty("win").GetBoolean();var ch=x.GetProperty("change").GetDouble();
                T(1095,y,24,36,win?"W":"L",16,win?Green:Red,FontStyle.Bold);
                T(1125,y,300,36,$"[{x.GetProperty("format").GetString()}] {x.GetProperty("map").GetString()} · vs {x.GetProperty("vs").GetString()}",14,Color.white);
                T(1425,y,120,36,(ch>=0?"+":"−")+Math.Abs(ch).ToString("0.0"),15,ch>=0?Green:Red,FontStyle.Bold,TextAnchor.MiddleRight);
                Fill(R(1090,y+38,455,1),new Color(1,1,1,0.1f));
                row++;
            }
        if(row==0)T(1095,150,450,36,"No ranked matches yet this season.",14,Dim);
        T(1090,160+Math.Max(row,1)*40,460,44,"A result counts only when both sides' game reports agree. A leaver loses.",12,Dim);

        // bottom: ladder strip
        T(58,640,1000,30,$"RANK LADDER ({SetNames[s].ToUpperInvariant()} SET) · ELO WHERE EACH RANK STARTS",17,Color.white,FontStyle.Bold);
        for(int i=0;i<20;i++)
        {
            float x=58+i*74.5f;bool cur=i+1==m.level;
            if(cur)Fill(R(x-4,676,70,92),new Color(0.42f,0.8f,0.38f,0.18f));
            DrawEp(R(x+12,680,40,62),s,i+1);
            T(x-4,746,70,20,i<18?BandStart[i].ToString():i==18?"#2-3":"#1",12,cur?Green:Dim,cur?FontStyle.Bold:FontStyle.Normal,TextAnchor.MiddleCenter);
        }
    }
    static void Stat(float x,float y,string label,string val){Fill(R(x,y,140,62),Panel);T(x+10,y+4,130,30,val,20,Color.white,FontStyle.Bold);T(x+10,y+34,130,22,label,12,Dim);}
    static string Ord(int n)=>n+(n%100 is 11 or 12 or 13?"th":(n%10) switch{1=>"st",2=>"nd",3=>"rd",_=>"th"});

    static void Find(int party,string leader,float now)
    {
        if(queue=="r1v1"&&party>1){note="1v1 is solo only. Leave the party, or pick Team.";noteUntil=now+6f;return;}
        if(party>1&&leader!=MySteam()){note="The party leader starts the search; you go along.";noteUntil=now+6f;return;}
        try
        {
            var args=new object[]{now,null};
            if(mCanStart.Invoke(null,args) is not true){note="ArrowQueue refused the search (see its message at the top).";noteUntil=now+6f;return;}
            mBegin.Invoke(null,new object[]{(string)args[1],now,null,queue});
            MelonLogger.Msg($"FREEDOM_ARROW_RANKED search {queue} (party {party})");
            note="Searching. The lobby opens by itself when a match is found.";noteUntil=now+8f;
        }
        catch(Exception e){error="Search failed: "+(e.InnerException?.Message??e.Message);}
    }

    static void BoardTab(JsonElement me,bool have)
    {
        if(Btn(58,100,140,36,"1v1",boardLadder=="1v1",15)){boardLadder="1v1";selRow=-1;}
        if(Btn(206,100,140,36,"Team",boardLadder=="team",15)){boardLadder="team";selRow=-1;}
        var json=boardLadder=="1v1"?board1:boardT;
        var mine=Mine(me,have,boardLadder);int s=Set;
        T(360,100,170,36,mine.place>0?$"YOU · {Ord(mine.place)}":"YOU · not placed",13,Green,FontStyle.Bold,TextAnchor.MiddleRight);
        if(json.Length==0){T(58,150,470,30,"Loading…",14,Dim);return;}
        JsonElement b;try{b=JsonDocument.Parse(json).RootElement;}catch{return;}
        var rows=b.GetProperty("rows");int n=rows.GetArrayLength();
        T(58,138,470,22,$"{b.GetProperty("players").GetInt32()} rated players · season {b.GetProperty("season").GetInt32()} · updates every 30 s",12,Dim);
        if(n==0){T(58,170,470,30,"Nobody is rated yet. Win a ranked match to be first.",14,Dim);return;}
        var view=R(58,166,470,620);var content=new Rect(0,0,view.width-16*S,n*42*S);
        boardScroll=GUI.BeginScrollView(view,boardScroll,content);
        float sx=X0;X0=0;var y0=0f;
        int i=0;
        foreach(var r in rows.EnumerateArray())
        {
            var rr=new Rect(0,y0+i*42*S,content.width,40*S);
            bool me2=r.GetProperty("steamId").GetString()==MySteam();
            Fill(rr,i==selRow?new Color(1,1,1,0.18f):me2?new Color(0.42f,0.8f,0.38f,0.15f):new Color(0,0,0,0.45f));
            var name=r.GetProperty("name").GetString()??"?";
            Fill(new Rect(rr.x,rr.y,36*S,rr.height),new Color(0.35f,0.4f,0.45f,0.8f));
            GUI.Label(new Rect(rr.x,rr.y,36*S,rr.height),name.Length>0?name[..1].ToUpperInvariant():"?",St(15,Color.white,FontStyle.Bold,TextAnchor.MiddleCenter));
            GUI.Label(new Rect(rr.x+44*S,rr.y,260*S,rr.height),name,St(15,Color.white,FontStyle.Bold));
            GUI.Label(new Rect(rr.x+300*S,rr.y,70*S,rr.height),r.GetProperty("rating").GetDouble().ToString("0"),St(13,Dim,FontStyle.Normal,TextAnchor.MiddleRight));
            DrawEp(new Rect(rr.x+382*S,rr.y+3*S,30*S,rr.height-6*S),s,r.GetProperty("level").GetInt32());   // the epaulet replaces #1, #2, #3
            if(GUI.Button(rr,GUIContent.none,GUIStyle.none))selRow=i;
            i++;
        }
        X0=sx;
        GUI.EndScrollView();
        Fill(R(548,110,1,680),new Color(1,1,1,0.12f));
        T(580,100,400,30,"PROFILE",17,Color.white,FontStyle.Bold);
        JsonElement p=default;bool sel=false;
        if(selRow>=0&&selRow<n){p=rows[selRow];sel=true;}
        else foreach(var r in rows.EnumerateArray())if(r.GetProperty("steamId").GetString()==MySteam()){p=r;sel=true;break;}
        if(!sel){T(580,140,600,30,"Pick a player on the left.",14,Dim);return;}
        int lv=p.GetProperty("level").GetInt32();double rating=p.GetProperty("rating").GetDouble();int w=p.GetProperty("wins").GetInt32(),l=p.GetProperty("losses").GetInt32();
        DrawEp(R(590,145,100,170),s,lv);
        T(705,160,600,46,p.GetProperty("name").GetString()??"?",32,Color.white,FontStyle.Bold);
        T(705,208,600,30,$"{RankName(lv,s)} · Elo {rating:0}",20,Green);
        T(705,240,700,26,$"{Ord(p.GetProperty("place").GetInt32())} on the {(boardLadder=="1v1"?"1v1":"team")} ladder · shown in your {SetNames[s]} set",13,Dim);
        T(580,340,600,30,"RANKED STATISTICS · SEASON "+b.GetProperty("season").GetInt32(),17,Color.white,FontStyle.Bold);
        Stat(580,380,"Ranked matches",(w+l).ToString());Stat(730,380,"Wins",w.ToString());Stat(880,380,"Win rate",w+l>0?$"{100.0*w/(w+l):0}%":"-");
        T(580,760,960,40,"Instead of #1, #2, #3 every row shows the player's rank epaulet. Place 1 wears rank 20, places 2-3 rank 19 (only at 2170 Elo or more); everyone else wears the rank of their Elo band.",12,Dim);
    }

    static void LadderTab()
    {
        int s=Set;
        T(58,100,1000,30,"RANKS AND THE ELO WHERE EACH STARTS · "+SetNames[s].ToUpperInvariant()+" SET",17,Color.white,FontStyle.Bold);
        for(int i=0;i<20;i++)
        {
            int col=i/10,rowi=i%10;float x=58+col*760,y=145+rowi*66;
            Fill(R(x,y,720,60),Panel);
            DrawEp(R(x+10,y+4,30,52),s,i+1);
            T(x+60,y,60,60,(i+1).ToString(),18,Dim,FontStyle.Bold);
            T(x+110,y,380,60,RankName(i+1,s),18,Color.white,FontStyle.Bold);
            T(x+480,y,230,60,i<17?$"{BandStart[i]}–{BandStart[i+1]-1}":i==17?"2170 and above":i==18?"2170+ and places 2-3":"2170+ and place 1",15,Green,FontStyle.Normal,TextAnchor.MiddleRight);
        }
        T(58,815,1500,24,"New players start at 1000 (rank 1). Win against stronger teams to climb faster; a loss never takes you below 600.",13,Dim);
    }
}
