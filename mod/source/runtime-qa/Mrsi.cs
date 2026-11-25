using System.Runtime.InteropServices;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Ballistics.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Components.Ownership;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;
// MRSI (Osama 24 Nov 2026 22:3x PST, thread 1575024642593398836: "try to build it as best as you can to be multiplayer friendly. keep it simple and
// minimal hooks. we want reliability"). Batch branch codex/batch/osama/mrsi. Idea from the SCORPION "Artillery MRSI" kit 1.1.0, which reshaped shells only
// for fire missions started on the shooter's PC, so other players saw normal shells (desync).
// How this one stays the same on every PC (read from BA 1.2.2.1):
// - The MRSI loadout (mrsi_1124.py) has its own gun row, so the deck says which guns are MRSI; the gun fires 3 rounds per fire mission by its own data.
// - One postfix on ShootingSystem.WeaponForceFire (RVA 0x80E4C0), the one call that makes every shot: the shooter's PC calls it from
//   ShootingSystem.InternalUpdate, every other PC from NetworkShootService.Remote (0x601609) with the shot message's rotation and random index.
//   FireStats.cs already patches it. It runs once per shot (no per-frame hook) and returns at once unless the round is a trajectory shell.
// - A trajectory shell's flight time is (2000 x DistanceDelta - CurrentDistance) / HorizontalSpeed (GetTimeToTrajectoryEnd 0x82BBC0), and
//   TrajectoryShellSystem.InternalUpdate only adds HorizontalSpeed x dt each frame. So each PC slows each shell of a salvo until it reaches the
//   salvo's landing time, and raises the arc to match (HorizontalSpeed = v cos(a), HorizontalSpeedProportion = tan(a), GetShotParameters 0x82C4A0).
//   The heights array is new for every shot (InterpolateArtilleryTrajectory allocates 2001 floats), so it is scaled in place; no pointer is written.
// - Salvo landing time (game time): first shell's flight + (salvo - 1) x interval + 1 s; every later shell of the salvo aims for the same time.
//   Remote PCs get each shot after the same network delay, so all 3 land together there too (as late as any shell arrives there in vanilla).
// - Laser-guided rounds (Copperhead) keep their normal flight. No mrsi.json or no listed gun: the hook is not installed.
static class Mrsi
{
    [StructLayout(LayoutKind.Explicit,Size=24)]
    struct Trajectory { [FieldOffset(0)] public float DistanceDelta; [FieldOffset(8)] public IntPtr PointHeights; [FieldOffset(16)] public float LastTan; [FieldOffset(20)] public byte Initialized; }
    sealed class Salvo { public int Shells; public float Deadline,Last; }
    const int MaxLog=60;
    static readonly Dictionary<int,float> intervals=new();
    static readonly Dictionary<int,Salvo> salvos=new();
    static int salvoSize=3,logged;
    static bool broken;
    public static void Install(HarmonyLib.Harmony h,string root)
    {
        var file=Path.Combine(root,"mrsi.json");
        if(!File.Exists(file))return;
        var cfg=JsonNode.Parse(File.ReadAllText(file))!;
        salvoSize=cfg["salvo"]?.GetValue<int>()??3;
        foreach(var (id,w) in cfg["weapons"]!.AsObject())intervals[int.Parse(id)]=w!["interval"]!.GetValue<float>();
        if(intervals.Count==0||salvoSize<2)return;
        var m=AccessTools.Method(typeof(ShootingSystem),"WeaponForceFire")??throw new MissingMethodException("ShootingSystem.WeaponForceFire");
        h.Patch(m,postfix:new HarmonyMethod(typeof(Mrsi),nameof(After)));
        MelonLogger.Msg($"FREEDOM_ARROW_MRSI installed: {intervals.Count} MRSI guns, {salvoSize} rounds land together ({string.Join(", ",intervals.Select(kv=>kv.Key+" every "+kv.Value+" s"))})");
        DiagnosticLog.Write("mrsi_installed",new{guns=intervals.Keys.ToArray(),salvo=salvoSize});
    }
    public static void After(in Entity __0,ref Entity __1)
    {
        if(broken||!Runtime.IsApplied)return;
        try
        {
            var shell=__1;
            if(!shell.IsAlive||!shell.Has<TrajectoryShellComponent>()||!shell.Has<WarheadComponent>())return;
            var warhead=NativeEcs.Read<WarheadComponent>(shell);
            int gun=warhead.WeaponInfo?.Id??0;
            if(!intervals.TryGetValue(gun,out float interval)||warhead.AmmunitionInfo==null||warhead.AmmunitionInfo.LaserGuided)return;
            float now=GameController.Instance.GameTime;
            var tr=NativeEcs.Field<TrajectoryShellComponent,Trajectory>(shell,"Trajectory");
            float d=NativeEcs.Field<TrajectoryShellComponent,float>(shell,"CurrentDistance");
            float hs=NativeEcs.Field<TrajectoryShellComponent,float>(shell,"HorizontalSpeed");
            float tan=NativeEcs.Field<TrajectoryShellComponent,float>(shell,"HorizontalSpeedProportion");
            if(tr.PointHeights==IntPtr.Zero||hs<=0||tr.DistanceDelta<=0)return;
            long length=Marshal.ReadInt64(tr.PointHeights,0x18);
            if(length<3||length>100000)return;
            float stock=(2000f*tr.DistanceDelta-d)/hs;
            // One salvo per gun: a new one after salvoSize shells, or when the gun has not fired for longer than its interval + 3 s.
            int key=__0.GetHashCode();   // FireStats.cs keys guns the same way
            if(!salvos.TryGetValue(key,out var s)||s.Shells>=salvoSize||now-s.Last>interval+3)
                salvos[key]=s=new Salvo{Deadline=now+stock+(salvoSize-1)*interval+1};
            int k=++s.Shells;s.Last=now;
            float want=s.Deadline-now;
            bool remote=__0.IsAlive&&__0.Has<NetworkWeaponRemoteComponent>();
            if(want<=stock+0.05f){Log($"shell {k}/{salvoSize} gun {gun} {(remote?"remote":"local")} t {now:F2}: late, normal flight {stock:F2} s");return;}
            // Same muzzle speed v, slower horizontal speed: steeper launch angle, higher arc, same impact point.
            float v=hs*MathF.Sqrt(1+tan*tan),hs2=(2000f*tr.DistanceDelta-d)/want,cos=Math.Clamp(hs2/v,0.02f,1f),tan2=MathF.Sqrt(1-cos*cos)/cos;
            float scale=ScaleArc(tr,length,tan2);
            NativeEcs.WriteField<TrajectoryShellComponent,float>(shell,"HorizontalSpeed",hs2);
            NativeEcs.WriteField<TrajectoryShellComponent,float>(shell,"HorizontalSpeedProportion",tan2);
            Log($"shell {k}/{salvoSize} gun {gun} {(remote?"remote":"local")} t {now:F2}: flight {stock:F2} -> {want:F2} s, lands t {s.Deadline:F2}, speed {hs:F1} -> {hs2:F1}, arc x{scale:F2}");
            if(salvos.Count>512)foreach(var old in salvos.Where(kv=>now-kv.Value.Last>120).Select(kv=>kv.Key).ToList())salvos.Remove(old);
        }
        catch(Exception e){broken=true;MelonLogger.Error("FREEDOM_ARROW_MRSI_FAILED: off from now on, shells fly normally. "+e);}
    }
    // Raise every height above the straight line from muzzle to impact by one factor, so the first step's slope is tan2. Endpoints stay.
    static unsafe float ScaleArc(Trajectory tr,long length,float tan2)
    {
        float* h=(float*)(tr.PointHeights+0x20);
        int n=(int)length-1;
        float c1=h[0]+(h[n]-h[0])/n,above=h[1]-c1;
        if(above<=1e-4f)return 1;
        float scale=Math.Clamp((tan2*tr.DistanceDelta+h[0]-c1)/above,1f,20f);
        for(int j=1;j<n;j++){float c=h[0]+(h[n]-h[0])*j/n;h[j]=c+scale*(h[j]-c);}
        return scale;
    }
    static void Log(string line)
    {
        if(logged>=MaxLog)return;
        logged++;MelonLogger.Msg("FREEDOM_ARROW_MRSI "+line);
    }
}
