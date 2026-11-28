using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Missile performance log (Osama 27 Nov 2026 16:3x PST, bugs thread: "make sure we log missile performance", after the helicopter ATGMs went
// to 160 deg/s). Logging only; it changes nothing in the game. MissileHitChance hands over every guided missile at its first hit-chance roll
// (missile, its target, ammo id). Every 0.2 s this follows the missile and the target by position; when the missile is gone it waits 1.5 s
// for the target's health to settle and writes one FREEDOM_ARROW_MISSILE_RESULT line: flight time, closest approach and last distance to
// the target, the target's average speed during the flight, its health before and after, and "hit" when the target lost health within 20
// world units of the missile's end. Every 60 s one FREEDOM_ARROW_MISSILE_PERF line per ammo gives launches, hits, and hits on moving targets
// (above 3 units/s) and on still ones. Health is read the same way as MatchLog (HealthComponent._health); positions from ViewComponent.
// No game method is patched here: no SetMissileDead hook (that crashed the game in dev.94).
static class MissilePerf
{
    const float Every=0.2f,Settle=1.5f,HitRange=20f,Moving=3f,Report=60f;
    const int MaxLines=3000,MaxTracked=512;
    sealed class Track
    {
        public Entity Missile,Target;public int Ammo;public float Launch,HpBefore,Closest=float.MaxValue,Last=-1,Ended=-1,Travel;
        public Vector3 TargetStart,TargetLast;public bool HaveTarget;
    }
    sealed class Sum{public int Launches,Ended,Hits,MovingShots,MovingHits,StillShots,StillHits;public float MissSum;public int Misses;}
    static readonly List<Track> tracked=new();
    static readonly Dictionary<int,Sum> sums=new();
    static float next,nextReport;
    static int lines;
    static bool broken;

    static float Health(Entity e)=>e.IsAlive&&e.Has<HealthComponent>()?NativeEcs.Field<HealthComponent,float>(e,"_health"):-1f;
    static bool Pos(Entity e,out Vector3 p)
    {
        p=default;
        if(!e.IsAlive||!e.Has<ViewComponent>())return false;
        var t=NativeEcs.Read<ViewComponent>(e).transform;if(t==null)return false;
        p=t.position;return true;
    }

    // Called by MissileHitChance at a missile's first roll.
    public static void Launch(Entity missile,Entity target,int ammo)
    {
        if(broken||tracked.Count>=MaxTracked)return;
        try
        {
            var k=new Track{Missile=missile,Target=target,Ammo=ammo,Launch=Time.time,HpBefore=Health(target)};
            if(Pos(target,out var tp)){k.TargetStart=tp;k.TargetLast=tp;k.HaveTarget=true;}
            tracked.Add(k);
            Get(ammo).Launches++;
        }
        catch(Exception x){Fail(x);}
    }
    static Sum Get(int ammo){if(!sums.TryGetValue(ammo,out var s))sums[ammo]=s=new Sum();return s;}

    public static void Tick()
    {
        if(broken||!Runtime.IsApplied)return;
        float now=Time.time;
        if(now<next&&now>=next-10f)return;
        next=now+Every;
        try
        {
            for(int i=tracked.Count-1;i>=0;i--)
            {
                var k=tracked[i];
                if(k.Ended<0)
                {
                    if(Pos(k.Missile,out var mp))
                    {
                        if(Pos(k.Target,out var tp)){k.Travel+=Vector3.Distance(new Vector3(tp.x,0,tp.z),new Vector3(k.TargetLast.x,0,k.TargetLast.z));k.TargetLast=tp;k.HaveTarget=true;}
                        if(k.HaveTarget){k.Last=Vector3.Distance(mp,k.TargetLast);if(k.Last<k.Closest)k.Closest=k.Last;}
                        if(now-k.Launch>60f){k.Ended=now;}
                        continue;
                    }
                    k.Ended=now;
                    continue;
                }
                if(now-k.Ended<Settle)continue;
                Finish(k,now);
                tracked.RemoveAt(i);
            }
            if(nextReport<=0||now<nextReport-Report-10f)nextReport=now+Report;
            if(now>=nextReport){nextReport=now+Report;Summary();}
        }
        catch(Exception x){Fail(x);}
    }

    static void Finish(Track k,float now)
    {
        float flight=k.Ended-k.Launch;
        float after=Health(k.Target);
        bool lost=k.HpBefore>0&&(after<0||after<k.HpBefore-0.01f);
        bool near=k.Last>=0&&k.Last<=HitRange;
        bool hit=lost&&near;
        float speed=flight>0.1f?k.Travel/flight:0;
        bool moving=speed>Moving;
        var s=Get(k.Ammo);
        s.Ended++;
        if(moving)s.MovingShots++;else s.StillShots++;
        if(hit){s.Hits++;if(moving)s.MovingHits++;else s.StillHits++;}
        else if(k.Last>=0){s.MissSum+=k.Last;s.Misses++;}
        if(++lines<=MaxLines)
            MelonLogger.Msg($"FREEDOM_ARROW_MISSILE_RESULT ammo {k.Ammo} {(hit?"hit":"miss")} flight {flight:0.0}s end {(k.Last<0?"n/a":k.Last.ToString("0.#"))} closest {(k.Closest==float.MaxValue?"n/a":k.Closest.ToString("0.#"))} "
                +$"target {k.Target.GetHashCode()} speed {speed:0.0}/s {(moving?"moving":"still")} hp {k.HpBefore:0.#}->{(after<0?"dead":after.ToString("0.#"))} missile {k.Missile.GetHashCode()}");
    }

    static void Summary()
    {
        foreach(var (ammo,s) in sums)
        {
            if(s.Launches==0)continue;
            MelonLogger.Msg($"FREEDOM_ARROW_MISSILE_PERF ammo {ammo}: launches {s.Launches}, ended {s.Ended}, hits {s.Hits} ({(s.Ended>0?100f*s.Hits/s.Ended:0):0}%); "
                +$"moving targets {s.MovingHits}/{s.MovingShots}, still {s.StillHits}/{s.StillShots}; average miss distance {(s.Misses>0?s.MissSum/s.Misses:0):0.#}");
        }
    }

    static void Fail(Exception x)
    {
        broken=true;tracked.Clear();
        MelonLogger.Warning("FREEDOM_ARROW_MISSILE_PERF off for this session: "+x.Message);
    }
}
