using System.Collections;
using System.Reflection;
using System.Text.Json.Nodes;
using HarmonyLib;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
namespace FreedomArrow;
// Create a lobby: one tab per game size (Lateralus 16 Nov 2026, thread 1571554273639006392: "the menu that pops up should have tabs or
// some selector buttons to view maps of each game size seperately. 1v1, 2v2, 3v3, and 5v5 (we will never create maps dedicated to 4v4 so
// don't add a tab for that)"). The window is ArrowQueue's Panels.ShowMaps(maps, def, onPick, onCancel, mode, create) (decompiled
// ArrowQueue.dll 0ab2455b). For create == true the prefix keeps the full list and leaves only the maps of one size in it; the postfix adds
// the four tabs at the top right with ArrowQueue's own UiKit.TextButton. A tab click shows the window again with that size. A map is in a
// size by the "[1v1]" etc. tag in its name; a map without a tag is in every tab. Tabs with no maps do nothing (an empty card grid has
// a negative height). The search window (create == false) is not changed.
// Only the mod's own copy of an [FA] map (Lateralus 17 Nov 2026, same thread: "when I have local copies of a map in my game install, it
// shows them in this menu, I only want to see the copy that comes with the mod"). The game lists every scenario on the disk, and a map
// author's own copy (another GUID, which InstallScenarios keeps) or an old version (his [1v1] Dead Center 0.1) appears beside the packaged
// one. So the window keeps an [FA] map only if this package ships that name (UserData/FreedomArrow/scenarios/*/meta.json "scenario"). When
// the listed copy of a shipped name has another GUID (ArrowQueue keeps one map per name), it is swapped for the packaged copy, found with
// ArrowQueue's own Game.AllScenarios and Game.Workshop. Maps without the [FA] prefix are not changed. Nothing is deleted from the disk.
static class LobbyMapTabs
{
    static readonly string[] Sizes={"1v1","2v2","3v3","5v5"};
    static MethodInfo show,button;static FieldInfo win,openToSearch,orange,dim;static MethodInfo showOpen;
    static IList full;static object def,onPick,onCancel;static string mode,tab;static bool again,broken;
    static MethodInfo all,workshop;static Dictionary<string,string> shipped;
    public static void Install(HarmonyLib.Harmony h)
    {
        var panels=AccessTools.TypeByName("ArrowQueue.Panels");var kit=AccessTools.TypeByName("ArrowQueue.UiKit");var page=AccessTools.TypeByName("ArrowQueue.ModPage");
        show=panels==null?null:AccessTools.Method(panels,"ShowMaps");button=kit==null?null:AccessTools.Method(kit,"TextButton");
        win=panels==null?null:AccessTools.Field(panels,"_win");openToSearch=panels==null?null:AccessTools.Field(panels,"OpenToSearch");showOpen=panels==null?null:AccessTools.Method(panels,"ShowOpen");
        orange=page==null?null:AccessTools.Field(page,"Orange");dim=page==null?null:AccessTools.Field(page,"Dim");
        var game=AccessTools.TypeByName("ArrowQueue.Game");
        all=game==null?null:AccessTools.Method(game,"AllScenarios");workshop=game==null?null:AccessTools.Method(game,"Workshop");
        if(show==null||button==null||win==null||openToSearch==null||showOpen==null||orange==null||dim==null||show.GetParameters().Length!=6)
        {MelonLogger.Error("FREEDOM_ARROW_LOBBY_TABS: ArrowQueue map window not found; Create a lobby shows every map in one list");return;}
        h.Patch(show,prefix:new HarmonyMethod(typeof(LobbyMapTabs),nameof(Before)),postfix:new HarmonyMethod(typeof(LobbyMapTabs),nameof(After)));
        MelonLogger.Msg("FREEDOM_ARROW_LOBBY_TABS installed: Create a lobby has 1v1 / 2v2 / 3v3 / 5v5 tabs");
    }
    static string NameOf(object m)=>(m?.GetType().GetProperty("Name")?.GetValue(m) as string??"").Trim();
    static string SizeOf(object m)
    {
        var name=NameOf(m);
        return Sizes.FirstOrDefault(s=>name.Contains("["+s+"]"));
    }
    static string GuidOf(object m)
    {
        try
        {
            var g=m.GetType().GetProperty("Guid")?.GetValue(m)?.ToString();
            if(!string.IsNullOrEmpty(g))return g;
            var folder=m.GetType().GetProperty("Folder")?.GetValue(m) as string;
            var meta=folder==null?null:Path.Combine(folder,"meta.json");
            return meta!=null&&File.Exists(meta)?JsonNode.Parse(File.ReadAllText(meta))?["guid"]?.GetValue<string>():null;
        }
        catch{return null;}
    }
    static Dictionary<string,string> Shipped()
    {
        var names=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
        var root=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","scenarios");
        if(!Directory.Exists(root))return names;
        foreach(var folder in Directory.GetDirectories(root))
        {
            try
            {
                var meta=JsonNode.Parse(File.ReadAllText(Path.Combine(folder,"meta.json")));
                names[(meta?["scenario"]?.GetValue<string>()??Path.GetFileName(folder)).Trim()]=meta?["guid"]?.GetValue<string>()??"";
            }
            catch{}
        }
        return names;
    }
    static object ModCopy(string name,string guid)
    {
        if(all==null||workshop==null||guid=="")return null;
        foreach(var s in (IEnumerable)all.Invoke(null,null)!)
            if(string.Equals(NameOf(s),name,StringComparison.OrdinalIgnoreCase)&&string.Equals(GuidOf(s),guid,StringComparison.OrdinalIgnoreCase))
                return workshop.Invoke(null,new[]{s});
        return null;
    }
    static void ModCopiesOnly(IList maps)
    {
        shipped??=Shipped();
        if(shipped.Count==0)return;   // no packaged scenarios found: leave ArrowQueue's list as it is
        var keep=new List<object>();var dropped=new List<string>();var swapped=new List<string>();
        foreach(var m in maps)
        {
            var name=NameOf(m);
            if(!name.StartsWith("[FA]")){keep.Add(m);continue;}
            if(!shipped.TryGetValue(name,out var guid)){dropped.Add(name);continue;}
            var g=GuidOf(m);
            if(g!=null&&!string.Equals(g,guid,StringComparison.OrdinalIgnoreCase)&&ModCopy(name,guid) is {} mod){keep.Add(mod);swapped.Add(name);continue;}
            keep.Add(m);
        }
        if(dropped.Count+swapped.Count==0)return;
        maps.Clear();foreach(var m in keep)maps.Add(m);
        MelonLogger.Msg($"FREEDOM_ARROW_LOBBY_TABS: local map copies left out: {string.Join(", ",dropped)}; swapped for the mod's copy: {string.Join(", ",swapped)}");
    }
    static int Count(string size){int n=0;foreach(var m in full)if(SizeOf(m) is var s&&(s==null||s==size))n++;return n;}
    static void Before(object[] __args)
    {
        if(broken||!(__args[5] is true)||__args[0] is not IList maps)return;
        try
        {
            if(!again)
            {
                try{ModCopiesOnly(maps);}
                catch(Exception x){MelonLogger.Error("FREEDOM_ARROW_LOBBY_TABS: local map filter skipped. "+(x.InnerException??x).Message);}
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
