using System.Reflection;
using System.Text.Json.Nodes;
using HarmonyLib;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
namespace FreedomArrow;
// Lateralus 20 Nov 2026 (thread 1572962048705429598): "it would nice if the map selection in the create mod lobby menu, showed "New" and
// "Updated" when we add new maps or update the existing maps (with version change). Not in a new menu, but just marked with those labels
// either overlaid on the map picture or near it." The build writes UserData/FreedomArrow/map-labels.json: each map compared with the
// current playtest release on the live manifest (tools/pla-specs/map_labels.py). A name the release did not have is New when its name
// without the version number is also new, and Updated when only the version number differs. ArrowQueue's map window draws a picture card
// (Panels.Card, 6 maps or fewer) or a text row (Panels.RowItem) per map (decompiled ArrowQueue.dll 0ab2455b); a postfix puts the tag on
// the newest child of the parent: top right of the picture, or at the right end of the row (the name gets 100 px less room).
// Lateralus 27 Nov 2026: "I want the create a lobby menu to label ranked maps with \"ranked\", similar to the \"last map\", \"new\", and \"updated\"
// labels". A map in the ranked pool (maps.json, MapSizes.IsRanked) also gets RANKED; with two tags the second sits under the first on a picture
// card and to the left of it on a row (the name gets 100 px less room per tag).
static class MapLabels
{
    static readonly Dictionary<string,string> labels=new(StringComparer.OrdinalIgnoreCase);
    static MethodInfo box,label;static bool broken;
    public static void Install(HarmonyLib.Harmony h)
    {
        var path=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","map-labels.json");
        if(File.Exists(path))
            foreach(var (name,v) in JsonNode.Parse(File.ReadAllText(path))!["maps"]!.AsObject()){var s=v!.GetValue<string>();if(s=="new"||s=="updated")labels[name.Trim()]=s;}
        else MelonLogger.Msg("FREEDOM_ARROW_MAP_LABELS: no map-labels.json, so no New / Updated tags");
        var panels=AccessTools.TypeByName("ArrowQueue.Panels");var kit=AccessTools.TypeByName("ArrowQueue.UiKit");
        var card=panels==null?null:AccessTools.Method(panels,"Card");var row=panels==null?null:AccessTools.Method(panels,"RowItem");
        box=kit==null?null:AccessTools.Method(kit,"Box");label=panels==null?null:AccessTools.Method(panels,"Label");
        if(card==null||row==null||box==null||label==null||box.GetParameters().Length!=8||label.GetParameters().Length!=8)
        {MelonLogger.Error("FREEDOM_ARROW_MAP_LABELS: ArrowQueue map cards not found; no New / Updated / Ranked tags");return;}
        h.Patch(card,postfix:new HarmonyMethod(typeof(MapLabels),nameof(AfterCard)));
        h.Patch(row,postfix:new HarmonyMethod(typeof(MapLabels),nameof(AfterRow)));
        MelonLogger.Msg($"FREEDOM_ARROW_MAP_LABELS installed: {string.Join(", ",labels.Select(l=>l.Key+" = "+l.Value))}; ranked tags from maps.json");
    }
    static string NameOf(object m)=>(m?.GetType().GetProperty("Name")?.GetValue(m) as string)?.Trim();
    static void AfterCard(object[] __args)=>Tag(__args,true);
    static void AfterRow(object[] __args)=>Tag(__args,false);
    static readonly Color NewFill=new(0.19f,0.46f,0.26f,0.95f),UpdatedFill=new(0.24f,0.46f,0.68f,0.95f),RankedFill=new(0.62f,0.45f,0.10f,0.95f);
    static void Tag(object[] a,bool card)
    {
        if(broken||a[0] is not Transform parent||parent.childCount==0||NameOf(a[1]) is not {} name)return;
        var tags=new List<(string text,Color fill)>();
        if(labels.TryGetValue(name,out var kind))tags.Add(kind=="new"?("NEW",NewFill):("UPDATED",UpdatedFill));
        if(MapSizes.IsRanked(name))tags.Add(("RANKED",RankedFill));
        if(tags.Count==0)return;
        try
        {
            var item=parent.GetChild(parent.childCount-1);
            var corner=new Vector2(1f,1f);
            for(int i=0;i<tags.Count;i++)
            {
                var at=card?new Vector2(-10f,-10f-28f*i):new Vector2(-12f-104f*i,-14f);
                var tag=(GameObject)box.Invoke(null,new object[]{item,"FaMapLabel",corner,corner,at,new Vector2(96f,22f),tags[i].fill,false})!;
                var text=label.Invoke(null,new object[]{tag.transform,12f,0f,2f,96f,18f,Color.white,true})!;
                text.GetType().GetProperty("text")!.SetValue(text,tags[i].text);
                var align=text.GetType().GetProperty("alignment")!;align.SetValue(text,Enum.ToObject(align.PropertyType,514));   // centre, as ArrowQueue's own tag
            }
            if(!card&&item.Find("Bar/Text") is RectTransform bar)bar.sizeDelta=new Vector2(bar.sizeDelta.x-100f*tags.Count,bar.sizeDelta.y);
        }
        catch(Exception x){broken=true;MelonLogger.Error("FREEDOM_ARROW_MAP_LABELS_FAILED: no tags from now on. "+x.Message);}
    }
}
