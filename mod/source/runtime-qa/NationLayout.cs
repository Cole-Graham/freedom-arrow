using HarmonyLib;
using MelonLoader;
using UnityEngine;
using UnityEngine.UI;
using Il2CppBrokenArrow.Client.Ecs.Decks_v2.UI;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.ArmyBuilder;
using Il2CppBrokenArrow.DataBase.Models;

namespace FreedomArrow;

// Room for a fourth nation (Eurocorp), Osama 23 Nov 2026: "expand the choose a nation menu to fit a fourth flag ... In the Armory, move the row
// with nations and spec up just a tiny bit so we can fit a second row. The first row is the US and its specs, the second row is China and then
// Russia. All the other elements are kept the same ... edit the ui elements only enough".
// Only native objects are changed. The game still makes every flag and spec button and keeps its callbacks and filter bits.
// - Create Deck popup (DeckCreationPopup._countryContainer): with more flags than fit, the container is scaled down evenly, keeping its left and
//   top edges, so the flags fill the same width. Scale is not touched by layout groups.
// - Arsenal (HangarUnitFilter._countryButtonsContainer, one CountryFilterButtonsGroup per nation): the bar moves up by the room a second row needs;
//   China and Russia move into a copy of the bar container (made while it is empty, so no native button is cloned) under the US row.
// Sizes come from the live objects and are logged (FREEDOM_ARROW_NATION_LAYOUT), as the prefabs are not in our asset export.
static class NationLayout
{
    const int Russia=1,China=4;
    const string Row2Name="FA_NationRow2";
    static readonly Dictionary<IntPtr,int> groupCountry=new();
    static readonly Dictionary<IntPtr,(Vector2 Pivot,Vector2 Pos)> deckOriginal=new();
    static readonly Dictionary<IntPtr,Vector2> liftOriginal=new();
    static bool failed;
    static bool Ready=>!failed&&Runtime.IsApplied;

    public static void Install(HarmonyLib.Harmony harmony)
    {
        harmony.Patch(AccessTools.Method(typeof(CountryFilterButtonsGroup),"Initialize"),postfix:new HarmonyMethod(typeof(NationLayout),nameof(GroupReady)));
        harmony.Patch(AccessTools.Method(typeof(HangarUnitFilter),"Initialize"),postfix:new HarmonyMethod(typeof(NationLayout),nameof(ArsenalRows)));
        harmony.Patch(AccessTools.Method(typeof(HangarUnitFilter),"Release"),prefix:new HarmonyMethod(typeof(NationLayout),nameof(ArsenalRelease)));
        harmony.Patch(AccessTools.Method(typeof(DeckCreationPopup),"RenderCountries"),postfix:new HarmonyMethod(typeof(NationLayout),nameof(DeckFlags)));
        MelonLogger.Msg("FREEDOM_ARROW_NATION_LAYOUT installed: Create Deck flags fit the row; Arsenal US row + China/Russia row");
    }
    static void Fail(Exception e){failed=true;MelonLogger.Error("FREEDOM_ARROW_NATION_LAYOUT_FAILED: native layout kept. "+e);}

    public static void GroupReady(CountryFilterButtonsGroup __instance,Countries country)
    {
        if(Ready&&country!=null)groupCountry[__instance.Pointer]=country.Id;
    }

    // ---------- Create Deck popup
    public static void DeckFlags(DeckCreationPopup __instance)
    {
        if(!Ready)return;
        try
        {
            var rt=__instance._countryContainer?.GetComponent<RectTransform>();if(rt==null)return;
            if(!deckOriginal.TryGetValue(rt.Pointer,out var orig))deckOriginal[rt.Pointer]=orig=(rt.pivot,rt.anchoredPosition);
            rt.localScale=Vector3.one;rt.pivot=orig.Pivot;rt.anchoredPosition=orig.Pos;
            LayoutRebuilder.ForceRebuildLayoutImmediate(rt);
            var kids=Active(rt);
            var hlg=rt.GetComponent<HorizontalLayoutGroup>();
            float left=rt.rect.xMin+(hlg!=null?hlg.padding.left:0),width=rt.rect.width-(hlg!=null?hlg.padding.horizontal:0);
            var (xl,xr,yt)=Bounds(rt,kids);float need=xr-xl;
            string state=$"flags {kids.Count}, row {width:0.#} wide, flags need {need:0.#}, spacing {(hlg!=null?hlg.spacing:-1):0.#}";
            if(kids.Count<=3||need<=width+0.5f){MelonLogger.Msg("FREEDOM_ARROW_NATION_LAYOUT deck: "+state+"; unchanged");return;}
            float k=width/need;
            // Scale about the point that keeps the flags' left edge at the row's left edge and their top edge in place.
            float px=(left-k*xl)/(1-k);
            SetPivot(rt,new Vector2((px-rt.rect.xMin)/rt.rect.width,(yt-rt.rect.yMin)/rt.rect.height));
            rt.localScale=new Vector3(k,k,1);
            MelonLogger.Msg($"FREEDOM_ARROW_NATION_LAYOUT deck: {state}; scaled x{k:0.###} to fit");
        }
        catch(Exception e){Fail(e);}
    }

    // ---------- Arsenal flag bar
    public static void ArsenalRows(HangarUnitFilter __instance)
    {
        if(!Ready)return;
        try
        {
            var bar=__instance._countryButtonsContainer?.GetComponent<RectTransform>();var groups=__instance._countryFilterButtonsGroups;
            if(bar==null||groups==null||groups.Count==0)return;
            var parent=bar.parent.GetComponent<RectTransform>();
            var row2=parent.Find(Row2Name)?.GetComponent<RectTransform>();
            if(row2==null)
            {
                // Copy the bar while it is empty: park its children, clone, put them back. No native button is cloned.
                var park=new List<Transform>();for(int i=0;i<bar.childCount;i++)park.Add(bar.GetChild(i));
                var hold=new GameObject("FA_NationPark").transform;hold.SetParent(parent,false);hold.gameObject.SetActive(false);
                foreach(var c in park)c.SetParent(hold,false);
                row2=UnityEngine.Object.Instantiate(bar.gameObject,parent,false).GetComponent<RectTransform>();row2.name=Row2Name;
                foreach(var c in park)c.SetParent(bar,false);
                UnityEngine.Object.Destroy(hold.gameObject);
                row2.SetSiblingIndex(bar.GetSiblingIndex()+1);
                if(parent.GetComponent<LayoutGroup>()!=null)(row2.GetComponent<LayoutElement>()??row2.gameObject.AddComponent<LayoutElement>()).ignoreLayout=true;
            }
            // Row 1: the US and every nation that is not China or Russia (Eurocorp), in native order. Row 2: China, then Russia.
            var first=new List<Transform>();Transform china=null,russia=null;
            for(int i=0;i<groups.Count;i++)
            {
                var g=groups[i];if(g==null)continue;
                int id=groupCountry.TryGetValue(g.Pointer,out var c)?c:0;
                if(id==China)china=g.transform;else if(id==Russia)russia=g.transform;else first.Add(g.transform);
            }
            int firstIndex=int.MaxValue;foreach(var t in first)if(t.parent==bar)firstIndex=Math.Min(firstIndex,t.GetSiblingIndex());
            foreach(var t in new[]{china,russia})if(t!=null)t.SetParent(row2,false);
            if(china!=null)china.SetSiblingIndex(0);if(russia!=null)russia.SetSiblingIndex(row2.childCount-1);
            // Row 2 starts under the US flag, not under ALL (if ALL sits inside the bar).
            LayoutRebuilder.ForceRebuildLayoutImmediate(bar);
            var h1=bar.GetComponent<HorizontalLayoutGroup>();var h2=row2.GetComponent<HorizontalLayoutGroup>();
            Transform us=first.Count>0?first[0]:null;
            int pad=-1;
            if(h1!=null&&h2!=null&&us!=null&&us.parent==bar)
            {
                // The width of everything left of the US flag in row 1 (the ALL button), from preferred widths, so it does not depend on whether
                // the bar has been laid out yet (Osama 23 Nov 18:0x: in dev.10 China sat under ALL, "the Chinese flag is right under the US").
                float x=h1.padding.left;
                for(int i=0;i<us.GetSiblingIndex();i++){var c=bar.GetChild(i).GetComponent<RectTransform>();if(c!=null&&c.gameObject.activeSelf)x+=LayoutUtility.GetPreferredWidth(c)+h1.spacing;}
                pad=Mathf.RoundToInt(x);
                h2.padding=new RectOffset(pad,h1.padding.right,h1.padding.top,h1.padding.bottom);
            }
            // Move the bar up just enough for a second row above the search line, and put row 2 under it.
            var lift=LiftTarget(bar,__instance);
            if(!liftOriginal.TryGetValue(lift.Pointer,out var orig))liftOriginal[lift.Pointer]=orig=lift.anchoredPosition;
            lift.anchoredPosition=orig;
            if(parent.GetComponent<LayoutGroup>()!=null)LayoutRebuilder.ForceRebuildLayoutImmediate(parent);
            float rowH=RowHeight(bar),gap=Mathf.Max(4f,rowH*0.15f);
            float room=Room(bar,__instance);
            float up=Mathf.Max(0f,rowH+gap-room);
            lift.anchoredPosition=orig+new Vector2(0,up);
            row2.anchorMin=bar.anchorMin;row2.anchorMax=bar.anchorMax;row2.pivot=bar.pivot;row2.sizeDelta=bar.sizeDelta;
            row2.localPosition=bar.localPosition-new Vector3(0,rowH+gap,0);
            LayoutRebuilder.ForceRebuildLayoutImmediate(row2);
            MelonLogger.Msg($"FREEDOM_ARROW_NATION_LAYOUT arsenal: groups {groups.Count}, row 1 {first.Count} nation(s) + ALL{(firstIndex>0&&firstIndex!=int.MaxValue?" inside the bar":" outside the bar")}, "+
                $"row 2 China={(china!=null)} Russia={(russia!=null)} starts at {pad}; row {rowH:0.#} high, gap {gap:0.#}, room below {room:0.#}, moved up {up:0.#} ({lift.name}); "+
                $"bar parent layout={(parent.GetComponent<LayoutGroup>()?.GetType().Name??"none")}, bar layout={(h1!=null?"HLG":"none")}");
        }
        catch(Exception e){Fail(e);}
    }

    // Before the native release, China and Russia go back into the native bar, so the game releases its groups as it made them.
    public static void ArsenalRelease(HangarUnitFilter __instance)
    {
        if(failed)return;
        try
        {
            var bar=__instance._countryButtonsContainer;var row2=bar?.parent?.Find(Row2Name);if(row2==null)return;
            while(row2.childCount>0)row2.GetChild(0).SetParent(bar,false);
        }
        catch(Exception e){Fail(e);}
    }

    // The object to move up: the bar itself, or its nearest ancestor that a layout group does not place and that does not hold the search line.
    static RectTransform LiftTarget(RectTransform bar,HangarUnitFilter f)
    {
        var search=f._searchNameInputField?.transform;
        for(var t=bar;t!=null;t=t.parent?.GetComponent<RectTransform>())
        {
            if(search!=null&&search.IsChildOf(t))break;
            if(t.parent==null||t.parent.GetComponent<LayoutGroup>()==null)return t;
        }
        return bar;
    }
    static float RowHeight(RectTransform bar)
    {
        float h=0;foreach(var c in Active(bar))h=Mathf.Max(h,c.rect.height);
        return h>0?h:bar.rect.height;
    }
    // Free height between the bar's bottom and the top of the search line (world space, in the bar parent's units).
    static float Room(RectTransform bar,HangarUnitFilter f)
    {
        var s=f._searchNameInputField?.GetComponent<RectTransform>();if(s==null)return 0;
        var p=bar.parent;var a=new Vector3[4];var b=new Vector3[4];bar.GetWorldCorners(a);s.GetWorldCorners(b);
        float barBottom=p.InverseTransformPoint(a[0]).y,searchTop=p.InverseTransformPoint(b[1]).y;
        return Mathf.Max(0f,barBottom-searchTop);
    }
    static List<RectTransform> Active(RectTransform rt)
    {
        var l=new List<RectTransform>();
        for(int i=0;i<rt.childCount;i++){var c=rt.GetChild(i);if(c.gameObject.activeSelf)l.Add(c.GetComponent<RectTransform>());}
        return l;
    }
    // Left, right and top edges of the children in the container's local space.
    static (float Xl,float Xr,float Yt) Bounds(RectTransform rt,List<RectTransform> kids)
    {
        float xl=float.MaxValue,xr=float.MinValue,yt=float.MinValue;
        foreach(var c in kids)
        {
            var p=c.localPosition;var r=c.rect;
            xl=Mathf.Min(xl,p.x+r.xMin);xr=Mathf.Max(xr,p.x+r.xMax);yt=Mathf.Max(yt,p.y+r.yMax);
        }
        return kids.Count==0?(rt.rect.xMin,rt.rect.xMax,rt.rect.yMax):(xl,xr,yt);
    }
    // Change the pivot without moving the rectangle.
    static void SetPivot(RectTransform rt,Vector2 pivot)
    {
        var d=pivot-rt.pivot;var size=rt.rect.size;
        rt.pivot=pivot;rt.anchoredPosition+=new Vector2(d.x*size.x*rt.localScale.x,d.y*size.y*rt.localScale.y);
    }
}
