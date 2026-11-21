using System;
using HarmonyLib;
using MelonLoader;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar;
using UnityEngine;
namespace FreedomArrow;
// 0.9.4-dev.1 (Lateralus, 21 November 2026: "queue up the fix for force firing through smoke for 0.9.4"). A unit could smoke itself and keep
// firing out with Fire at position (force fire on the ground), while nobody could see in. Firing at a unit through smoke is already refused by
// the game (IsTargetShootable: a team-spotted target needs SmokeTerrainDistance <= 0.5); the ground-point check had no smoke test. This is
// ActualArrow's fix (FlatIncomeMod 0.9.17 SmokeGroundPatch, AA Lite 1.0.6 and Full 1.2.x; our FlatIncomeMod 0.9.16 does not have it):
// a postfix on FogOfWarUnit's ground-point raycast callback (compiler class __c__DisplayClass43_0, same name in BA 1.2.2.1) makes the point
// not shootable when the line to it crosses more than 0.5 of smoke. Artillery fire missions use another path and are not changed.
static class SmokeGroundFire
{
    const float MaxSmoke=0.5f;
    static bool broken,logged;
    public static void Install(HarmonyLib.Harmony h)
    {
        var m=AccessTools.Method(typeof(FogOfWarUnit.__c__DisplayClass43_0),"Method_Internal_Void_Il2CppStructArray_1_FilterTask_PDM_0");
        if(m==null){MelonLogger.Error("FREEDOM_ARROW_SMOKE_GROUND: ground-point callback not found; Fire at position still shoots through smoke");return;}
        h.Patch(m,postfix:new HarmonyMethod(typeof(SmokeGroundFire),nameof(After)));
        MelonLogger.Msg("FREEDOM_ARROW_SMOKE_GROUND installed: Fire at position does not shoot through smoke");
    }
    static void After(FogOfWarUnit.__c__DisplayClass43_0 __instance,Il2CppStructArray<FilterTask> results)
    {
        if(broken||__instance==null||results==null||results.Length==0)return;
        try
        {
            var task=results[0];
            if(task.SmokeTerrainDistance<=MaxSmoke)return;
            var point=__instance.groundPoint;
            if(point==null)return;
            point.IsShootable=false;
            if(task.TargetVisible)point.FilterHitDistance=new Il2CppSystem.Nullable<float>(Mathf.Max(0f,Vector3.Distance(task.CastStartPosition,task.CastEndPosition)-task.SmokeTerrainDistance));
            if(!logged){logged=true;MelonLogger.Msg($"FREEDOM_ARROW_SMOKE_GROUND refused a ground target through {task.SmokeTerrainDistance} of smoke");}
        }
        catch(Exception e){broken=true;MelonLogger.Error("FREEDOM_ARROW_SMOKE_GROUND_FAILED: off from now on. "+e.Message);}
    }
}
