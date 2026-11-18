using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks;
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;
using Il2CppBrokenArrow.Client.Ecs.UI.BaseElements.Dropzone;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.ArmyBuilder;
using MelonLoader;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
namespace FreedomArrow;
// Drag and drop to reorder units in the deck editor (Lateralus 18 Nov 2026, thread 1572659362558771252: "improving the deck editing menu,
// so players can drag and drop units to re-order them"). Read from GameAssembly 1.2.2.1: each category is one DeckSlotModel[] in
// Deck.Slots and the order is the array order; SlotIndex (+0x1C, saved as "slot") mirrors it. RemoveUnitFromSlot (0x6F4780) shifts later
// slots down the same way. DeckCategory draws one child of _slotsContainer per slot (BaseInit 0x567470). We put the game's own
// UiDragElement, set to send events only, on each filled slot. A drop on another slot of the same category moves the slot in the array,
// renumbers SlotIndex and raises Deck.SendSlotChangedEvent(slot, true): DeckCategory.OnSlotChanged (0x568110) then redraws the whole
// category from the array, and DeckOverview.OnSlotChanged (0x571520) marks the deck changed and shows Save. Content and points do not
// change, so the deck stays a valid vanilla deck. The battle shop lists cards in this order (ShopPanelUI.ShowMainCards uses IterSlots).
static class DeckReorder
{
    static readonly Color Mark=new(1f,0.55f,0.1f,0.95f);
    static DeckCategory cat; static int from=-1, to=-1; static GameObject ghost, marker; static CanvasGroup dimmed;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(DeckCategory),nameof(DeckCategory.BaseInit)),postfix:new HarmonyMethod(typeof(DeckReorder),nameof(After)));
        MelonLogger.Msg("FREEDOM_ARROW_DECK_REORDER installed: drag a unit in the deck editor to move it within its category");
    }
    // BaseInit draws every slot of one category (on open and after any removal). Add the drag handle to each filled slot.
    static void After(DeckCategory __instance)
    {
        try
        {
            var box=__instance._slotsContainer;if(box==null)return;
            for(int i=0;i<box.childCount;i++)
            {
                var slot=box.GetChild(i).gameObject;
                var button=slot.GetComponentInChildren<DeckUnitButton>(true);
                if(button==null||button.Slot==null||!button.Slot.IsValid)continue;
                var drag=slot.GetComponent<UiDragElement>()??slot.AddComponent<UiDragElement>();
                drag._getOnlyDragDataEvents=true;
                var c=__instance;var s=button.Slot;
                drag.add_BeginDragEvent((Action<PointerEventData>)(e=>Begin(c,s,slot,e)));
                drag.add_DragEvent((Action<PointerEventData>)(e=>Move(e)));
                drag.add_EndDragEvent((Action<PointerEventData>)(e=>End(e)));
            }
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_DECK_REORDER_FAILED: no drag handles on this category. "+e.Message);}
    }
    static void Begin(DeckCategory c,DeckSlotModel s,GameObject slot,PointerEventData e)
    {
        try
        {
            Clear();cat=c;from=s.SlotIndex;to=-1;
            dimmed=slot.GetComponent<CanvasGroup>()??slot.AddComponent<CanvasGroup>();dimmed.alpha=0.45f;
            var canvas=slot.GetComponentInParent<Canvas>().rootCanvas;
            var size=slot.GetComponent<RectTransform>().rect.size;
            ghost=Picture("FA_DeckReorderGhost",canvas.transform,size,new Color(1,1,1,0.85f));
            var icon=slot.GetComponentInChildren<DeckUnitButton>(true)?._unitIcon;
            if(icon!=null&&icon.sprite!=null){var g=ghost.GetComponent<Image>();g.sprite=icon.sprite;g.preserveAspect=true;}
            marker=Picture("FA_DeckReorderMarker",canvas.transform,new Vector2(6,size.y),Mark);marker.SetActive(false);
            Move(e);
        }
        catch(Exception x){MelonLogger.Error("FREEDOM_ARROW_DECK_REORDER_FAILED: drag start. "+x.Message);Clear();}
    }
    static GameObject Picture(string name,Transform parent,Vector2 size,Color color)
    {
        var go=new GameObject(name);go.transform.SetParent(parent,false);
        var img=go.AddComponent<Image>();img.color=color;img.raycastTarget=false;
        var rt=go.GetComponent<RectTransform>();rt.sizeDelta=size;rt.SetAsLastSibling();
        return go;
    }
    static void Place(GameObject go,Vector2 screen,Camera cam)
    {
        var rt=go.GetComponent<RectTransform>();
        if(RectTransformUtility.ScreenPointToWorldPointInRectangle(rt.parent.GetComponent<RectTransform>(),screen,cam,out var w))rt.position=w;
    }
    static void Move(PointerEventData e)
    {
        if(cat==null||ghost==null)return;
        try
        {
            var cam=e.pressEventCamera;Place(ghost,e.position,cam);
            to=Target(e.position,cam,out var rt);
            if(to<0||to==from){marker.SetActive(false);return;}
            var corners=new Vector3[4];rt.GetWorldCorners(corners);
            var edge=to<from?(corners[0]+corners[1])/2:(corners[2]+corners[3])/2;   // left edge when moving left, right edge when moving right
            marker.SetActive(true);marker.GetComponent<RectTransform>().position=edge;
        }
        catch(Exception x){MelonLogger.Error("FREEDOM_ARROW_DECK_REORDER_FAILED: drag. "+x.Message);Clear();}
    }
    // Slot index under the pointer in the dragged category; an empty slot means "last filled slot"; -1 = outside the category.
    static int Target(Vector2 screen,Camera cam,out RectTransform hit)
    {
        hit=null;var box=cat._slotsContainer;int last=-1,found=-1;
        for(int i=0;i<box.childCount;i++)
        {
            var child=box.GetChild(i);if(!child.gameObject.activeInHierarchy)continue;
            var b=child.GetComponentInChildren<DeckUnitButton>(true);bool filled=b!=null&&b.Slot!=null&&b.Slot.IsValid;
            var rt=child.GetComponent<RectTransform>();
            if(filled){last=b.Slot.SlotIndex;if(found<0)hit=rt;}
            if(found<0&&RectTransformUtility.RectangleContainsScreenPoint(rt,screen,cam)){hit=rt;found=filled?b.Slot.SlotIndex:int.MaxValue;}
        }
        if(found==int.MaxValue){found=last;for(int i=0;i<box.childCount;i++){var b=box.GetChild(i).GetComponentInChildren<DeckUnitButton>(true);if(b!=null&&b.Slot!=null&&b.Slot.IsValid&&b.Slot.SlotIndex==last)hit=box.GetChild(i).GetComponent<RectTransform>();}}
        return found;
    }
    static void End(PointerEventData e)
    {
        try
        {
            if(cat==null)return;
            int target=Target(e.position,e.pressEventCamera,out _);
            if(target>=0&&target!=from)Apply(cat,from,target);
        }
        catch(Exception x){MelonLogger.Error("FREEDOM_ARROW_DECK_REORDER_FAILED: drop; the deck is unchanged unless the log shows a move. "+x.Message);}
        finally{Clear();}
    }
    static void Apply(DeckCategory c,int a,int b)
    {
        var deck=c._deck;var type=c._type;var slots=deck.Slots[type];
        if(a<0||b<0||a>=slots.Length||b>=slots.Length||!slots[a].IsValid||!slots[b].IsValid)return;
        var moving=slots[a];
        if(a<b)for(int k=a;k<b;k++)slots[k]=slots[k+1];
        else for(int k=a;k>b;k--)slots[k]=slots[k-1];
        slots[b]=moving;
        for(int k=0;k<slots.Length;k++)slots[k].SlotIndex=k;
        deck.SendSlotChangedEvent(moving,true);   // redraws the category from the array and marks the deck changed (Save)
        MelonLogger.Msg($"FREEDOM_ARROW_DECK_REORDER {type}: slot {a} -> {b} (unit {moving.UnitID})");
    }
    static void Clear()
    {
        if(dimmed!=null)dimmed.alpha=1f;
        if(ghost!=null)UnityEngine.Object.Destroy(ghost);
        if(marker!=null)UnityEngine.Object.Destroy(marker);
        ghost=marker=null;dimmed=null;cat=null;from=to=-1;
    }
}
