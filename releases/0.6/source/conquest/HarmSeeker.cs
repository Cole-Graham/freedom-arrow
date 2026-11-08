using System.Runtime.CompilerServices;
using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;

namespace FreedomArrow.Conquest;
// 0.6 dev.29 (Osama, 7 November 2026): an anti-radiation missile (seeker type SEAD) that loses its target, for example when
// the radar turns off, flies on to the target's position at that moment. Read from the game code (GameAssembly 6000.3.24f1):
// SeekerSystem.DropCurrentTarget (RVA 0x8279D0) already sends a dropped missile on to SeekerComponent.LastTargetPosition,
// but it sets that point to the target position plus a random miss vector (GenerateMissVector, RVA 0x828170). This hook
// saves the target position before the drop and writes it back over the miss point after it. A dropped missile still
// turns at the game's reduced dead-missile rate (25%). Only SEAD missiles whose target is still alive are changed.
public sealed partial class Prototype
{
    const int SeadSeeker=200,MaxHarmLog=40;
    static bool harmOff;
    static int harmLogged;
    [ThreadStatic] static Vector3? harmPoint;
    struct NullableEntity{public byte HasValue;public byte P1,P2,P3;public long Value;}
    static void InstallHarmSeeker()
    {
        if(Unsafe.SizeOf<Entity>()!=8||Unsafe.SizeOf<NullableEntity>()!=12)throw new InvalidOperationException("Entity layout changed");
        Patch(typeof(SeekerSystem),"DropCurrentTarget",nameof(HarmDropBefore),nameof(HarmDropAfter));
        MelonLogger.Msg("FREEDOM_ARROW_HARM installed: a SEAD missile that loses a live target flies to its last position");
    }
    public static void HarmDropBefore(in Entity __0)
    {
        harmPoint=null;
        if(harmOff)return;
        try
        {
            var missile=__0;
            if(!missile.IsAlive||!missile.Has<SeekerComponent>())return;
            if(NativeEcs.Field<SeekerComponent,int>(missile,"Type")!=SeadSeeker)return;
            var t=NativeEcs.Field<SeekerComponent,NullableEntity>(missile,"Target");
            if(t.HasValue==0)return;
            var raw=t.Value;var target=Unsafe.As<long,Entity>(ref raw);
            if(!target.IsAlive||!target.Has<ViewComponent>())return;
            harmPoint=NativeEcs.Read<ViewComponent>(target).transform.position;
        }
        catch(Exception e){harmOff=true;harmPoint=null;MelonLogger.Error("FREEDOM_ARROW_HARM_FAILED: vanilla behaviour for this session. "+e.Message);}
    }
    public static void HarmDropAfter(in Entity __0)
    {
        if(harmOff||harmPoint==null)return;
        var point=harmPoint.Value;harmPoint=null;
        try
        {
            var missile=__0;
            if(!missile.IsAlive||!missile.Has<SeekerComponent>())return;
            var miss=NativeEcs.Field<SeekerComponent,Vector3>(missile,"LastTargetPosition");
            NativeEcs.WriteField<SeekerComponent,Vector3>(missile,"LastTargetPosition",point);
            var back=NativeEcs.Field<SeekerComponent,Vector3>(missile,"LastTargetPosition");
            var at=NativeEcs.Read<ViewComponent>(missile).transform.position;
            if(++harmLogged<=MaxHarmLog)
                MelonLogger.Msg($"FREEDOM_ARROW_HARM target_lost flies to ({back.x:0},{back.y:0},{back.z:0}) instead of miss point ({miss.x:0},{miss.y:0},{miss.z:0}); {Vector3.Distance(at,point):0} world units to go");
            if(stateFile!=null)StateLine("harm_last_position",new{x=point.x,y=point.y,z=point.z,miss_x=miss.x,miss_z=miss.z,distance=Vector3.Distance(at,point)});
        }
        catch(Exception e){harmOff=true;MelonLogger.Error("FREEDOM_ARROW_HARM_FAILED: vanilla behaviour for this session. "+e.Message);}
    }
}
