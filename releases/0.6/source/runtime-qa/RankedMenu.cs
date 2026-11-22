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
    static Texture2D card,patch;
    static int set=-1;              // chosen set; -1 = follow the vanilla pick
    static int vanillaSet=-1;       // from the game's profile epaulet
    static string mySteam="";

    // ArrowQueue (reflection; it is a separate unchanged mod)
    static Type tFlow,tUi,tApi,tGame,tSignal;
    static MethodInfo mBegin,mCanStart,mStop,mPicked,mSupported;
    static PropertyInfo pActive,pCurrent,pMySteam,pInLobby;
    static FieldInfo fLink,fPartyNews,fPartyCurrent,fIncoming,fOnline,fOnlineList;
    static MethodInfo mInvite,mAccept,mDecline,mLeave,mKick;

    public static void Install(HarmonyLib.Harmony h)
    {
        dir=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","ranked");
        settingsFile=Path.Combine(dir,"settings.json");
        card=Load(Path.Combine(dir,"card.png"),"FA_ranked_card");patch=Load(Path.Combine(dir,"patch.png"),"FA_ranked_patch");
        try{var s=JsonDocument.Parse(File.ReadAllText(settingsFile)).RootElement;if(s.TryGetProperty("set",out var v))set=Array.IndexOf(SetNames,v.GetString());}catch{}
        tFlow=AccessTools.TypeByName("ArrowQueue.Flow");tUi=AccessTools.TypeByName("ArrowQueue.Ui");tApi=AccessTools.TypeByName("ArrowQueue.Api");
        tGame=AccessTools.TypeByName("ArrowQueue.Game");tSignal=AccessTools.TypeByName("ArrowQueue.Signal");
        if(tFlow==null||tUi==null||tApi==null||tGame==null||tSignal==null)throw new InvalidOperationException("ArrowQueue types not found");
        mBegin=AccessTools.Method(tFlow,"Begin");mPicked=AccessTools.Method(tFlow,"Picked");mCanStart=AccessTools.Method(tUi,"CanStart");
        mStop=AccessTools.Method(tApi,"Stop");mSupported=AccessTools.Method(tGame,"SupportedScenarios");
        pActive=AccessTools.Property(tApi,"Active");pCurrent=AccessTools.Property(tApi,"Current");
        pMySteam=AccessTools.Property(tGame,"MySteamId");pInLobby=AccessTools.Property(tGame,"InLobby");
        fLink=AccessTools.Field(tSignal,"_link");fPartyNews=AccessTools.Field(tApi,"PartyNews");
        var tParty=AccessTools.TypeByName("ArrowQueue.Party");   // ArrowQueue's own party calls (invite, accept, decline, leave, kick)
        fPartyCurrent=AccessTools.Field(tParty,"Current");fIncoming=AccessTools.Field(tParty,"Incoming");
        fOnline=AccessTools.Field(tApi,"Online");fOnlineList=AccessTools.Field(tApi,"OnlineList");
        mInvite=AccessTools.Method(tParty,"Invite");mAccept=AccessTools.Method(tParty,"Accept");mDecline=AccessTools.Method(tParty,"Decline");
        mLeave=AccessTools.Method(tParty,"Leave");mKick=AccessTools.Method(tParty,"Kick");
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
    static int boardTop;
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
        // The Play tab's own button must be selected: Campaign and other sub-screens keep PlayTab active (card was drawn over the
        // Campaign map on Vengeance 22 Nov 09:31), but hide the top tabs.
        if(!PlaySelected())return No("Play tab button not selected");
        if(play.IsScenarioTabActive)return No("Scenarios sub-tab open");
        var c=play._buttonsContainer;if(c==null||!c.activeInHierarchy)return No("Play buttons hidden");
        // The game's cards: active children of the buttons container (or of its first level, if the cards sit one level deeper), left to right.
        var rects=Cards(c.transform);
        if(rects.Count<2&&c.transform.childCount>0)for(int i=0;i<c.transform.childCount&&rects.Count<2;i++)rects=Cards(c.transform.GetChild(i));
        if(rects.Count<2)return No($"found {rects.Count} card rects under {c.name} ({c.transform.childCount} children)");
        rects.Sort((a,b)=>a.x.CompareTo(b.x));
        // Vanilla cards grow in place on hover (Lateralus 22 Nov: hovering Multiplayer pushed the Ranked card right; hovering
        // Skirmish grew both). The card is placed from the cards' rest layout (all the same width), kept per screen size;
        // a hovered vanilla card gives the hover scale and anchor that the Ranked card copies.
        bool rest=rects.All(r=>Math.Abs(r.width-rects[0].width)<1f);
        int key=Screen.width*100000+Screen.height;
        if(rest){baseCards=rects;baseKey=key;}
        else if(baseCards!=null&&baseKey==key&&baseCards.Count==rects.Count)
            for(int i=0;i<rects.Count;i++)
            {
                var b0=baseCards[i];var h0=rects[i];float gi=h0.width/b0.width;
                if(gi<=measured+0.004f)continue;   // the hover grows over a few frames: keep the largest size seen
                measured=gi;grow=gi;
                growAx=Mathf.Clamp01((b0.x-h0.x)/Math.Max(1f,h0.width-b0.width));
                growAy=Mathf.Clamp01((b0.y-h0.y)/Math.Max(1f,h0.height-b0.height));
                if(gi>=loggedGrow+0.02f){loggedGrow=gi;MelonLogger.Msg($"FREEDOM_ARROW_RANKED vanilla hover: x{grow:0.000}, anchor {growAx:0.00},{growAy:0.00} ({b0} -> {h0})");}
            }
        var use=baseCards!=null&&baseKey==key&&baseCards.Count==rects.Count?baseCards:rects;
        last=use[^1];pitch=use[^1].x-use[^2].x;
        if(!(last.width>20f&&pitch>last.width*0.5f))return No($"odd card layout: last {last}, pitch {pitch}");
        if(why!="shown"){why="shown";MelonLogger.Msg($"FREEDOM_ARROW_RANKED cards: {string.Join(" ",rects)}");}
        return true;
    }
    static List<Rect> baseCards;static int baseKey;
    // Default from a Vengeance screenshot (Multiplayer card 245 -> 269 px wide when hovered); replaced by the measured vanilla hover.
    static float grow=1.098f,growAx=0.5f,growAy=0.4f,hoverT,measured=1f,loggedGrow=1f;
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
    static MainMenuButton playButton;static float nextButtonScan;
    static bool PlaySelected()
    {
        if(playButton==null||playButton.WasCollected)
        {
            playButton=null;
            if(Time.unscaledTime<nextButtonScan)return false;
            nextButtonScan=Time.unscaledTime+2f;
            foreach(var b in Resources.FindObjectsOfTypeAll<MainMenuButton>())
                if(b.gameObject.scene.IsValid()&&b._buttonText!=null&&b._buttonText.text.Trim().Equals("Play",StringComparison.OrdinalIgnoreCase)){playButton=b;break;}
            if(playButton==null)return false;
        }
        return playButton.isActiveAndEnabled&&playButton.Selected;
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
            var e=Event.current;
            bool hover=r.Contains(e.mousePosition);
            if(e.type==EventType.Repaint)hoverT=Mathf.MoveTowards(hoverT,hover?1f:0f,Time.unscaledDeltaTime*8f);
            float g=1f+(grow-1f)*hoverT;   // grow like the vanilla cards, with their measured anchor
            var d=new Rect(r.x-(r.width*(g-1f))*growAx,r.y-(r.height*(g-1f))*growAy,r.width*g,r.height*g);
            GUI.DrawTexture(d,card,ScaleMode.StretchToFill);
            if(hover)Fill(new Rect(d.x,d.yMax-4*S0(),d.width,4*S0()),Red);
            if(GUI.Button(r,GUIContent.none,GUIStyle.none))Open();
        }
        catch(Exception ex){MelonLogger.Warning("FREEDOM_ARROW_RANKED: "+ex.Message);Close("error");play=null;}
    }

    // ---------- drawing ----------
    static readonly Color Red=new(0.886f,0.212f,0.243f),Green=new(0.42f,0.8f,0.38f),Dim=new(0.75f,0.75f,0.75f),Panel=new(0,0,0,0.45f);
    static float S,X0;   // scale (design height 900) and left offset (design width 1600, centred)
    static float S0()=>Screen.height/1080f;
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
        if(e.type==EventType.KeyDown&&e.keyCode==KeyCode.Escape){if(picking)picking=false;else Close("Esc");e.Use();return;}
        if(picking){InvitePicker(now);return;}   // modal: nothing under it takes clicks
        // Two tabs (Lateralus 22 Nov: "Leaderboard and Rank Ladder are redundant"); the leaderboard has 1v1 and Team sub-menus.
        string[] tabs={"Ranked","Leaderboard"};float[] tw={152,232};
        float tx=58;
        for(int i=0;i<2;i++)
        {
            bool on=i==tab;
            T(tx,14,tw[i],56,tabs[i],34,on?Color.white:Dim,on?FontStyle.Bold:FontStyle.Normal);
            Fill(R(tx,72,tw[i]-26,on?3:2),on?Color.white:new Color(1,1,1,0.28f));
            if(GUI.Button(R(tx,14,tw[i],62),GUIContent.none,GUIStyle.none)){tab=i;selRow=-1;nextBoard=-100f;}
            tx+=tw[i]+20;
        }
        if(TestHub)T(1180,26,380,24,"TEST SERVER · ratings here are test ratings",13,new Color(1f,0.75f,0.3f),FontStyle.Bold,TextAnchor.MiddleRight);
        JsonElement me=default;bool haveMe=false;
        try{if(meJson.Length>0){me=JsonDocument.Parse(meJson).RootElement;haveMe=true;}}catch{}
        if(tab==0)RankedTab(me,haveMe,now);else BoardTab(me,haveMe);
        if(error.Length>0)T(58,806,900,24,error,14,new Color(1f,0.55f,0.5f));
        // esc BACK, as in the mock-up
        var back=R(756,846,110,30);bool hb=back.Contains(e.mousePosition);
        Frame(R(760,853,28,19),hb?Color.white:Dim,1);T(760,853,28,19,"esc",11,hb?Color.white:Dim,FontStyle.Normal,TextAnchor.MiddleCenter);
        T(794,846,80,30,"BACK",18,hb?Color.white:new Color(0.92f,0.92f,0.92f),FontStyle.Bold);
        if(GUI.Button(back,GUIContent.none,GUIStyle.none))Close("Back");
        T(560,874,480,20,"Freedom Arrow "+Runtime.DiagnosticPackageVersion,13,Dim,FontStyle.Normal,TextAnchor.MiddleCenter);
        if(!drawnOnce&&e.type==EventType.Repaint){drawnOnce=true;MelonLogger.Msg($"FREEDOM_ARROW_RANKED menu drawn (tab {tab}, {Screen.width}x{Screen.height})");}
    }
    static bool drawnOnce;
    static readonly Color Line=new(1,1,1,0.10f),Box=new(0,0,0,0.42f);
    static void Frame(Rect r,Color c,float t){t=Mathf.Max(1f,t*S);Fill(new Rect(r.x,r.y,r.width,t),c);Fill(new Rect(r.x,r.yMax-t,r.width,t),c);Fill(new Rect(r.x,r.y,t,r.height),c);Fill(new Rect(r.xMax-t,r.y,t,r.height),c);}
    static void H(float x,float y,float w,string s)=>T(x,y,w,30,s,17,Color.white,FontStyle.Bold);
    static bool Choice(float x,float y,float w,float h,string label,bool on,int size=17)
    {
        var r=R(x,y,w,h);bool hover=r.Contains(Event.current.mousePosition);
        Fill(r,on?new Color(0.36f,0.06f,0.08f,0.95f):new Color(0,0,0,hover?0.8f:0.6f));
        Frame(r,on?Red:hover?new Color(1,1,1,0.45f):new Color(1,1,1,0.18f),1);
        GUI.Label(r,label,St(size,Color.white,on?FontStyle.Bold:FontStyle.Normal,TextAnchor.MiddleCenter));
        return GUI.Button(r,GUIContent.none,GUIStyle.none);
    }
    static void Row(float y,float h,string label,string value)
    {
        T(58,y,150,h,label,15,Dim);T(200,y,328,h,value,14,Color.white,FontStyle.Normal,TextAnchor.MiddleRight);
        Fill(R(58,y+h,470,1),Line);
    }
    static (int lv,double from,double to,int next) Band(double rating,int lv)
    {
        int b=Math.Min(18,lv);double from=BandStart[b-1];
        return lv>=18?(lv,2170,2170,lv):(lv,from,BandStart[b],b+1);
    }
    static string Ago(JsonElement t){try{var d=DateTime.UtcNow-t.GetDateTime().ToUniversalTime();return d.TotalMinutes<60?$"{(int)d.TotalMinutes}m":d.TotalHours<24?$"{(int)d.TotalHours}h":$"{(int)d.TotalDays}d";}catch{return "";}}

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
        // left: find a match (mock-up docs/ranked/mock-2-ranked-menu.jpg)
        H(58,116,470,"FIND A RANKED MATCH");
        bool active=false;
        try{active=pActive.GetValue(null) is true;}catch{}
        if(Choice(58,156,230,42,"1v1",queue=="r1v1")&&!active)queue="r1v1";
        if(Choice(298,156,230,42,"Team · 3v3 / 5v5",queue=="rteam")&&!active)queue="rteam";
        Row(212,36,"Queue",queue=="r1v1"?"Solo only · 1v1 ladder":"Solo or party · 3v3 or 5v5 · team ladder");
        T(58,250,90,48,"Map pool",15,Dim);T(150,250,378,48,Pools[queue],14,Color.white,FontStyle.Normal,TextAnchor.MiddleRight);Fill(R(58,298,470,1),Line);
        Row(300,36,"Rules","FA "+Runtime.DiagnosticPackageVersion+" · conquest 300");
        Row(338,36,"Map","picked by the server");
        int party=1;string leader="";
        try{var pr=fPartyNews?.GetValue(null);var pv=pr==null?null:Traverse.Create(pr).Property("party").GetValue();if(pv!=null){party=Math.Max(1,(Traverse.Create(pv).Property("members").GetValue() as Array)?.Length??1);leader=Traverse.Create(pv).Property("leader").GetValue<string>()??"";}}catch{}
        if(party>1)T(58,374,470,20,$"Party of {party}"+(leader==MySteam()?" · you lead the search":" · the leader starts the search"),13,new Color(0.6f,0.85f,1f));
        // FIND MATCH with the FA patch (Lateralus 22 Nov: "the patch logo on the find match button")
        var fb=R(58,398,470,64);bool hf=fb.Contains(Event.current.mousePosition);
        if(active)
        {
            Fill(fb,new Color(0.22f,0.22f,0.24f,0.95f));Frame(fb,new Color(1,1,1,0.25f),1);
            var secs=(int)Math.Max(0,now-searchFrom);
            GUI.Label(fb,$"SEARCHING  {secs/60}:{secs%60:00}   ·   CANCEL",St(22,Color.white,FontStyle.Bold,TextAnchor.MiddleCenter));
            if(GUI.Button(fb,GUIContent.none,GUIStyle.none)){try{mStop.Invoke(null,new object[]{true,false});MelonLogger.Msg("FREEDOM_ARROW_RANKED search cancelled");}catch(Exception ex){error=ex.Message;}}
        }
        else
        {
            Fill(fb,hf?new Color(0.93f,0.25f,0.28f):Red);Fill(new Rect(fb.x,fb.y,fb.width,fb.height*0.45f),new Color(1,1,1,0.07f));Frame(fb,new Color(1f,0.55f,0.55f,0.6f),1);
            if(patch!=null)GUI.DrawTexture(R(176,409,42,42),patch,ScaleMode.ScaleToFit);
            T(234,398,290,64,"FIND MATCH",28,Color.white,FontStyle.Bold);
            if(GUI.Button(fb,GUIContent.none,GUIStyle.none)){searchFrom=now;Find(party,leader,now);}
        }
        int searching=0;
        try{if(have)searching=me.GetProperty("searching").GetProperty(queue).GetInt32();}catch{}
        T(58,468,470,24,$"{searching} {(searching==1?"player":"players")} searching {(queue=="r1v1"?"1v1":"team games")}",13,Dim,FontStyle.Normal,TextAnchor.MiddleCenter);
        if(now<noteUntil)T(58,494,470,40,note,13,new Color(1f,0.75f,0.3f),FontStyle.Normal,TextAnchor.MiddleCenter);
        if(queue=="rteam")PartyPanel(now);

        // middle: your rank
        var lad=Ladder(queue);var m=Mine(me,have,lad);int s=Set;
        int season=1;try{if(have)season=me.GetProperty("season").GetInt32();}catch{}
        H(590,116,440,$"YOUR RANK · {(lad=="1v1"?"1V1":"TEAM")} · SEASON {season}");
        Fill(R(590,157,440,186),new Color(0,0,0,0.5f));Frame(R(590,157,440,186),new Color(1,1,1,0.08f),1);
        DrawEp(R(608,170,86,160),s,m.level);
        T(716,186,300,48,RankName(m.level,s),32,Color.white,FontStyle.Bold);
        T(716,236,44,30,"Elo",21,Green);T(758,236,200,30,$"{m.rating:0}",21,new Color(0.92f,0.92f,0.92f));
        T(716,272,300,24,$"Rank {m.level} of 20 · "+(m.place>0?$"{Ord(m.place)} on the leaderboard":"not placed yet"),13,Dim);
        var bd=Band(m.rating,m.level);float frac=m.level>=18?1f:(float)Math.Clamp((m.rating-bd.from)/Math.Max(1,bd.to-bd.from),0,1);
        Fill(R(590,360,440,8),new Color(1,1,1,0.15f));Fill(R(590,360,440*frac,8),Color.white);
        T(590,372,220,22,$"{RankName(m.level,s)} {bd.from:0}",13,Dim);
        T(810,372,220,22,m.level>=18?"top band":$"{bd.to-m.rating:0} to {RankName(bd.next,s)} ({bd.to:0})",13,Dim,FontStyle.Normal,TextAnchor.MiddleRight);
        int games=m.wins+m.losses;
        Stat(590,409,"Ranked matches",games.ToString());Stat(740,409,"Win rate",games>0?$"{100.0*m.wins/games:0}%":"-");Stat(890,409,"Best Elo",$"{m.best:0}");
        // epaulet set picker: the chosen set has a green border (mock-up)
        for(int i=0;i<5;i++)
        {
            var r=R(590+i*89.5f,490,82,90);bool on=i==s,hov=r.Contains(Event.current.mousePosition)&&i<4;
            Fill(r,new Color(0,0,0,on?0.62f:hov?0.6f:0.42f));
            Frame(r,on?Green:hov?new Color(1,1,1,0.35f):new Color(1,1,1,0.1f),on?2:1);
            DrawEp(new Rect(r.x+r.width*0.32f,r.y+8*S,r.width*0.36f,50*S),i,Math.Max(1,m.level));
            GUI.Label(new Rect(r.x,r.yMax-28*S,r.width,22*S),SetNames[i]+(i==4?" (soon)":""),St(11,i==4?Dim:Color.white,FontStyle.Normal,TextAnchor.MiddleCenter));
            if(i<4&&GUI.Button(r,GUIContent.none,GUIStyle.none)){set=i;SaveSettings();MelonLogger.Msg("FREEDOM_ARROW_RANKED set "+SetNames[i]);}
        }
        T(590,584,440,36,set<0?$"Following your vanilla epaulet ({SetNames[s]}). The set only changes how your rank looks.":"The epaulet set only changes how your rank looks; the rank is the same.",12,Dim);

        // right: recent matches, opponent epaulet before the name
        H(1090,116,460,"RECENT RANKED MATCHES");
        int row=0;
        if(m.recent.ValueKind==JsonValueKind.Array)
            foreach(var x in m.recent.EnumerateArray())
            {
                if(row>=10)break;
                float y=155+row*39;bool win=x.GetProperty("win").GetBoolean();var ch=x.GetProperty("change").GetDouble();
                double vr=x.TryGetProperty("vsRating",out var v)?v.GetDouble():1000;
                T(1096,y,24,38,win?"W":"L",15,win?Green:Red,FontStyle.Bold);
                T(1140,y,170,38,$"[{x.GetProperty("format").GetString()}] {x.GetProperty("map").GetString()}",14,Color.white);
                T(1306,y,28,38,"vs",13,Dim);
                DrawEp(R(1330,y+8,14,22),s,Level(vr,0));
                T(1350,y,62,38,x.GetProperty("vs").GetString()??"",14,Color.white);
                T(1412,y,40,38,Ago(x.GetProperty("t")),13,Dim,FontStyle.Normal,TextAnchor.MiddleRight);
                T(1462,y,82,38,(ch>=0?"+":"−")+Math.Abs(ch).ToString("0.0"),14,ch>=0?Green:Red,FontStyle.Bold,TextAnchor.MiddleRight);
                Fill(R(1090,y+38,455,1),Line);
                row++;
            }
        if(row==0){T(1096,155,450,38,"No ranked matches yet this season.",14,Dim);Fill(R(1090,193,455,1),Line);}
        T(1090,166+Math.Max(row,1)*39,460,24,"A result counts only when both sides' game reports agree. A leaver loses.",12,Dim);

        // bottom: rank ladder strip
        H(58,640,1100,$"RANK LADDER ({SetNames[s].ToUpperInvariant()} SET) · ELO WHERE EACH RANK STARTS");
        for(int i=0;i<20;i++)
        {
            float x=58+i*74.6f;bool cur=i+1==m.level;
            if(cur){Fill(R(x+8,676,48,70),new Color(0.42f,0.8f,0.38f,0.16f));Frame(R(x+8,676,48,70),new Color(0.42f,0.8f,0.38f,0.6f),1);}
            DrawEp(R(x+16,680,32,62),s,i+1);
            T(x-4,746,72,20,i<18?BandStart[i].ToString():i==18?"#2–3":"#1",12,cur?Green:Dim,cur?FontStyle.Bold:FontStyle.Normal,TextAnchor.MiddleCenter);
        }
    }
    static float searchFrom;

    // Party for the Team queue (Lateralus 22 Nov: "a way to create a party/group to queue up for team games"). Uses ArrowQueue's
    // own party (the hub's PartyAction): invite online players on the same build, accept/decline invites, kick, leave.
    static bool picking;static int pickTop;
    static object[] Arr(FieldInfo f){try{return (f?.GetValue(null) as Array)?.Cast<object>().ToArray()??Array.Empty<object>();}catch{return Array.Empty<object>();}}
    static string P(object o,string prop){try{return Traverse.Create(o).Property(prop).GetValue()?.ToString()??"";}catch{return "";}}
    static void PartyPanel(float now)
    {
        var cur=fPartyCurrent?.GetValue(null);
        var members=cur==null?Array.Empty<object>():(Traverse.Create(cur).Property("members").GetValue() as Array)?.Cast<object>().ToArray()??Array.Empty<object>();
        string leader=cur==null?"":P(cur,"leader");bool lead=members.Length==0||leader==MySteam();
        // Compact, so it fits above the rank ladder strip: one row of member chips, one row of buttons.
        var inc=Arr(fIncoming);
        if(inc.Length>0)
        {
            var i=inc[0];
            Fill(R(58,528,470,34),new Color(0.1f,0.25f,0.4f,0.85f));
            T(68,528,240,34,$"{P(i,"fromName")} invited you to a party",13,Color.white,FontStyle.Bold);
            if(Choice(318,531,100,28,"Accept",false,13)){try{mAccept.Invoke(null,new[]{i});}catch(Exception e){error=e.InnerException?.Message??e.Message;}}
            if(Choice(424,531,100,28,"Decline",false,13)){try{mDecline.Invoke(null,new[]{i});}catch(Exception e){error=e.InnerException?.Message??e.Message;}}
        }
        else H(58,530,470,$"YOUR PARTY · {Math.Max(1,members.Length)}/5"+(members.Length>=4?" · plays 5v5":""));
        if(members.Length==0)T(58,566,470,30,"Just you. Invite players to queue together (up to 5).",13,Dim);
        else for(int k=0;k<Math.Min(5,members.Length);k++)
        {
            var m=members[k];string id=P(m,"steamId");bool isLead=id==leader,isMe=id==MySteam();
            var cr=R(58+k*94,566,90,30);
            Fill(cr,isMe?new Color(0.42f,0.8f,0.38f,0.18f):new Color(0,0,0,0.5f));Frame(cr,isLead?new Color(1f,0.8f,0.3f,0.7f):new Color(1,1,1,0.15f),1);
            GUI.Label(new Rect(cr.x+6*S,cr.y,cr.width-(lead&&!isMe?26:8)*S,cr.height),(isLead?"★ ":"")+P(m,"name"),St(12,Color.white,isLead?FontStyle.Bold:FontStyle.Normal));
            if(lead&&!isMe)
            {
                var kr=new Rect(cr.xMax-22*S,cr.y+5*S,18*S,20*S);
                GUI.Label(kr,"X",St(12,kr.Contains(Event.current.mousePosition)?Red:Dim,FontStyle.Bold,TextAnchor.MiddleCenter));
                if(GUI.Button(kr,GUIContent.none,GUIStyle.none)){try{mKick.Invoke(null,new object[]{id});}catch(Exception e){error=e.InnerException?.Message??e.Message;}}
            }
        }
        if(lead&&members.Length<5&&Choice(58,602,230,30,"+ INVITE PLAYERS",false,13)){picking=true;pickTop=0;}
        if(members.Length>1&&Choice(298,602,230,30,lead?"DISBAND PARTY":"LEAVE PARTY",false,13)){try{mLeave.Invoke(null,null);}catch(Exception e){error=e.InnerException?.Message??e.Message;}}
    }
    static void InvitePicker(float now)
    {
        var info=fOnline?.GetValue(null)??fOnlineList?.GetValue(null);
        var all=info==null?Array.Empty<object>():(Traverse.Create(info).Property("players").GetValue() as Array)?.Cast<object>().ToArray()??Array.Empty<object>();
        var list=all.Where(p=>P(p,"steamId")!=MySteam()&&P(p,"sameBuild")=="True"&&P(p,"inParty")!="True").OrderBy(p=>P(p,"name"),StringComparer.OrdinalIgnoreCase).ToList();
        var box=R(560,110,520,690);
        Fill(box,new Color(0.06f,0.07f,0.08f,0.99f));Frame(box,new Color(1,1,1,0.2f),1);
        H(584,124,400,"INVITE TO YOUR PARTY");
        T(584,154,470,22,$"{list.Count} online on your Freedom Arrow build",13,Dim);
        const int Vis=13;var area=R(584,184,470,Vis*42);var ev=Event.current;
        try{if(ev.type==EventType.ScrollWheel&&area.Contains(ev.mousePosition)){pickTop=Math.Clamp(pickTop+(ev.delta.y>0?3:-3),0,Math.Max(0,list.Count-Vis));ev.Use();}}catch{}
        pickTop=Math.Clamp(pickTop,0,Math.Max(0,list.Count-Vis));
        if(list.Count==0)T(584,190,470,30,"Nobody else is online on this build right now.",14,Dim);
        for(int i=pickTop;i<Math.Min(list.Count,pickTop+Vis);i++)
        {
            var p=list[i];float y=184+(i-pickTop)*42;
            Fill(R(584,y,470,38),new Color(0,0,0,0.5f));
            T(596,y,300,38,P(p,"name"),15,Color.white,FontStyle.Bold);
            T(860,y,80,38,P(p,"state"),12,Dim,FontStyle.Normal,TextAnchor.MiddleRight);
            if(Choice(950,y+5,96,28,"Invite",false,13))
            {
                try{mInvite.Invoke(null,new object[]{p,now});note="Invitation sent to "+P(p,"name")+".";noteUntil=now+6f;MelonLogger.Msg("FREEDOM_ARROW_RANKED party invite "+P(p,"name"));}
                catch(Exception e){error=e.InnerException?.Message??e.Message;}
            }
        }
        if(Choice(700,756,240,34,"CLOSE",false,14))picking=false;
    }
    static void Stat(float x,float y,string label,string val){Fill(R(x,y,140,62),Box);T(x+10,y+4,130,30,val,20,Color.white,FontStyle.Bold);T(x+10,y+34,130,22,label,12,Dim);}
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
            note="The lobby opens by itself when a match is found.";noteUntil=now+8f;
        }
        catch(Exception e){error="Search failed: "+(e.InnerException?.Message??e.Message);}
    }

    static readonly Color[] Avatar={new(0.55f,0.25f,0.27f),new(0.25f,0.35f,0.5f),new(0.3f,0.45f,0.3f),new(0.45f,0.4f,0.25f),new(0.4f,0.3f,0.5f),new(0.25f,0.45f,0.45f)};
    static void BoardTab(JsonElement me,bool have)
    {
        // Sub-menus 1v1 / Team (Lateralus 22 Nov): each shows its own leaderboard and statistics.
        if(Choice(58,100,140,38,"1v1",boardLadder=="1v1",16)){boardLadder="1v1";selRow=-1;boardTop=0;}
        if(Choice(206,100,140,38,"Team",boardLadder=="team",16)){boardLadder="team";selRow=-1;boardTop=0;}
        var json=boardLadder=="1v1"?board1:boardT;
        var mine=Mine(me,have,boardLadder);int s=Set;
        T(58,146,300,26,$"Updated every 30 s · {(boardLadder=="1v1"?"1v1":"Team (3v3 + 5v5)")}",14,Color.white);
        DrawEp(R(360,148,14,22),s,mine.level);
        T(378,146,130,26,mine.place>0?$"YOUR RANK · {Ord(mine.place)}":"YOUR RANK · —",13,Green,FontStyle.Bold,TextAnchor.MiddleRight);
        Fill(R(528,110,1,680),new Color(1,1,1,0.12f));
        if(json.Length==0){T(58,180,470,30,"Loading…",14,Dim);return;}
        JsonElement b;try{b=JsonDocument.Parse(json).RootElement;}catch{return;}
        var rows=b.GetProperty("rows");int n=rows.GetArrayLength();
        if(n==0){T(58,180,470,30,"Nobody is rated yet. Win a ranked match to be first.",14,Dim);}
        else
        {
            // Manual scrolling: GUI.BeginScrollView is stripped from this game ("Method unstripping failed", Vengeance 22 Nov 09:31).
            const int Visible=14;
            var view=R(58,176,470,Visible*42);var ev=Event.current;
            try{if(ev.type==EventType.ScrollWheel&&view.Contains(ev.mousePosition)){boardTop=Math.Clamp(boardTop+(ev.delta.y>0?3:-3),0,Math.Max(0,n-Visible));ev.Use();}}catch{}
            boardTop=Math.Clamp(boardTop,0,Math.Max(0,n-Visible));
            if(n>Visible)T(58,176+Visible*42,470,22,$"{boardTop+1}–{Math.Min(n,boardTop+Visible)} of {n} · mouse wheel to scroll",12,Dim,FontStyle.Normal,TextAnchor.MiddleCenter);
            int i=0;
            foreach(var r in rows.EnumerateArray())
            {
                if(i<boardTop||i>=boardTop+Visible){i++;continue;}
                var rr=R(58,176+(i-boardTop)*42,450,40);
                bool me2=r.GetProperty("steamId").GetString()==MySteam();bool hov=rr.Contains(Event.current.mousePosition);
                Fill(rr,i==selRow?new Color(1,1,1,0.2f):me2?new Color(0.42f,0.8f,0.38f,0.14f):new Color(0,0,0,hov?0.62f:0.45f));
                var name=r.GetProperty("name").GetString()??"?";
                Fill(new Rect(rr.x,rr.y,36*S,rr.height),Avatar[(name.Length>0?name[0]:0)%Avatar.Length]);
                var ini=name.FirstOrDefault(char.IsLetterOrDigit);
                GUI.Label(new Rect(rr.x,rr.y,36*S,rr.height),ini==default(char)?"?":char.ToUpperInvariant(ini).ToString(),St(16,Color.white,FontStyle.Bold,TextAnchor.MiddleCenter));
                GUI.Label(new Rect(rr.x+44*S,rr.y,300*S,rr.height),name,St(15,Color.white,FontStyle.Bold));
                GUI.Label(new Rect(rr.x+330*S,rr.y,74*S,rr.height),r.GetProperty("rating").GetDouble().ToString("0"),St(13,Dim,FontStyle.Normal,TextAnchor.MiddleRight));
                DrawEp(new Rect(rr.x+416*S,rr.y+3*S,22*S,rr.height-6*S),s,r.GetProperty("level").GetInt32());   // the epaulet replaces #1, #2, #3
                if(GUI.Button(rr,GUIContent.none,GUIStyle.none))selRow=i;
                i++;
            }
        }
        // profile of the selected player (or you)
        H(580,108,400,"PROFILE");
        JsonElement p=default;bool sel=false;
        if(selRow>=0&&selRow<n){p=rows[selRow];sel=true;}
        else foreach(var r in rows.EnumerateArray())if(r.GetProperty("steamId").GetString()==MySteam()){p=r;sel=true;break;}
        string pname;int lv,place,w,l;double rating,best;string last;
        if(sel){pname=p.GetProperty("name").GetString()??"?";lv=p.GetProperty("level").GetInt32();place=p.GetProperty("place").GetInt32();rating=p.GetProperty("rating").GetDouble();
            w=p.GetProperty("wins").GetInt32();l=p.GetProperty("losses").GetInt32();best=p.TryGetProperty("best",out var bb)?bb.GetDouble():rating;last=p.TryGetProperty("last",out var ll)?ll.GetString()??"":"";}
        else{pname="You";lv=mine.level;place=mine.place;rating=mine.rating;w=mine.wins;l=mine.losses;best=mine.best;last="";
            if(mine.recent.ValueKind==JsonValueKind.Array)foreach(var x in mine.recent.EnumerateArray())last+=x.GetProperty("win").GetBoolean()?"W":"L";}
        DrawEp(R(584,148,90,166),s,lv);
        T(700,160,700,48,pname,32,Color.white,FontStyle.Bold);
        T(700,208,180,30,RankName(lv,s),20,new Color(0.92f,0.92f,0.92f));
        T(700+Math.Min(180,RankName(lv,s).Length*10.5f),208,200,30,$"· Elo {rating:0}",20,Green);
        T(700,240,700,24,(place>0?$"{Ord(place)} · ":"not placed · ")+$"{SetNames[s]} epaulets"+(lv>=18?" · 2170+ is the top band; places 1–3 above it":""),13,Dim);
        var bd=Band(rating,lv);float frac=lv>=18?1f:(float)Math.Clamp((rating-bd.from)/Math.Max(1,bd.to-bd.from),0,1);
        Fill(R(700,268,520,8),new Color(1,1,1,0.15f));Fill(R(700,268,520*frac,8),Color.white);
        T(700,280,260,22,$"{RankName(lv,s)} {bd.from:0}",13,Dim);
        T(960,280,260,22,lv>=18?"top band":$"{bd.to-rating:0} to {RankName(bd.next,s)} ({bd.to:0})",13,Dim,FontStyle.Normal,TextAnchor.MiddleRight);
        H(580,350,700,$"RANKED STATISTICS · {(boardLadder=="1v1"?"1V1":"TEAM")} · SEASON {(have?me.GetProperty("season").GetInt32():1)}");
        int g=w+l;
        Big(580,398,g.ToString(),"Ranked matches");Big(712,398,g>0?$"{100.0*w/g:0}%":"-","Win rate");Big(812,398,$"{best:0}","Best Elo");Big(914,398,$"{w}–{l}","Wins–losses");
        H(580,486,400,"LAST 10 RESULTS");
        if(last.Length==0)T(580,522,500,28,"No results yet.",14,Dim);
        for(int k=0;k<Math.Min(10,last.Length);k++)
        {
            bool win=last[k]=='W';var r=R(580+k*32,522,26,26);
            Fill(r,win?new Color(0.25f,0.5f,0.25f):new Color(0.5f,0.15f,0.15f));
            GUI.Label(r,win?"W":"L",St(12,win?new Color(0.75f,1f,0.7f):new Color(1f,0.6f,0.6f),FontStyle.Bold,TextAnchor.MiddleCenter));
        }
        T(580,752,960,40,"Instead of #1, #2, #3 every row shows the player's rank epaulet. Place 1 wears rank 20, places 2–3 rank 19 (only at 2170 Elo or more); everyone else wears the rank of their Elo band.",12,Dim);
    }
    static void Big(float x,float y,string val,string label){T(x,y,130,34,val,22,Color.white,FontStyle.Bold);T(x,y+34,130,22,label,13,Dim);}
}
