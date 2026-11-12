using System.Reflection;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppDefaultEcs;
using Il2CppFMOD;
using Il2CppFMODUnity;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
namespace FreedomArrow;

// DF-31 specialization of the shipped ActualArrow ballistic warning. Its IsRocket
// classification runs once for each new ballistic entity, BEFORE the enemy-owner
// filter. No camera, visibility or team restriction is added here. Do not patch
// the IL2CPP projectile spawner's non-blittable ShellSpawnData arguments.
static class NuclearLaunchWarning
{
    const int Df31Ammo=2010399;
    static bool installed,triggering,reportedFailure;
    static object row;
    static FieldInfo labelField;
    static Func<string> normalLabel;
    static MethodInfo trigger,loadAlarm;
    static Type alarmType;
    static Sound sound;
    static Channel channel;
    static bool soundReady;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        if(installed)return;
        var assembly=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="FlatIncomeMod");
        if(assembly==null)return;
        var warnings=assembly.GetType("FlatIncomeMod.Warnings")??throw new MissingMemberException("Ballistic warning type missing");
        var classify=AccessTools.Method(warnings,"IsRocket",new[]{typeof(Entity)})??throw new MissingMethodException("Ballistic classifier changed");
        row=AccessTools.Field(warnings,"Missile")?.GetValue(null)??throw new MissingFieldException("Ballistic warning row missing");
        labelField=AccessTools.Field(row.GetType(),"Label")??throw new MissingFieldException("Ballistic label missing");
        normalLabel=(Func<string>)labelField.GetValue(row);
        trigger=AccessTools.Method(warnings,"Trigger",new[]{row.GetType()})??throw new MissingMethodException("Ballistic Trigger missing");
        alarmType=assembly.GetType("FlatIncomeMod.AlarmSound")??throw new MissingMemberException("Ballistic audio missing");
        loadAlarm=AccessTools.Method(alarmType,"Load")??throw new MissingMethodException("Ballistic audio loader missing");
        harmony.Patch(classify,postfix:new HarmonyMethod(typeof(NuclearLaunchWarning),nameof(Classified)));
        harmony.Patch(trigger,prefix:new HarmonyMethod(typeof(NuclearLaunchWarning),nameof(BeforeTrigger)));
        installed=true;
        MelonLogger.Msg("PLA_NUCLEAR_WARNING installed: ammo 2010399; existing ballistic poll before team filter; game alarm bus/settings; runtime launch unverified");
    }
    static void BeforeTrigger(object __0)
    {
        if(ReferenceEquals(__0,row))labelField.SetValue(row,triggering?(Func<string>)(()=>"DF-31 NUCLEAR MISSILE LAUNCHED"):normalLabel);
    }
    static void Classified(Entity __0,ref bool __result)
    {
        if(!Runtime.IsApplied||__result)return;
        try
        {
            if(!__0.IsAlive||!__0.Has<WarheadComponent>())return;
            if(NativeEcs.Read<WarheadComponent>(__0).AmmunitionInfo?.Id!=Df31Ammo)return;
            triggering=true;
            try{trigger.Invoke(null,new[]{row});}finally{triggering=false;}
            Play();
            // The normal ballistic warning now skips this entity, so its generic
            // enemy-only label and alarm cannot overwrite/double the nuclear cue.
            __result=true;
            MelonLogger.Msg($"PLA_NUCLEAR_WARNING launch entity {__0.GetHashCode()} ammo {Df31Ammo}; team-independent local alert");
        }
        catch(Exception e)
        {
            triggering=false;
            if(!reportedFailure){reportedFailure=true;MelonLogger.Error("PLA_NUCLEAR_WARNING_FAILED: normal ballistic warning retained. "+e.Message);}
        }
    }
    static void Play()
    {
        // Keep the user's existing ballistic alarm mute and volume preference.
        if(MelonPreferences.GetEntry<bool>("FlatIncomeMod","MissileSound")?.Value==false)return;
        var path=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","audio","df31-nuclear-warning.wav");
        if(!soundReady)
        {
            Check(RuntimeManager.CoreSystem.createSound(path,MODE.LOOP_OFF|MODE._2D|MODE.CREATESAMPLE,out sound),"load");
            soundReady=true;
        }
        // Reuse the ballistic warning's selected game bus, including its routing
        // under the game's master output. Leave the original alarm file untouched.
        if(!(bool)(AccessTools.Field(alarmType,"_ready")?.GetValue(null)??false))loadAlarm.Invoke(null,null);
        bool grouped=(bool)(AccessTools.Field(alarmType,"_hasGroup")?.GetValue(null)??false);
        var group=grouped?(ChannelGroup)AccessTools.Field(alarmType,"_group").GetValue(null):default;
        channel.stop();
        Check(RuntimeManager.CoreSystem.playSound(sound,group,true,out channel),"play");
        float gain=Math.Clamp(MelonPreferences.GetEntry<float>("FlatIncomeMod","MissileSoundVolume")?.Value??0.8f,0f,1f)*0.30f;
        Check(channel.setVolume(gain),"volume");
        Check(channel.setPaused(false),"unpause");
        MelonLogger.Msg($"PLA_NUCLEAR_WARNING audio gain {gain:0.000}; original synthesized draft; game bus {(grouped?"ballistic":"master")}");
    }
    static void Check(RESULT result,string operation)
    {if(result!=RESULT.OK)throw new InvalidOperationException($"Nuclear warning {operation}: {result}");}
    public static void Shutdown()
    {
        if(!soundReady)return;
        channel.stop();sound.release();soundReady=false;
    }
}
