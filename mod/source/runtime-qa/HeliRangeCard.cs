using System.Globalization;
using System.Text.RegularExpressions;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.VisualTools;
using Il2Cpp;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;
using Il2CppBrokenArrow.Client.Ecs.UI.BaseElements.Tooltip;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Helicopter range on the cards and range tool (Lateralus 21 Nov 2026; Lateralus 0.9 Changelog, "Helicopter range" tab, rows 7, 8, 14, 18, 20).
// - Weapon ammo panel (AmmoInfoExpansionPanel.Init, after the game has placed every line): a "Helicopter Range" line above "Low Alt. Range" (Lateralus 21 Nov), only for ammo that can target
//   helicopters (TargetType flag 8) and has a helicopter range; same card metres as the low-altitude line.
// - Radar tooltip (edited after SetUnitAbilities), for every unit with a radar (Lateralus 23 Nov 2026): helicopter, low-altitude and
//   high-altitude blocks, each with its range and optics multiplier, so no optics multiplier is hidden.
// - Optics stat tooltip: a "Helicopter Range: N m" line above "Low Alt. Range" for every unit with sensors (Lateralus 21 Nov: always show,
//   tooltip only).
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
        h.Patch(AccessTools.Method(typeof(UnitInfoCard),"SetUnitAbilities"),prefix:new HarmonyMethod(typeof(HeliRangeCard),nameof(UnitBefore)),postfix:new HarmonyMethod(typeof(HeliRangeCard),nameof(AbilitiesAfter)));
        h.Patch(AccessTools.Method(typeof(UnitInfoCard),"SetUnitStatistic"),prefix:new HarmonyMethod(typeof(HeliRangeCard),nameof(UnitBefore)),postfix:new HarmonyMethod(typeof(HeliRangeCard),nameof(StatsAfter)));
        try { h.Patch(AccessTools.Method(typeof(FOWToolScript),"SetWeaponRanges"),postfix:new HarmonyMethod(typeof(HeliRangeCard),nameof(CirclesAfter))); }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_HELI_CARD_FAILED: range tool circle not installed. "+e.Message);}
        MelonLogger.Msg("FREEDOM_ARROW_HELI_CARD installed: weapon Helicopter Range line, radar tooltip lines, optics tooltip line, range tool circle");
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
    // Radar tooltip. SetUnitAbilities builds it with SetTraitItem inlined (0x55E048 onwards: no call to 0x55D4D0), so a SetTraitItem hook never
    // ran (Lateralus 21 Nov, test3). The postfix rewrites the finished tooltip for every unit with a radar (Lateralus 23 Nov 2026: the radar also
    // gives the detection bonus, and "make the tool tip show both so the differences aren't hidden anymore ... space the formatting of the
    // tooltip out like this"): three blocks split by a blank line, helicopter, low altitude, high altitude, each with its range and its optics
    // multiplier. Vanilla lists the range multipliers only, so an optics multiplier that differs (vanilla SHORAD high altitude x2.0 optics /
    // x1.0 range, long-range x2.0 / x3.0) was hidden. Range lines keep the game's own labels; the other labels are English, or Chinese when the
    // game language is Chinese (as PartySizeWarning picks its text). Lines the game adds besides its two range lines are kept below the blocks.
    static string tipLang="\0";static bool tipChinese;
    internal static bool Chinese()
    {
        string code="";
        try{Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<Il2CppBrokenArrow.Shared.Ecs.Localization.LocalizationService>(out var loc,false);code=loc?.CurrentLanguage??"";}
        catch{code="";}
        if(code!=tipLang){tipLang=code;var c=code.Trim().ToLowerInvariant();tipChinese=c.StartsWith("zh")||c.Contains("chin");}
        return tipChinese;
    }
    static string X(float v)=>"x "+v.ToString("0.0#",CultureInfo.InvariantCulture);
    public static void AbilitiesAfter(UnitInfoCard __instance,Units __0)
    {
        if(traitBroken||__instance==null||__0==null)return;
        var a=__0.ActiveAbilities;
        if(!RadarGroup(a,out var m))return;
        try
        {
            string low=InfoCardLocalization.TextAmmoRangeLowAlt,high=InfoCardLocalization.TextAmmoRangeHighAlt;
            if(string.IsNullOrEmpty(low)||string.IsNullOrEmpty(high))return;
            bool zh=Chinese(),found=false;
            string heliRange=zh?"直升机射程":"Helicopter Range",heliOptics=zh?"直升机光学":"Helicopter Optics",
                   lowOptics=zh?"低空光学":"Low Alt. Optics",highOptics=zh?"高空光学":"High Alt. Optics";
            foreach(var tip in __instance.GetComponentsInChildren<UiTooltip>(true))
            {
                if(tip==null)continue;
                var data=tip.Data;string text=data.TextLocKey;
                if(string.IsNullOrEmpty(text)||text.Contains(heliRange))continue;
                var lines=text.Split('\n').ToList();
                bool Range(string x,string label)=>x.TrimStart().StartsWith(label)&&x.Contains(" x ");
                if(!lines.Any(x=>Range(x,low)))continue;
                var rest=lines.Where(x=>!Range(x,low)&&!Range(x,high)&&x.Trim().Length>0).ToList();
                var block=new List<string>{
                    $"{heliRange}: {X(m.range)}",$"{heliOptics}: {X(m.optics)}","",
                    $"{low}: {X(a.RadarLowAltWeaponRangeModifier)}",$"{lowOptics}: {X(a.RadarLowAltOpticsModifier)}","",
                    $"{high}: {X(a.RadarHighAltWeaponRangeModifier)}",$"{highOptics}: {X(a.RadarHighAltOpticsModifier)}"};
                if(rest.Count>0){block.Add("");block.AddRange(rest);}
                data.TextLocKey=string.Join("\n",block);tip.Data=data;found=true;
                Log($"radar tooltip {__0.HUDName}: {data.TextLocKey.Replace("\n"," | ")}");
            }
            if(!found)Log($"radar tooltip {__0.HUDName}: no tooltip with a '{low}: x' line");
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
            string low=InfoCardLocalization.TextAmmoRangeLowAlt;if(string.IsNullOrEmpty(low))return;
            foreach(var item in __instance.GetComponentsInChildren<UnitStatisticItem>(false))
            {
                if(item?.Icon?.sprite==null||item.Icon.sprite.Pointer!=sprite.Pointer)continue;
                // The game writes the optics tooltip text straight into TooltipData.TextLocKey (SetStatData 0x562EF0: tooltip+0x48), one line per
                // altitude ("Low Alt. Range: 3200 m"). The helicopter line goes above the low-altitude line, in the same card metres
                // (Lateralus 21 Nov: tooltip only, not on the stat bar; test3 scaled from the ground value and showed 1778 m instead of 3200 m).
                var tip=item.Tooltip;if(tip==null)continue;
                var data=tip.Data;string text=data.TextLocKey;
                if(string.IsNullOrEmpty(text)||text.Contains("Helicopter Range"))continue;
                var lines=text.Split('\n').ToList();int at=lines.FindIndex(x=>x.TrimStart().StartsWith(low));
                if(at<0){Log($"optics tooltip {__0.HUDName}: no '{low}' line in '{text.Replace("\n"," | ")}'");continue;}
                float shown=Number(lines[at]);float scale=shown>0?shown/l:2f;
                lines.Insert(at,$"Helicopter Range: {MathF.Round(heli*scale):0} m");
                data.TextLocKey=string.Join("\n",lines);tip.Data=data;
                Log($"optics tooltip {__0.HUDName}: {data.TextLocKey.Replace("\n"," | ")}");
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
