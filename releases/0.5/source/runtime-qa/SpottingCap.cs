using System.Collections.Concurrent;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// Spotting cap: an observer never sees a ground target beyond the vanilla ground optics of its sensor tier.
// Both native vision paths pass their range result to CreateFilterTaskForTarget as maxDistance, so the cap is set there.
// Unit cards show optics as tier names, so the card does not have to show capped or formula ranges.
static class SpottingCap
{
    const int MaxLog=15;
    static readonly Dictionary<float,float> capTable=new();
    static readonly ConcurrentDictionary<(IntPtr,int),float> observerCaps=new();
    static readonly Dictionary<string,(float min,string name,string color)[]> names=new();
    static IntPtr hasFog,getFog,getFogCode;
    static bool capBroken,cardBroken;
    static long calls,capped;
    static int unknownLogged,cardLogged;
    static IntPtr Store(string name,Type component)
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
        var cfg=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"optics-names.json")));
        var colors=cfg["Colors"].AsObject();
        foreach(string channel in new[]{"Ground","LowAltitude","HighAltitude"})
        {
            var tiers=cfg[channel].AsArray().Select(t=>(t[0].GetValue<float>(),t[1].GetValue<string>(),colors[t[2].GetValue<string>()].GetValue<string>())).ToArray();
            if(tiers.Length==0||tiers[0].Item1!=0||tiers.Zip(tiers.Skip(1)).Any(p=>p.Second.Item1<=p.First.Item1))throw new InvalidDataException("optics-names.json: "+channel+" must start at 0 and rise");
            names[channel]=tiers;
        }
        hasFog=Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(FogOfWarComponent));
        getFog=Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(FogOfWarComponent));
        getFogCode=*(IntPtr*)getFog;
        if(getFogCode==IntPtr.Zero)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> has no code");
        harmony.Patch(AccessTools.Method(typeof(FogOfWarUnit),"CreateFilterTaskForTarget"),prefix:new HarmonyMethod(typeof(SpottingCap),nameof(CapBefore)));
        try { harmony.Patch(AccessTools.Method(typeof(UnitInfoCard),"SetUnitStatistic"),postfix:new HarmonyMethod(typeof(SpottingCap),nameof(CardAfter))); }
        catch(Exception e) { MelonLogger.Error("FREEDOM_ARROW_OPTICS_NAMES_FAILED: card names not installed. "+e.Message); }
        MelonLogger.Msg("FREEDOM_ARROW_SPOTTING_CAP installed "+string.Join(", ",capTable.OrderBy(p=>p.Key).Select(p=>$"{p.Key:g}->{p.Value:g}"))+" (raw; displayed m = raw x 2)");
    }
    static unsafe float ObserverCap(Entity observer)
    {
        IntPtr error=IntPtr.Zero;
        IntPtr has=Il2CppInterop.Runtime.IL2CPP.il2cpp_runtime_invoke(hasFog,(IntPtr)(&observer),null,ref error);
        Il2CppInterop.Runtime.Il2CppException.RaiseExceptionIfNecessary(error);
        if(has==IntPtr.Zero||!*(bool*)Il2CppInterop.Runtime.IL2CPP.il2cpp_object_unbox(has))return 0;
        float ground=*(float*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getFogCode)(&observer,getFog);
        if(capTable.TryGetValue(ground,out float cap))return cap;
        if(Interlocked.Increment(ref unknownLogged)<=MaxLog)MelonLogger.Warning($"FREEDOM_ARROW_SPOTTING_CAP no cap for ground optics {ground:g}; this observer is not capped");
        return 0;
    }
    public static void CapBefore(FogOfWarUnit __instance,ref float __3)
    {
        if(capBroken||!Runtime.IsApplied)return;
        try
        {
            long n=Interlocked.Increment(ref calls);
            if(n==1)MelonLogger.Msg($"FREEDOM_ARROW_SPOTTING_CAP first call thread {Environment.CurrentManagedThreadId} maxDistance {__3:0.#}");
            var observer=__instance.UnitEntity;
            float cap=observerCaps.GetOrAdd((__instance.Pointer,observer.GetHashCode()),_=>ObserverCap(observer));
            if(cap<=0||__3<=cap)return;
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
    static string Label(string channel,float value)
    {
        var tier=names[channel].Last(t=>value>=t.min);
        return $"<color={tier.color}>{tier.name}</color>";
    }
    static readonly Regex Metres=new(@"\d[\d\s.,]*\s*m\b");
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
            // The native card shows low-altitude optics for helicopters and ground optics for every other unit.
            bool heli=__0.CategoryType==Il2CppNetworkCommon.Enums.Common.UnitCategoryType.Helicopters;
            string main=heli?Label("LowAltitude",low):Label("Ground",ground);
            string[] lines={Label("Ground",ground),Label("LowAltitude",low),Label("HighAltitude",high)};
            foreach(var item in __instance.GetComponentsInChildren<UnitStatisticItem>(false))
            {
                var icon=item.Icon;
                if(icon==null||icon.sprite==null||icon.sprite.Pointer!=sprite.Pointer)continue;
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
                if(++cardLogged<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_OPTICS_NAMES {__0.Name}: ground {ground:g} low {low:g} high {high:g} -> {main}");
            }
        }
        catch(Exception e)
        {
            cardBroken=true;
            MelonLogger.Error("FREEDOM_ARROW_OPTICS_NAMES_FAILED: off for this session. "+e.Message);
        }
    }
}
