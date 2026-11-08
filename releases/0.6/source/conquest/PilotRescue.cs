using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.Cleanups;
using Il2CppBrokenArrow.Client.Ecs.Economy.Systems;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;
using Il2CppBrokenArrow.MissionEditor.Data.Meta;
using Il2CppBrokenArrow.MissionEditor.Data.SpawnPoint;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Shared.Ecs.Other;
using Il2CppNetworkCommon.Enums;

namespace FreedomArrow.Conquest;
// 0.6 dev.7 (Osama, 7 November 2026): pilot rescue. A plane shot down nearer an enemy spawn always ejects its pilot;
// a plane that comes down nearer its own team's spawn, or runs out of fuel, ejects nobody (dev.8: nor before any zone is captured). The pilot pays out through
// the game's own back-to-base refund; pilot prices are 100 (fighter pilot and crew) and 120 (bomber crew) in the tables.
// Read from the game code (GameAssembly 6000.3.24f1): UnitDeathSystem.TrySpawnPilot (RVA 0x7B1C80) spawns the pilot for
// planes inside the map when Random x 100 <= PlanesConfig.DeathChance; fuel-out deaths use FuelOutChance instead.
// The refund (RefundSystem.RefundUnit, RVA 0x6DBEC0) starts from the unit's Cost. Halves come from the map's spawn points,
// so no map needs its own setup.
public sealed partial class Prototype
{
    const int MaxPilotLog=40;
    static bool pilotOff;
    static int pilotLogged;
    static readonly HashSet<int> PilotUnits=new(){322,323,324,325,326,327};
    static void InstallPilotRescue()
    {
        if(!config.PilotRescue){MelonLogger.Msg("FREEDOM_ARROW_PILOT_RESCUE off in settings.json");return;}
        Patch(typeof(UnitDeathSystem),"TrySpawnPilot",nameof(PilotBefore),null);
        Patch(typeof(RefundSystem),"RefundUnit",null,nameof(PilotRefundAfter));
        MelonLogger.Msg("FREEDOM_ARROW_PILOT_RESCUE installed: enemy half always ejects, own half and fuel-out eject nobody");
    }
    public static bool PilotBefore(UnitDeathSystem __instance,in Entity __0,IPlayerInfo __1,bool __2)
    {
        if(pilotOff)return true;
        try
        {
            var plane=__0;
            var unit=NativeEcs.Read<UnitComponent>(plane);
            var owner=unit.Owner??__1;
            var pos=NativeEcs.Read<ViewComponent>(plane).transform.position;
            var side=owner.TeamSide;
            string name=unit.UnitData?.Name;
            if(__2){PilotLine("fuel_out_no_pilot",name,side,pos,null,null);return false;}
            int captured=CapturedZoneCount();
            if(captured==0){PilotLine("no_zones_captured_no_pilot",name,side,pos,null,null);return false;}
            var (own,enemy)=SpawnDistances(pos,side);
            if(own==null||enemy==null){PilotLine("no_spawns_vanilla",name,side,pos,own,enemy);return true;}
            if(own<=enemy){PilotLine("own_half_no_pilot",name,side,pos,own,enemy);return false;}
            var planes=__instance._config.PlanesConfig;
            planes.DeathChance=100;
            PilotLine("enemy_half_pilot",name,side,pos,own,enemy);
            return true;
        }
        catch(Exception e)
        {
            pilotOff=true;
            MelonLogger.Error("FREEDOM_ARROW_PILOT_RESCUE_FAILED: vanilla pilots for this session. "+e.Message);
            return true;
        }
    }
    // dev.8 (Osama): early game, before either team has captured a zone, nobody ejects. -1 without a conquest/war-goals mode.
    static int CapturedZoneCount()
    {
        var owners=view?.CapturedOwners;
        if(owners==null)return -1;
        int n=0;
        foreach(var team in new[]{TeamSide.Alpha,TeamSide.Bravo})
            if(owners.TryGetValue(team,out var ids)&&ids!=null)n+=ids.Count;
        return n;
    }
    // Nearest spawn point of the plane's own team and of any other playing team, measured on the ground plane.
    // dev.27: hidden spawn points count too (FindObjectsOfType skipped them; Osama's 2v2 Chkalovsk log of dev.15 found none
    // for 19 planes), and the team comes from the spawn point's map data when the script field is empty.
    static bool spawnsLogged;
    static TeamSide SpawnTeam(SpawnPointScript s)
    {
        var team=s._spawnPointTeamSide;
        if(team==TeamSide.Alpha||team==TeamSide.Bravo)return team;
        var data=(s._gameplayData??s._editorData)?.Team?.LinkedData?.TryCast<TeamData>();
        return data!=null?data.TeamSide:team;
    }
    static (float? own,float? enemy) SpawnDistances(Vector3 pos,TeamSide side)
    {
        float? own=null,enemy=null;
        var all=UnityEngine.Object.FindObjectsOfType<SpawnPointScript>(true);
        if(!spawnsLogged)
        {
            spawnsLogged=true;
            int active=0,alpha=0,bravo=0,other=0;
            foreach(var s in all){if(s.gameObject.activeInHierarchy)active++;var t=SpawnTeam(s);if(t==TeamSide.Alpha)alpha++;else if(t==TeamSide.Bravo)bravo++;else other++;}
            MelonLogger.Msg($"FREEDOM_ARROW_PILOT_RESCUE spawn points {all.Length} ({active} active): Alpha {alpha}, Bravo {bravo}, other {other}");
        }
        foreach(var s in all)
        {
            var team=SpawnTeam(s);
            if(team!=TeamSide.Alpha&&team!=TeamSide.Bravo)continue;
            var p=s.transform.position;
            float d=new Vector2(p.x-pos.x,p.z-pos.z).magnitude;
            if(team==side)own=Math.Min(own??d,d);else enemy=Math.Min(enemy??d,d);
        }
        return (own,enemy);
    }
    public static void PilotRefundAfter(in Entity __0,bool __1,float __result)
    {
        if(pilotOff||__1)return;
        try
        {
            var e=__0;
            if(!e.IsAlive||!e.Has<UnitComponent>())return;
            var unit=NativeEcs.Read<UnitComponent>(e).UnitData;
            if(unit==null||!PilotUnits.Contains(unit.Id))return;
            MelonLogger.Msg($"FREEDOM_ARROW_PILOT_RESCUE refund {unit.Name} (unit {unit.Id}, cost {unit.Cost}): {__result:0.##} points");
            if(stateFile!=null)StateLine("pilot_refund",new{unit.Id,unit.Name,unit.Cost,refund=__result});
        }
        catch(Exception ex){MelonLogger.Error("FREEDOM_ARROW_PILOT_RESCUE refund log failed: "+ex.Message);}
    }
    static void PilotLine(string rule,string plane,TeamSide side,Vector3 pos,float? own,float? enemy)
    {
        if(++pilotLogged<=MaxPilotLog)
            MelonLogger.Msg($"FREEDOM_ARROW_PILOT_RESCUE {rule} {plane} team {side} at ({pos.x:0},{pos.z:0}); nearest own spawn {own:0}, nearest enemy spawn {enemy:0} (world units)");
        if(stateFile!=null)StateLine("pilot",new{rule,plane,side=side.ToString(),x=pos.x,z=pos.z,own,enemy});
    }
}
