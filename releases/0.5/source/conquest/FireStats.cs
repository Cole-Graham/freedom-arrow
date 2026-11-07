using System.Collections.Concurrent;
using MelonLoader;
using UnityEngine;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;

namespace FreedomArrow.Conquest;
// 0.5 dev.1: fire statistics for balance tests (shots, real hits, time between shots per weapon).
// Counting only; it changes nothing in the game. A real hit is counted in QueueCrit (CombatHooks.cs).
// Every 60 s of play the log gets one FREEDOM_ARROW_FIRE_STATS line per ammunition; totals are cumulative.
public sealed partial class Prototype
{
    sealed class FireCount { public int Shots,Hits; public float GapSum; public int Gaps; public float GapMin=float.MaxValue; }
    static readonly ConcurrentDictionary<string,FireCount> fireCounts=new();
    static readonly ConcurrentDictionary<int,float> lastShot=new();
    static float nextFireReport=-1;
    static bool fireOff;
    static FireCount NewCount(string ammo) => new FireCount();
    static void InstallFireStats()
    {
        Patch(typeof(ShootingSystem),"WeaponForceFire",null,nameof(CountShot));
        MelonLogger.Msg("FREEDOM_ARROW_FIRE_STATS installed: shots, hits and time between shots per ammunition, logged every 60 s");
    }
    public static void CountShot(in Entity __0)
    {
        if(fireOff||!combatActive)return;
        try
        {
            var weapon=__0;
            if(!weapon.IsAlive||!weapon.Has<WeaponComponent>())return;
            var w=NativeEcs.Read<WeaponComponent>(weapon);
            var ammo=w?.SelectedAmmunition;
            if(ammo==null)return;
            var c=fireCounts.GetOrAdd(ammo.Name,NewCount);
            float now=Time.time;
            lock(c)
            {
                c.Shots++;
                if(lastShot.TryGetValue(weapon.GetHashCode(),out float before))
                {
                    float gap=now-before;
                    if(gap>0&&gap<120){c.GapSum+=gap;c.Gaps++;if(gap<c.GapMin)c.GapMin=gap;}
                }
            }
            lastShot[weapon.GetHashCode()]=now;
            // dev.37: set the squad reload before the shot is logged, so timing.reload shows the value the game will use.
            try{SquadReloadShot(w);}catch(Exception e){if(++squadReloadLogged<=5)MelonLogger.Warning("FREEDOM_ARROW_SQUAD_RELOAD failed: "+e.Message);}
            LogShot(weapon,w,ammo.Name);
        }
        catch(Exception e) { fireOff=true;MelonLogger.Error("FREEDOM_ARROW_FIRE_STATS_FAILED: counting off for this session. "+e.Message); }
    }
    static void CountHit(string ammo)
    {
        if(fireOff)return;
        var c=fireCounts.GetOrAdd(ammo,NewCount);
        lock(c)c.Hits++;
    }
    static void FireStatsFrame()
    {
        if(fireOff||!combatActive||fireCounts.IsEmpty)return;
        float now=Time.time;
        if(nextFireReport<0){nextFireReport=now+60;return;}
        if(now<nextFireReport)return;
        nextFireReport=now+60;
        foreach(var (ammo,c) in fireCounts.OrderBy(p=>p.Key))
        {
            int shots,hits,gaps;float sum,min;
            lock(c){shots=c.Shots;hits=c.Hits;gaps=c.Gaps;sum=c.GapSum;min=c.GapMin;}
            string rate=shots>0?$"{100.0*hits/shots:0.#}%":"n/a";
            string gap=gaps>0?$"mean gap {sum/gaps:0.##} s, shortest {min:0.##} s ({gaps} gaps)":"no repeat shots";
            MelonLogger.Msg($"FREEDOM_ARROW_FIRE_STATS t={now:0} {ammo}: shots {shots}, hits {hits}, hit rate {rate}; {gap}");
            if(stateFile!=null)StateLine("fire_stats",new{t=now,ammo,shots,hits,gaps,meanGap=gaps>0?sum/gaps:0,minGap=gaps>0?min:0});
        }
    }
}
