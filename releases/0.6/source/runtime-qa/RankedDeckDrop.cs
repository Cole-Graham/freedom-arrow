using HarmonyLib;
using Il2CppBrokenArrow.BrokenArrow.Client.Ecs.UI.BaseElements.DropDown;
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;
using Il2CppBrokenArrow.Client.Ecs.UI.BaseElements;
using Il2CppBrokenArrow.Client.Ecs.UI.BaseElements.Utils;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.TeamPanel;
using Il2CppInterop.Runtime;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Default deck = the game's own lobby deck dropdown (Lateralus 22 Nov: "I want it to be in the dropdown just like in the normal lobby deck
// selection where the two specialization emblems are overlaid on the nation flag next to the deck name. Only the preview of the deck
// should pop-up when hovering over the selections"). A copy of TeamPanelPlayerInfo._decksDropdown is filled with
// UiDropDownItem.GetDeckDropdownItem (the lobby's own deck rows: flag + spec emblems + name); hover shows the deck preview.
static partial class RankedMenu
{
    static UiDropDown deckDrop;static bool deckDropFailed;static List<DeckDataModel> dropDecks=new();static string dropSig="";
    static readonly List<Il2CppSystem.Delegate> dropKeep=new();
    static bool DeckDropReady=>deckDrop!=null&&!deckDrop.WasCollected;
    // the dropdown lives under the page body and is kept across rebuilds; Build only moves it
    static bool MakeDeckDrop()
    {
        if(DeckDropReady)return true;
        if(deckDropFailed||!Alive(root))return false;
        try
        {
            UiDropDown tpl=null;int best=-1;
            foreach(var o in Resources.FindObjectsOfTypeAll(Il2CppType.Of<TeamPanelPlayerInfo>()))
            {
                var p=o.TryCast<TeamPanelPlayerInfo>();var d=p?._decksDropdown;if(d==null)continue;
                int score=p.gameObject.scene.IsValid()?1:2;   // prefab first: a clean copy with no lobby state
                if(score>best){tpl=d;best=score;}
            }
            if(tpl==null){deckDropFailed=true;MelonLogger.Warning("FREEDOM_ARROW_RANKED_PAGE no lobby deck dropdown found: the list is used");return false;}
            var tr=tpl.GetComponent<RectTransform>();float tw=tr!=null&&tr.rect.width>50?tr.rect.width:410,th=tr!=null&&tr.rect.height>10?tr.rect.height:40;
            var go=UnityEngine.Object.Instantiate(tpl.gameObject,root,false);go.name="FA_RankedDeckDropdown";go.SetActive(true);
            deckDrop=go.GetComponent<UiDropDown>();
            var rt=go.GetComponent<RectTransform>();rt.anchorMin=rt.anchorMax=new Vector2(0,1);rt.pivot=new Vector2(0,1);rt.sizeDelta=new Vector2(tw,th);
            Action<int> changed=i=>{try{if(i>=0&&i<dropDecks.Count){deckName=dropDecks[i].Name;SaveSettings();nextDeckReport=0;MelonLogger.Msg("FREEDOM_ARROW_RANKED default deck "+deckName);}ShowPreview(null);sig="";}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED deck pick: "+e.Message);}};
            Action<int> hover=i=>{try{if(i>=0&&i<dropDecks.Count)ShowPreview(dropDecks[i]);}catch{}};
            Action closed=()=>ShowPreview(null);
            var dc=DelegateSupport.ConvertDelegate<Il2CppSystem.Action<int>>(changed);var dh=DelegateSupport.ConvertDelegate<Il2CppSystem.Action<int>>(hover);var dx=DelegateSupport.ConvertDelegate<Il2CppSystem.Action>(closed);
            dropKeep.Add(dc);dropKeep.Add(dh);dropKeep.Add(dx);
            deckDrop.DropdownValueChangedEvent=dc;deckDrop.DropdownHoverEnterEvent=dh;deckDrop.DropdownClosedEvent=dx;
            dropSig="";
            MelonLogger.Msg($"FREEDOM_ARROW_RANKED_PAGE deck dropdown copied from the lobby ({tw:0}x{th:0}, {(best==2?"prefab":"scene")})");
            return true;
        }
        catch(Exception e){deckDropFailed=true;deckDrop=null;MelonLogger.Warning("FREEDOM_ARROW_RANKED_PAGE deck dropdown: "+e);return false;}
    }
    // place it (design units, top-left of the body) and refill when the valid deck list or the choice changed
    static bool PlaceDeckDrop(float x,float y,float w,float h)
    {
        if(!MakeDeckDrop())return false;
        try
        {
            var rt=deckDrop.GetComponent<RectTransform>();
            float k=Mathf.Min(w/Mathf.Max(1,rt.sizeDelta.x),h/Mathf.Max(1,rt.sizeDelta.y));rt.localScale=new Vector3(k,k,1);rt.anchoredPosition=new Vector2(x,-y);
            deckDrop.gameObject.SetActive(true);deckDrop.transform.SetAsLastSibling();
            var decks=ValidDecks();var s=deckName+"|"+string.Join("|",decks.Select(d=>d.Name));
            if(s!=dropSig)
            {
                dropSig=s;dropDecks=new List<DeckDataModel>(decks);
                var list=new Il2CppSystem.Collections.Generic.List<DropDownItemContext>();
                for(int i=0;i<dropDecks.Count;i++)list.Add(UiDropDownItem.GetDeckDropdownItem(i,dropDecks[i].Cast<IDeckDataModel>()).Cast<DropDownItemContext>());
                deckDrop.InitDropdown(list.Cast<Il2CppSystem.Collections.Generic.IEnumerable<DropDownItemContext>>(),false,true);
                int cur=dropDecks.FindIndex(d=>d.Name==deckName);
                if(cur>=0)deckDrop.SetValue(cur,true);
            }
            return true;
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED_PAGE deck dropdown fill: "+e.Message);deckDropFailed=true;try{deckDrop.gameObject.SetActive(false);}catch{}deckDrop=null;return false;}
    }
    static void HideDeckDrop(){try{if(DeckDropReady){deckDrop.CloseDropdownArea();deckDrop.gameObject.SetActive(false);}}catch{}}
}
