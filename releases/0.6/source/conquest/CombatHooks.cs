using System.Collections.Concurrent;
using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Services;
using Il2CppBrokenArrow.Client.Ecs.UI.HUD.Service;
using Il2CppBrokenArrow.Client.Ecs.UI.HUD.Utils;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Shared.Ecs.Helpers;
using Il2CppBrokenArrow.Shared.Ecs.Services;

namespace FreedomArrow.Conquest;
// 0.4 crit rules and the wider front arc. The rules are in CritRule (Scoring.cs).
// The AI also calls CalculateHitDamage to score shots. Only a real hit calls GetPenetrationForShell first,
// so that call marks the next calculation as real. Hooks only queue; game state changes are on the main thread,
// with the same steps as the native crit system: set the level, refresh the unit's stats, send to the other players.
public sealed partial class Prototype
{
    const int MaxCombatLog=40;
    static readonly CriticalEffectTypes[] RandomYellows={CriticalEffectTypes.Optics,CriticalEffectTypes.Targeting,CriticalEffectTypes.Loading};
    [ThreadStatic] static bool realHit;
    [ThreadStatic] static Vector3 impact;
    static volatile bool combatActive;
    static bool combatOff;
    static int combatLogged,arcWidened;
    static readonly ConcurrentDictionary<int,(bool rear,bool tankGun,bool atgm)> ammoKinds=new();
    static readonly ConcurrentQueue<(Entity target,int kind,ArmorSides side,float damage,string ammo)> critHits=new();
    // A widened side result, kept until the same thread's next real hit uses it. The AI also asks for armor sides when it aims.
    [ThreadStatic] static bool arcPending;
    [ThreadStatic] static float arcAngle;
    static int arcLogged;
    static readonly ConcurrentQueue<(Entity target,float angle,float damage,string ammo,int calls)> arcHits=new();
    static readonly System.Random critRandom=new();
    static void InstallCombatHooks()
    {
        if(config.Crits)
        {
            Patch(typeof(BattleSystemHelpers),"GetPenetrationForShell",null,nameof(MarkRealHit));
            Patch(typeof(BattleSystemHelpers),"CalculateHitDamage",null,nameof(QueueCrit));
        }
        if(config.FrontArcDegrees>45)Patch(typeof(BattleSystemHelpers),"GetArmorSideFromShotVector",nameof(ArcBefore),nameof(ArcAfter));
        InstallBombRoof();
        InstallFireRear();
        MelonLogger.Msg($"FREEDOM_ARROW_COMBAT installed crits {config.Crits} damage {config.CritDamage} ATGM damage {config.AtgmCritDamage} rear penetration {config.RearCritMinPenetration} front arc {config.FrontArcDegrees}");
    }
    public static void MarkRealHit() { realHit=true; }
    public static void QueueCrit(Entity __0,Ammunitions __2,ArmorSides __5,float __result)
    {
        bool real=realHit;realHit=false;
        bool arc=arcPending;arcPending=false;
        if(!real||!combatActive||__2==null)return;
        CountHit(__2.Name);
        try{LogHit(__0,__2.Name,__2.Id,__5.ToString(),__result,__2.ArmorTargeted.ToString(),__2.Damage);}catch{}
        try
        {
            if(arc&&__5==ArmorSides.Front)arcHits.Enqueue((__0,arcAngle,__result,__2.Name,arcWidened));
            var k=ammoKinds.GetOrAdd(__2.Id,_=>(CritRule.RearAntiTank((int)__2.TrajectoryType,(long)__2.TargetType,__2.PenetrationAtMinRange,config.RearCritMinPenetration),
                CritRule.TankGun((int)__2.TrajectoryType,(int)__2.ArmorTargeted,__2.Name),
                CritRule.Atgm((int)__2.TrajectoryType,(int)__2.ArmorTargeted,__2.IsTopArmorArmorAttack,__2.Name)));
            int kind=CritRule.Kind((int)__5,__result,config.CritDamage,k.rear,k.tankGun,k.atgm,config.AtgmCritDamage);
            if(kind!=0)critHits.Enqueue((__0,kind,__5,__result,__2.Name));
        }
        catch(Exception e) { StopCombat(e); }
    }
    public static void ArcBefore(Vector3 __2) { impact=__2; }
    public static void ArcAfter(in Entity __1,ref ArmorSides __result)
    {
        arcPending=false;
        if(__result!=ArmorSides.Sides||!combatActive)return;
        try
        {
            // The game turns the impact vector around before it measures the angle; this is the same measurement.
            var target=__1;
            var local=TransformationHelper.ToLocalDirection(-impact,ref target);
            BattleSystemHelpers.LocalDirectionToLocalAngles(local,out float horizontal,out _);
            if(!CritRule.WidenFront((int)__result,horizontal,config.FrontArcDegrees))return;
            __result=ArmorSides.Front;
            Interlocked.Increment(ref arcWidened);
            arcPending=true;arcAngle=horizontal;
        }
        catch(Exception e) { StopCombat(e); }
    }
    static void CombatFrame()
    {
        if(combatOff)return;
        combatActive=(view!=null&&Guarded(view.Service))||EditorTest();
        ShotFrame(combatActive);
        FireStatsFrame();
        while(arcHits.TryDequeue(out var arc))
        {
            string name=arc.target.IsAlive&&arc.target.Has<UnitComponent>()?NativeEcs.Read<UnitComponent>(arc.target).UnitData?.Name:null;
            if(++arcLogged<=MaxCombatLog)MelonLogger.Msg($"FREEDOM_ARROW_FRONT_ARC real hit on {name} at {arc.angle:0.#} degrees counted as front, {arc.damage:0.##} by {arc.ammo}; widened side calls so far {arc.calls}");
            if(stateFile!=null)StateLine("front_arc",new{e=arc.target.GetHashCode(),name,angle=arc.angle,damage=arc.damage,ammo=arc.ammo,calls=arc.calls});
        }
        while(critHits.TryDequeue(out var hit))
        {
            if(!combatActive)continue;
            try { ApplyCrit(hit.target,hit.kind,hit.side,hit.damage,hit.ammo); }
            catch(Exception e) { StopCombat(e);return; }
        }
    }
    static void ApplyCrit(Entity target,int kind,ArmorSides side,float damage,string ammo)
    {
        if(!target.IsAlive||!target.Has<UnitComponent>()||!target.Has<CriticalEffectComponent>())return;
        var unit=NativeEcs.Read<UnitComponent>(target).UnitData;
        if(unit==null||!CritRule.Target((int)unit.Role))return;
        // The snapshot shares the live status dictionary with the game.
        var status=NativeEcs.Read<CriticalEffectComponent>(target).CriticalEffectStatus;
        var raised=new List<string>();
        void Raise(CriticalEffectTypes type,int level)
        {
            if(status[type]>=level)return;
            status[type]=level;raised.Add($"{type} {level}");
        }
        if(kind==1)Raise(CriticalEffectTypes.Mobility,CritRule.Red);
        else
        {
            Raise(CriticalEffectTypes.Mobility,CritRule.Yellow);
            var open=RandomYellows.Where(t=>status[t]==0).ToArray();
            if(open.Length>0)Raise(open[critRandom.Next(open.Length)],CritRule.Yellow);
        }
        if(raised.Count==0)return;
        target.Enable<BuffUpdateComponent>();
        Session.TryGetService<NetworkUnitService>(out var network,false);
        network?.SendUnitGetCriticalEffect(ref target);
        if(Session.TryGetService<HUDService>(out var hud,false))
        {
            hud._updateTypes.Add(HUDUpdateType.ByUnitState);
            hud._updateEntities.Add(target);
        }
        string rule=kind==1?"rear_red":"yellow_plus_one";
        if(++combatLogged<=MaxCombatLog)
            MelonLogger.Msg($"FREEDOM_ARROW_CRIT {rule} {unit.Name} {side} {damage:0.##} by {ammo}: {string.Join(", ",raised)}; sent {network!=null}");
        if(stateFile!=null)StateLine("crit",new{e=target.GetHashCode(),unit.Id,unit.Name,rule,side=side.ToString(),damage,ammo,raised,sent=network!=null});
    }
    static void StopCombat(Exception e)
    {
        combatOff=true;combatActive=false;
        MelonLogger.Error("FREEDOM_ARROW_COMBAT_FAILED: crit and front arc hooks off for this session. "+e.Message);
    }
}
