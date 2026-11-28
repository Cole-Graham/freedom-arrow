using HarmonyLib;
using Il2CppBrokenArrow.BrokenArrow.Client.Ecs.MapEnvironment;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal;
using Il2CppBrokenArrow.Shared.Ecs.Localization;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppNetworkCommon.Enums.Common;
using MelonLoader;
using UnityEngine;
using UnityEngine.AddressableAssets;

namespace FreedomArrow;

// "Basic Hangar Indoors" (Osama 27 Nov 2026 16:0x PST, thread 1573418243715113213): a third hangar option, the default, that shows every unit,
// ground units too, on the spot where the basic hangar shows planes. 16:1x: "make sure ... the planes despawn when ground units are selected
// because in vanilla they keep the planes there because ground units use a different slot".
// Game code (GameAssembly 1.2.2.1):
// - EnvironmentService._contentMembershipHangarsMapping (ContentMembership -> HangarData[]) lists the hangars; the menu's environment buttons
//   (SwitchMenu.PrepareEnvironmentOptions) and SwitchEnvironment read it. The choice is the HangarData name in PlayerPrefs "hangar_environment",
//   default "HangarMain" (EnvironmentService.LoadHangarEnvironment 0x2D6840, called from InitHangarData 0x2D66E0 <- MainMenuUIController.Start).
// - ArsenalUnitPreviewData.GetSpawnPointByUnitType (0x540B10; callers InternalShowModelAsync and UpdateCurrentPreviewPosition) gives the
//   first spawn point whose UnitType flags match the unit.
// - ArsenalUnitPreview keeps one model per spawn-point type (_spawnedModel) and, before it shows a unit, calls DestroyModel (0x541050) for that
//   unit's type only. That is why a plane stays when a tank is shown.
// This file adds a HangarData copy of HangarMain named BasicHangarIndoors (own AssetReference to the same prefab), switches to it once per
// install (PlayerPrefs marker; later choices stay), sends every unit type to the Aircraft spawn point while it is the current hangar, and then
// removes every shown model, not only the same type, before a new unit is shown.
static class HangarIndoors
{
    internal const string Name="BasicHangarIndoors";
    const string Label="Basic Hangar Indoors",LabelZh="基础机库（室内）",Basic="HangarMain",Pref="hangar_environment",Marker="fa_hangar_indoors_default_v1";
    static EnvironmentService env;
    static bool busy,loggedSpawn,loggedClear;

    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(EnvironmentService),nameof(EnvironmentService.InitHangarData))??throw new MissingMethodException("EnvironmentService.InitHangarData"),
            prefix:new HarmonyMethod(typeof(HangarIndoors),nameof(AddHangar)));
        h.Patch(AccessTools.Method(typeof(ArsenalUnitPreviewData),nameof(ArsenalUnitPreviewData.GetSpawnPointByUnitType))??throw new MissingMethodException("ArsenalUnitPreviewData.GetSpawnPointByUnitType"),
            postfix:new HarmonyMethod(typeof(HangarIndoors),nameof(Spawn)));
        h.Patch(AccessTools.Method(typeof(ArsenalUnitPreview),nameof(ArsenalUnitPreview.DestroyModel))??throw new MissingMethodException("ArsenalUnitPreview.DestroyModel"),
            prefix:new HarmonyMethod(typeof(HangarIndoors),nameof(ClearAll)));
        h.Patch(AccessTools.Method(typeof(ArsenalUnitPreview),nameof(ArsenalUnitPreview.UpdateCurrentPreviewPosition))??throw new MissingMethodException("ArsenalUnitPreview.UpdateCurrentPreviewPosition"),
            prefix:new HarmonyMethod(typeof(HangarIndoors),nameof(KeepShown)));
        h.Patch(AccessTools.Method(typeof(LocalizationService),nameof(LocalizationService.TryResolveSimpleKey))??throw new MissingMethodException("LocalizationService.TryResolveSimpleKey"),
            postfix:new HarmonyMethod(typeof(HangarIndoors),nameof(Resolve)));
        MelonLogger.Msg("FREEDOM_ARROW_HANGAR_INDOORS installed");
    }

    static bool Active()
    {
        try{return env!=null&&env.CurrentHangarEnvironmentName==Name;}catch{return false;}
    }

    // Prefix of InitHangarData (main menu start): add the hangar once per game start, then make it the default once per install.
    public static void AddHangar(EnvironmentService __instance)
    {
        env=__instance;
        try
        {
            var map=__instance._contentMembershipHangarsMapping;
            if(map==null){MelonLogger.Warning("FREEDOM_ARROW_HANGAR_INDOORS no hangar list");return;}
            HangarData basic=null;object key=null;bool have=false;
            foreach(var pair in map)
            {
                if(pair.Value==null)continue;
                foreach(var d in pair.Value)
                {
                    if(d==null)continue;
                    if(d._name==Name)have=true;
                    if(d._name==Basic&&basic==null){basic=d;key=pair.Key;}
                }
            }
            if(!have)
            {
                if(basic==null){MelonLogger.Warning("FREEDOM_ARROW_HANGAR_INDOORS HangarMain not found; option not added");return;}
                var membership=(Il2CppNetworkCommon.Enums.ContentMembership)key;
                var old=map[membership];
                var arr=new Il2CppReferenceArray<HangarData>(old.Length+1);
                for(int i=0;i<old.Length;i++)arr[i]=old[i];
                var d=new HangarData();
                d._name=Name;
                d._nameLocalizationKey=Label;
                // Own AssetReference to the same prefab: SwitchEnvironment loads the new hangar before it releases the old one.
                d._environmentReference=new AssetReferenceGameObject(basic._environmentReference.AssetGUID);
                d._previewSpriteReference=basic._previewSpriteReference;
                arr[old.Length]=d;
                map[membership]=arr;
                MelonLogger.Msg($"FREEDOM_ARROW_HANGAR_INDOORS added '{Label}' after {Basic} ({membership}, {arr.Length} hangars), prefab {basic._environmentReference.AssetGUID}");
            }
            if(PlayerPrefs.GetInt(Marker,0)!=1)
            {
                string was=PlayerPrefs.HasKey(Pref)?PlayerPrefs.GetString(Pref):"(none)";
                PlayerPrefs.SetString(Pref,Name);PlayerPrefs.SetInt(Marker,1);PlayerPrefs.Save();
                MelonLogger.Msg($"FREEDOM_ARROW_HANGAR_INDOORS default set once: {was} -> {Name}");
            }
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HANGAR_INDOORS add failed: "+e);}
    }

    // Every unit type uses the Aircraft spawn point while this hangar is shown. Osama 27 Nov 22:1x: "units in the indoor hanger spawn facing away
    // not towards the entrance": the spot is used turned 180 degrees about its vertical axis (a sibling transform at the same place, made once per
    // spot), so every unit, planes too, faces the entrance.
    static Transform turned,turnedFrom;
    static Transform Turned(Transform t)
    {
        if(turned!=null&&turnedFrom==t)return turned;
        var go=new GameObject("FA indoor spot (facing entrance)");
        go.transform.SetParent(t.parent,false);
        go.transform.position=t.position;
        go.transform.rotation=t.rotation*Quaternion.Euler(0f,180f,0f);
        go.transform.localScale=t.localScale;
        turned=go.transform;turnedFrom=t;
        return turned;
    }
    public static void Spawn(ArsenalUnitPreviewData __instance,UnitType __0,ref Transform __result)
    {
        if(busy||!Active())return;
        busy=true;
        try
        {
            var t=(__0&UnitType.Aircraft)!=0?__result:__instance.GetSpawnPointByUnitType(UnitType.Aircraft);
            if(t!=null)
            {
                __result=Turned(t);
                if(!loggedSpawn){loggedSpawn=true;MelonLogger.Msg($"FREEDOM_ARROW_HANGAR_INDOORS {__0} shown at the aircraft spot '{t.name}', turned to face the entrance");}
            }
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HANGAR_INDOORS spawn: "+e.Message);}
        finally{busy=false;}
    }

    // Before the game removes the old model of the new unit's type, remove the models of every other type too: one spot, one model.
    public static void ClearAll(ArsenalUnitPreview __instance,UnitType __0)
    {
        if(busy||!Active())return;
        Clear(__instance,keep:0,why:$"show {__0}");
    }

    // Hangar switched (MainMenuScreen.UpdateArsenalUnitPreviewPosition): keep only the model of the unit on display.
    public static void KeepShown(ArsenalUnitPreview __instance)
    {
        if(busy||!Active())return;
        UnitType shown=0;
        try{shown=__instance._unitDisplayed?.Type??0;}catch{}
        Clear(__instance,shown,"hangar switch");
    }

    static void Clear(ArsenalUnitPreview p,UnitType keep,string why)
    {
        busy=true;
        try
        {
            var shown=p._spawnedModel;
            if(shown==null)return;
            var types=new List<UnitType>();
            foreach(var pair in shown)if(pair.Value!=null)types.Add(pair.Key);
            int n=0;
            foreach(var t in types)
            {
                if(keep!=0&&t==keep)continue;
                p.DestroyModel(t);n++;
            }
            if(n>0&&!loggedClear){loggedClear=true;MelonLogger.Msg($"FREEDOM_ARROW_HANGAR_INDOORS {why}: removed {n} model(s) from the shared spot");}
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_HANGAR_INDOORS clear: "+e.Message);}
        finally{busy=false;}
    }

    // The option label: the game shows hangar names through localization keys.
    public static void Resolve(LocalizationService __instance,string __0,ref string __1,bool __2,ref bool __result)
    {
        if(__result||__0!=Label)return;
        string code="";try{code=__instance?.CurrentLanguage??"";}catch{}
        var c=code.Trim().ToLowerInvariant();
        __1=c.StartsWith("zh")||c.Contains("chin")?LabelZh:Label;__result=true;
    }
}
