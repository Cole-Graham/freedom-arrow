using System.Globalization;
using System.Text.RegularExpressions;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.VisualTools;
using Il2Cpp;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Helicopter range on the cards and range tool (Lateralus 21 Nov 2026; Lateralus 0.9 Changelog, "Helicopter range" tab, rows 7, 8, 14, 18, 20).
// - Weapon ammo panel (AmmoInfoExpansionPanel.Init, after the game has placed every line): a "Helicopter Range" line above "Low Alt. Range" (Lateralus 21 Nov), only for ammo that can target
//   helicopters (TargetType flag 8) and has a helicopter range; same card metres as the low-altitude line.
// - Radar tooltip (UnitInfoCard.SetTraitItem, the text built in SetUnitAbilities): "Helicopter Range: x N" for units with a helicopter-capable
//   weapon, and "Helicopter Optics: x N" for every radar unit, from the unit's radar row group in helicopter-range.json.
// - Optics stat: a second small line "Heli N m" under the optics value for every unit with sensors (Lateralus 21 Nov: always show).
// - Range tool (FOWToolScript.SetWeaponRanges): an orange circle at the helicopter range of each helicopter-capable weapon of the selected unit,
//   x the radar helicopter multiplier while the radar is on. Placed only when the weapon's own low-altitude circle is found, so the scale is
//   the game's own.
static class HeliRangeCard
{
    const string LineName="FA_HeliRange";
    static bool ammoBroken,traitBroken,opticsBroken,circleBroken;
    static Units current;
    static int logged;
    static readonly List<GameObject> circles=new();
    static EntitySet weaponSet;static World weaponWorld;
    public static void Install(HarmonyLib.Harmony h)
    {
        if(HeliRange.ammoRange.Count==0&&HeliRange.radar.Count==0){MelonLogger.Msg("FREEDOM_ARROW_HELI_CARD not installed: no helicopter data");return;}
        h.Patch(AccessTools.Method(typeof(AmmoInfoExpansionPanel),"Init"),prefix:new HarmonyMethod(typeof(HeliRangeCard),nameof(AmmoBefore)),postfix:new HarmonyMethod(typeof(HeliRangeCard),nameof(AmmoAfter)));
        h.Patch(AccessTools.Method(typeof(UnitInfoCard),"SetUnitAbilities"),prefix:new HarmonyMethod(typeof(HeliRangeCard),nameof(UnitBefore)));
        h.Patch(AccessTools.Method(typeof(UnitInfoCard),"SetTraitItem"),prefix:new HarmonyMethod(typeof(HeliRangeCard),nameof(TraitBefore)));
        h.Patch(AccessTools.Method(typeof(UnitInfoCard),"SetUnitStatistic"),prefix:new HarmonyMethod(typeof(HeliRangeCard),nameof(UnitBefore)),postfix:new HarmonyMethod(typeof(HeliRangeCard),nameof(StatsAfter)));
        try { h.Patch(AccessTools.Method(typeof(FOWToolScript),"SetWeaponRanges"),postfix:new HarmonyMethod(typeof(HeliRangeCard),nameof(CirclesAfter))); }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_HELI_CARD_FAILED: range tool circle not installed. "+e.Message);}
        MelonLogger.Msg("FREEDOM_ARROW_HELI_CARD installed: weapon Helicopter Range line, radar tooltip lines, optics note, range tool circle");
    }
    static void Log(string m){if(Interlocked.Increment(ref logged)<=40)MelonLogger.Msg("FREEDOM_ARROW_HELI_CARD "+m);}
    // The last number in a card value ("200 - 2200 m" -> 2200; "1000 m" -> 1000). Test2 joined every digit ("2002200").
    static readonly Regex LastNumber=new(@"\d+(?:\.\d+)?(?=\D*$)");
    static float Number(string text)
    {
        var m=LastNumber.Match(text??"");
        return m.Success&&float.TryParse(m.Value,NumberStyles.Float,CultureInfo.InvariantCulture,out float v)?v:0;
    }
    // The same text with its last number replaced, so "200 - 2200 m" keeps its minimum range and unit.
    static string WithLast(string text,float value)=>LastNumber.Replace(text??"",$"{MathF.Round(value):0}",1);
    static bool CanHitHeli(Ammunitions a)=>a!=null&&(((long)a.TargetType)&8)!=0;
    // Init places some lines by position after SetMainAmmoStats (Dispersion = SetStatisticLine(..., siblingIndex 4) at 0x53E4B9, Guidance = 1),
    // so the line goes in after Init, and the old line leaves the container before Init runs: Destroy() waits for the end of the frame, and a
    // line still in the container shifted Dispersion (Lateralus 21 Nov, Centurion C-RAM).
    static void RemoveLine(AmmoInfoExpansionPanel panel)
    {
        var box=panel?._ammoStatsContainer;
        if(box==null)return;
        for(int i=box.childCount-1;i>=0;i--)
        {
            var c=box.GetChild(i);
            if(c==null||c.name!=LineName)continue;
            c.gameObject.SetActive(false);c.SetParent(null,false);UnityEngine.Object.Destroy(c.gameObject);
        }
    }
    public static void AmmoBefore(AmmoInfoExpansionPanel __instance)
    {
        if(ammoBroken)return;
        try{RemoveLine(__instance);}
        catch(Exception e){ammoBroken=true;MelonLogger.Error("FREEDOM_ARROW_HELI_CARD_FAILED: ammo line off. "+e.Message);}
    }
    public static void AmmoAfter(AmmoInfoExpansionPanel __instance,Ammunitions __1)
    {
        if(ammoBroken||__instance==null)return;
        try
        {
            RemoveLine(__instance);
            if(!CanHitHeli(__1)||!HeliRange.ammoRange.TryGetValue(__1.Id,out float heli))return;
            string low=InfoCardLocalization.TextAmmoRangeLowAlt;
            var items=__instance._activeStatisticItems;
            if(items==null||string.IsNullOrEmpty(low))return;
            for(int i=0;i<items.Count;i++)
            {
                var item=items[i];
                if(item?.TitleText==null||item.TitleText.text!=low)continue;
                float shown=Number(item.ValueText?.text),raw=__1.LowAltRange>0?__1.LowAltRange:__1.GroundRange;
                float scale=shown>0&&raw>0?shown/raw:2f;
                var go=UnityEngine.Object.Instantiate(item.gameObject,item.transform.parent);
                go.name=LineName;go.transform.SetSiblingIndex(item.transform.GetSiblingIndex());go.SetActive(true);
                var line=go.GetComponent<StatisticItem>();
                line.TitleText.text="Helicopter Range";line.ValueText.text=shown>0?WithLast(item.ValueText.text,heli*scale):$"{MathF.Round(heli*scale):0} m";
                Log($"ammo line {__1.Name}: Helicopter Range {line.ValueText.text} (Low Alt. Range {item.ValueText?.text})");
                return;
            }
        }
        catch(Exception e){ammoBroken=true;MelonLogger.Error("FREEDOM_ARROW_HELI_CARD_FAILED: ammo line off. "+e.Message);}
    }
    public static void UnitBefore(Units __0){current=__0;}
    static bool RadarGroup(Abilities a,out (float range,float optics) m)
    {
        m=default;
        if(a==null||!a.IsRadar)return false;
        return HeliRange.radar.TryGetValue((a.RadarLowAltOpticsModifier,a.RadarHighAltOpticsModifier,a.RadarLowAltWeaponRangeModifier,
            a.RadarHighAltWeaponRangeModifier,a.RadarSwitchCooldown,a.IsRadarStatic),out m);
    }
    public static void TraitBefore(ref string __1)
    {
        if(traitBroken||current==null||string.IsNullOrEmpty(__1))return;
        try
        {
            string low=InfoCardLocalization.TextAmmoRangeLowAlt,radarTitle=InfoCardLocalization.TextAbilityRadar;
            if(!((!string.IsNullOrEmpty(radarTitle)&&__1.Contains(radarTitle))||(!string.IsNullOrEmpty(low)&&__1.Contains(low))))return;
            if(__1.Contains("Helicopter Optics")||!RadarGroup(current.ActiveAbilities,out var m))return;
            string add=(HeliRange.heliUnits.Contains(current.Id)?$"\nHelicopter Range: x {m.range:0.##}":"")+$"\nHelicopter Optics: x {m.optics:0.##}";
            __1+=add;
            Log($"radar tooltip {current.HUDName}: +{add.Replace("\n"," | ")}");
        }
        catch(Exception e){traitBroken=true;MelonLogger.Error("FREEDOM_ARROW_HELI_CARD_FAILED: radar tooltip lines off. "+e.Message);}
    }
    public static void StatsAfter(UnitInfoCard __instance,Units __0)
    {
        if(opticsBroken||__0?.Sensors==null||__0.Sensors.Count==0)return;
        try
        {
            float g=0,l=0,hi=0;
            for(int i=0;i<__0.Sensors.Count;i++){var s=__0.Sensors[i];g=Math.Max(g,s.OpticsGround);l=Math.Max(l,s.OpticsLowAltitude);hi=Math.Max(hi,s.OpticsHighAltitude);}
            if(l<=0)return;
            if(!HeliRange.sensorOptics.TryGetValue((g,l,hi),out float heli))heli=l;  // Lateralus 21 Nov: always show, also when equal to low optics
            var sprite=__instance._infocardConfig?.Optics;if(sprite==null)return;
            foreach(var item in __instance.GetComponentsInChildren<UnitStatisticItem>(false))
            {
                if(item?.Icon?.sprite==null||item.Icon.sprite.Pointer!=sprite.Pointer||item.Text==null||item.Text.text.Contains("Heli"))continue;
                float shown=Number(item.Text.text);bool heliUnit=__0.CategoryType==Il2CppNetworkCommon.Enums.Common.UnitCategoryType.Helicopters;
                float scale=shown>0?shown/(heliUnit?l:g):2f;
                item.Text.text+=$"\n<size=75%>Heli {MathF.Round(heli*scale):0} m</size>";
            }
        }
        catch(Exception e){opticsBroken=true;MelonLogger.Error("FREEDOM_ARROW_HELI_CARD_FAILED: optics note off. "+e.Message);}
    }
    public static unsafe void CirclesAfter(FOWToolScript __instance,Entity __0)
    {
        if(circleBroken||__instance==null)return;
        try
        {
            foreach(var c in circles)if(c!=null)UnityEngine.Object.Destroy(c);
            circles.Clear();
            var list=__instance._circles;
            if(list==null||list.Count==0||!__0.IsAlive||!__0.Has<UnitComponent>())return;
            if(!HeliRange.heliUnits.Contains(NativeEcs.Read<UnitComponent>(__0).UnitData.Id))return;
            var world=ShootingSystem._gameContext;if(world==null)return;
            if(weaponSet==null||weaponWorld==null||weaponWorld.Pointer!=world.Pointer){weaponWorld=world;weaponSet=world.GetEntities().With<WeaponComponent>().AsSet();}
            byte* radar=HeliRange.ActiveRadar(__0);
            float lowMod=1,heliMod=1;
            if(radar!=null){lowMod=*(float*)(radar+0x14);heliMod=HeliRange.Lookup(radar,out var m)?m.range:lowMod;}
            ulong key=System.Runtime.CompilerServices.Unsafe.As<Entity,ulong>(ref __0);
            var arr=weaponSet._entities;int n=Math.Min(weaponSet.Count,arr?.Length??0);
            var done=new HashSet<float>();
            for(int i=0;i<n;i++)
            {
                var e=arr![i];if(!e.IsAlive)continue;
                var wc=NativeEcs.Read<WeaponComponent>(e);var ammo=wc?.SelectedAmmunition;
                var unit=wc?.GetUnitEntity()??default;
                if(ammo==null||System.Runtime.CompilerServices.Unsafe.As<Entity,ulong>(ref unit)!=key)continue;
                if(!CanHitHeli(ammo)||!HeliRange.ammoRange.TryGetValue(ammo.Id,out float heli))continue;
                float lowRange=(ammo.LowAltRange>0?ammo.LowAltRange:ammo.GroundRange)*lowMod;
                FowCircle match=null;float scale=0;
                for(int k=0;k<list.Count&&match==null;k++)
                {
                    var c=list[k];if(c==null||lowRange<=0)continue;
                    foreach(float s in new[]{1f,2f})if(MathF.Abs(c.Radius-lowRange*s)<0.5f*s){match=c;scale=s;break;}
                }
                if(match==null){Log($"range tool: no low-altitude circle found for {ammo.Name} ({lowRange:0.#}); helicopter circle skipped");continue;}
                float r=heli*heliMod*scale;
                if(!done.Add(r))continue;
                var go=UnityEngine.Object.Instantiate(match.gameObject,match.transform.parent);go.name=LineName;
                var circle=go.GetComponent<FowCircle>();circle.Radius=r;circle.Color=new Color(1f,0.55f,0f,match.Color.a);circle.IsVisible=match.IsVisible;
                go.SetActive(match.gameObject.activeSelf);
                circles.Add(go);
                Log($"range tool: helicopter circle {r:0.#} for {ammo.Name} (low-altitude circle {match.Radius:0.#}, radar x{heliMod:g})");
            }
        }
        catch(Exception e){circleBroken=true;MelonLogger.Error("FREEDOM_ARROW_HELI_CARD_FAILED: range tool circle off. "+e.Message);}
    }
}
