using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;

namespace FreedomArrow.Conquest;
// 0.6 (Osama, 7 November 2026): an anti-radiation missile (seeker type SEAD) keeps its lock on a radar that turns off.
// Read from the game code (GameAssembly 6000.3.24f1): SeekerSystem.DropCurrentTarget (RVA 0x8279D0) drops the target and
// sends the missile to a miss point near it at the reduced dead-missile turn rate (25%). dev.29-41 rewrote that point and
// dev.42-43 aimed it straight ahead; both still missed in Osama's tests. From dev.44 the drop is skipped while the target
// is alive, so the missile keeps homing at full turn rate. A dead target or a switch to a new target drops as in vanilla.
public sealed partial class Prototype
{
    const int SeadSeeker=200,MaxHarmLog=40;
    static bool harmOff;
    static int harmLogged;
    // Nullable<Entity> as IL2CPP lays it out: bool at 0, Entity (short, short, int) at 4, 12 bytes (SeekerComponent.Target 0x44, HasLOSOnCurrentTarget 0x50).
    [StructLayout(LayoutKind.Sequential,Pack=4)] struct NullableEntity{public byte HasValue;public byte P1,P2,P3;public int Lo,Hi;}
    static void InstallHarmSeeker()
    {
        if(Unsafe.SizeOf<Entity>()!=8||Unsafe.SizeOf<NullableEntity>()!=12)throw new InvalidOperationException($"Entity layout changed (Entity {Unsafe.SizeOf<Entity>()} bytes, Nullable {Unsafe.SizeOf<NullableEntity>()} bytes; expected 8 and 12)");
        Patch(typeof(SeekerSystem),"DropCurrentTarget",nameof(HarmDropBefore),null);
        MelonLogger.Msg("FREEDOM_ARROW_HARM installed: a SEAD missile keeps its lock on a radar that turns off");
    }
    // dev.44 (Osama: HARMs still deviate with radar off). dev.42/43 flew them straight after the drop, and the dev.43 test
    // log showed why that misses: lock lost 632 world units out, radar 10 degrees off the nose, so a straight line passes
    // about 110 units wide. Now a SEAD missile whose target is still alive keeps its lock: the drop is skipped, so it
    // goes on homing on the radar's position with its full turn rate. A dead target, or a switch to a new target
    // (dropBeforeTargetChange), still drops as in vanilla.
    static readonly HashSet<int> harmKept=new();
    public static bool HarmDropBefore(in Entity __0,bool __2)
    {
        if(harmOff||__2)return true;
        try
        {
            var missile=__0;
            if(!missile.IsAlive||!missile.Has<SeekerComponent>())return true;
            if(NativeEcs.Field<SeekerComponent,int>(missile,"Type")!=SeadSeeker)return true;
            var t=NativeEcs.Field<SeekerComponent,NullableEntity>(missile,"Target");
            if(t.HasValue==0)return true;
            long raw=(uint)t.Lo|((long)t.Hi<<32);var target=Unsafe.As<long,Entity>(ref raw);
            if(!target.IsAlive||!target.Has<ViewComponent>())return true;
            if(harmKept.Add(missile.GetHashCode())&&++harmLogged<=MaxHarmLog)
            {
                var at=NativeEcs.Read<ViewComponent>(missile).transform;var radar=NativeEcs.Read<ViewComponent>(target).transform.position;
                MelonLogger.Msg($"FREEDOM_ARROW_HARM target_lost lock kept on the radar at ({radar.x:0},{radar.y:0},{radar.z:0}); {Vector3.Distance(at.position,radar):0} world units away, {Vector3.Angle(at.forward,radar-at.position):0} degrees off the nose");
                if(stateFile!=null)StateLine("harm_lock_kept",new{x=radar.x,z=radar.z,distance=Vector3.Distance(at.position,radar),off_nose=Vector3.Angle(at.forward,radar-at.position)});
            }
            return false;
        }
        catch(Exception e){harmOff=true;MelonLogger.Error("FREEDOM_ARROW_HARM_FAILED: vanilla behaviour for this session. "+e.Message);return true;}
    }
}
