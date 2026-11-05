using System.Runtime.CompilerServices;
using System.Reflection;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Client.Ecs.Infantry.Components;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs.Components.Movement;
using Il2CppBrokenArrow.Shared.Ecs.Enums;
using Il2CppDefaultEcs;
using Il2CppInterop.Runtime;
using MelonLoader;
namespace FreedomArrow;
// Infantry damage in woods. Vanilla has no terrain factor in CalculateHitDamage. Buildings use BuildingsConfig (DetectionConfig).
static class CoverDamage
{
    const int MaxLog=15,MaxHitLog=300;
    [ThreadStatic] static bool inRealHit;
    static int hitsLogged;
    static float forest;
    static int logged,probed;
    static bool broken;
    static IntPtr hasInfantry,hasTerrain,getTerrain,getTerrainCode;
    static IntPtr Store(string name,Type component)
    {
        var type=typeof(Entity).GetNestedType(name,BindingFlags.NonPublic|BindingFlags.Public)?.MakeGenericType(component)??throw new MissingMemberException("Entity."+name);
        RuntimeHelpers.RunClassConstructor(type.TypeHandle);
        var pointer=(IntPtr)(type.GetField("Pointer",BindingFlags.Static|BindingFlags.NonPublic|BindingFlags.Public)??throw new MissingFieldException(name+".Pointer")).GetValue(null);
        return pointer!=IntPtr.Zero?pointer:throw new InvalidOperationException("Entity."+name+" is not compiled for "+component.Name);
    }
    public static unsafe void Install(HarmonyLib.Harmony harmony,string root)
    {
        var config=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"game-config.json")));
        forest=config["ForestDamageTaken"].GetValue<float>();
        CoverDamagePolicy.Factor(forest,0);
        hasInfantry=Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(InfantryUnitComponent));
        hasTerrain=Store("MethodInfoStoreGeneric_Has_Public_Boolean_0`1",typeof(TerrainTypeComponent));
        getTerrain=Store("MethodInfoStoreGeneric_Get_Public_byref_T_0`1",typeof(TerrainTypeComponent));
        getTerrainCode=*(IntPtr*)getTerrain;
        if(getTerrainCode==IntPtr.Zero)throw new InvalidOperationException("Entity.Get<TerrainTypeComponent> has no code");
        harmony.Patch(AccessTools.Method(typeof(BattleSystemHelpers),"CalculateHitDamage"),postfix:new HarmonyMethod(typeof(CoverDamage),nameof(After)));
        // Shell selection and overkill scoring also call CalculateHitDamage. Only hits inside DealUnitDamage are real.
        // The hit log is evidence only. Its failure must not stop cover damage.
        try{harmony.Patch(AccessTools.Method(typeof(ShellHitSystem),"DealUnitDamage"),prefix:new HarmonyMethod(typeof(CoverDamage),nameof(EnterHit)),postfix:new HarmonyMethod(typeof(CoverDamage),nameof(LeaveHit)));}
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_HIT_FAILED: no hit log this session. "+e.Message);}
        MelonLogger.Msg($"FREEDOM_ARROW_COVER_DAMAGE installed forest {forest}");
    }
    static unsafe bool Has(IntPtr method,Entity e)
    {
        IntPtr error=IntPtr.Zero;
        IntPtr result=IL2CPP.il2cpp_runtime_invoke(method,(IntPtr)(&e),null,ref error);
        Il2CppInterop.Runtime.Il2CppException.RaiseExceptionIfNecessary(error);
        return result!=IntPtr.Zero&&*(bool*)IL2CPP.il2cpp_object_unbox(result);
    }
    static void EnterHit()=>inRealHit=true;
    static void LeaveHit()=>inRealHit=false;
    static unsafe void After(Entity __0,float __1,Ammunitions __2,float __3,bool __4,ArmorSides __5,ref float __result)
    {
        if(broken||__result<=0||!Runtime.IsApplied)return;
        try
        {
            if(inRealHit&&__2!=null&&(int)__2.TrajectoryType is 20 or 30 or 40&&Interlocked.Increment(ref hitsLogged)<=MaxHitLog)MelonLogger.Msg($"FREEDOM_ARROW_HIT {__2.Name} base {__1:0.##} pen {__3:0.##} side {__5} top {__4} damage {__result:0.##}");
            if(!Has(hasInfantry,__0)||!Has(hasTerrain,__0))return;
            var terrain=*(TerrainType*)((delegate* unmanaged<Entity*,IntPtr,IntPtr>)getTerrainCode)(&__0,getTerrain);
            if(Interlocked.Increment(ref probed)<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_COVER_DAMAGE infantry hit on {terrain}");
            if(terrain!=TerrainType.Forest)return;
            float before=__result;
            __result=before*CoverDamagePolicy.Factor(forest,__2?.IgnoreCover??0);
            if(Interlocked.Increment(ref logged)<=MaxLog)MelonLogger.Msg($"FREEDOM_ARROW_COVER_DAMAGE {terrain} {__2?.Name}: {before:0.##} -> {__result:0.##}");
        }
        catch(Exception e)
        {
            broken=true;
            MelonLogger.Error("FREEDOM_ARROW_COVER_DAMAGE_FAILED: off for this session. "+e.Message);
        }
    }
}
