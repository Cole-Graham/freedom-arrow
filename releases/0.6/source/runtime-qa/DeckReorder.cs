using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.ArmyBuilder;
using MelonLoader;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;
namespace FreedomArrow;
// Drag and drop to reorder units in the deck editor (Lateralus 18 Nov 2026, thread 1572659362558771252: "improving the deck editing menu,
// so players can drag and drop units to re-order them"). Read from GameAssembly 1.2.2.1: each category is one DeckSlotModel[] in
// Deck.Slots and the order is the array order; SlotIndex (+0x1C, saved as "slot") mirrors it. RemoveUnitFromSlot (0x6F4780) shifts later
// slots down the same way. DeckCategory draws one child of _slotsContainer per slot (BaseInit 0x567470); a filled slot's root object is
// its DeckUnitButton. The slot's own UiDragElement is switched off in the deck view and stayed off when switched on (dev.38-test1 found no
// drag events on Vengeance), so this reads the mouse itself: press on a filled slot, move more than 12 px, release on another slot of the
// same category. The drop moves the slot in the array, renumbers SlotIndex and raises Deck.SendSlotChangedEvent(slot, true):
// DeckCategory.OnSlotChanged (0x568110) then redraws the whole category from the array, and DeckOverview.OnSlotChanged (0x571520) marks
// the deck changed and shows Save. Content and points do not change, so the deck stays a valid vanilla deck. The battle shop lists cards
// in this order (ShopPanelUI.ShowMainCards uses IterSlots). Work per frame only while the deck editor is open (DeckOverview.Active).
static class DeckReorder
{
    const float Threshold=12f;
    static readonly Color Mark=new(1f,0.55f,0.1f,0.95f);
    static readonly List<DeckCategory> cats=new();
    static DeckCategory cat; static GameObject source; static int from=-1; static Vector2 pressAt; static bool dragging;
    static GameObject ghost, marker; static CanvasGroup dimmed; static bool broken;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(DeckCategory),nameof(DeckCategory.BaseInit)),postfix:new HarmonyMethod(typeof(DeckReorder),nameof(After)));
        MelonLogger.Msg("FREEDOM_ARROW_DECK_REORDER installed: drag a unit in the deck editor to move it within its category");
    }
    static void After(DeckCategory __instance){ if(!cats.Any(c=>c!=null&&c.Pointer==__instance.Pointer))cats.Add(__instance); }
    public static void Tick()
    {
        if(broken||(!dragging&&source==null&&!DeckOverview.Active))return;
        try
        {
            var mouse=Mouse.current;if(mouse==null)return;
            var pos=mouse.position.ReadValue();
            if(mouse.leftButton.wasPressedThisFrame){Clear();Press(pos);return;}
            if(source==null)return;
            if(!mouse.leftButton.isPressed){if(dragging)Drop(pos);Clear();return;}
            if(!dragging&&(pos-pressAt).magnitude>Threshold)Begin();
            if(dragging)Move(pos);
        }
        catch(Exception x){broken=true;Clear();MelonLogger.Error("FREEDOM_ARROW_DECK_REORDER_FAILED: reordering off until restart; decks are unchanged unless the log shows a move. "+x);}
    }
    static Camera Cam(Component c){var cv=c.GetComponentInParent<Canvas>()?.rootCanvas;return cv==null||cv.renderMode==RenderMode.ScreenSpaceOverlay?null:cv.worldCamera;}
    static bool Filled(Transform t,out DeckSlotModel s){var b=t.GetComponentInChildren<DeckUnitButton>(true);s=b?.Slot;return s!=null&&s.IsValid;}
    static void Press(Vector2 pos)
    {
        cats.RemoveAll(c=>c==null||c._slotsContainer==null);
        foreach(var c in cats)
        {
            if(!c.gameObject.activeInHierarchy)continue;
            var box=c._slotsContainer;var cam=Cam(c);
            for(int i=0;i<box.childCount;i++)
            {
                var t=box.GetChild(i);
                if(!t.gameObject.activeInHierarchy||!Filled(t,out var s))continue;
                if(!RectTransformUtility.RectangleContainsScreenPoint(t.GetComponent<RectTransform>(),pos,cam))continue;
                cat=c;source=t.gameObject;from=s.SlotIndex;pressAt=pos;return;
            }
        }
    }
    static void Begin()
    {
        dragging=true;
        dimmed=source.GetComponent<CanvasGroup>()??source.AddComponent<CanvasGroup>();dimmed.alpha=0.45f;
        var canvas=source.GetComponentInParent<Canvas>().rootCanvas;
        var size=source.GetComponent<RectTransform>().rect.size;
        ghost=Picture("FA_DeckReorderGhost",canvas.transform,size*0.8f,new Color(1,1,1,0.85f));
        var icon=source.GetComponentInChildren<DeckUnitButton>(true)?._unitIcon;
        if(icon!=null&&icon.sprite!=null){var g=ghost.GetComponent<Image>();g.sprite=icon.sprite;g.preserveAspect=true;}
        marker=Picture("FA_DeckReorderMarker",canvas.transform,new Vector2(6,size.y),Mark);marker.SetActive(false);
    }
    static GameObject Picture(string name,Transform parent,Vector2 size,Color color)
    {
        var go=new GameObject(name);go.transform.SetParent(parent,false);
        var img=go.AddComponent<Image>();img.color=color;img.raycastTarget=false;
        var rt=go.GetComponent<RectTransform>();rt.sizeDelta=size;rt.SetAsLastSibling();
        return go;
    }
    static void Move(Vector2 pos)
    {
        var cam=Cam(cat);var rt=ghost.GetComponent<RectTransform>();
        if(RectTransformUtility.ScreenPointToWorldPointInRectangle(rt.parent.GetComponent<RectTransform>(),pos,cam,out var w))rt.position=w;
        int to=Target(pos,cam,out var hit);
        if(to<0||to==from||hit==null){marker.SetActive(false);return;}
        var corners=new Vector3[4];hit.GetWorldCorners(corners);
        marker.SetActive(true);marker.GetComponent<RectTransform>().position=to<from?(corners[0]+corners[1])/2:(corners[2]+corners[3])/2;   // left edge moving left, right edge moving right
    }
    // Slot index under the pointer in the dragged category; an empty slot means "after the last filled slot"; -1 = outside the category.
    static int Target(Vector2 pos,Camera cam,out RectTransform hit)
    {
        hit=null;var box=cat._slotsContainer;int last=-1;RectTransform lastRt=null;bool overEmpty=false;
        for(int i=0;i<box.childCount;i++)
        {
            var t=box.GetChild(i);if(!t.gameObject.activeInHierarchy)continue;
            var rt=t.GetComponent<RectTransform>();bool filled=Filled(t,out var s);
            if(filled&&s.SlotIndex>last){last=s.SlotIndex;lastRt=rt;}
            if(!RectTransformUtility.RectangleContainsScreenPoint(rt,pos,cam))continue;
            if(filled){hit=rt;return s.SlotIndex;}
            overEmpty=true;
        }
        if(overEmpty){hit=lastRt;return last;}
        return -1;
    }
    static void Drop(Vector2 pos)
    {
        int to=Target(pos,Cam(cat),out _);
        if(to<0||to==from)return;
        var deck=cat._deck;var type=cat._type;var slots=deck.Slots[type];
        if(from>=slots.Length||to>=slots.Length||!slots[from].IsValid||!slots[to].IsValid)return;
        var moving=slots[from];
        if(from<to)for(int k=from;k<to;k++)slots[k]=slots[k+1];
        else for(int k=from;k>to;k--)slots[k]=slots[k-1];
        slots[to]=moving;
        for(int k=0;k<slots.Length;k++)slots[k].SlotIndex=k;
        deck.SendSlotChangedEvent(moving,true);   // redraws the category from the array and marks the deck changed (Save)
        MelonLogger.Msg($"FREEDOM_ARROW_DECK_REORDER {type}: slot {from} -> {to} (unit {moving.UnitID})");
    }
    static void Clear()
    {
        if(dimmed!=null)dimmed.alpha=1f;
        if(ghost!=null)UnityEngine.Object.Destroy(ghost);
        if(marker!=null)UnityEngine.Object.Destroy(marker);
        ghost=marker=null;dimmed=null;cat=null;source=null;from=-1;dragging=false;
    }
}
