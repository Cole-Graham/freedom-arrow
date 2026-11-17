using System.Reflection;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels.Systems;
using Il2CppBrokenArrow.Client.Ecs.Utils;
using Il2CppBrokenArrow.Shared.Ecs;
using Il2CppFMOD;
using Il2CppFMODUnity;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// 0.9.0-dev.35 warning sounds (Osama 16 Nov 2026 20:2x-20:4x and 22:2x PST, thread 1571014792016171120). Files in UserData/FreedomArrow/audio/.
// - Ballistic missile alarm: "on the incoming incoming alarm, we take a 2 second snippet ... that's our ballistic alarm". The alarm belongs to
//   FlatIncomeMod (ActualArrow), which rewrites its ballistic_alarm.ogg from its own DLL at every start, so the sound is swapped after its
//   AlarmSound.Load: ballistic-alarm-cram.ogg (C-RAM "Incoming, incoming, incoming", 2 s).
// - Aircraft detected: "arleigh burke is the aircraft detection sound". FlatIncomeMod's plane warning only shows text; aircraft-alarm-burke.ogg
//   (2 s) now plays with it, on the same game bus, volume setting and mute switch as the ballistic alarm.
// - "40% warning sound which is now the default, it should equalize with the voice lines": FlatIncomeMod's MissileSoundVolume default 0.8 -> 0.4;
//   a player still on the old default moves to 0.4, a player's own value stays. Both alarm files are -20.7 LUFS, so at 0.4 they sit at the level
//   of the voice lines (-16 LUFS x 0.234).
// - Nuclear launch: "this warning should be for any nuclear weapon launched", "in english but for different accents based on faction". Each player
//   hears their own faction's announcement (US Adam, Russia Egor, China San Chi) over Osama's alarm, at the voice-line volume
//   (ChinaVoice.Announce). DF-31A through NuclearLaunchWarning's ballistic hook; the nuclear cruise missiles (Kinzhal, Kh-102, LRSO, ALCM) through
//   FlatIncomeMod's unit query for cruise missiles. The B61 bomb is not a unit and is not covered yet.
static class AlertSounds
{
    static readonly int[] CruiseNukes={340,453,901,902};   // Kh-47M2 Kinzhal, Kh-102, AGM-181A LRSO, AGM-86B ALCM (AmmunitionsJson, nuclear warheads)
    static string dir="";static bool installed,volumeSet,broken;static int logs;
    static Type alarmType,coreType;static object planeRow;static MethodInfo query;static Type unitTypeEnum;
    static Sound burke;static bool burkeReady;static Channel burkeChannel;static float burkeNext;
    static readonly HashSet<long> seen=new();
    static float nextPoll,nextCountry,lastNuke=-100f;static int localCountry;static IntPtr countryWorld;
    static EntitySet units;static IntPtr unitsWorld;

    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        dir=Path.Combine(root,"audio");
        SetVolumeDefault();
        if(installed)return;
        var asm=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="FlatIncomeMod");
        if(asm==null)return;
        alarmType=asm.GetType("FlatIncomeMod.AlarmSound")??throw new MissingMemberException("AlarmSound");
        coreType=asm.GetType("FlatIncomeMod.Core");
        var warnings=asm.GetType("FlatIncomeMod.Warnings")??throw new MissingMemberException("Warnings");
        planeRow=AccessTools.Field(warnings,"Plane")?.GetValue(null)??throw new MissingFieldException("Warnings.Plane");
        var trigger=AccessTools.Method(warnings,"Trigger",new[]{planeRow.GetType()})??throw new MissingMethodException("Warnings.Trigger");
        harmony.Patch(AccessTools.Method(alarmType,"Load")??throw new MissingMethodException("AlarmSound.Load"),postfix:new HarmonyMethod(typeof(AlertSounds),nameof(AfterAlarmLoad)));
        // 0.9.0-dev.36 (Osama 17 Nov 2026 10:1x PST, thread 1567745029781454889: "swap the air warning out and make that the missile warning and then
        // remove the air warning in general because I think there already is one in vanilla"): the Burke sound is now the ballistic missile alarm
        // (AfterAlarmLoad) and nothing plays on the aircraft warning any more; BeforeTrigger is kept but no longer patched.
        var game=asm.GetType("FlatIncomeMod.Game");
        query=game==null?null:AccessTools.Method(game,"Query");
        unitTypeEnum=query?.GetParameters()[0].ParameterType;
        harmony.Patch(AccessTools.Method(typeof(LabelSystem),"Update")??throw new MissingMethodException("LabelSystem.Update"),
            postfix:new HarmonyMethod(typeof(AlertSounds),nameof(AfterLabels)));
        installed=true;
        MelonLogger.Msg($"FREEDOM_ARROW_ALERT_SOUNDS installed: ballistic alarm Burke, no aircraft sound, nuclear by faction; cruise query {(query!=null?"on":"missing")}");
    }

    // FlatIncomeMod creates its entries in its own OnInitializeMelon; this runs again from every Install call until it finds them.
    static void SetVolumeDefault()
    {
        if(volumeSet)return;
        try
        {
            var e=MelonPreferences.GetEntry<float>("FlatIncomeMod","MissileSoundVolume");if(e==null)return;
            e.DefaultValue=0.4f;
            if(Math.Abs(e.Value-0.8f)<0.0001f){e.Value=0.4f;MelonPreferences.Save();}
            volumeSet=true;MelonLogger.Msg($"FREEDOM_ARROW_ALERT_SOUNDS alarm volume default 0.4 (player value {e.Value:0.00})");
        }
        catch(Exception x){volumeSet=true;MelonLogger.Warning("FREEDOM_ARROW_ALERT_SOUNDS volume default failed: "+x.Message);}
    }

    public static void AfterAlarmLoad()
    {
        try
        {
            if(!(bool)(AccessTools.Field(alarmType,"_ready").GetValue(null)??false))return;
            var f=AccessTools.Field(alarmType,"_sound");var old=(Sound)f.GetValue(null);
            if(RuntimeManager.CoreSystem.createSound(Path.Combine(dir,"aircraft-alarm-burke.ogg"),MODE.LOOP_OFF|MODE._2D|MODE.CREATESAMPLE,out var s)!=RESULT.OK)return;
            f.SetValue(null,s);old.release();
            MelonLogger.Msg("FREEDOM_ARROW_ALERT_SOUNDS ballistic alarm = Arleigh Burke alarm");
        }
        catch(Exception x){MelonLogger.Warning("FREEDOM_ARROW_ALERT_SOUNDS ballistic swap failed, the old alarm stays: "+x.Message);}
    }

    public static void BeforeTrigger(object __0)
    {
        if(!ReferenceEquals(__0,planeRow))return;
        try
        {
            if(MelonPreferences.GetEntry<bool>("FlatIncomeMod","MissileSound")?.Value==false)return;
            float now=Time.unscaledTime;if(now<burkeNext)return;burkeNext=now+3f;
            if(!burkeReady){if(RuntimeManager.CoreSystem.createSound(Path.Combine(dir,"aircraft-alarm-burke.ogg"),MODE.LOOP_OFF|MODE._2D|MODE.CREATESAMPLE,out burke)!=RESULT.OK)return;burkeReady=true;}
            bool grouped=(bool)(AccessTools.Field(alarmType,"_hasGroup")?.GetValue(null)??false);
            var group=grouped?(ChannelGroup)AccessTools.Field(alarmType,"_group").GetValue(null):default;
            burkeChannel.stop();
            if(RuntimeManager.CoreSystem.playSound(burke,group,true,out burkeChannel)!=RESULT.OK)return;
            burkeChannel.setVolume(Mathf.Clamp01(MelonPreferences.GetEntry<float>("FlatIncomeMod","MissileSoundVolume")?.Value??0.4f));
            burkeChannel.setPaused(false);
            if(logs++<50)MelonLogger.Msg("FREEDOM_ARROW_ALERT_SOUNDS aircraft detected: Burke alarm");
        }
        catch(Exception x){if(logs++<50)MelonLogger.Warning("FREEDOM_ARROW_ALERT_SOUNDS aircraft alarm failed: "+x.Message);}
    }

    // Nuclear announcement for the local player's faction. Called by NuclearLaunchWarning (DF-31A) and by the cruise-missile poll below.
    public static void Nuke(string what)
    {
        float now=Time.unscaledTime;if(now-lastNuke<8f)return;lastNuke=now;
        string side=localCountry switch{1=>"ru",4=>"cn",_=>"us"};
        ChinaVoice.Announce(Path.Combine(dir,$"nuke-warning-{side}.mp3"));
        MelonLogger.Msg($"FREEDOM_ARROW_ALERT_SOUNDS nuclear launch ({what}): announcement {side} (local country {localCountry})");
    }

    public static void AfterLabels(LabelSystem __instance)
    {
        if(broken||!Runtime.IsApplied)return;
        try
        {
            float now=Time.unscaledTime;
            var world=Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems.ShootingSystem._gameContext;if(world==null||world._isDisposed)return;
            if(now>nextCountry&&(localCountry==0||countryWorld!=world.Pointer))
            {
                nextCountry=now+2f;
                var me=__instance._sessionContext?.CurrentPlayer;
                if(me!=null)
                {
                    if(unitsWorld!=world.Pointer){try{units?.Dispose();}catch{}units=world.GetEntities().With<UnitComponent>().AsSet();unitsWorld=world.Pointer;localCountry=0;}
                    var list=units._entities;int n=Math.Min(units.Count,list?.Length??0);
                    for(int i=0;i<n;i++)
                    {
                        var e=list[i];if(!e.IsAlive)continue;
                        var u=NativeEcs.Read<UnitComponent>(e);
                        if(u.Owner?.TryCast<PlayerInfo>()?.Pointer!=me.Pointer||u.UnitData==null)continue;
                        localCountry=u.UnitData.CountryId;countryWorld=world.Pointer;
                        MelonLogger.Msg($"FREEDOM_ARROW_ALERT_SOUNDS local country {localCountry}");break;
                    }
                }
            }
            if(query==null||now<nextPoll)return;nextPoll=now+0.5f;
            var into=Activator.CreateInstance(query.GetParameters()[1].ParameterType)!;
            query.Invoke(null,new[]{Enum.ToObject(unitTypeEnum,512),into});   // UnitType.CruiseMissile
            foreach(var item in (System.Collections.IEnumerable)into)
            {
                var t=item.GetType();var e=(Entity)t.GetField("Item1")!.GetValue(item)!;long k=(long)t.GetField("Item2")!.GetValue(item)!;
                if(!seen.Add(k))continue;
                if(seen.Count>4096)seen.Clear();
                if(!e.IsAlive||!e.Has<WarheadComponent>())continue;
                int ammo=NativeEcs.Read<WarheadComponent>(e).AmmunitionInfo?.Id??0;
                if(Array.IndexOf(CruiseNukes,ammo)<0)continue;
                NuclearLaunchWarning.Banner();Nuke("cruise ammo "+ammo);
            }
        }
        catch(Exception x){broken=true;MelonLogger.Warning("FREEDOM_ARROW_ALERT_SOUNDS nuclear watch off: "+x.Message);}
    }
}
