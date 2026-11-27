using System.IO.Compression;
using System.Text;
using HarmonyLib;
using Il2CppBrokenArrow.BrokenArrow.Client.Ecs.UI.Menu.Deck;
using Il2CppBrokenArrow.Client.Ecs.Decks;
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;
using Il2CppBrokenArrow.Client.Ecs.UI.BaseElements;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.ArmyBuilder;
using Il2CppNetworkCommon.Enums.Common;
using Il2CppInterop.Runtime;
using MelonLoader;
using UnityEngine;
using UnityEngine.EventSystems;
namespace FreedomArrow;
// Deck codes (Osama 26 Nov 2026 21:5x PST, #Website thread: "can we make deck codes so we can have people send each other decks? like in
// wargame?"; 21:55 "can you build this please"). Read from GameAssembly 1.2.2.1: every deck-list entry (DeckListButton) has a ShareButton
// (UiButton +0x30) wired to DeckListPanel.OnShareDeckClick, and UrlListenerService.HandleImportDeck(json) exists, but both bodies are empty:
// their RVA 0x5730 is the shared empty-method stub of 11,479 methods, so they must never be patched. This adds our own click handler to
// the vanilla Share button (copies a code to the clipboard) and a native "Import deck code" button cloned from the deck list's
// Create-deck button (reads the clipboard). A code is "FA1-" + base64url(deflate(compact deck)): name, nation, 2 specs, and per card the
// unit, count, transport, skins and option IDs (a mod ID is the option's own ModificationId, so it is not stored). Import builds the deck
// through DeckService.CreateDeck, fills the slots, runs the game's own TryFixDeck (drops anything this build does not have) and SaveDeck.
// Decks stay in Decks/FreedomArrow (DeckFolder.cs). Menu-only: nothing here runs in a battle.
static class DeckCodes
{
    const string Prefix="FA1-";
    const string ImportName="FA Import Deck Code";
    static readonly HashSet<IntPtr> wired=new();
    static readonly List<Il2CppSystem.Action<GameObject,PointerEventData.InputButton>> keep=new();
    static DeckListPanel panel; static Il2CppTMPro.TextMeshProUGUI note; static float noteUntil;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(DeckListButton),nameof(DeckListButton.Init)),postfix:new HarmonyMethod(typeof(DeckCodes),nameof(AfterButton)));
        h.Patch(AccessTools.Method(typeof(DeckListPanel),nameof(DeckListPanel.LoadDecks)),postfix:new HarmonyMethod(typeof(DeckCodes),nameof(AfterList)));
        MelonLogger.Msg("FREEDOM_ARROW_DECK_CODES installed: Share copies a deck code; 'Import deck code' adds the deck in the clipboard");
    }
    static Il2CppSystem.Action<GameObject,PointerEventData.InputButton> Click(Action a,string what)
    {
        var d=DelegateSupport.ConvertDelegate<Il2CppSystem.Action<GameObject,PointerEventData.InputButton>>(new Action<GameObject,PointerEventData.InputButton>((go,b)=>
        {
            if(b!=PointerEventData.InputButton.Left)return;
            try{a();}catch(Exception e){Say("Deck code failed: "+e.Message);MelonLogger.Error("FREEDOM_ARROW_DECK_CODES "+what+" failed: "+e);}
        }));
        keep.Add(d);return d;
    }
    // ---------------------------------------------------------------- UI
    static void AfterButton(DeckListButton __instance)
    {
        try
        {
            var share=__instance.ShareButton;if(share==null)return;
            share.gameObject.SetActive(true);
            if(!wired.Add(share.Pointer))return;
            var owner=__instance;
            share.add_ClickEvent(Click(()=>Export(owner),"share"));
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_DECK_CODES share button: "+e.Message);}
    }
    static void AfterList(DeckListPanel __instance)
    {
        try
        {
            panel=__instance;
            var create=__instance._createDeckButton;if(create==null)return;
            var parent=create.transform.parent;
            for(int i=0;i<parent.childCount;i++)if(parent.GetChild(i).name==ImportName)return;
            var go=UnityEngine.Object.Instantiate(create.gameObject,parent,false);go.name=ImportName;
            foreach(var tt in go.GetComponentsInChildren<Il2CppBrokenArrow.Shared.Ecs.Localization.TextTarget>(true))UnityEngine.Object.DestroyImmediate(tt);
            var label=go.GetComponentInChildren<Il2CppTMPro.TextMeshProUGUI>(true);
            if(label!=null)label.SetText(Chinese()?"导入卡组代码":"Import deck code");
            go.GetComponent<UiButton>()?.add_ClickEvent(Click(Import,"import"));
            go.transform.SetSiblingIndex(create.transform.GetSiblingIndex()+1);
            var nt=new GameObject("FA Deck Code Note");nt.layer=go.layer;
            var rt=nt.AddComponent<RectTransform>();rt.SetParent(go.transform,false);
            rt.anchorMin=new Vector2(0f,0f);rt.anchorMax=new Vector2(1f,0f);rt.pivot=new Vector2(0.5f,1f);rt.anchoredPosition=new Vector2(0f,-4f);rt.sizeDelta=new Vector2(0f,40f);
            note=nt.AddComponent<Il2CppTMPro.TextMeshProUGUI>();
            if(label!=null&&label.font!=null)note.font=label.font;
            note.fontSize=16;note.enableWordWrapping=true;note.alignment=Il2CppTMPro.TextAlignmentOptions.Top;note.raycastTarget=false;note.color=new Color(1f,0.85f,0.4f,1f);note.SetText("");
            MelonLogger.Msg($"FREEDOM_ARROW_DECK_CODES import button made from '{create.gameObject.name}' under '{parent.name}' (label {(label!=null?"set":"not found")})");
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_DECK_CODES import button: "+e.Message);}
    }
    public static void Tick(){ if(note!=null&&noteUntil>0f&&Time.unscaledTime>noteUntil){noteUntil=0f;try{note.SetText("");}catch{note=null;}} }
    static void Say(string s){MelonLogger.Msg("FREEDOM_ARROW_DECK_CODES: "+s);try{if(note!=null){note.SetText(s);noteUntil=Time.unscaledTime+6f;}}catch{note=null;}}
    static bool Chinese(){try{return Application.systemLanguage==SystemLanguage.Chinese||Application.systemLanguage==SystemLanguage.ChineseSimplified;}catch{return false;}}
    // ---------------------------------------------------------------- export
    static void Export(DeckListButton b)
    {
        var m=b.DeckDataModel?.TryCast<DeckDataModel>();
        if(m==null){Say("This deck can't be shared.");return;}
        var code=Encode(m,out int cards);
        GUIUtility.systemCopyBuffer=code;
        Say(Chinese()?$"已复制卡组代码（{cards} 张卡，{code.Length} 字符）":$"Deck code copied: {cards} cards, {code.Length} characters. Paste it anywhere.");
        DiagnosticLog.Write("deck_code_export",new{deck=m.Name,cards,length=code.Length});
    }
    static IEnumerable<UnitCategoryType> Cats()=>Enum.GetValues(typeof(UnitCategoryType)).Cast<UnitCategoryType>();
    public static string Encode(DeckDataModel m,out int cards)
    {
        var w=new MemoryStream();cards=0;
        void V(int x){uint u=(uint)Math.Max(0,x);while(u>=0x80){w.WriteByte((byte)(u|0x80));u>>=7;}w.WriteByte((byte)u);}
        V(1);V(m.CountryID);V(m.Spec1ID);V(m.Spec2ID);
        var nb=Encoding.UTF8.GetBytes((m.Name??"").Length>40?m.Name.Substring(0,40):(m.Name??""));V(nb.Length);w.Write(nb,0,nb.Length);
        var slots=m._slots;
        foreach(var cat in Cats())
        {
            if(slots==null||!slots.TryGetValue(cat,out var row)||row==null)continue;
            var used=new List<DeckSlotModel>();
            for(int i=0;i<row.Length;i++){var s=row[i];if(s!=null&&s.UnitID!=0&&s.Count>0)used.Add(s);}
            if(used.Count==0)continue;
            V((int)cat+1);V(used.Count);
            foreach(var s in used)
            {
                cards++;
                var mods=Opts(s.ModList);var tmods=s.TransportID!=0?Opts(s.TransportModList):new List<int>();
                int f=(s.TransportID!=0?1:0)|(s.UnitSkinId!=0?2:0)|(s.TransportSkinId!=0?4:0)|(mods.Count>0?8:0)|(tmods.Count>0?16:0);
                V(s.UnitID);V(s.Count);V(f);
                if((f&1)!=0){V(s.TransportID);V(s.TransportCount);}
                if((f&2)!=0)V(s.UnitSkinId);
                if((f&4)!=0)V(s.TransportSkinId);
                if((f&8)!=0){V(mods.Count);foreach(var o in mods)V(o);}
                if((f&16)!=0){V(tmods.Count);foreach(var o in tmods)V(o);}
            }
        }
        V(0);
        var z=new MemoryStream();
        using(var d=new DeflateStream(z,System.IO.Compression.CompressionLevel.SmallestSize,true))d.Write(w.ToArray(),0,(int)w.Length);
        return Prefix+Convert.ToBase64String(z.ToArray()).TrimEnd('=').Replace('+','-').Replace('/','_');
    }
    static List<int> Opts(Il2CppSystem.Collections.Generic.List<DeckModData> l)
    {
        var r=new List<int>();if(l==null)return r;
        for(int i=0;i<l.Count;i++){var o=l[i];if(o!=null&&o.OptionID!=0)r.Add(o.OptionID);}
        return r;
    }
    // ---------------------------------------------------------------- import
    public sealed class Card{public UnitCategoryType Cat;public int Unit,Count,Transport,TransportCount,Skin,TransportSkin;public List<int> Mods=new(),TransportMods=new();}
    public sealed class Decoded{public int Country,Spec1,Spec2;public string Name="";public List<Card> Cards=new();}
    public static Decoded Decode(string text)
    {
        int at=text.IndexOf(Prefix,StringComparison.Ordinal);
        if(at<0)throw new FormatException(Chinese()?"剪贴板里没有卡组代码（以 FA1- 开头）。":"No deck code in the clipboard (it starts with FA1-).");
        var sb=new StringBuilder();
        for(int i=at+Prefix.Length;i<text.Length;i++){char c=text[i];if(char.IsLetterOrDigit(c)||c=='-'||c=='_')sb.Append(c);else if(!char.IsWhiteSpace(c))break;}
        var b64=sb.ToString().Replace('-','+').Replace('_','/');b64+=new string('=',(4-b64.Length%4)%4);
        var raw=new MemoryStream();
        using(var d=new DeflateStream(new MemoryStream(Convert.FromBase64String(b64)),CompressionMode.Decompress))d.CopyTo(raw);
        var buf=raw.ToArray();int p=0;
        int V(){int r=0,sh=0;while(true){if(p>=buf.Length)throw new FormatException("The deck code is cut short.");byte x=buf[p++];r|=(x&0x7F)<<sh;if((x&0x80)==0)return r;sh+=7;if(sh>28)throw new FormatException("Bad deck code.");}}
        if(V()!=1)throw new FormatException("This deck code is from a newer Freedom Arrow. Update the mod first.");
        var o=new Decoded{Country=V(),Spec1=V(),Spec2=V()};
        int n=V();if(n<0||n>200||p+n>buf.Length)throw new FormatException("Bad deck code.");o.Name=Encoding.UTF8.GetString(buf,p,n);p+=n;
        for(int c=V();c!=0;c=V())
        {
            int count=V();if(count>40)throw new FormatException("Bad deck code.");
            for(int i=0;i<count;i++)
            {
                var k=new Card{Cat=(UnitCategoryType)(c-1),Unit=V(),Count=V()};int f=V();
                if((f&1)!=0){k.Transport=V();k.TransportCount=V();}
                if((f&2)!=0)k.Skin=V();
                if((f&4)!=0)k.TransportSkin=V();
                if((f&8)!=0){int m=V();for(int j=0;j<m;j++)k.Mods.Add(V());}
                if((f&16)!=0){int m=V();for(int j=0;j<m;j++)k.TransportMods.Add(V());}
                o.Cards.Add(k);
            }
        }
        return o;
    }
    static DeckService Service()=>panel?._deckService;
    static void Import()
    {
        var svc=Service();if(svc==null){Say("Open the deck list first.");return;}
        var db=svc._dbService;if(db==null||!db.IsLoaded){Say("Unit data is not loaded yet.");return;}
        var d=Decode(GUIUtility.systemCopyBuffer??"");
        // Name: the shared name, made unique among this player's decks.
        var names=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var all=svc.AllValidDecks;if(all!=null)foreach(var x in all)if(x?.Name!=null)names.Add(x.Name);
        string baseName=string.IsNullOrWhiteSpace(d.Name)?"Imported deck":d.Name.Trim(),name=baseName;
        for(int i=2;names.Contains(name);i++)name=$"{baseName} ({i})";
        int dropped=0;
        var m=svc.CreateDeck(name,d.Country,d.Spec1,d.Spec2);
        if(m==null){Say("The game refused this nation or specialization pair.");return;}
        var slots=m._slots;
        if(slots==null){slots=new Il2CppSystem.Collections.Generic.Dictionary<UnitCategoryType,Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<DeckSlotModel>>();m._slots=slots;}
        foreach(var g in d.Cards.GroupBy(k=>k.Cat))
        {
            var list=g.ToList();
            Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<DeckSlotModel> row=null;
            if(slots.ContainsKey(g.Key))row=slots[g.Key];
            int len=Math.Max(row?.Length??0,list.Count);
            if(row==null||row.Length<len)
            {
                var nr=new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<DeckSlotModel>(len);
                for(int i=0;i<len;i++)nr[i]=row!=null&&i<row.Length&&row[i]!=null?row[i]:new DeckSlotModel{Category=g.Key,SlotIndex=i};
                row=nr;slots[g.Key]=row;
            }
            for(int i=0;i<list.Count;i++)
            {
                var k=list[i];
                if(db.GetUnitById(k.Unit,false)==null){dropped++;continue;}
                var s=row[i]??new DeckSlotModel();row[i]=s;
                s.Category=g.Key;s.SlotIndex=i;s.UnitID=k.Unit;s.Count=k.Count;s.UnitSkinId=k.Skin;
                s.ModList=Mods(db,k.Mods,ref dropped);
                if(k.Transport!=0&&db.GetUnitById(k.Transport,false)!=null){s.TransportID=k.Transport;s.TransportCount=k.TransportCount;s.TransportSkinId=k.TransportSkin;s.TransportModList=Mods(db,k.TransportMods,ref dropped);}
                else{if(k.Transport!=0)dropped++;s.TransportID=0;s.TransportCount=0;s.TransportModList=new Il2CppSystem.Collections.Generic.List<DeckModData>();}
            }
        }
        svc.TryFixDeck(m,false,out bool fixedOk);
        bool saved=svc.SaveDeck(m,m.Name);
        try{panel.LoadDecks();}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_DECK_CODES list refresh: "+e.Message);}
        Say(Chinese()?$"已导入卡组“{name}”：{d.Cards.Count} 张卡"+(dropped>0?$"，{dropped} 项本版本没有，已移除":""):$"Imported \"{name}\": {d.Cards.Count} cards"+(dropped>0?$"; {dropped} item(s) not in this build were left out":"")+(saved?"":" (save failed, see log)"));
        DiagnosticLog.Write("deck_code_import",new{name,cards=d.Cards.Count,dropped,fixedOk,saved,country=d.Country,spec1=d.Spec1,spec2=d.Spec2});
    }
    static Il2CppSystem.Collections.Generic.List<DeckModData> Mods(Il2CppBrokenArrow.Shared.Ecs.DataBaseService db,List<int> opts,ref int dropped)
    {
        var l=new Il2CppSystem.Collections.Generic.List<DeckModData>();
        foreach(var id in opts)
        {
            var o=db.GetOptionById(id);var mod=o!=null?db.GetModificationById(o.ModificationId):null;
            if(o==null||mod==null){dropped++;continue;}
            l.Add(new DeckModData(mod,o));
        }
        return l;
    }
}
