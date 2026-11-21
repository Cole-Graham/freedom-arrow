using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// Helicopter range and optics (Lateralus 21 Nov 2026; Lateralus 0.9 Changelog, "Helicopter range" tab). Driven by helicopter-range.json.
// Range: BattleSystemHelpers.GetAmmoShootingDistance gives a helicopter at Low altitude the ammo's LowAltRange (GroundRange if 0) x the shooter's
// radar LowAltWeaponRangeModifier when the radar is on. This postfix uses the helicopter range of the ammo (if listed) and the radar row's
// helicopter range multiplier instead. Optics: FogOfWarUnit.CreateFilterTaskForTarget receives the vision range of every observer-target check;
// for a helicopter target seen by a unit with radar on, the range is scaled by helicopter optics multiplier / LowAltOpticsModifier.
// Radar rows are found by the values the game copies into RadarAbilityComponent (switched on = byte 0x0, multipliers 0xC-0x18, cooldown 0x1C,
// static 0x20). Calls and time spent are logged every perfLogSeconds (test builds: performance check).
static class HeliRange
{
    const int MaxLog=12;
    static readonly Dictionary<int,float> ammoRange=new();
    static readonly Dictionary<(float,float,float,float,float,bool),(float range,float optics)> radar=new();
    static readonly ConcurrentDictionary<ulong,bool> heliTargets=new();
    static readonly ConcurrentDictionary<ulong,bool> radarUnits=new();
    static IntPtr hasHeli,hasRadar,getRadar,getRadarCode,getAlt,getAltCode;
    static bool rangeBroken,opticsBroken;
    static long rangeCalls,rangeChanged,rangeTicks,opticsCalls,opticsChanged,opticsTicks,lastLog;
    static int logged,unknown;
    static long logEvery;
    public static unsafe void Install(HarmonyLib.Harmony harmony,string root)
    {
        var path=Path.Combine(root,"helicopter-range.json");
        if(!File.Exists(path)){MelonLogger.Msg("FREEDOM_ARROW_HELI_RANGE not installed: no helicopter-range.json");return;}
        var j=JsonNode.Parse(File.ReadAllText(path));
        foreach(var (k,v) in j["ammo"].AsObject())ammoRange[int.Parse(k)]=v.GetValue<float>();
        foreach(var r in j["radar"].AsArray())
            radar[(r["lowAltOptics"].GetValue<float>(),r["highAltOptics"].GetValue<float>(),r["lowAltRange"].GetValue<float>(),r["highAltRange"].GetValue<float>(),
                   r["switchCooldown"].GetValue<float>(),r["static"].GetValue<bool>())]=(r["helicopterRangeMultiplier"].GetValue<float>(),r["helicopterOpticsMultiplier"].GetValue<float>());
        logEvery=Stopwatch.Frequency*(long)(j["perfLogSeconds"]?.GetValue<int>()??60);
        hasHeli=SpottingCap.Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(UnitHelicopterFlag));
        hasRadar=SpottingCap.Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(RadarAbilityComponent));
        getRadar=SpottingCap.Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(RadarAbilityComponent));
        getAlt=SpottingCap.Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(AltitudeComponent));
        getRadarCode=*(IntPtr*)getRadar;getAltCode=*(IntPtr*)getAlt;
        if(getRadarCode==IntPtr.Zero||getAltCode==IntPtr.Zero)throw new InvalidOperationException("Entity.Get<RadarAbilityComponent/AltitudeComponent> has no code");
        harmony.Patch(AccessTools.Method(typeof(BattleSystemHelpers),"GetAmmoShootingDistance"),postfix:new HarmonyMethod(typeof(HeliRange),nameof(RangeAfter)));
        harmony.Patch(AccessTools.Method(typeof(FogOfWarUnit),"CreateFilterTaskForTarget"),prefix:new HarmonyMethod(typeof(HeliRange),nameof(OpticsBefore)));
        lastLog=Stopwatch.GetTimestamp();
        MelonLogger.Msg($"FREEDOM_ARROW_HELI_RANGE installed: {ammoRange.Count} ammo helicopter ranges, {radar.Count} radar groups: "+
            string.Join("; ",radar.Select(p=>$"low optics {p.Key.Item1:g}/range {p.Key.Item3:g} -> heli range x{p.Value.range:g}, heli optics x{p.Value.optics:g}")));
    }
    static ulong Key(Entity e)=>System.Runtime.CompilerServices.Unsafe.As<Entity,ulong>(ref e);
    static bool IsHeli(Entity e)
    {
        ulong k=Key(e);
        if(heliTargets.TryGetValue(k,out bool h))return h;
        h=SpottingCap.Has(hasHeli,e);if(heliTargets.Count>20000)heliTargets.Clear();heliTargets[k]=h;return h;
    }
    // The unit's radar when it is switched on; null otherwise. Units never gain or lose the radar component, so that test is cached.
    static unsafe byte* ActiveRadar(Entity e)
    {
        ulong k=Key(e);
        if(!radarUnits.TryGetValue(k,out bool has)){has=SpottingCap.Has(hasRadar,e);if(radarUnits.Count>20000)radarUnits.Clear();radarUnits[k]=has;}
        if(!has)return null;
        byte* c=(byte*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getRadarCode)(&e,getRadar);
        return c!=null&&c[0]!=0?c:null;
    }
    static unsafe bool Lookup(byte* c,out (float range,float optics) m)
    {
        var k=(*(float*)(c+0xC),*(float*)(c+0x10),*(float*)(c+0x14),*(float*)(c+0x18),*(float*)(c+0x1C),c[0x20]!=0);
        if(radar.TryGetValue(k,out m))return true;
        if(Interlocked.Increment(ref unknown)<=MaxLog)MelonLogger.Warning($"FREEDOM_ARROW_HELI_RANGE no radar entry for {k}; low-altitude values kept");
        return false;
    }
    public static unsafe void RangeAfter(Entity __0,Entity __1,Ammunitions __2,ref float __result)
    {
        if(rangeBroken||!Runtime.IsApplied)return;
        long t0=Stopwatch.GetTimestamp();
        try
        {
            Interlocked.Increment(ref rangeCalls);
            if(__2==null||!IsHeli(__1))return;
            if(*((byte*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getAltCode)(&__1,getAlt)+0x18)!=1)return;   // GlobalAltitudeLevel Low
            bool listed=ammoRange.TryGetValue(__2.Id,out float heli);
            float mod=1;bool changedMod=false;
            byte* c=ActiveRadar(__0);
            if(c!=null){float low=*(float*)(c+0x14);mod=low;if(Lookup(c,out var m)&&m.range!=low){mod=m.range;changedMod=true;}}
            if(!listed&&!changedMod)return;
            float baseRange=listed?heli:(__2.LowAltRange>0?__2.LowAltRange:__2.GroundRange);
            float before=__result;__result=baseRange*mod;
            Interlocked.Increment(ref rangeChanged);
            if(Interlocked.Increment(ref logged)<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_HELI_RANGE range {__2.Name} vs helicopter: {before:0.#} -> {__result:0.#} (radar x{mod:g})");
        }
        catch(Exception e){rangeBroken=true;MelonLogger.Error("FREEDOM_ARROW_HELI_RANGE_FAILED: range part off for this session. "+e.Message);}
        finally{Interlocked.Add(ref rangeTicks,Stopwatch.GetTimestamp()-t0);Report();}
    }
    public static unsafe void OpticsBefore(FogOfWarUnit __instance,Entity __0,ref float __3)
    {
        if(opticsBroken||!Runtime.IsApplied)return;
        long t0=Stopwatch.GetTimestamp();
        try
        {
            Interlocked.Increment(ref opticsCalls);
            if(!IsHeli(__0))return;
            byte* c=ActiveRadar(__instance.UnitEntity);
            if(c==null)return;
            float low=*(float*)(c+0xC);
            if(low<=0||!Lookup(c,out var m)||m.optics==low)return;
            float before=__3;__3*=m.optics/low;
            Interlocked.Increment(ref opticsChanged);
            if(Interlocked.Increment(ref logged)<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_HELI_RANGE optics vs helicopter: {before:0.#} -> {__3:0.#} (x{m.optics:g} instead of x{low:g})");
        }
        catch(Exception e){opticsBroken=true;MelonLogger.Error("FREEDOM_ARROW_HELI_RANGE_FAILED: optics part off for this session. "+e.Message);}
        finally{Interlocked.Add(ref opticsTicks,Stopwatch.GetTimestamp()-t0);Report();}
    }
    static void Report()
    {
        long now=Stopwatch.GetTimestamp(),last=Interlocked.Read(ref lastLog);
        if(now-last<logEvery||Interlocked.CompareExchange(ref lastLog,now,last)!=last)return;
        double s=(double)(now-last)/Stopwatch.Frequency,us=1e6/Stopwatch.Frequency;
        long rc=Interlocked.Exchange(ref rangeCalls,0),rt=Interlocked.Exchange(ref rangeTicks,0),rx=Interlocked.Exchange(ref rangeChanged,0);
        long oc=Interlocked.Exchange(ref opticsCalls,0),ot=Interlocked.Exchange(ref opticsTicks,0),ox=Interlocked.Exchange(ref opticsChanged,0);
        MelonLogger.Msg($"FREEDOM_ARROW_HELI_PERF {s:0}s: range {rc/s:0}/s, {(rc>0?rt*us/rc:0):0.00} us/call, {rt*us/s/1000:0.000} ms/s, changed {rx}; "+
                        $"optics {oc/s:0}/s, {(oc>0?ot*us/oc:0):0.00} us/call, {ot*us/s/1000:0.000} ms/s, changed {ox}");
    }
}
