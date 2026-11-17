using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels.Systems;
using Il2CppBrokenArrow.Client.Ecs.Utils;
using Il2CppBrokenArrow.Shared.Ecs;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using Il2CppNetworkCommon.Enums;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// 0.9.0-dev.36 match snapshots for anti-cheat (Osama 17 Nov 2026 12:2x-12:3x PST, thread 1571014792016171120: "can't we log which enemies he sees and
// then we can check if it's possible or not", "We want it to be minimal though and we can run the analysis after", "I don't want analysis running on their
// machines. I don't want performance hits").
// Only records, no checks here: every 5 s in a battle, one line with every unit: side (L own, A ally, E enemy), unit type, x/z position, health, and for
// enemies whether the local side has spotted it (FogOfWarComponent.VisibleTo holds a unit of the local team) and whether its model is drawn on this PC.
// Drawn but not spotted = a model shown through fog; positions and health let the logs of all players in a match be compared afterwards on our side.
// "P" lines name every player who owns units in the battle (UID, team, bot, Steam name), once each (Osama 12:5x: "we could definitely find out who is not
// sending logs or if their logs differ from other players consistently"): a player named in others' logs with no upload of his own stands out.
// The file goes up with the game log (LogUpload). One renderer per unit is looked up once and cached; a snapshot reads components only.
static class MatchLog
{
    const float Every=5f;
    static string file="";static StreamWriter w;static bool broken;static float next;static int snaps;
    static IntPtr world;static EntitySet units;static float battleStart;
    static readonly Dictionary<int,Renderer> view=new();
    static readonly HashSet<IntPtr> players=new();
    static readonly System.Text.StringBuilder line=new(8192);
    public static string File=>file;

    public static void Install(HarmonyLib.Harmony harmony,string root,string session)
    {
        file=Path.Combine(root,"diagnostics",$"match-{session}.log");
        harmony.Patch(AccessTools.Method(typeof(LabelSystem),"Update")??throw new MissingMethodException("LabelSystem.Update"),
            postfix:new HarmonyMethod(typeof(MatchLog),nameof(After)));
        MelonLogger.Msg("FREEDOM_ARROW_MATCH_LOG installed: unit snapshot every 5 s in battle -> "+Path.GetFileName(file));
    }

    public static void Flush(){try{lock(line)w?.Flush();}catch{}}

    static void After(LabelSystem __instance)
    {
        if(broken||!Runtime.IsApplied||Time.unscaledTime<next)return;
        next=Time.unscaledTime+Every;
        long t0=System.Diagnostics.Stopwatch.GetTimestamp();
        try
        {
            var ctx=Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems.ShootingSystem._gameContext;if(ctx==null||ctx._isDisposed)return;
            var me=__instance._sessionContext?.CurrentPlayer;if(me==null)return;
            if(world!=ctx.Pointer)
            {
                try{units?.Dispose();}catch{}
                units=ctx.GetEntities().With<UnitComponent>().AsSet();world=ctx.Pointer;view.Clear();players.Clear();battleStart=Time.time;
                if(w==null){Directory.CreateDirectory(Path.GetDirectoryName(file)!);w=new StreamWriter(new FileStream(file,FileMode.Append,FileAccess.Write,FileShare.ReadWrite|FileShare.Delete));}
                w.WriteLine($"B {DateTime.UtcNow:u} team {me.TeamSide}");
            }
            var side=me.TeamSide;
            var list=units._entities;int n=Math.Min(units.Count,list?.Length??0);
            line.Clear().Append("S ").Append((int)(Time.time-battleStart));
            for(int i=0;i<n;i++)
            {
                var e=list[i];if(!e.IsAlive)continue;
                var u=NativeEcs.Read<UnitComponent>(e);var owner=u.Owner;if(owner==null||u.UnitData==null)continue;
                if(players.Add(owner.Pointer))
                {
                    var pi=owner.TryCast<PlayerInfo>();
                    w.WriteLine($"P {pi?.UID} {owner.TeamSide} {(pi!=null&&pi.IsBot?"bot":"human")} {(owner.Pointer==me.Pointer?"me":"other")} {pi?.PlayerName}");
                }
                bool enemy=owner.TeamSide!=side;
                char who=enemy?'E':owner.Pointer==me.Pointer?'L':'A';
                var t=e.Has<ViewComponent>()?NativeEcs.Read<ViewComponent>(e).transform:null;
                var p=t!=null?t.position:Vector3.zero;
                float hp=e.Has<HealthComponent>()?NativeEcs.Field<HealthComponent,float>(e,"_health"):-1f;
                line.Append(' ').Append(e.GetHashCode()).Append(':').Append(who).Append(':').Append(u.UnitData.Id).Append(':')
                    .Append((int)p.x).Append(':').Append((int)p.z).Append(':').Append(hp.ToString("0.#",System.Globalization.CultureInfo.InvariantCulture));
                if(!enemy)continue;
                line.Append(':').Append(Spotted(e,side)?'1':'0').Append(Drawn(e,t)?'1':'0');
            }
            // Own cost, so the snapshot's frame time can be checked in the uploaded logs (Osama: no performance hits).
            line.Append(" ms=").Append(((System.Diagnostics.Stopwatch.GetTimestamp()-t0)*1000.0/System.Diagnostics.Stopwatch.Frequency).ToString("0.00",System.Globalization.CultureInfo.InvariantCulture));
            lock(line){w.WriteLine(line);w.Flush();}
            snaps++;
        }
        catch(Exception x){broken=true;MelonLogger.Warning("FREEDOM_ARROW_MATCH_LOG off: "+x.Message);}
    }

    static bool Spotted(Entity target,TeamSide side)
    {
        if(!target.Has<FogOfWarComponent>())return false;
        var seen=NativeEcs.Read<FogOfWarComponent>(target).VisibleTo;if(seen==null)return false;
        foreach(var o in seen)if(o.IsAlive&&o.Has<UnitComponent>()&&NativeEcs.Read<UnitComponent>(o).Owner?.TeamSide==side)return true;
        return false;
    }

    // The game's own model (not FAModels' FAM_holder copy, which only mirrors it), found once per unit.
    static bool Drawn(Entity e,Transform t)
    {
        if(t==null)return false;
        int k=e.GetHashCode();
        if(!view.TryGetValue(k,out var r))
        {
            var holder=t.root.Find("FAM_holder");
            foreach(var c in t.GetComponentsInChildren<Renderer>(true))
                if(c!=null&&(holder==null||!c.transform.IsChildOf(holder))){r=c;break;}
            view[k]=r;
        }
        return r!=null&&r.enabled&&r.gameObject.activeInHierarchy;
    }
}
