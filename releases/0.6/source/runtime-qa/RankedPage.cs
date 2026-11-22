using System.Text.Json;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.MainMenu;
using Il2CppInterop.Runtime;
using Il2CppTMPro;
using MelonLoader;
using UnityEngine;
using UnityEngine.UI;
namespace FreedomArrow;
// Ranked menu in the game's own UI (Lateralus 22 Nov 2026: "it should be worked into the vanilla menu designs, similar to how the mod's
// multiplayer/mod game menu works"). Same approach as ArrowQueue's Mod game page (ModTab/ModPage): a page object placed next to the
// main menu tabs' content (sibling of MainMenuButton._showTargetContent, same anchors), built from uGUI images, buttons and
// TextMeshPro text in the game's own font. Opening it deselects the game's tabs (their content hides, the top bar and the top-right
// block stay); a game tab click hides it; BACK reopens the Play tab. The layout is the ranked menu's 1600-unit design, scaled to the
// space under the tab row. Data changes rebuild the page (at most a few times a second). If the page cannot be attached, the old
// overlay menu opens instead and the reason is logged (FREEDOM_ARROW_RANKED_PAGE).
static partial class RankedMenu
{
    static GameObject page;static RectTransform root;static MainMenuButtonControling ctl;static TMP_FontAsset font;
    static bool pageShown,pageFailed,reselecting;
    static string sig="";static float nextSig;
    static readonly List<UnityEngine.Events.UnityAction> keep=new();
    const float DW=1600,DH=850;

    public static void InstallPage(HarmonyLib.Harmony h)
    {
        var m=AccessTools.Method(typeof(MainMenuButtonControling),"OnMainMenuButtonClick");
        if(m!=null)h.Patch(m,prefix:new HarmonyMethod(typeof(RankedMenu),nameof(GameTabClicked)));
    }
    static void GameTabClicked(){if(pageShown&&!reselecting)HidePage("game tab clicked",false);}

    static bool Alive(UnityEngine.Object o)=>o!=null&&!o.WasCollected;
    static bool Attach()
    {
        if(Alive(page)&&Alive(root))return true;
        ctl=UnityEngine.Object.FindObjectOfType<MainMenuButtonControling>();
        if(ctl==null)throw new InvalidOperationException("no MainMenuButtonControling");
        var buttons=ctl._buttons;GameObject content=null;MainMenuButton anyButton=null;
        for(int i=0;buttons!=null&&i<buttons.Length;i++){var b=buttons[i];if(b==null)continue;anyButton??=b;if(content==null&&b._showTargetContent!=null)content=b._showTargetContent;}
        if(content==null||anyButton==null)throw new InvalidOperationException("no tab content to sit next to");
        font=anyButton._buttonText!=null?anyButton._buttonText.font:null;
        page=new GameObject("FA_RankedPage");
        var prt=page.AddComponent<RectTransform>();prt.SetParent(content.transform.parent,false);
        var crt=content.GetComponent<RectTransform>();
        if(crt!=null){prt.anchorMin=crt.anchorMin;prt.anchorMax=crt.anchorMax;prt.pivot=crt.pivot;prt.offsetMin=crt.offsetMin;prt.offsetMax=crt.offsetMax;}
        else{prt.anchorMin=Vector2.zero;prt.anchorMax=Vector2.one;prt.offsetMin=prt.offsetMax=Vector2.zero;}
        page.SetActive(true);Canvas.ForceUpdateCanvases();
        // Under the tab row, like ArrowQueue's PlaceBody: top = tab row bottom - 30, left = tab row left, 60 right / 50 bottom margin.
        var corners=new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppStructArray<Vector3>(4);
        anyButton.transform.parent.GetComponent<RectTransform>().GetWorldCorners(corners);
        var tl=prt.InverseTransformPoint(corners[0]);var r=prt.rect;
        float left=Mathf.Max(r.xMin+40,tl.x),top=Mathf.Min(r.yMax-40,tl.y-30),right=r.xMax-60,bottom=r.yMin+50;
        // dark backdrop under the tab row only, so the top bar and the top-right block stay as they are
        var bg=new GameObject("Backdrop");var brt=bg.AddComponent<RectTransform>();brt.SetParent(prt,false);
        brt.anchorMin=brt.anchorMax=new Vector2(0,1);brt.pivot=new Vector2(0,1);
        brt.anchoredPosition=new Vector2(0,top+20-r.yMax);brt.sizeDelta=new Vector2(r.width,top+20-r.yMin);
        var bgi=bg.AddComponent<Image>();bgi.color=new Color(0.02f,0.03f,0.04f,0.86f);bgi.raycastTarget=true;
        var go=new GameObject("Body");root=go.AddComponent<RectTransform>();root.SetParent(prt,false);
        root.anchorMin=root.anchorMax=new Vector2(0,1);root.pivot=new Vector2(0,1);
        float w=right-left,hgt=top-bottom,sc=Mathf.Min(w/DW,hgt/DH);
        root.anchoredPosition=new Vector2(left-r.xMin+(w-DW*sc)/2,top-r.yMax);root.sizeDelta=new Vector2(DW,DH);root.localScale=new Vector3(sc,sc,1);
        page.SetActive(false);
        MelonLogger.Msg($"FREEDOM_ARROW_RANKED_PAGE attached next to '{content.name}' in '{content.transform.parent.name}': page {r.width:0}x{r.height:0}, body {w:0}x{hgt:0} at {left:0},{top:0}, scale {sc:0.00}, font {(font!=null?font.name:"default")}");
        return true;
    }
    // true when the page took over; false -> the overlay menu opens instead
    static bool ShowPage()
    {
        if(pageFailed)return false;
        try
        {
            Attach();
            try{var mt=AccessTools.TypeByName("ArrowQueue.ModTab");if(mt!=null&&AccessTools.Property(mt,"Shown")?.GetValue(null) is true)AccessTools.Method(mt,"Hide")?.Invoke(null,null);}catch{}
            var buttons=ctl._buttons;
            for(int i=0;buttons!=null&&i<buttons.Length;i++)if(buttons[i]!=null)buttons[i].Selected=false;
            page.SetActive(true);page.transform.SetAsLastSibling();
            pageShown=true;sig="";tab=0;selRow=-1;picking=false;nextAsk=nextBoard=-100f;
            MelonLogger.Msg("FREEDOM_ARROW_RANKED_PAGE shown");
            return true;
        }
        catch(Exception e){pageFailed=true;MelonLogger.Error("FREEDOM_ARROW_RANKED_PAGE failed, the overlay menu is used instead: "+e);return false;}
    }
    static void HidePage(string why,bool backToPlay)
    {
        if(!pageShown)return;
        pageShown=false;picking=false;
        if(Alive(page))page.SetActive(false);
        MelonLogger.Msg("FREEDOM_ARROW_RANKED_PAGE hidden: "+why);
        if(backToPlay&&Alive(playButton)){reselecting=true;try{playButton.InvokeClick();}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED_PAGE back to Play: "+e.Message);}reselecting=false;}
    }
    static void PageTick()
    {
        if(!pageShown)return;
        if(!Alive(page)){pageShown=false;return;}
        if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name!="Hangar_Scene"){HidePage("menu scene left",false);return;}
        try{if(pInLobby.GetValue(null) is true){HidePage("joined a lobby",false);return;}}catch{}
        try{var mt=AccessTools.TypeByName("ArrowQueue.ModTab");if(mt!=null&&AccessTools.Property(mt,"Shown")?.GetValue(null) is true){HidePage("Mod game page opened",false);return;}}catch{}
        var now=Time.unscaledTime;
        if(now>=nextAsk){nextAsk=now+5f;Ask();}
        if(tab==1&&now>=nextBoard){nextBoard=now+30f;AskBoards();}
        if(now<nextSig)return;nextSig=now+0.25f;
        var s=Signature(now);
        if(s==sig)return;
        sig=s;
        try{Build(now);}catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_RANKED_PAGE build: "+e);}
    }
    static string Signature(float now)
    {
        bool active=false;try{active=pActive.GetValue(null) is true;}catch{}
        var cur=fPartyCurrent?.GetValue(null);
        string party=cur==null?"":string.Join(",",((Traverse.Create(cur).Property("members").GetValue() as Array)?.Cast<object>()??Array.Empty<object>()).Select(m=>P(m,"steamId")+P(m,"state")))+"/"+P(cur,"leader");
        string inc=string.Join(",",Arr(fIncoming).Select(i=>P(i,"partyId")));
        int online=0;try{var info=fOnline?.GetValue(null)??fOnlineList?.GetValue(null);online=(info==null?null:Traverse.Create(info).Property("players").GetValue() as Array)?.Length??0;}catch{}
        return $"{tab}|{queue}|{boardLadder}|{selRow}|{boardTop}|{set}|{vanillaSet}|{meJson.GetHashCode()}|{board1.GetHashCode()}|{boardT.GetHashCode()}|{party}|{inc}|{active}|{(active?(int)(now-searchFrom):0)}|{picking}|{pickTop}|{online}|{(now<noteUntil?note:"")}|{error}";
    }

    // ---------- uGUI kit (design units, origin top-left of the body) ----------
    static Transform cur;
    static RectTransform Node(string name,float x,float y,float w,float h)
    {
        var go=new GameObject(name);var rt=go.AddComponent<RectTransform>();rt.SetParent(cur,false);
        rt.anchorMin=rt.anchorMax=new Vector2(0,1);rt.pivot=new Vector2(0,1);rt.anchoredPosition=new Vector2(x,-y);rt.sizeDelta=new Vector2(w,h);
        return rt;
    }
    static Image Img(float x,float y,float w,float h,Color c,bool ray=false){var i=Node("Img",x,y,w,h).gameObject.AddComponent<Image>();i.color=c;i.raycastTarget=ray;return i;}
    static void Frm(float x,float y,float w,float h,Color c,float t=1){Img(x,y,w,t,c);Img(x,y+h-t,w,t,c);Img(x,y,t,h,c);Img(x+w-t,y,t,h,c);}
    static TextMeshProUGUI Txt(float x,float y,float w,float h,string s,float size,Color c,bool bold=false,TextAlignmentOptions a=TextAlignmentOptions.MidlineLeft,bool wrap=false)
    {
        var t=Node("Txt",x,y,w,h).gameObject.AddComponent<TextMeshProUGUI>();
        if(font!=null)t.font=font;
        t.fontSize=size;t.color=c;t.alignment=a;t.raycastTarget=false;t.enableWordWrapping=wrap;t.overflowMode=TextOverflowModes.Ellipsis;t.richText=false;
        if(bold)t.fontStyle=FontStyles.Bold;
        t.text=s??"";return t;
    }
    static Button Click(float x,float y,float w,float h,Action a,Image look=null)
    {
        var img=look??Img(x,y,w,h,new Color(0,0,0,0),true);img.raycastTarget=true;
        var b=img.gameObject.AddComponent<Button>();b.targetGraphic=img;
        var cb=b.colors;cb.highlightedColor=new Color(1.25f,1.25f,1.25f,1);cb.pressedColor=new Color(0.8f,0.8f,0.8f,1);cb.selectedColor=Color.white;b.colors=cb;
        var ua=DelegateSupport.ConvertDelegate<UnityEngine.Events.UnityAction>(new Action(()=>{try{a();sig="";}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED_PAGE click: "+e.Message);}}));
        keep.Add(ua);b.onClick.AddListener(ua);return b;
    }
    static void Choice(float x,float y,float w,float h,string label,bool on,float size,Action a)
    {
        var bg=Img(x,y,w,h,on?new Color(0.36f,0.06f,0.08f,0.95f):new Color(0,0,0,0.6f),true);
        Frm(x,y,w,h,on?Red:new Color(1,1,1,0.2f));
        Txt(x,y,w,h,label,size,Color.white,on,TextAlignmentOptions.Center);
        Click(x,y,w,h,a,bg);
    }
    static readonly Dictionary<Texture2D,Sprite> sprites=new();
    static Sprite Spr(Texture2D t){if(t==null)return null;if(!sprites.TryGetValue(t,out var s)||s==null||s.WasCollected){s=Sprite.Create(t,new Rect(0,0,t.width,t.height),new Vector2(0.5f,0.5f));s.hideFlags=HideFlags.DontUnloadUnusedAsset;sprites[t]=s;}return s;}
    static void Pic(float x,float y,float w,float h,Texture2D t,bool fit=true){if(t==null)return;var i=Img(x,y,w,h,Color.white);i.sprite=Spr(t);i.preserveAspect=fit;}
    static void EpImg(float x,float y,float w,float h,int s,int lv){if(s==4){Txt(x,y,w,h,"PLA",Math.Min(14,h*0.4f),new Color(1f,0.8f,0.2f),true,TextAlignmentOptions.Center);return;}Pic(x,y,w,h,Ep(s,lv));}
    static void Head(float x,float y,float w,string s)=>Txt(x,y,w,30,s,19,Color.white,true);
    static void HLine(float x,float y,float w)=>Img(x,y,w,1,new Color(1,1,1,0.1f));

    static void Build(float now)
    {
        for(int i=root.childCount-1;i>=0;i--)UnityEngine.Object.Destroy(root.GetChild(i).gameObject);
        keep.Clear();cur=root;
        JsonElement me=default;bool have=false;
        try{if(meJson.Length>0){me=JsonDocument.Parse(meJson).RootElement;have=true;}}catch{}
        // sub-tabs
        string[] tabs={"Ranked","Leaderboard"};float tx=0;
        for(int i=0;i<2;i++)
        {
            bool on=i==tab;float w=i==0?150:230;int k=i;
            Txt(tx,0,w,52,tabs[i],34,on?Color.white:new Color(0.75f,0.75f,0.75f),on);
            Img(tx,56,w-26,on?3:2,on?Color.white:new Color(1,1,1,0.28f));
            Click(tx,0,w,60,()=>{tab=k;selRow=-1;nextBoard=-100f;});
            tx+=w+20;
        }
        if(TestHub)Txt(560,14,560,24,"TEST SERVER · ratings here are test ratings",14,new Color(1f,0.75f,0.3f),true,TextAlignmentOptions.MidlineRight);
        if(tab==0)RankedBody(me,have,now);else BoardBody(me,have);
        if(error.Length>0)Txt(0,778,900,24,error,15,new Color(1f,0.55f,0.5f));
        Frm(700,812,30,20,new Color(0.75f,0.75f,0.75f));Txt(700,812,30,20,"esc",12,new Color(0.75f,0.75f,0.75f),false,TextAlignmentOptions.Center);
        Txt(738,806,90,32,"BACK",20,Color.white,true);
        Click(690,804,150,36,()=>HidePage("Back",true));
        if(picking)Picker(now);
    }

    static void RankedBody(JsonElement me,bool have,float now)
    {
        var dim=new Color(0.75f,0.75f,0.75f);
        bool active=false;try{active=pActive.GetValue(null) is true;}catch{}
        Head(0,86,470,"FIND A RANKED MATCH");
        Choice(0,126,230,42,"1v1",queue=="r1v1",18,()=>{if(!(pActive.GetValue(null) is true))queue="r1v1";});
        Choice(240,126,230,42,"Team · 3v3 / 5v5",queue=="rteam",18,()=>{if(!(pActive.GetValue(null) is true))queue="rteam";});
        void Row(float y,float h,string l,string v){Txt(0,y,150,h,l,16,dim);Txt(142,y,328,h,v,15,Color.white,false,TextAlignmentOptions.MidlineRight,true);HLine(0,y+h,470);}
        Row(182,36,"Queue",queue=="r1v1"?"Solo only · 1v1 ladder":"Solo or group · 3v3 or 5v5 · team ladder");
        Row(220,48,"Map pool",Pools[queue]);
        Row(270,36,"Rules","FA "+Runtime.DiagnosticPackageVersion+" · conquest 300");
        Row(308,36,"Map","picked by the server");
        int party=1;string leader="";
        try{var pr=fPartyNews?.GetValue(null);var pv=pr==null?null:Traverse.Create(pr).Property("party").GetValue();if(pv!=null){party=Math.Max(1,(Traverse.Create(pv).Property("members").GetValue() as Array)?.Length??1);leader=Traverse.Create(pv).Property("leader").GetValue<string>()??"";}}catch{}
        // FIND MATCH with the FA patch
        if(active)
        {
            var b=Img(0,362,470,64,new Color(0.22f,0.22f,0.24f,0.95f),true);Frm(0,362,470,64,new Color(1,1,1,0.25f));
            var secs=(int)Math.Max(0,now-searchFrom);
            Txt(0,362,470,64,$"SEARCHING  {secs/60}:{secs%60:00}   ·   CANCEL",24,Color.white,true,TextAlignmentOptions.Center);
            Click(0,362,470,64,()=>{mStop.Invoke(null,new object[]{true,false});MelonLogger.Msg("FREEDOM_ARROW_RANKED search cancelled");},b);
        }
        else
        {
            var b=Img(0,362,470,64,Red,true);Img(0,362,470,28,new Color(1,1,1,0.07f));Frm(0,362,470,64,new Color(1f,0.55f,0.55f,0.6f));
            Pic(118,373,42,42,patch);
            Txt(176,362,290,64,"FIND MATCH",30,Color.white,true);
            Click(0,362,470,64,()=>{searchFrom=Time.unscaledTime;Find(party,leader,Time.unscaledTime);},b);
        }
        int searching=0;try{if(have)searching=me.GetProperty("searching").GetProperty(queue).GetInt32();}catch{}
        Txt(0,432,470,24,$"{searching} {(searching==1?"player":"players")} searching {(queue=="r1v1"?"1v1":"team games")}",14,dim,false,TextAlignmentOptions.Center);
        if(now<noteUntil)Txt(0,456,470,30,note,14,new Color(1f,0.75f,0.3f),false,TextAlignmentOptions.Center,true);
        if(queue=="rteam")GroupBody();

        // your rank
        var lad=Ladder(queue);var m=Mine(me,have,lad);int s=Set;
        int season=1;try{if(have)season=me.GetProperty("season").GetInt32();}catch{}
        Head(532,86,440,$"YOUR RANK · {(lad=="1v1"?"1V1":"TEAM")} · SEASON {season}");
        Img(532,127,440,186,new Color(0,0,0,0.5f));Frm(532,127,440,186,new Color(1,1,1,0.08f));
        EpImg(550,140,86,160,s,m.level);
        Txt(658,156,300,48,RankName(m.level,s),34,Color.white,true);
        Txt(658,206,44,30,"Elo",22,Green);Txt(702,206,200,30,$"{m.rating:0}",22,new Color(0.92f,0.92f,0.92f));
        Txt(658,242,300,24,$"Rank {m.level} of 20 · "+(m.place>0?$"{Ord(m.place)} on the leaderboard":"not placed yet"),14,dim);
        var bd=Band(m.rating,m.level);float frac=m.level>=18?1f:(float)Math.Clamp((m.rating-bd.from)/Math.Max(1,bd.to-bd.from),0,1);
        Img(532,330,440,8,new Color(1,1,1,0.15f));if(frac>0)Img(532,330,440*frac,8,Color.white);
        Txt(532,342,220,22,$"{RankName(m.level,s)} {bd.from:0}",14,dim);
        Txt(752,342,220,22,m.level>=18?"top band":$"{bd.to-m.rating:0} to {RankName(bd.next,s)} ({bd.to:0})",14,dim,false,TextAlignmentOptions.MidlineRight);
        int games=m.wins+m.losses;
        void Stat(float x,string v,string l){Img(x,379,140,62,new Color(0,0,0,0.42f));Txt(x+10,383,130,30,v,22,Color.white,true);Txt(x+10,413,130,22,l,13,dim);}
        Stat(532,games.ToString(),"Ranked matches");Stat(682,games>0?$"{100.0*m.wins/games:0}%":"-","Win rate");Stat(832,$"{m.best:0}","Best Elo");
        for(int i=0;i<5;i++)
        {
            float x=532+i*89.5f;bool on=i==s;int k=i;
            var b=Img(x,460,82,90,new Color(0,0,0,on?0.62f:0.42f),i<4);
            Frm(x,460,82,90,on?Green:new Color(1,1,1,0.1f),on?2:1);
            EpImg(x+26,468,30,50,i,Math.Max(1,m.level));
            Txt(x,522,82,22,SetNames[i]+(i==4?" (soon)":""),12,i==4?dim:Color.white,false,TextAlignmentOptions.Center);
            if(i<4)Click(x,460,82,90,()=>{set=k;SaveSettings();MelonLogger.Msg("FREEDOM_ARROW_RANKED set "+SetNames[k]);},b);
        }
        Txt(532,556,440,36,set<0?$"Following your vanilla epaulet ({SetNames[s]}). The set only changes how your rank looks.":"The epaulet set only changes how your rank looks; the rank is the same.",13,dim,false,TextAlignmentOptions.TopLeft,true);

        // recent matches
        Head(1032,86,460,"RECENT RANKED MATCHES");
        int row=0;
        if(m.recent.ValueKind==JsonValueKind.Array)
            foreach(var x in m.recent.EnumerateArray())
            {
                if(row>=10)break;
                float y=125+row*39;bool win=x.GetProperty("win").GetBoolean();var ch=x.GetProperty("change").GetDouble();
                double vr=x.TryGetProperty("vsRating",out var v)?v.GetDouble():1000;
                Txt(1038,y,24,38,win?"W":"L",16,win?Green:Red,true);
                Txt(1080,y,170,38,$"[{x.GetProperty("format").GetString()}] {x.GetProperty("map").GetString()}",15,Color.white);
                Txt(1246,y,28,38,"vs",14,dim);EpImg(1272,y+8,14,22,s,Level(vr,0));
                Txt(1292,y,62,38,x.GetProperty("vs").GetString()??"",15,Color.white);
                Txt(1354,y,40,38,Ago(x.GetProperty("t")),14,dim,false,TextAlignmentOptions.MidlineRight);
                Txt(1404,y,82,38,(ch>=0?"+":"-")+Math.Abs(ch).ToString("0.0"),15,ch>=0?Green:Red,true,TextAlignmentOptions.MidlineRight);
                HLine(1032,y+38,455);row++;
            }
        if(row==0){Txt(1038,125,450,38,"No ranked matches yet this season.",15,dim);HLine(1032,163,455);}
        Txt(1032,136+Math.Max(row,1)*39,460,24,"A result counts only when both sides' game reports agree. A leaver loses.",13,dim);

        // rank ladder strip
        Head(0,616,1100,$"RANK LADDER ({SetNames[s].ToUpperInvariant()} SET) · ELO WHERE EACH RANK STARTS");
        for(int i=0;i<20;i++)
        {
            float x=i*74.6f;bool c=i+1==m.level;
            if(c){Img(x+8,652,48,70,new Color(0.42f,0.8f,0.38f,0.16f));Frm(x+8,652,48,70,new Color(0.42f,0.8f,0.38f,0.6f));}
            EpImg(x+16,656,32,62,s,i+1);
            Txt(x-4,722,72,20,i<18?BandStart[i].ToString():i==18?"#2-3":"#1",13,c?Green:dim,c,TextAlignmentOptions.Center);
        }
    }

    // GROUP, like the game's own block: five square slots, Steam picture + name, "+" on open slots.
    static void GroupBody()
    {
        var curP=fPartyCurrent?.GetValue(null);
        var members=curP==null?Array.Empty<object>():(Traverse.Create(curP).Property("members").GetValue() as Array)?.Cast<object>().ToArray()??Array.Empty<object>();
        string leader=curP==null?"":P(curP,"leader");bool lead=members.Length==0||leader==MySteam();
        var inc=Arr(fIncoming);
        if(inc.Length>0)
        {
            var i=inc[0];
            Img(0,490,470,30,new Color(0.1f,0.25f,0.4f,0.85f));
            Txt(8,490,250,30,$"{P(i,"fromName")} invited you to a group",14,Color.white,true);
            Choice(260,492,100,26,"Accept",false,13,()=>mAccept.Invoke(null,new[]{i}));
            Choice(366,492,100,26,"Decline",false,13,()=>mDecline.Invoke(null,new[]{i}));
        }
        else
        {
            Head(0,490,300,"GROUP"+(members.Length>=4?" · plays 5v5":""));
            if(members.Length>1){Txt(350,490,120,30,lead?"DISBAND":"LEAVE",13,new Color(0.75f,0.75f,0.75f),true,TextAlignmentOptions.MidlineRight);Click(350,490,120,30,()=>mLeave.Invoke(null,null));}
        }
        for(int k=0;k<5;k++)
        {
            float x=k*99.5f,y=526;
            if(k<members.Length||(k==0&&members.Length==0))
            {
                string id=k<members.Length?P(members[k],"steamId"):MySteam();string name=k<members.Length?P(members[k],"name"):"You";
                bool isLead=k<members.Length&&id==leader,isMe=id==MySteam();
                Img(x,y,72,72,new Color(0.1f,0.11f,0.12f,0.95f));
                var av=SteamPic(id);
                if(av!=null)Pic(x+2,y+2,68,68,av,false);
                else{var ini=name.FirstOrDefault(char.IsLetterOrDigit);Txt(x,y,72,72,ini==default(char)?"?":char.ToUpperInvariant(ini).ToString(),28,new Color(0.75f,0.75f,0.75f),true,TextAlignmentOptions.Center);}
                Frm(x,y,72,72,isMe?new Color(0.42f,0.8f,0.38f,0.8f):new Color(1,1,1,0.45f));
                if(isLead&&members.Length>1)Frm(x,y,72,72,new Color(1f,0.8f,0.3f,0.9f),2);   // leader: gold frame
                Txt(x-14,y+74,100,18,name,13,new Color(0.85f,0.85f,0.85f),true,TextAlignmentOptions.Center);
                if(lead&&!isMe&&k<members.Length){Img(x+52,y+2,18,18,new Color(0,0,0,0.7f));Txt(x+52,y+2,18,18,"X",13,Color.white,true,TextAlignmentOptions.Center);Click(x+52,y+2,18,18,()=>mKick.Invoke(null,new object[]{id}));}
            }
            else
            {
                var b=Img(x,y,72,72,new Color(0.1f,0.13f,0.14f,0.8f),lead);Frm(x,y,72,72,new Color(1,1,1,0.35f));
                Txt(x,y,72,72,"+",34,new Color(0.8f,0.8f,0.8f,lead?1f:0.4f),true,TextAlignmentOptions.Center);
                if(lead)Click(x,y,72,72,()=>{picking=true;pickTop=0;},b);
            }
        }
    }

    static void Picker(float now)
    {
        var info=fOnline?.GetValue(null)??fOnlineList?.GetValue(null);
        var all=info==null?Array.Empty<object>():(Traverse.Create(info).Property("players").GetValue() as Array)?.Cast<object>().ToArray()??Array.Empty<object>();
        var list=all.Where(p=>P(p,"steamId")!=MySteam()&&P(p,"sameBuild")=="True"&&P(p,"inParty")!="True").OrderBy(p=>P(p,"name"),StringComparer.OrdinalIgnoreCase).ToList();
        Img(-200,-200,DW+400,DH+400,new Color(0,0,0,0.5f),true);   // blocks the page under the list
        Img(540,60,520,700,new Color(0.06f,0.07f,0.08f,0.99f),true);Frm(540,60,520,700,new Color(1,1,1,0.2f));
        Head(564,74,400,"INVITE TO YOUR GROUP");
        Txt(564,104,470,22,$"{list.Count} online on your Freedom Arrow build",14,new Color(0.75f,0.75f,0.75f));
        const int Vis=12;pickTop=Math.Clamp(pickTop,0,Math.Max(0,list.Count-Vis));
        if(list.Count==0)Txt(564,140,470,30,"Nobody else is online on this build right now.",15,new Color(0.75f,0.75f,0.75f));
        for(int i=pickTop;i<Math.Min(list.Count,pickTop+Vis);i++)
        {
            var p=list[i];float y=134+(i-pickTop)*46;
            Img(564,y,470,40,new Color(0,0,0,0.5f));
            Txt(576,y,300,40,P(p,"name"),16,Color.white,true);
            Txt(840,y,80,40,P(p,"state"),13,new Color(0.75f,0.75f,0.75f),false,TextAlignmentOptions.MidlineRight);
            Choice(930,y+6,96,28,"Invite",false,14,()=>{mInvite.Invoke(null,new object[]{p,Time.unscaledTime});note="Invitation sent to "+P(p,"name")+".";noteUntil=Time.unscaledTime+6f;MelonLogger.Msg("FREEDOM_ARROW_RANKED group invite "+P(p,"name"));});
        }
        if(list.Count>Vis)
        {
            Choice(564,690,60,30,"Prev",false,14,()=>pickTop-=Vis);Choice(974,690,60,30,"Next",false,14,()=>pickTop+=Vis);
            Txt(630,690,340,30,$"{pickTop+1}-{Math.Min(list.Count,pickTop+Vis)} of {list.Count}",13,new Color(0.75f,0.75f,0.75f),false,TextAlignmentOptions.Center);
        }
        Choice(680,722,240,30,"CLOSE",false,15,()=>picking=false);
    }

    static void BoardBody(JsonElement me,bool have)
    {
        var dim=new Color(0.75f,0.75f,0.75f);
        Choice(0,76,140,38,"1v1",boardLadder=="1v1",17,()=>{boardLadder="1v1";selRow=-1;boardTop=0;});
        Choice(148,76,140,38,"Team",boardLadder=="team",17,()=>{boardLadder="team";selRow=-1;boardTop=0;});
        var json=boardLadder=="1v1"?board1:boardT;var mine=Mine(me,have,boardLadder);int s=Set;
        Txt(0,120,300,26,$"Updated every 30 s · {(boardLadder=="1v1"?"1v1":"Team (3v3 + 5v5)")}",15,Color.white);
        EpImg(302,122,14,22,s,mine.level);
        Txt(320,120,130,26,mine.place>0?$"YOUR RANK · {Ord(mine.place)}":"YOUR RANK · —",14,Green,true,TextAlignmentOptions.MidlineRight);
        Img(470,86,1,680,new Color(1,1,1,0.12f));
        if(json.Length==0){Txt(0,156,450,30,"Loading…",15,dim);return;}
        JsonElement b;try{b=JsonDocument.Parse(json).RootElement;}catch{return;}
        var rows=b.GetProperty("rows");int n=rows.GetArrayLength();
        const int Vis=13;boardTop=Math.Clamp(boardTop,0,Math.Max(0,n-Vis));
        if(n==0)Txt(0,156,450,30,"Nobody is rated yet. Win a ranked match to be first.",15,dim);
        for(int i=boardTop;i<Math.Min(n,boardTop+Vis);i++)
        {
            var r=rows[i];float y=152+(i-boardTop)*42;int k=i;
            bool me2=r.GetProperty("steamId").GetString()==MySteam();
            var bg=Img(0,y,450,40,i==selRow?new Color(1,1,1,0.2f):me2?new Color(0.42f,0.8f,0.38f,0.14f):new Color(0,0,0,0.45f),true);
            var name=r.GetProperty("name").GetString()??"?";var ini=name.FirstOrDefault(char.IsLetterOrDigit);
            var pic=SteamPic(r.GetProperty("steamId").GetString());
            Img(0,y,40,40,Avatar[(ini==default(char)?0:ini)%Avatar.Length]);
            if(pic!=null)Pic(0,y,40,40,pic,false);else Txt(0,y,40,40,ini==default(char)?"?":char.ToUpperInvariant(ini).ToString(),17,Color.white,true,TextAlignmentOptions.Center);
            Txt(48,y,280,40,name,16,Color.white,true);
            Txt(330,y,74,40,r.GetProperty("rating").GetDouble().ToString("0"),14,dim,false,TextAlignmentOptions.MidlineRight);
            EpImg(416,y+3,22,34,s,r.GetProperty("level").GetInt32());   // the epaulet replaces #1, #2, #3
            Click(0,y,450,40,()=>selRow=k,bg);
        }
        if(n>Vis)
        {
            Choice(0,152+Vis*42+6,60,28,"Prev",false,14,()=>boardTop-=Vis);Choice(390,152+Vis*42+6,60,28,"Next",false,14,()=>boardTop+=Vis);
            Txt(60,152+Vis*42+6,330,28,$"{boardTop+1}-{Math.Min(n,boardTop+Vis)} of {n}",13,dim,false,TextAlignmentOptions.Center);
        }
        Head(522,78,400,"PROFILE");
        JsonElement p=default;bool sel=false;
        if(selRow>=0&&selRow<n){p=rows[selRow];sel=true;}
        else foreach(var r in rows.EnumerateArray())if(r.GetProperty("steamId").GetString()==MySteam()){p=r;sel=true;break;}
        string pname;int lv,place,w,l;double rating,best;string last;
        if(sel){pname=p.GetProperty("name").GetString()??"?";lv=p.GetProperty("level").GetInt32();place=p.GetProperty("place").GetInt32();rating=p.GetProperty("rating").GetDouble();
            w=p.GetProperty("wins").GetInt32();l=p.GetProperty("losses").GetInt32();best=p.TryGetProperty("best",out var bb)?bb.GetDouble():rating;last=p.TryGetProperty("last",out var ll)?ll.GetString()??"":"";}
        else{pname="You";lv=mine.level;place=mine.place;rating=mine.rating;w=mine.wins;l=mine.losses;best=mine.best;last="";
            if(mine.recent.ValueKind==JsonValueKind.Array)foreach(var x in mine.recent.EnumerateArray())last+=x.GetProperty("win").GetBoolean()?"W":"L";}
        EpImg(526,118,90,166,s,lv);
        Txt(642,130,700,48,pname,34,Color.white,true);
        Txt(642,178,700,30,$"{RankName(lv,s)}  ·  Elo {rating:0}",21,new Color(0.92f,0.92f,0.92f));
        Txt(642,210,800,24,(place>0?$"{Ord(place)} · ":"not placed · ")+$"{SetNames[s]} epaulets"+(lv>=18?" · 2170+ is the top band; places 1-3 above it":""),14,dim);
        var bd=Band(rating,lv);float frac=lv>=18?1f:(float)Math.Clamp((rating-bd.from)/Math.Max(1,bd.to-bd.from),0,1);
        Img(642,238,520,8,new Color(1,1,1,0.15f));if(frac>0)Img(642,238,520*frac,8,Color.white);
        Txt(642,250,260,22,$"{RankName(lv,s)} {bd.from:0}",14,dim);
        Txt(902,250,260,22,lv>=18?"top band":$"{bd.to-rating:0} to {RankName(bd.next,s)} ({bd.to:0})",14,dim,false,TextAlignmentOptions.MidlineRight);
        int season=1;try{if(have)season=me.GetProperty("season").GetInt32();}catch{}
        Head(522,320,700,$"RANKED STATISTICS · {(boardLadder=="1v1"?"1V1":"TEAM")} · SEASON {season}");
        int g=w+l;
        void Big(float x,string v,string lab){Txt(x,366,130,34,v,24,Color.white,true);Txt(x,400,130,22,lab,14,dim);}
        Big(522,g.ToString(),"Ranked matches");Big(662,g>0?$"{100.0*w/g:0}%":"-","Win rate");Big(772,$"{best:0}","Best Elo");Big(884,$"{w}-{l}","Wins-losses");
        Head(522,456,400,"LAST 10 RESULTS");
        if(last.Length==0)Txt(522,492,500,28,"No results yet.",15,dim);
        for(int k=0;k<Math.Min(10,last.Length);k++)
        {
            bool win=last[k]=='W';
            Img(522+k*32,492,26,26,win?new Color(0.25f,0.5f,0.25f):new Color(0.5f,0.15f,0.15f));
            Txt(522+k*32,492,26,26,win?"W":"L",13,win?new Color(0.75f,1f,0.7f):new Color(1f,0.6f,0.6f),true,TextAlignmentOptions.Center);
        }
        Txt(522,722,960,44,"Instead of #1, #2, #3 every row shows the player's rank epaulet. Place 1 wears rank 20, places 2-3 rank 19 (only at 2170 Elo or more); everyone else wears the rank of their Elo band.",13,dim,false,TextAlignmentOptions.TopLeft,true);
    }
}
