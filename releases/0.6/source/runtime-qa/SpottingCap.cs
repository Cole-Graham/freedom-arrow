using System.Collections.Concurrent;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// Spotting cap: an observer never sees a ground target beyond the vanilla ground optics of its sensor tier.
// Both native vision paths pass their range result to CreateFilterTaskForTarget as maxDistance, so the cap is set there.
// The native air path (planes and missiles: aircraft or fuse, not helicopter) also ends there; Lateralus, 8 November 2026:
// those targets are not capped, so planes are seen at native low/high-altitude optics. Helicopters keep the cap.
// Unit cards show optics in metres (Lateralus, 8 November 2026), with the cap applied where it applies: ground always,
// low altitude against helicopters (low-flying planes are not capped), high altitude never.
static class SpottingCap
{
    const int MaxLog=15;
    static readonly Dictionary<float,float> capTable=new();
    static readonly ConcurrentDictionary<(IntPtr,int),float> observerCaps=new();
    static IntPtr hasFog,getFog,getFogCode,hasAircraft,hasHeli,hasFuse;
    static bool capBroken,cardBroken;
    static long calls,capped,airSkipped;
    static int unknownLogged,cardLogged;
    internal static IntPtr Store(string name,Type component)
    {
        var type=typeof(Entity).GetNestedType(name,BindingFlags.NonPublic|BindingFlags.Public)?.MakeGenericType(component)??throw new MissingMemberException("Entity."+name);
        RuntimeHelpers.RunClassConstructor(type.TypeHandle);
        var pointer=(IntPtr)(type.GetField("Pointer",BindingFlags.Static|BindingFlags.NonPublic|BindingFlags.Public)??throw new MissingFieldException(name+".Pointer")).GetValue(null);
        return pointer!=IntPtr.Zero?pointer:throw new InvalidOperationException("Entity."+name+" is not compiled for "+component.Name);
    }
    public static unsafe void Install(HarmonyLib.Harmony harmony,string root)
    {
        var caps=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"spotting-caps.json")))["OpticsGroundCaps"].AsObject();
        foreach(var (k,v) in caps)capTable[float.Parse(k,System.Globalization.CultureInfo.InvariantCulture)]=v.GetValue<float>();
        if(capTable.Count==0)throw new InvalidDataException("spotting-caps.json is empty");
        hasFog=Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(FogOfWarComponent));
        getFog=Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(FogOfWarComponent));
        getFogCode=*(IntPtr*)getFog;
        hasAircraft=Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(UnitAircraftComponent));
        hasHeli=Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(UnitHelicopterFlag));
        hasFuse=Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(FuseComponent));
        if(getFogCode==IntPtr.Zero)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> has no code");
        harmony.Patch(AccessTools.Method(typeof(FogOfWarUnit),"CreateFilterTaskForTarget"),prefix:new HarmonyMethod(typeof(SpottingCap),nameof(CapBefore)));
        try { harmony.Patch(AccessTools.Method(typeof(UnitInfoCard),"SetUnitStatistic"),postfix:new HarmonyMethod(typeof(SpottingCap),nameof(CardAfter))); }
        catch(Exception e) { MelonLogger.Error("FREEDOM_ARROW_OPTICS_CARD_FAILED: card optics hook not installed. "+e.Message); }
        MelonLogger.Msg("FREEDOM_ARROW_SPOTTING_CAP installed "+string.Join(", ",capTable.OrderBy(p=>p.Key).Select(p=>$"{p.Key:g}->{p.Value:g}"))+" (raw; displayed m = raw x 2)");
    }
    internal static unsafe bool Has(IntPtr store,Entity entity)
    {
        IntPtr error=IntPtr.Zero;
        IntPtr has=Il2CppInterop.Runtime.IL2CPP.il2cpp_runtime_invoke(store,(IntPtr)(&entity),null,ref error);
        Il2CppInterop.Runtime.Il2CppException.RaiseExceptionIfNecessary(error);
        return has!=IntPtr.Zero&&*(bool*)Il2CppInterop.Runtime.IL2CPP.il2cpp_object_unbox(has);
    }
    // Same test as the native air branch (FogOfWarUnit.CalculateVisionRangeForTarget): a helicopter is checked first.
    static bool IsPlaneOrMissile(Entity target)=>!Has(hasHeli,target)&&(Has(hasAircraft,target)||Has(hasFuse,target));
    static unsafe float ObserverCap(Entity observer)
    {
        if(!Has(hasFog,observer))return 0;
        float ground=*(float*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getFogCode)(&observer,getFog);
        if(capTable.TryGetValue(ground,out float cap))return cap;
        if(Interlocked.Increment(ref unknownLogged)<=MaxLog)MelonLogger.Warning($"FREEDOM_ARROW_SPOTTING_CAP no cap for ground optics {ground:g}; this observer is not capped");
        return 0;
    }
    public static void CapBefore(FogOfWarUnit __instance,Entity __0,ref float __3)
    {
        if(capBroken||!Runtime.IsApplied)return;
        try
        {
            long n=Interlocked.Increment(ref calls);
            if(n==1)MelonLogger.Msg($"FREEDOM_ARROW_SPOTTING_CAP first call thread {Environment.CurrentManagedThreadId} maxDistance {__3:0.#}");
            var observer=__instance.UnitEntity;
            float cap=observerCaps.GetOrAdd((__instance.Pointer,observer.GetHashCode()),_=>ObserverCap(observer));
            if(cap<=0||__3<=cap)return;
            if(IsPlaneOrMissile(__0))
            {
                long a=Interlocked.Increment(ref airSkipped);
                if(a<=MaxLog||IsPowerOfTen(a))MelonLogger.Msg($"FREEDOM_ARROW_SPOTTING_CAP air target not capped: {__3:0.#} raw kept (cap {cap:0.#}); {a} air skips");
                return;
            }
            long c=Interlocked.Increment(ref capped);
            // Log the first few, then each power of ten, so the log proves the cap without flooding it.
            if(c<=MaxLog||IsPowerOfTen(c))MelonLogger.Msg($"FREEDOM_ARROW_SPOTTING_CAP capped {__3:0.#} -> {cap:0.#} raw; capped {c} of {n} checks");
            __3=cap;
        }
        catch(Exception e)
        {
            capBroken=true;
            MelonLogger.Error("FREEDOM_ARROW_SPOTTING_CAP_FAILED: off for this session. "+e.Message);
        }
    }
    static bool IsPowerOfTen(long v){while(v>=10&&v%10==0)v/=10;return v==1;}
    static readonly Regex Metres=new(@"\d[\d\s.,]*\s*m\b");
    // Display metres per raw optics unit, read from the native card text (EffectiveRangeMultiplier, 2 in vanilla).
    static float CardScale(string text,float raw)
    {
        var m=Metres.Match(text??"");
        if(!m.Success||raw<=0)return 2f;
        string digits=new string(m.Value.Where(char.IsDigit).ToArray());
        return float.TryParse(digits,out float shown)&&shown>0?shown/raw:2f;
    }
    static string M(float raw,float scale)=>$"{MathF.Round(raw*scale):0} m";
    public static void CardAfter(UnitInfoCard __instance,Units __0)
    {
        if(cardBroken||__0==null)return;
        try
        {
            float ground=0,low=0,high=0;
            var sensors=__0.Sensors;
            if(sensors==null||sensors.Count==0)return;
            for(int i=0;i<sensors.Count;i++)
            {
                var s=sensors[i];
                ground=Math.Max(ground,s.OpticsGround);low=Math.Max(low,s.OpticsLowAltitude);high=Math.Max(high,s.OpticsHighAltitude);
            }
            var sprite=__instance._infocardConfig?.Optics;
            if(sprite==null)return;
            // Same cap the hook uses: the vanilla ground optics of this unit's tier; unknown or zero tiers are not capped.
            float cap=capTable.TryGetValue(ground,out float c)&&c>0?c:float.MaxValue;
            float groundShown=Math.Min(ground,cap),heliShown=Math.Min(low,cap);
            // The native card shows low-altitude optics for helicopters and ground optics for every other unit.
            bool heli=__0.CategoryType==Il2CppNetworkCommon.Enums.Common.UnitCategoryType.Helicopters;
            foreach(var item in __instance.GetComponentsInChildren<UnitStatisticItem>(false))
            {
                var icon=item.Icon;
                if(icon==null||icon.sprite==null||icon.sprite.Pointer!=sprite.Pointer)continue;
                float scale=CardScale(item.Text.text,heli?low:ground);
                string lowText=heliShown<low?$"{M(heliShown,scale)} vs helicopters, {M(low,scale)} vs planes":M(low,scale);
                string main=heli?M(heliShown,scale):M(groundShown,scale);
                string[] lines={M(groundShown,scale),lowText,M(high,scale)};
                item.Text.text=main;
                var tooltip=item.Tooltip;
                if(tooltip!=null)
                {
                    var data=tooltip.Data;
                    if(data.TextLocKey!=null)
                    {
                        string text=data.TextLocKey;
                        var parts=new System.Text.StringBuilder();
                        int at=0,i=0;
                        foreach(Match m in Metres.Matches(text))
                        {
                            if(i>=lines.Length)break;
                            parts.Append(text,at,m.Index-at).Append(lines[i++]);at=m.Index+m.Length;
                        }
                        data.TextLocKey=parts.Append(text,at,text.Length-at).ToString();
                        tooltip.Data=data;
                    }
                }
                if(++cardLogged<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_OPTICS_CARD {__0.Name}: ground {ground:g} (shown {groundShown:g}) low {low:g} (helicopters {heliShown:g}) high {high:g} raw; x{scale:0.##} -> {main}");
            }
        }
        catch(Exception e)
        {
            cardBroken=true;
            MelonLogger.Error("FREEDOM_ARROW_OPTICS_CARD_FAILED: off for this session; the card shows native optics. "+e.Message);
        }
    }
}
