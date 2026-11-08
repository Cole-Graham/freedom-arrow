using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;

namespace FreedomArrow.Conquest;
// 0.6 (Osama, 7 November 2026): an anti-radiation missile (seeker type SEAD) hits where a radar was when it switched off.
// Read from the game code (GameAssembly 6000.3.24f1): SeekerSystem.DropCurrentTarget (RVA 0x8279D0) drops the target and
// sends the missile to a miss point near it at a reduced turn rate. dev.29-43 rewrote that point and still missed in
// Osama's tests; dev.44 skipped the drop and followed a radar that drove away. From dev.45 the drop is skipped only
// while the radar stays near the spot where it went dark; if it moves away, the missile is released to that spot.
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
        Patch(typeof(SeekerSystem),"InternalUpdate",nameof(HarmSeekerUpdateBefore),null);
        MelonLogger.Msg("FREEDOM_ARROW_HARM installed: a SEAD missile keeps its lock on a dark radar that stays within 25 world units of where it went dark");
    }
    // dev.44 kept the lock unconditionally, so a HARM followed a radar that switched off and drove away (Osama: wrong).
    // dev.45: the lock is kept only while the radar stays within ReleaseDistance of where it was when it went dark. Once it
    // moves further, the missile lets go (the game's own drop) and its aim point is set to that original spot, so it hits
    // where the radar was, not where it went. A dead target or a switch to a new target drops as in vanilla.
    const float ReleaseDistance=25f;
    static readonly Dictionary<long,Vector3> harmKept=new();
    static bool harmReleasing;
    static long Key(Entity e)=>Unsafe.As<Entity,long>(ref e);
    static bool LiveSeadTarget(Entity missile,out Entity target)
    {
        target=default;
        if(!missile.IsAlive||!missile.Has<SeekerComponent>())return false;
        if(NativeEcs.Field<SeekerComponent,int>(missile,"Type")!=SeadSeeker)return false;
        var t=NativeEcs.Field<SeekerComponent,NullableEntity>(missile,"Target");
        if(t.HasValue==0)return false;
        long raw=(uint)t.Lo|((long)t.Hi<<32);target=Unsafe.As<long,Entity>(ref raw);
        return target.IsAlive&&target.Has<ViewComponent>();
    }
    public static bool HarmDropBefore(in Entity __0,bool __2)
    {
        if(harmOff||harmReleasing||__2)return true;
        try
        {
            var missile=__0;
            if(!LiveSeadTarget(missile,out var target))return true;
            var radar=NativeEcs.Read<ViewComponent>(target).transform.position;
            if(!harmKept.ContainsKey(Key(missile)))
            {
                harmKept[Key(missile)]=radar;
                if(++harmLogged<=MaxHarmLog)
                {
                    var at=NativeEcs.Read<ViewComponent>(missile).transform;
                    MelonLogger.Msg($"FREEDOM_ARROW_HARM target_lost lock kept on the radar's spot ({radar.x:0},{radar.y:0},{radar.z:0}); {Vector3.Distance(at.position,radar):0} world units away, {Vector3.Angle(at.forward,radar-at.position):0} degrees off the nose; released if the radar moves over {ReleaseDistance:0}");
                }
                if(stateFile!=null)StateLine("harm_lock_kept",new{x=radar.x,z=radar.z});
            }
            return false;
        }
        catch(Exception e){harmOff=true;MelonLogger.Error("FREEDOM_ARROW_HARM_FAILED: vanilla behaviour for this session. "+e.Message);return true;}
    }
    // Runs for every missile on each seeker update; only missiles in harmKept do any work.
    public static void HarmSeekerUpdateBefore(in Entity __0)
    {
        if(harmOff||harmKept.Count==0)return;
        var missile=__0;long key=Key(missile);
        if(!harmKept.TryGetValue(key,out var spot))return;
        try
        {
            if(!LiveSeadTarget(missile,out var target)){harmKept.Remove(key);return;}
            var now=NativeEcs.Read<ViewComponent>(target).transform.position;
            float moved=Vector3.Distance(now,spot);
            if(moved<=ReleaseDistance)return;
            harmKept.Remove(key);
            harmReleasing=true;
            try{SeekerSystem.DropCurrentTarget(ref missile);}finally{harmReleasing=false;}
            if(missile.IsAlive&&missile.Has<SeekerComponent>())NativeEcs.WriteField<SeekerComponent,Vector3>(missile,"LastTargetPosition",spot);
            if(++harmLogged<=MaxHarmLog)MelonLogger.Msg($"FREEDOM_ARROW_HARM released: radar moved {moved:0} world units, missile flies to its old spot ({spot.x:0},{spot.y:0},{spot.z:0})");
            if(stateFile!=null)StateLine("harm_released",new{moved,x=spot.x,z=spot.z});
        }
        catch(Exception e){harmOff=true;harmKept.Clear();MelonLogger.Error("FREEDOM_ARROW_HARM_FAILED: vanilla behaviour for this session. "+e.Message);}
    }
}
