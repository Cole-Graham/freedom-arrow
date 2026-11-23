using System.Reflection;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Mod Lobbies page without the group and search systems (Lateralus 22 Nov 2026, thread 1572962048705429598: "the whole group and search
// system for mod lobbies is really pointless, we just want to remove it (but don't remove it from the ranked system)"; "we still want the
// unranked mod lobbies, but everyone just manually joins lobbies"). ArrowQueue's ModPage.Build (decompiled ArrowQueue.dll 0ab2455b, 0.10.31)
// makes the left column: FORMAT squares (Mode_*), the FIND bar (Action), the search Status line, GROUP (GroupHead, Leave, Member0-4,
// MemberName0-4, GroupHint), CREATE YOUR OWN LOBBY (Create) and ONLINE WITH THE MOD (ModHead/ModCount/ModSub). The postfix moves the
// format, find, status and group parts into an inactive holder (ArrowQueue's own refresh can switch them on, they stay hidden) and moves
// Create and the online count up. Who is online keeps its list, without the Invite/Remove buttons (FillPeople postfix). ArrowQueue's
// party backend is unchanged: the Ranked page's group uses it.
static class ModLobbyNoGroup
{
    static FieldInfo fRows,fHint;static MethodInfo mText;static bool logged;
    public static void Install(HarmonyLib.Harmony h)
    {
        var page=AccessTools.TypeByName("ArrowQueue.ModPage");
        var build=page==null?null:AccessTools.Method(page,"Build");var fill=page==null?null:AccessTools.Method(page,"FillPeople");
        fRows=page==null?null:AccessTools.Field(page,"_rows");fHint=page==null?null:AccessTools.Field(page,"_hint");
        mText=AccessTools.Method(AccessTools.TypeByName("ArrowQueue.Text"),"T");
        if(build==null||fill==null){MelonLogger.Error("FREEDOM_ARROW_MOD_LOBBY_NO_GROUP: ArrowQueue ModPage.Build/FillPeople not found; the group and search stay");return;}
        h.Patch(build,postfix:new HarmonyMethod(typeof(ModLobbyNoGroup),nameof(AfterBuild)));
        h.Patch(fill,postfix:new HarmonyMethod(typeof(ModLobbyNoGroup),nameof(AfterPeople)));
        MelonLogger.Msg("FREEDOM_ARROW_MOD_LOBBY_NO_GROUP installed: Mod Lobbies page without group and search (Ranked keeps them)");
    }
    static readonly string[] Hide={"FormatHead","Action","Status","GroupHead","Leave","GroupHint"};
    static void AfterBuild(Transform body)
    {
        try
        {
            var left=body==null?null:body.Find("Left");if(left==null){MelonLogger.Warning("FREEDOM_ARROW_MOD_LOBBY_NO_GROUP: no Left column");return;}
            var holder=new GameObject("FA hidden group and search");holder.SetActive(false);holder.transform.SetParent(left,false);
            var move=new List<Transform>();
            for(int i=0;i<left.childCount;i++){var c=left.GetChild(i);var n=c.name;if(Array.IndexOf(Hide,n)>=0||n.StartsWith("Mode_")||n.StartsWith("Member"))move.Add(c);}
            foreach(var c in move)c.SetParent(holder.transform,false);
            // Create goes where FORMAT was; ONLINE WITH THE MOD follows it (the same 60/20/24 spacing as before)
            Y(left,"Create",70f);Y(left,"ModHead",130f);Y(left,"ModCount",150f);Y(left,"ModSub",154f);
            if(!logged){logged=true;MelonLogger.Msg($"FREEDOM_ARROW_MOD_LOBBY_NO_GROUP page built: {move.Count} group/search parts hidden");}
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_MOD_LOBBY_NO_GROUP build: "+e.Message);}
    }
    static void Y(Transform parent,string name,float y)
    {
        var t=parent.Find(name);var rt=t==null?null:t.GetComponent<RectTransform>();
        if(rt!=null)rt.anchoredPosition=new Vector2(rt.anchoredPosition.x,-y);
    }
    static void AfterPeople()
    {
        try
        {
            if(fRows?.GetValue(null) is Transform rows)
                foreach(var t in rows.GetComponentsInChildren<Transform>(true))if(t.name=="Invite"||t.name=="Kick")t.gameObject.SetActive(false);
            if(fHint?.GetValue(null) is Il2CppTMPro.TextMeshProUGUI hint)
                hint.text=mText?.Invoke(null,new object[]{"Игроки в сети с модом. Серые — другая сборка.","Players online with the mod. Grey: another build."}) as string??"Players online with the mod. Grey: another build.";
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_MOD_LOBBY_NO_GROUP people: "+e.Message);}
    }
}
