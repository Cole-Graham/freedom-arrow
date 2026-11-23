using System.Collections.Concurrent;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using Il2CppGalaxyCoreCommon;
using Il2CppInterop.Runtime;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// ZTZ-99A laser dazzler (Osama 16 Nov 2026, thread 1571014792016171120: "make it look like APS but shoots at ATGMs ... and shoots a laser
// effect", "maybe 100m is fine ... like an APS that has a longer range", "we don't want it stopping rpgs and recoilless rounds",
// "make it bright red? and intense, hot color"). The unit gets a native APS ability (charges, cooldown, popup, supply and multiplayer sync
// stay native). Read from GameAssembly 12e70883:
// - HitDetectionSystem.GetUnitBox(unit, ammo) (RVA 0x7F1060) multiplies the unit's hit box by APSHitboxProportion when the ammo has
//   CanBeIntercepted (Ammunitions +0xA4) and the unit's APS is ready (APSCount > 0, APSCooldownTimer <= 0). The unit search around each
//   shell is at least MINIMAL_SEARCH = 100 m, so a box that reaches about 100 m is still found.
// - ShellHitSystem.InternalUpdate(shell) (0x7FDA70), on a unit hit: CanBeIntercepted + APS ready -> APS destroys the shell, no damage.
// RPG, recoilless and other unguided rounds carry CanBeIntercepted too. So:
// 1. Box (postfix on GetUnitBox, runs on the hit detection worker threads): for a listed unit with a ready APS and guided interceptable
//    ammo (Seeker > 0, +0x108), the box grows to at least BoxSize metres on each axis. Unguided ammo keeps the native box (the ability
//    row sets APSHitboxProportion 1.0, so the native code does not grow it either).
// 2. Hit (prefix/postfix on ShellHitSystem.InternalUpdate, main thread): an unguided interceptable round that hits a listed unit loses
//    CanBeIntercepted for that one call, so it does normal damage and the APS is kept. A guided one records the hit point for the beam.
// 3. Beam (LateUpdate): when a listed unit's APSCount drops, a red beam from the dazzler head to the recorded point for BeamSeconds.
// Units and numbers: UserData/FreedomArrow/dazzler.json. Logs: dazzler_installed / dazzler_box_native / dazzler_fire / dazzler_rpg_pass /
// dazzler_metrics / dazzler_failed. Not measured in a game yet.
// 4. Laser weapon (Osama 16 Nov 2026 03:3x: "could we add a laser weapon that panicks units?", "replace the 762 gun on the ZTZ ... we can use the
//    same laser as the aps"): the 99A coax (weapon 2009081) fires LSDW pulses, ammo with almost no damage and high StressDamage (native
//    stress -> Shocked -> Panicked). Native targeting and firing; here only the beam per shot (same beam as the APS) and the log
//    dazzler_laser_shot with the target's stress before the pulse lands. Weapons: laserWeapons in dazzler.json.
static unsafe class Dazzler
{
    // Read from the game's metadata at install (BA 1.2.2 values 0xA4 / 0x108); the first main-thread hit cross-checks them again.
    static int CanBeInterceptedOffset=0xA4,SeekerOffset=0x108;
    static HashSet<int> unitIds=new();
    static float laserBeamSeconds=0.2f,boxSize=200,period=0.05f,beamSeconds=0.35f,coreWidth=0.12f,glowWidth=0.45f,headHeight=2.8f;
    static Color core=new(1f,0.92f,0.8f,1f),glow=new(1f,0.06f,0.02f,0.75f);
    static bool enabled,failed,offsetsChecked;
    // Worker snapshot: listed units whose APS is ready now. Stale after MaxAge -> native box.
    static HashSet<ulong> ready=new();static long readyAt;const double MaxAge=0.25;
    static HashSet<ulong> listedKeys=new();
    static HashSet<int> laserIds=new();static HashSet<string> laserNames=new();static string cardIcon;static EntitySet weaponSet;static readonly List<(Entity E,ulong Key,ulong Unit)> lasers=new();
    static readonly Dictionary<ulong,int> laserShots=new(),laserMags=new();static int laserBeams,laserLogs,laserLogErrors;static bool stressOk;
    static World world;static EntitySet unitSet;static float next,nextScan,nextMetrics;
    static readonly List<(Entity E,ulong Key)> listed=new();
    static readonly Dictionary<ulong,int> lastCount=new();
    static readonly Dictionary<ulong,(Vector3 P,float T,int Ammo)> lastHit=new();
    static readonly ConcurrentQueue<(ulong Unit,float X,float Y,float Z)> nativeBoxes=new();
    static readonly HashSet<ulong> boxLogged=new();
    static int grown,fires,beams,passes;
    static Ammunitions restore,restoreDamage;static float savedDamage;static HashSet<int> laserAmmo=new();static int laserHits;
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var file=Path.Combine(root,"dazzler.json");if(!File.Exists(file))return;
        var j=JsonNode.Parse(File.ReadAllText(file))!;
        unitIds=j["units"]!.AsArray().Select(x=>x!.GetValue<int>()).ToHashSet();if(unitIds.Count==0)return;
        boxSize=2*(j["reachMeters"]?.GetValue<float>()??100);
        laserIds=j["laserWeapons"]?.AsArray().Select(x=>x!.GetValue<int>()).ToHashSet()??new();
        laserNames=j["laserWeaponNames"]?.AsArray().Select(x=>x!.GetValue<string>()).ToHashSet()??new();
        cardIcon=j["cardIcon"]?.GetValue<string>();
        // Arsenal card (Osama 03:5x: "on the unit card, where it displays APS, I want it to display this icon instead without ammo count").
        if(!string.IsNullOrEmpty(cardIcon))
        {
            try
            {
                var card=AccessTools.Method(typeof(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitInfoCard),"SetUnitAbilities")??throw new MissingMethodException("SetUnitAbilities");
                harmony.Patch(card,prefix:new HarmonyMethod(typeof(Dazzler),nameof(CardBefore)),postfix:new HarmonyMethod(typeof(Dazzler),nameof(CardAfter)));
            }
            catch(Exception x){DiagnosticLog.Write("dazzler_card_failed",new{error=x.ToString()});MelonLogger.Error("FREEDOM_ARROW_DAZZLER_CARD_FAILED: APS icon stays. "+x.Message);}
            // Battle order panel (Osama 04:3x: "change the in game aps icon to the laser, and don't show the ammo count"): the APS button's count
            // goes through UiOrderButton.SetUsage(state, charges). Only LSDW units carry 999 charges, so >= HudCharges marks an LSDW selection.
            try
            {
                var use=AccessTools.Method(typeof(Il2CppBrokenArrow.Client.Ecs.UI.Orders.UiOrderButton),"SetUsage")??throw new MissingMethodException("UiOrderButton.SetUsage");
                harmony.Patch(use,prefix:new HarmonyMethod(typeof(Dazzler),nameof(UsageBefore)));
            }
            catch(Exception x){DiagnosticLog.Write("dazzler_hud_failed",new{error=x.ToString()});MelonLogger.Error("FREEDOM_ARROW_DAZZLER_HUD_FAILED: APS button stays. "+x.Message);}
        }
        laserAmmo=j["laserAmmo"]?.AsArray().Select(x=>x!.GetValue<int>()).ToHashSet()??new();
        stressOk=NativeEcs.Compiled<StressComponent>()&&NativeEcs.Compiled<TargetComponent>()&&NativeEcs.Compiled<WeaponComponent>();
        var b=j["beam"];
        if(b!=null)
        {
            beamSeconds=b["seconds"]?.GetValue<float>()??beamSeconds;laserBeamSeconds=b["laserSeconds"]?.GetValue<float>()??laserBeamSeconds;coreWidth=b["coreWidth"]?.GetValue<float>()??coreWidth;
            glowWidth=b["glowWidth"]?.GetValue<float>()??glowWidth;headHeight=b["headHeight"]?.GetValue<float>()??headHeight;
            Color C(JsonNode n,Color d)=>n==null?d:new(n[0]!.GetValue<float>(),n[1]!.GetValue<float>(),n[2]!.GetValue<float>(),n[3]!.GetValue<float>());
            core=C(b["core"],core);glow=C(b["glow"],glow);
        }
        if(Unsafe.SizeOf<Entity>()!=8)throw new InvalidOperationException("Entity layout changed");
        CanBeInterceptedOffset=FieldOffset("<CanBeIntercepted>k__BackingField");SeekerOffset=FieldOffset("<Seeker>k__BackingField");
        if(!NativeEcs.Compiled<CounterMeasuresComponent>()||!NativeEcs.Compiled<HitComponent>()||!NativeEcs.Compiled<UnitComponent>()||!NativeEcs.Compiled<TransformComponent>())
            throw new InvalidOperationException("component getter not compiled");
        var box=AccessTools.Method(typeof(HitDetectionSystem),"GetUnitBox")??throw new MissingMethodException("GetUnitBox");
        var bp=box.GetParameters();
        if(box.ReturnType!=typeof(GalaxyVector3)||bp.Length!=2||bp[0].ParameterType!=typeof(Entity)||bp[1].ParameterType!=typeof(Ammunitions))
            throw new InvalidOperationException("GetUnitBox signature changed");
        var hit=AccessTools.Method(typeof(ShellHitSystem),"InternalUpdate")??throw new MissingMethodException("ShellHitSystem.InternalUpdate");
        var hp=hit.GetParameters();
        if(hp.Length!=1||hp[0].ParameterType!=typeof(Entity).MakeByRefType())throw new InvalidOperationException("ShellHitSystem.InternalUpdate signature changed");
        harmony.Patch(box,postfix:new HarmonyMethod(typeof(Dazzler),nameof(BoxAfter)));
        harmony.Patch(hit,prefix:new HarmonyMethod(typeof(Dazzler),nameof(HitBefore)),postfix:new HarmonyMethod(typeof(Dazzler),nameof(HitAfter)));
        enabled=true;
        DiagnosticLog.Write("dazzler_installed",new{units=unitIds.ToArray(),lasers=laserIds.ToArray(),laserNames=laserNames.ToArray(),cardIcon,canBeInterceptedOffset=CanBeInterceptedOffset,seekerOffset=SeekerOffset,boxSize,beamSeconds,core=new[]{core.r,core.g,core.b,core.a},glow=new[]{glow.r,glow.g,glow.b,glow.a}});
        MelonLogger.Msg($"FREEDOM_ARROW_DAZZLER installed: units {string.Join(",",unitIds)}, guided missiles stopped at {boxSize/2:0} m, unguided rounds pass");
    }
    static int FieldOffset(string name)
    {
        var c=Il2CppClassPointerStore<Ammunitions>.NativeClassPtr;if(c==IntPtr.Zero)throw new InvalidOperationException("Ammunitions class missing");
        var f=IL2CPP.il2cpp_class_get_field_from_name(c,name);if(f==IntPtr.Zero)throw new MissingFieldException("Ammunitions",name);
        return checked((int)IL2CPP.il2cpp_field_get_offset(f));
    }
    // ---------- Battle APS button: icon and no count for LSDW units; the original sprites come back for any other APS unit.
    const uint HudCharges=900;static readonly Dictionary<IntPtr,Sprite> hudOriginal=new();static bool hudLogged;
    static void UsageBefore(Il2CppBrokenArrow.Client.Ecs.UI.Orders.UiOrderButton __instance,ref bool __0,uint __1)
    {
        try
        {
            bool lsdw=__0&&__1>=HudCharges;
            foreach(var img in __instance.GetComponentsInChildren<UnityEngine.UI.Image>(true))
            {
                var sp=img.sprite;if(sp==null)continue;var key=img.Pointer;
                if(lsdw)
                {
                    if(!sp.name.StartsWith("Ability_Aps"))continue;
                    var cache=Il2CppBrokenArrow.Client.Ecs.UI.IconsLoader._sprites;Sprite icon=null;
                    if(cache==null||!cache.TryGetValue(cardIcon,out icon)){ChinaUi.Seed();cache=Il2CppBrokenArrow.Client.Ecs.UI.IconsLoader._sprites;if(cache==null||!cache.TryGetValue(cardIcon,out icon))return;}
                    hudOriginal[key]=sp;img.sprite=icon;
                    if(!hudLogged){hudLogged=true;DiagnosticLog.Write("dazzler_hud_icon",new{charges=__1,replaced=sp.name});}
                }
                else if(hudOriginal.TryGetValue(key,out var orig)&&orig!=null){img.sprite=orig;hudOriginal.Remove(key);}
            }
            if(lsdw)__0=false;   // no charge count on the button
        }
        catch(Exception x){DiagnosticLog.Write("dazzler_hud_failed",new{error=x.ToString()});}
    }
    // ---------- Arsenal card: the APS entry of a listed unit shows cardIcon and no charge count. Items are pooled, so counts this hook hid are
    // shown again before the native code fills the next card.
    static readonly List<GameObject> hiddenCounts=new();static bool cardLogged;
    static void CardBefore()
    {
        foreach(var g in hiddenCounts)try{if(g!=null)g.SetActive(true);}catch{}
        hiddenCounts.Clear();
    }
    static void CardAfter(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitInfoCard __instance,Units __0)
    {
        try
        {
            // Only the LSDW loadout (999 charges). The ZTZ-99B options (GL-6 APS, LSDW + GL-6 APS) are the same unit 904 with the normal 2-charge APS
            // and keep the native APS icon and count (Osama 23 Nov 2026 11:3x).
            if(__0==null||!unitIds.Contains(__0.Id)||(__0.ActiveAbilities?.APSQuantity??0)<HudCharges)return;
            Sprite icon=null;var cache=Il2CppBrokenArrow.Client.Ecs.UI.IconsLoader._sprites;
            if(cache==null||!cache.TryGetValue(cardIcon,out icon)){ChinaUi.Seed();cache=Il2CppBrokenArrow.Client.Ecs.UI.IconsLoader._sprites;if(cache==null||!cache.TryGetValue(cardIcon,out icon))return;}
            var items=__instance._activeAbilitiesItems;if(items==null)return;
            for(int i=0;i<items.Count;i++)
            {
                var it=items[i];var img=it?.Icon;if(img==null||img.sprite==null||img.sprite.name!="APS")continue;
                img.sprite=icon;var c=it.CountContainer;if(c!=null&&c.activeSelf){c.SetActive(false);hiddenCounts.Add(c);}
                if(!cardLogged){cardLogged=true;DiagnosticLog.Write("dazzler_card_icon",new{unit=__0.Id,icon=cardIcon});}
            }
        }
        catch(Exception x){DiagnosticLog.Write("dazzler_card_failed",new{error=x.ToString()});}
    }
    // Hit detection worker threads: reads the snapshot and two ammo fields only.
    static void BoxAfter(Entity __0,Ammunitions __1,ref GalaxyVector3 __result)
    {
        if(!enabled||failed||__1==null)return;
        var r=Volatile.Read(ref ready);if(r.Count==0)return;
        ulong k=Key(__0);if(!r.Contains(k))return;
        if((Stopwatch.GetTimestamp()-Volatile.Read(ref readyAt))/(double)Stopwatch.Frequency>MaxAge)return;
        byte* p=(byte*)__1.Pointer;if(p==null||p[CanBeInterceptedOffset]==0||*(int*)(p+SeekerOffset)<=0)return;
        if(nativeBoxes.Count<64)nativeBoxes.Enqueue((k,__result.X,__result.Y,__result.Z));
        if(__result.X<boxSize)__result.X=boxSize;if(__result.Y<boxSize)__result.Y=boxSize;if(__result.Z<boxSize)__result.Z=boxSize;
        Interlocked.Increment(ref grown);
    }
    // Main thread. An unguided interceptable round that hits a listed unit does normal damage: CanBeIntercepted is off for this call only.
    static void HitBefore(ref Entity __0)
    {
        Restore();
        if(!enabled||failed)return;
        try
        {
            var shell=__0;if(!shell.IsAlive||!shell.Has<HitComponent>())return;
            var h=NativeEcs.Read<HitComponent>(shell);
            // Laser pulse (Osama 03:44 "forcing it to fire when it does no damage"): the ammo row has a normal Damage so native targeting
            // scores and fires it like a gun; the damage is zero only while this hit is processed. StressDamage is a separate field.
            if(laserAmmo.Count>0)
            {
                var la=h.AmmoInfo;
                if(la!=null&&laserAmmo.Contains(la.Id)){savedDamage=la.Damage;la.Damage=0f;restoreDamage=la;laserHits++;return;}
            }
            var t=h.TargetEntity;if(!listedKeys.Contains(Key(t)))return;
            var ammo=h.AmmoInfo;if(ammo==null)return;
            if(!offsetsChecked)
            {
                byte* p=(byte*)ammo.Pointer;
                if((p[CanBeInterceptedOffset]!=0)!=ammo.CanBeIntercepted||*(int*)(p+SeekerOffset)!=(int)ammo.Seeker)
                    throw new InvalidOperationException("Ammunitions field offsets changed");
                offsetsChecked=true;
            }
            if(!ammo.CanBeIntercepted)return;
            float now=Time.time;
            if((int)ammo.Seeker<=0)
            {
                ammo.CanBeIntercepted=false;restore=ammo;
                if(passes++<200)DiagnosticLog.Write("dazzler_rpg_pass",new{t=now,unit=Key(t).ToString("X16"),ammo=ammo.Id});
                return;
            }
            var pt=h.Point;lastHit[Key(t)]=(new Vector3(pt.X,pt.Y,pt.Z),now,ammo.Id);
        }
        catch(Exception x){Fail(x);}
    }
    static void HitAfter()=>Restore();
    static void Restore()
    {
        if(restore!=null){restore.CanBeIntercepted=true;restore=null;}
        if(restoreDamage!=null){restoreDamage.Damage=savedDamage;restoreDamage=null;}
    }
    static void Fail(Exception x)
    {
        try{Restore();}catch{}restore=restoreDamage=null;
        failed=true;Volatile.Write(ref ready,new HashSet<ulong>());try{foreach(var b in live)Drop(b);live.Clear();}catch{}
        DiagnosticLog.Write("dazzler_failed",new{error=x.ToString()});MelonLogger.Error("FREEDOM_ARROW_DAZZLER_FAILED: native APS. "+x.Message);
    }
    public static void SceneChanged()
    {
        Volatile.Write(ref ready,new HashSet<ulong>());listedKeys=new();
        try{if(world!=null&&!world._isDisposed){unitSet?.Dispose();weaponSet?.Dispose();}}catch{}
        world=null;unitSet=null;weaponSet=null;lasers.Clear();laserShots.Clear();laserMags.Clear();listed.Clear();lastCount.Clear();lastHit.Clear();boxLogged.Clear();next=nextScan=0;
        foreach(var b in live)Drop(b);live.Clear();
    }
    public static void LateUpdate()
    {
        if(live.Count>0)FadeBeams();   // also after a failure, so no beam is left on screen (dev.21 test)
        if(!enabled||failed)return;
        if(!Runtime.IsApplied||!Conquest.Prototype.DiagnosticSceneActive){Volatile.Write(ref ready,new HashSet<ulong>());return;}
        float now=Time.time;if(now<next)return;next=now+period;
        try
        {
            var current=ShootingSystem._gameContext;if(current==null||current._isDisposed)return;
            if(world==null||world.Pointer!=current.Pointer){SceneChanged();world=current;unitSet=world.GetEntities().With<UnitComponent>().With<CounterMeasuresComponent>().AsSet();if(laserIds.Count>0||laserNames.Count>0)weaponSet=world.GetEntities().With<WeaponComponent>().AsSet();}
            if(now>=nextScan)
            {
                nextScan=now+2;listed.Clear();var keys=new HashSet<ulong>();var ua=unitSet._entities;int n=Math.Min(unitSet.Count,ua?.Length??0);
                for(int i=0;i<n&&i<4096;i++)
                {
                    var e=ua[i];if(!e.IsAlive||!e.Has<UnitComponent>())continue;
                    var d=NativeEcs.Read<UnitComponent>(e).UnitData;if(d==null||!unitIds.Contains(d.Id))continue;
                    // A listed unit is a laser unit only while its APS holds LSDW charges (999). Osama 23 Nov 2026 11:3x: the ZTZ-99B loadouts
                    // (GL-6 APS, LSDW + GL-6 APS) use the normal APS: 2 charges, 10 s, native 2x hit box reach, RPGs intercepted. Before this they
                    // got the 200 m laser reach and the RPG pass because the unit ID is 904 for every loadout.
                    if(NativeEcs.EncodedInt<CounterMeasuresComponent>(e,"APSCount")<HudCharges)continue;
                    listed.Add((e,Key(e)));keys.Add(Key(e));
                }
                listedKeys=keys;
                lasers.Clear();
                if(weaponSet!=null&&stressOk)
                {
                    var wa=weaponSet._entities;int wn=Math.Min(weaponSet.Count,wa?.Length??0);
                    for(int i=0;i<wn&&i<8192;i++)
                    {
                        var e=wa[i];if(!e.IsAlive||!e.Has<WeaponComponent>())continue;
                        var w=NativeEcs.Read<WeaponComponent>(e);var info=w?.WeaponInfo;if(info==null||!(laserIds.Contains(info.Id)||laserNames.Contains(info.HUDName)))continue;
                        var u=w.GetUnitEntity();if(u.IsAlive)lasers.Add((e,Key(e),Key(u)));
                    }
                }
            }
            var r=new HashSet<ulong>();
            foreach(var (e,k) in listed)
            {
                if(!e.IsAlive||!e.Has<CounterMeasuresComponent>())continue;
                int count=NativeEcs.EncodedInt<CounterMeasuresComponent>(e,"APSCount");
                if(NativeEcs.Property<CounterMeasuresComponent,bool>(e,"HasReadyAPS"))r.Add(k);
                if(lastCount.TryGetValue(k,out var was)&&count<was&&lastHit.TryGetValue(k,out var h)&&now-h.T<1f)
                {
                    var head=NativeEcs.Property<TransformComponent,Vector3>(e,"Position")+Vector3.up*headHeight;
                    fires++;Beam(head,h.P);
                    DiagnosticLog.Write("dazzler_fire",new{t=now,unit=k.ToString("X16"),ammo=h.Ammo,distance=Vector3.Distance(head,h.P),charges=count});
                    lastHit.Remove(k);
                }
                lastCount[k]=count;
            }
            Volatile.Write(ref ready,r);Volatile.Write(ref readyAt,Stopwatch.GetTimestamp());
            foreach(var (e,k,uk) in lasers)
            {
                if(!e.IsAlive||!e.Has<WeaponComponent>())continue;
                var w=NativeEcs.Read<WeaponComponent>(e);var u=w.GetUnitEntity();if(!u.IsAlive||!u.Has<TransformComponent>())continue;
                int made=w.ShotsMade.Value,mag=w.AmmoInMagazine.Value;
                // ShotsMade goes up once per shot and back down when the weapon resets its count; only the rise is a shot (dev.23 drew two beams per pulse).
                // dev.35 (Osama 16 Nov 22:2x: "lasers seem to only fire every other shot"): a single-shot burst can rise and reset ShotsMade inside one
                // scan, so that pulse showed no beam. A drop in AmmoInMagazine is also a shot (a reload only raises it).
                bool rose=laserShots.TryGetValue(k,out var was)&&made>was,spent=laserMags.TryGetValue(k,out var mWas)&&mag<mWas;
                laserMags[k]=mag;
                if((rose||spent)&&e.Has<TargetComponent>())
                {
                    var t=NativeEcs.Field<TargetComponent,Entity>(e,"Target");
                    if(t.IsAlive&&t.Has<TransformComponent>())
                    {
                        var head=NativeEcs.Property<TransformComponent,Vector3>(u,"Position")+Vector3.up*headHeight;
                        var at=NativeEcs.Property<TransformComponent,Vector3>(t,"CenterPosition");
                        Beam(head,at,laserBeamSeconds);laserBeams++;
                        if(laserLogs++<3000)
                        try
                        {
                            bool hs=t.Has<StressComponent>();
                            DiagnosticLog.Write("dazzler_laser_shot",new{t=now,unit=uk.ToString("X16"),target=Key(t).ToString("X16"),
                                targetType=t.Has<UnitComponent>()?(int)NativeEcs.Read<UnitComponent>(t).UnitData.Type:-1,distance=Vector3.Distance(head,at),
                                stress=hs?NativeEcs.Field<StressComponent,float>(t,"CurrentStressValue"):-1f,level=hs?(int)NativeEcs.Field<StressComponent,byte>(t,"CurrentStressLevel"):-1});
                        }
                        catch(Exception x){if(laserLogErrors++<5)DiagnosticLog.Write("dazzler_laser_log_failed",new{error=x.Message});}
                    }
                }
                laserShots[k]=made;
            }

            int flushed=0;
            while(flushed++<16&&nativeBoxes.TryDequeue(out var nb))
                if(boxLogged.Add(nb.Unit))DiagnosticLog.Write("dazzler_box_native",new{t=now,unit=nb.Unit.ToString("X16"),x=nb.X,y=nb.Y,z=nb.Z,grownTo=boxSize});
            if(now>=nextMetrics){nextMetrics=now+10;DiagnosticLog.Write("dazzler_metrics",new{t=now,units=listed.Count,ready=r.Count,boxesGrown=Volatile.Read(ref grown),fires,beams,rpgPasses=passes,lasers=lasers.Count,laserBeams,laserHitsZeroed=laserHits});}
        }
        catch(Exception x){Fail(x);}
    }
    // ---------- Beam: two cylinders (white-hot core, red glow) on a copy of the game's HDRP/Unlit border material, faded out.
    sealed class Live{public GameObject Go;public Renderer Core,Glow;public float Born,Life;}
    static readonly List<Live> live=new();
    static Material coreMat,glowMat;static bool materialMissing;
    static bool EnsureMaterials()
    {
        if(coreMat!=null&&glowMat!=null)return true;if(materialMissing)return false;
        Material source=null;
        foreach(var o in Resources.FindObjectsOfTypeAll(Il2CppType.Of<Material>()))
        {
            var m=o.TryCast<Material>();
            if(m!=null&&m.name=="ObjZone_Border"&&m.shader!=null&&m.shader.name=="HDRP/Unlit"){source=m;break;}
        }
        if(source==null){materialMissing=true;DiagnosticLog.Write("dazzler_beam_material_missing",new{material="ObjZone_Border"});return false;}
        Material Make(Color c,string name)
        {
            var m=new Material(source){hideFlags=HideFlags.HideAndDontSave,name=name};
            m.SetTexture("_UnlitColorMap",Texture2D.whiteTexture);m.SetTexture("_MainTex",Texture2D.whiteTexture);m.SetColor("_UnlitColor",c);return m;
        }
        coreMat=Make(core,"FreedomArrow dazzler core");glowMat=Make(glow,"FreedomArrow dazzler glow");return true;
    }
    static void Beam(Vector3 from,Vector3 to,float life=-1)
    {
        if(!EnsureMaterials())return;
        var go=new GameObject("FreedomArrow dazzler beam");
        Renderer Rod(float width,Material m)
        {
            var c=GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            var col=c.GetComponent<Collider>();if(col!=null)UnityEngine.Object.Destroy(col);
            c.transform.SetParent(go.transform,false);
            float len=Vector3.Distance(from,to);
            c.transform.position=(from+to)/2;c.transform.up=(to-from).normalized;c.transform.localScale=new Vector3(width,len/2,width);
            var r=c.GetComponent<Renderer>();r.sharedMaterial=m;r.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;r.receiveShadows=false;return r;
        }
        live.Add(new Live{Go=go,Glow=Rod(glowWidth,glowMat),Core=Rod(coreWidth,coreMat),Born=Time.time,Life=life>0?life:beamSeconds});beams++;
    }
    static void Drop(Live b)
    {
        try{if(b.Core!=null)UnityEngine.Object.Destroy(b.Core.material);if(b.Glow!=null)UnityEngine.Object.Destroy(b.Glow.material);if(b.Go!=null)UnityEngine.Object.Destroy(b.Go);}catch{}
    }
    static void FadeBeams()
    {
        float now=Time.time;
        for(int i=live.Count-1;i>=0;i--)
        {
            var b=live[i];float k=1-(now-b.Born)/b.Life;
            if(k<=0||b.Go==null){Drop(b);live.RemoveAt(i);continue;}
            b.Core.material.SetColor("_UnlitColor",new Color(core.r,core.g,core.b,core.a*k));
            b.Glow.material.SetColor("_UnlitColor",new Color(glow.r,glow.g,glow.b,glow.a*k));
        }
    }
}
