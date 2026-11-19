using System.Collections.Concurrent;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// AA eye height test (Lateralus 19 Nov 2026, thread 1572724406642286692: "forest height at 5 and the eye height increased to 8").
// The vision eye is the unit position plus FogOfWarComponent.UnitColliderCenter (0x60). FogOfWarHelper.TryGetEntityEyePoint reads it for
// the physics ray and the forest cost walk, and also when the unit is the target. Only vision code and the LoS tool read it
// (docs/engine/low-altitude-and-air-sight.md 3e). Ground units (infantry 2, vehicle 4, ship 32) with a WeaponComponent.IsAntiAir weapon
// get UnitColliderCenter.y raised to AaEyeHeight world units; an eye already that high is kept. game-config.json AaEyeHeight 0 = off.
// Proof that vision uses it: a prefix on FogOfWarUnit.CreateFilterTaskForTarget samples LastEyeData (0x14: HasEye, 0x18: eye position)
// of raised units; LateUpdate compares the sampled eye with the unit position.
static class AaEyeHeight
{
    const int MaxLog=40,MaxSampleLog=12,WeaponBatch=128,Ground=2|4|32;
    const float Interval=.5f,SummaryInterval=30f;
    static float height;
    static IntPtr hasFog,getFog,getFogCode;
    static readonly ConcurrentDictionary<ulong,float> raised=new();
    static readonly ConcurrentDictionary<ulong,float> seen=new();
    static readonly Dictionary<ulong,Entity> aaUnits=new();
    static readonly Dictionary<ulong,string> names=new();
    static readonly HashSet<ulong> checkedWeapons=new(),tall=new();
    static EntitySet weaponSet;
    static World world;
    static int cursor,logged;
    static long writes,rewrites,samples,ok,low;
    static bool broken,sampleBroken;
    static float nextScan,nextSummary;
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    public static unsafe void Install(HarmonyLib.Harmony harmony,string root)
    {
        if(Unsafe.SizeOf<Entity>()!=8)throw new InvalidOperationException("Entity layout changed");
        height=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"game-config.json")))["AaEyeHeight"].GetValue<float>();
        if(!(height>=0&&height<=50))throw new InvalidDataException("AaEyeHeight out of range");
        if(height==0){MelonLogger.Msg("FREEDOM_ARROW_AA_EYE off (AaEyeHeight 0): vanilla eye points");return;}
        hasFog=SpottingCap.Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(FogOfWarComponent));
        getFog=SpottingCap.Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(FogOfWarComponent));
        getFogCode=*(IntPtr*)getFog;
        if(getFogCode==IntPtr.Zero)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> has no code");
        harmony.Patch(AccessTools.Method(typeof(FogOfWarUnit),"CreateFilterTaskForTarget"),prefix:new HarmonyMethod(typeof(AaEyeHeight),nameof(SampleEye)));
        DiagnosticLog.Write("aa_eye_installed",new{height});
        MelonLogger.Msg($"FREEDOM_ARROW_AA_EYE installed: ground anti-air eye {height:g} world units ({height*2:g} m card scale); vision-code sampler on CreateFilterTaskForTarget");
    }
    public static void SceneChanged()
    {
        try{if(world!=null&&!world._isDisposed)weaponSet?.Dispose();}catch{ }
        weaponSet=null;world=null;cursor=0;nextScan=nextSummary=0;
        raised.Clear();seen.Clear();aaUnits.Clear();names.Clear();checkedWeapons.Clear();tall.Clear();
    }
    // Runs for every observer-target pair; only a dictionary lookup unless the observer is a raised unit not sampled since the last summary.
    public static unsafe void SampleEye(FogOfWarUnit __instance)
    {
        if(sampleBroken||raised.IsEmpty)return;
        try
        {
            byte* p=(byte*)__instance.Pointer;
            ulong unit=*(ulong*)(p+0x24);
            if(!raised.ContainsKey(unit)||seen.ContainsKey(unit)||!*(bool*)(p+0x14))return;
            seen[unit]=*(float*)(p+0x1C);
            Interlocked.Increment(ref samples);
        }
        catch(Exception e){sampleBroken=true;MelonLogger.Error("FREEDOM_ARROW_AA_EYE_SAMPLER_FAILED: sampler off; eye writes continue. "+e.Message);}
    }
    public static unsafe void LateUpdate()
    {
        if(height==0||broken||getFogCode==IntPtr.Zero||!Runtime.IsApplied)return;
        float now=Time.time;if(now<nextScan)return;nextScan=now+Interval;
        try
        {
            var current=ShootingSystem._gameContext;if(current==null||current._isDisposed)return;
            if(world==null||world.Pointer!=current.Pointer)
            {
                SceneChanged();world=current;nextScan=now+Interval;
                weaponSet=world.GetEntities().With<WeaponComponent>().AsSet();
                MelonLogger.Msg($"FREEDOM_ARROW_AA_EYE bound to battle world, weapons {weaponSet.Count}");
            }
            var weapons=weaponSet._entities;int count=Math.Min(weaponSet.Count,weapons?.Length??0);
            for(int n=0;n<Math.Min(WeaponBatch,count);n++)
            {
                if(cursor>=count)cursor=0;
                var w=weapons[cursor++];
                if(!w.IsAlive||!checkedWeapons.Add(Key(w))||!w.Has<WeaponComponent>())continue;
                var wc=NativeEcs.Read<WeaponComponent>(w);if(wc==null||!wc.IsAntiAir)continue;
                var unit=wc.GetUnitEntity();if(!unit.IsAlive||!unit.Has<UnitComponent>())continue;
                var d=NativeEcs.Read<UnitComponent>(unit).UnitData;if(d==null||((int)d.Type&Ground)==0)continue;
                aaUnits[Key(unit)]=unit;names[Key(unit)]=$"{d.Id} {d.Name}";
            }
            foreach(var (k,unit) in aaUnits.ToArray())
            {
                var u=unit;
                if(!u.IsAlive){aaUnits.Remove(k);raised.TryRemove(k,out _);seen.TryRemove(k,out _);continue;}
                if(!SpottingCap.Has(hasFog,u))continue;
                float* fow=(float*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getFogCode)(&u,getFog);
                if(fow==null)throw new InvalidOperationException("Entity.Get<FogOfWarComponent> returned null");
                float y=fow[25]; // UnitColliderCenter.y at 0x64
                if(y>=height)
                {
                    if(!raised.ContainsKey(k)&&tall.Add(k)&&++logged<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_AA_EYE keep {names[k]}: eye already {y:0.##}");
                    continue;
                }
                fow[25]=height;
                if(fow[25]!=height)throw new InvalidOperationException("UnitColliderCenter.y readback mismatch");
                writes++;
                if(!raised.TryAdd(k,height))rewrites++; // the game set the old eye again
                if(++logged<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_AA_EYE raise {names[k]}: eye y {y:0.##} -> {height:g} (read back {fow[25]:0.##})");
            }
            if(now>=nextSummary){nextSummary=now+SummaryInterval;Summary();}
        }
        catch(Exception e)
        {
            broken=true;
            DiagnosticLog.Write("aa_eye_failed",new{error=e.ToString(),writes,aa=aaUnits.Count});
            MelonLogger.Error("FREEDOM_ARROW_AA_EYE_FAILED: off for this session; eyes already raised stay raised. "+e);
        }
    }
    // Eye the vision code used, minus the unit position: about AaEyeHeight when the raise reached vision (more on a slope or with a centre offset).
    static void Summary()
    {
        int shown=0;
        foreach(var (k,eyeY) in seen.ToArray())
        {
            if(!aaUnits.TryGetValue(k,out var u)||!u.IsAlive)continue;
            float rel=eyeY-NativeEcs.Property<TransformComponent,Vector3>(u,"Position").y;
            bool good=rel>=height-1;
            if(good)ok++;else low++;
            if(++shown<=MaxSampleLog||!good)MelonLogger.Msg($"FREEDOM_ARROW_AA_EYE vision {names[k]}: eye used {rel:0.##} above the unit ({(good?"raised":"NOT raised")})");
        }
        seen.Clear();
        var s=new{height,aaUnits=aaUnits.Count,raised=raised.Count,keptTaller=tall.Count,writes,rewrites,samples,visionRaised=ok,visionLow=low,sampler=!sampleBroken};
        DiagnosticLog.Write("aa_eye_summary",s);
        MelonLogger.Msg($"FREEDOM_ARROW_AA_EYE summary ground AA units {s.aaUnits}, raised {s.raised}, already taller {s.keptTaller}, writes {writes}, game reset {rewrites}; vision checks raised {ok}, not raised {low}");
    }
}
