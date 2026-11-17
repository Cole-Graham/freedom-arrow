using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.AudioSystem.AudioCommand;
using Il2CppBrokenArrow.Client.Ecs.Audio;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using MelonLoader.Utils;
namespace FreedomArrow;

// 0.9.0-dev.10 (Osama 14 Nov 2026 23:3x PST: "for dev 10 also, remove all the voice lines for China"). China units (CountryId 4)
// borrow Russian and US sound presets, so they spoke Russian or C&C lines. AudioCommandSystem.PlayCommand(Entity) plays one
// unit's line through AudioCommandsCollection.GetEventByCommand, and plays nothing when that returns "". While PlayCommand runs
// for a China unit, GetEventByCommand returns "". Runs before FAMusic's postfix, so no other clip plays either.
// PlayCommand itself still runs, so the game's own command bookkeeping is unchanged.
// 0.9.0-dev.34 (Osama 16 Nov 2026 19:56 PST, thread 1571014792016171120): China units speak our own lines (work/china-voices,
// ElevenLabs, -16 LUFS like FAMusic's C&C clips). UserData/FreedomArrow/china-voices.json maps unit id -> voice set
// (ChinaVoice/<set>/<Trigger>/) and unit folder (ChinaVoice/Units/<unit>/<Trigger>/, added to the set's clips); unmapped China units
// use the set for their Type. The trigger comes from the command and from which collection slot the game picked (Selection or
// SelectionCBT, Move or MoveCBT, ...). A clip plays through our own FMOD system, as FAMusic does; with no clip the unit stays silent.
internal static class ChinaVoice
{
    const int China=4;
    [ThreadStatic] static bool chinaSpeaking;
    [ThreadStatic] static int speakerId,speakerType,speakerCategory;
    static bool broken;static int muted,played;
    static string dir="";static readonly Dictionary<int,(string set,string unit)> units=new();static readonly Dictionary<string,string> fallback=new();
    static float volume=0.234f;
    static IntPtr system,sound,channel;
    static readonly Dictionary<string,List<string>> files=new(),bags=new();static string last="";
    static readonly System.Random rng=new();

    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var play=AccessTools.Method(typeof(AudioCommandSystem),"PlayCommand")??throw new InvalidOperationException("AudioCommandSystem.PlayCommand not found");
        var pick=AccessTools.Method(typeof(AudioCommandsCollection),nameof(AudioCommandsCollection.GetEventByCommand))??throw new InvalidOperationException("GetEventByCommand not found");
        harmony.Patch(play,prefix:new HarmonyMethod(typeof(ChinaVoice),nameof(PlayBefore)),finalizer:new HarmonyMethod(typeof(ChinaVoice),nameof(PlayDone)));
        harmony.Patch(pick,postfix:new HarmonyMethod(typeof(ChinaVoice),nameof(PickAfter)){priority=Priority.First});
        dir=Path.Combine(root,"ChinaVoice");
        try{LoadConfig(Path.Combine(root,"china-voices.json"));OpenFmod();}
        catch(Exception e){system=IntPtr.Zero;MelonLogger.Warning("FREEDOM_ARROW_CHINA_VOICE lines off, China units stay silent: "+e.Message);}
        MelonLogger.Msg($"FREEDOM_ARROW_CHINA_VOICE installed: {units.Count} China units mapped, {(system!=IntPtr.Zero?"own lines on":"silent")}");
    }

    static void LoadConfig(string f)
    {
        var j=JsonNode.Parse(File.ReadAllText(f))!;
        foreach(var kv in j["units"]!.AsObject())units[int.Parse(kv.Key)]=((string)kv.Value!["set"]!,(string)kv.Value["unit"]);
        foreach(var kv in j["fallback"]!.AsObject())fallback[kv.Key]=(string)kv.Value!;
        volume=(float?)j["volume"]??volume;
    }

    static void OpenFmod()
    {
        // The game's FMOD library is in BrokenArrow_Data/Plugins/x86_64, not on the search path (FAMusic does the same).
        System.Runtime.InteropServices.NativeLibrary.Load(Path.Combine(MelonEnvironment.GameRootDirectory,"BrokenArrow_Data","Plugins","x86_64","fmodstudio.dll"));
        if(Fmod.FMOD_System_Create(out system,Fmod.Version)!=0||Fmod.FMOD_System_Init(system,4,0,IntPtr.Zero)!=0)throw new InvalidOperationException("FMOD system");
    }

    public static void Tick(){if(system!=IntPtr.Zero)Fmod.FMOD_System_Update(system);}

    public static void PlayBefore(in Entity __0)
    {
        chinaSpeaking=false;
        if(broken||!Runtime.IsApplied)return;
        try
        {
            var unit=__0;
            if(!unit.IsAlive||!unit.Has<UnitComponent>())return;
            var d=NativeEcs.Read<UnitComponent>(unit).UnitData;
            chinaSpeaking=d?.CountryId==China;
            if(chinaSpeaking){speakerId=d!.Id;speakerType=(int)d.Type;speakerCategory=(int)d.CategoryType;}
        }
        catch(Exception e){broken=true;MelonLogger.Warning("FREEDOM_ARROW_CHINA_VOICE disabled, China units use their preset voices: "+e.Message);}
    }

    public static Exception PlayDone(Exception __exception){chinaSpeaking=false;return __exception;}

    public static void PickAfter(AudioCommandsCollection __instance,AudioCommandType command,bool isUp,ref string __result)
    {
        if(!chinaSpeaking)return;
        var slot=__result??"";__result="";
        try{Speak(__instance,(int)command,isUp,slot);}
        catch(Exception e){if(muted++<20)MelonLogger.Warning("FREEDOM_ARROW_CHINA_VOICE line failed: "+e.Message);}
    }

    // Osama 7 Nov (FAMusic, same rule here): move and attack orders speak about half as often. The first order after 6 s quiet
    // always speaks; after that every second order stays silent.
    static float lastOrder=-100f;static bool skipOrder;
    static bool IsOrder(int c)=>c is 1 or 2 or 3 or 4 or 5 or 6 or 27;

    static void Speak(AudioCommandsCollection c,int cmd,bool isUp,string slot)
    {
        if(system==IntPtr.Zero)return;
        if(!units.TryGetValue(speakerId,out var map))
        {
            if(!fallback.TryGetValue($"{speakerType}:{speakerCategory}",out var s)&&!fallback.TryGetValue(speakerType.ToString(),out s))return;
            map=(s,null!);
        }
        var clips=Clips(map,Triggers(c,cmd,isUp,slot));
        if(clips.Count==0){if(muted++<20)MelonLogger.Msg($"FREEDOM_ARROW_CHINA_VOICE no line: unit {speakerId} command {cmd} {map.set}");return;}
        if(IsOrder(cmd))
        {
            var now=UnityEngine.Time.unscaledTime;
            if(now-lastOrder>6f)skipOrder=false;
            if(skipOrder){skipOrder=false;return;}
            skipOrder=true;lastOrder=now;
        }
        var file=Next(map.set+"|"+map.unit+"|"+cmd+"|"+slot,clips);
        if(channel!=IntPtr.Zero)Fmod.FMOD_Channel_Stop(channel);
        if(sound!=IntPtr.Zero)Fmod.FMOD_Sound_Release(sound);
        channel=sound=IntPtr.Zero;
        if(Fmod.FMOD_System_CreateSound(system,Encoding.UTF8.GetBytes(file+"\0"),0x80|0x8|0x1,IntPtr.Zero,out sound)!=0
           ||Fmod.FMOD_System_PlaySound(system,sound,IntPtr.Zero,0,out channel)!=0)return;
        Fmod.FMOD_Channel_SetVolume(channel,volume*Slider());
        if(played++<200)MelonLogger.Msg($"FREEDOM_ARROW_CHINA_VOICE unit {speakerId} command {cmd} -> {Path.GetRelativePath(dir,file)}");
    }

    // Folders to try, in order; the first one with clips wins. Names are the trigger folders under each set.
    static string[] Triggers(AudioCommandsCollection c,int cmd,bool isUp,string slot)
    {
        bool cbt(string s)=>!string.IsNullOrEmpty(s)&&slot==s;
        return cmd switch
        {
            0=>cbt(c.SelectionCBT)?new[]{"Selection_CBT","Selection"}:new[]{"Selection"},
            1=>new[]{"Attack","Missile","Strike"},
            2=>new[]{"FireAtPosition","FireAtWill","Attack"},
            3=>cbt(c.MoveCBT)?new[]{"Move_CBT","Move"}:new[]{"Move"},
            4=>new[]{"MoveAndAttack","Attack"},
            5=>new[]{"ReverseMove","Move"},
            6=>new[]{"FastMove","Move"},
            7=>new[]{"Smoke"},
            8=>new[]{"Spawn"},
            11=>new[]{isUp?"Heli_Up":"Heli_Down"},
            12=>new[]{"Board","LoadInfantry"},
            13=>new[]{"UnloadNow"},
            19=>new[]{"RTB"},
            20=>new[]{"Laser","Attack"},
            22=>new[]{cbt(c.RadarOn)?"Radar_ON":"Radar_OFF"},
            25=>cbt(c.CancelCommandCBT)?new[]{"Cancel_CBT","Cancel"}:new[]{"Cancel"},
            26=>new[]{"Impossible"},
            27=>new[]{"Sprint","FastMove","Move"},
            28=>new[]{"DefenceSmoke","Smoke"},
            30=>new[]{"Afterburner"},
            31=>cbt(c.GarrisonCBT)?new[]{"Garrison_CBT","Garrison"}:new[]{"Garrison"},
            32=>new[]{"Board"},
            33=>new[]{"LoadInfantry"},
            34=>new[]{"Hurt","Hurt_Panicked"},
            35=>new[]{"Fly_High"},
            36=>new[]{"Fly_Low"},
            37 or 38=>new[]{"Strike_Complete"},
            39=>new[]{"Bomb"},
            40=>new[]{"Strafe"},
            41 or 50=>new[]{"Flares"},
            43=>new[]{"Eject"},
            44=>new[]{"Fuel_Warning"},
            45=>new[]{"Fuel_Out"},
            46=>new[]{"Death"},
            48=>new[]{"EnemyDestroyed"},
            49=>new[]{"AmmoOut"},
            51=>new[]{"Panicked","Hurt_Panicked"},
            _=>Array.Empty<string>()
        };
    }

    // Attack also pools the plane Missile and Strike lines; every other command uses the first folder that has clips.
    static List<string> Clips((string set,string unit) map,string[] triggers)
    {
        var all=new List<string>();
        for(int i=0;i<triggers.Length;i++)
        {
            var t=triggers[i];
            all.AddRange(Files(Path.Combine(dir,map.set,t)));
            if(map.unit!=null)all.AddRange(Files(Path.Combine(dir,"Units",map.unit,t)));
            if(all.Count>0&&!(triggers[0]=="Attack"&&i<2))break;
        }
        return all;
    }

    static List<string> Files(string d)
    {
        if(!files.TryGetValue(d,out var l))files[d]=l=Directory.Exists(d)?Directory.GetFiles(d,"*.mp3").OrderBy(x=>x).ToList():new List<string>();
        return l;
    }

    // Each pool plays all its clips in shuffled order before any repeats, and the same file never plays twice in a row.
    static string Next(string key,List<string> clips)
    {
        if(!bags.TryGetValue(key,out var bag)||bag.Count==0)bags[key]=bag=clips.OrderBy(_=>rng.Next()).ToList();
        int i=bag.FindIndex(f=>f!=last);if(i<0)i=0;
        var file=bag[i];bag.RemoveAt(i);last=file;return file;
    }

    static float Slider()
    {
        try
        {
            var studio=Il2CppFMODUnity.RuntimeManager.StudioSystem.handle;
            if(Fmod.FMOD_Studio_System_GetParameterByName(studio,Encoding.UTF8.GetBytes("Volume_Voice_Commands\0"),out _,out float v)==0)
                return v>=0f&&v<=1f?v:(float)Math.Pow(10,Math.Min(v,0f)/20);
        }
        catch{}
        return 1f;
    }

    static class Fmod
    {
        public const uint Version=131345;   // FMOD.VERSION.number in the game's FMOD wrapper (dump.cs), as FAMusic
        const string Dll="fmodstudio";
        [DllImport(Dll)] public static extern int FMOD_System_Create(out IntPtr system,uint headerVersion);
        [DllImport(Dll)] public static extern int FMOD_System_Init(IntPtr system,int maxChannels,uint flags,IntPtr extra);
        [DllImport(Dll)] public static extern int FMOD_System_Update(IntPtr system);
        [DllImport(Dll)] public static extern int FMOD_System_CreateSound(IntPtr system,byte[] name,uint mode,IntPtr exinfo,out IntPtr sound);
        [DllImport(Dll)] public static extern int FMOD_System_PlaySound(IntPtr system,IntPtr sound,IntPtr group,int paused,out IntPtr channel);
        [DllImport(Dll)] public static extern int FMOD_Channel_SetVolume(IntPtr channel,float volume);
        [DllImport(Dll)] public static extern int FMOD_Channel_Stop(IntPtr channel);
        [DllImport(Dll)] public static extern int FMOD_Sound_Release(IntPtr sound);
        [DllImport(Dll)] public static extern int FMOD_Studio_System_GetParameterByName(IntPtr system,byte[] name,out float value,out float finalValue);
    }
}
