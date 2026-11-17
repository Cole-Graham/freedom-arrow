using System.Collections;
using System.Reflection;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Create a lobby: one tab per game size (Lateralus 16 Nov 2026, thread 1571554273639006392: "the menu that pops up should have tabs or
// some selector buttons to view maps of each game size seperately. 1v1, 2v2, 3v3, and 5v5 (we will never create maps dedicated to 4v4 so
// don't add a tab for that)"). The window is ArrowQueue's Panels.ShowMaps(maps, def, onPick, onCancel, mode, create) (decompiled
// ArrowQueue.dll 0ab2455b). For create == true the prefix keeps the full list and leaves only the maps of one size in it; the postfix adds
// the four tabs at the top right with ArrowQueue's own UiKit.TextButton. A tab click shows the window again with that size. A map is in a
// size by the "[1v1]" etc. tag in its name; a map without a tag is in every tab. Tabs with no maps do nothing (an empty card grid has
// a negative height). The search window (create == false) is not changed.
static class LobbyMapTabs
{
    static readonly string[] Sizes={"1v1","2v2","3v3","5v5"};
    static MethodInfo show,button;static FieldInfo win,openToSearch,orange,dim;static MethodInfo showOpen;
    static IList full;static object def,onPick,onCancel;static string mode,tab;static bool again,broken;
    public static void Install(HarmonyLib.Harmony h)
    {
        var panels=AccessTools.TypeByName("ArrowQueue.Panels");var kit=AccessTools.TypeByName("ArrowQueue.UiKit");var page=AccessTools.TypeByName("ArrowQueue.ModPage");
        show=panels==null?null:AccessTools.Method(panels,"ShowMaps");button=kit==null?null:AccessTools.Method(kit,"TextButton");
        win=panels==null?null:AccessTools.Field(panels,"_win");openToSearch=panels==null?null:AccessTools.Field(panels,"OpenToSearch");showOpen=panels==null?null:AccessTools.Method(panels,"ShowOpen");
        orange=page==null?null:AccessTools.Field(page,"Orange");dim=page==null?null:AccessTools.Field(page,"Dim");
        if(show==null||button==null||win==null||openToSearch==null||showOpen==null||orange==null||dim==null||show.GetParameters().Length!=6)
        {MelonLogger.Error("FREEDOM_ARROW_LOBBY_TABS: ArrowQueue map window not found; Create a lobby shows every map in one list");return;}
        h.Patch(show,prefix:new HarmonyMethod(typeof(LobbyMapTabs),nameof(Before)),postfix:new HarmonyMethod(typeof(LobbyMapTabs),nameof(After)));
        MelonLogger.Msg("FREEDOM_ARROW_LOBBY_TABS installed: Create a lobby has 1v1 / 2v2 / 3v3 / 5v5 tabs");
    }
    static string SizeOf(object m)
    {
        var name=m?.GetType().GetProperty("Name")?.GetValue(m) as string??"";
        return Sizes.FirstOrDefault(s=>name.Contains("["+s+"]"));
    }
    static int Count(string size){int n=0;foreach(var m in full)if(SizeOf(m) is var s&&(s==null||s==size))n++;return n;}
    static void Before(object[] __args)
    {
        if(broken||!(__args[5] is true)||__args[0] is not IList maps)return;
        try
        {
            if(!again)
            {
                full=(IList)Activator.CreateInstance(maps.GetType())!;foreach(var m in maps)full.Add(m);
                def=__args[1];onPick=__args[2];onCancel=__args[3];mode=__args[4] as string;
                if(full.Cast<object>().All(m=>SizeOf(m)==null)){full=null;return;}   // no size tags: ArrowQueue's own list
                tab=SizeOf(def) is {} d&&Count(d)>0?d:Sizes.First(s=>Count(s)>0);
            }
            if(full==null)return;
            maps.Clear();
            foreach(var m in full)if(SizeOf(m) is var s&&(s==null||s==tab))maps.Add(m);
        }
        catch(Exception x){broken=true;full=null;MelonLogger.Error("FREEDOM_ARROW_LOBBY_TABS_FAILED: one list from now on. "+x.Message);}
    }
    static void After(object[] __args)
    {
        if(broken||full==null||!(__args[5] is true))return;
        try
        {
            if(win.GetValue(null) is not GameObject w||w==null)return;
            for(int i=0;i<Sizes.Length;i++)
            {
                string size=Sizes[i];int n=Count(size);
                var color=size==tab?(Color)orange.GetValue(null)!:n>0?(Color)dim.GetValue(null)!:new Color(1f,1f,1f,0.25f);
                Action click=()=>Switch(size);
                // Right to left from the close button (x -26, 40 wide): 5v5 nearest it.
                button.Invoke(null,new object[]{w.transform,"FaSize"+size,new Vector2(1f,1f),new Vector2(-82f-(Sizes.Length-1-i)*72f,-28f),new Vector2(64f,30f),
                    size,18f,color,click,Enum.ToObject(button.GetParameters()[9].ParameterType,514)});   // 514 = centre, as ArrowQueue's default
            }
        }
        catch(Exception x){broken=true;MelonLogger.Error("FREEDOM_ARROW_LOBBY_TABS_FAILED: tabs not drawn. "+x.Message);}
    }
    static void Switch(string size)
    {
        if(broken||full==null||size==tab||Count(size)==0)return;
        try
        {
            bool open=(bool)openToSearch.GetValue(null)!;   // ShowMaps resets the "open to the mod search" box; keep the player's choice
            tab=size;again=true;
            var list=(IList)Activator.CreateInstance(full.GetType())!;
            show.Invoke(null,new object[]{list,def,onPick,onCancel,mode,true});
            openToSearch.SetValue(null,open);showOpen.Invoke(null,null);
        }
        catch(Exception x){broken=true;MelonLogger.Error("FREEDOM_ARROW_LOBBY_TABS_FAILED: tab switch. "+(x.InnerException??x).Message);}
        finally{again=false;}
    }
}
