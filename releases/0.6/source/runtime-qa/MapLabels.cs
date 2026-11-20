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
static class MapLabels
{
    static readonly Dictionary<string,string> labels=new(StringComparer.OrdinalIgnoreCase);
    static MethodInfo box,label;static bool broken;
    public static void Install(HarmonyLib.Harmony h)
    {
        var path=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","map-labels.json");
        if(!File.Exists(path)){MelonLogger.Msg("FREEDOM_ARROW_MAP_LABELS not installed: no map-labels.json");return;}
        var maps=JsonNode.Parse(File.ReadAllText(path))!["maps"]!.AsObject();
        foreach(var (name,v) in maps){var s=v!.GetValue<string>();if(s=="new"||s=="updated")labels[name.Trim()]=s;}
        if(labels.Count==0){MelonLogger.Msg("FREEDOM_ARROW_MAP_LABELS not installed: no new or updated maps");return;}
        var panels=AccessTools.TypeByName("ArrowQueue.Panels");var kit=AccessTools.TypeByName("ArrowQueue.UiKit");
        var card=panels==null?null:AccessTools.Method(panels,"Card");var row=panels==null?null:AccessTools.Method(panels,"RowItem");
        box=kit==null?null:AccessTools.Method(kit,"Box");label=panels==null?null:AccessTools.Method(panels,"Label");
        if(card==null||row==null||box==null||label==null||box.GetParameters().Length!=8||label.GetParameters().Length!=8)
        {MelonLogger.Error("FREEDOM_ARROW_MAP_LABELS: ArrowQueue map cards not found; no New / Updated tags");return;}
        h.Patch(card,postfix:new HarmonyMethod(typeof(MapLabels),nameof(AfterCard)));
        h.Patch(row,postfix:new HarmonyMethod(typeof(MapLabels),nameof(AfterRow)));
        MelonLogger.Msg($"FREEDOM_ARROW_MAP_LABELS installed: {string.Join(", ",labels.Select(l=>l.Key+" = "+l.Value))}");
    }
    static string Of(object m)=>(m?.GetType().GetProperty("Name")?.GetValue(m) as string)?.Trim() is {} n&&labels.TryGetValue(n,out var s)?s:null;
    static void AfterCard(object[] __args)=>Tag(__args,true);
    static void AfterRow(object[] __args)=>Tag(__args,false);
    static void Tag(object[] a,bool card)
    {
        if(broken||a[0] is not Transform parent||parent.childCount==0||Of(a[1]) is not {} kind)return;
        try
        {
            var item=parent.GetChild(parent.childCount-1);
            bool isNew=kind=="new";
            var fill=isNew?new Color(0.19f,0.46f,0.26f,0.95f):new Color(0.24f,0.46f,0.68f,0.95f);
            var corner=new Vector2(1f,1f);
            var tag=(GameObject)box.Invoke(null,new object[]{item,"FaMapLabel",corner,corner,card?new Vector2(-10f,-10f):new Vector2(-12f,-14f),new Vector2(96f,22f),fill,false})!;
            var text=label.Invoke(null,new object[]{tag.transform,12f,0f,2f,96f,18f,Color.white,true})!;
            text.GetType().GetProperty("text")!.SetValue(text,isNew?"NEW":"UPDATED");
            var align=text.GetType().GetProperty("alignment")!;align.SetValue(text,Enum.ToObject(align.PropertyType,514));   // centre, as ArrowQueue's own tag
            if(!card&&item.Find("Bar/Text") is RectTransform name)name.sizeDelta=new Vector2(name.sizeDelta.x-100f,name.sizeDelta.y);
        }
        catch(Exception x){broken=true;MelonLogger.Error("FREEDOM_ARROW_MAP_LABELS_FAILED: no tags from now on. "+x.Message);}
    }
}
