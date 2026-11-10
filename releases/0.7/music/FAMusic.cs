using System.Runtime.InteropServices;
using System.Text;
using HarmonyLib;
using MelonLoader;
using MelonLoader.Utils;
using Il2CppBrokenArrow.AudioSystem;

[assembly: MelonInfo(typeof(FAMusic.Player), "FA Music", "1.4.2", "Freedom Arrow development")]
[assembly: MelonGame(null, null)]
[assembly: HarmonyDontPatchAll]
namespace FAMusic;

// Plays audio files from UserData/FAMusic/Packs/<pack> instead of the game's music.
// A button on the main menu picks the pack, or "Game music" for the original soundtrack.
// It runs its own FMOD system, so it does not touch the game's sound banks.
public sealed class Player : MelonMod
{
    static readonly string Root = Path.Combine(MelonEnvironment.GameRootDirectory, "UserData", "FAMusic");
    static readonly string PacksDir = Path.Combine(Root, "Packs");
    static readonly string PackFile = Path.Combine(Root, "pack.txt");
    const string GameMusic = "Game music";
    static string pack = GameMusic;
    static int lastType = 2;
    // Battle clock for calm/combat music: starts when the battle music cue (type 50) arrives, game time (pauses and speed count).
    static float battleStart = -1f;
    static int OpeningSeconds()
    {
        // Freedom Arrow conquest: Round 1 (no scoring) lasts OpeningDelaySeconds. One home for the number: its settings file.
        try
        {
            var f = Path.Combine(MelonEnvironment.GameRootDirectory, "UserData", "FAConquestPrototype", "settings.json");
            var m = System.Text.RegularExpressions.Regex.Match(File.ReadAllText(f), "\"OpeningDelaySeconds\"\\s*:\\s*(\\d+)");
            if (m.Success) return int.Parse(m.Groups[1].Value);
        }
        catch { }
        return 300;
    }
    static void TrackBattle(int type)
    {
        if (type == 50 && lastType != 50) battleStart = UnityEngine.Time.time;
        else if (type != 50 && type != 100) battleStart = -1f;
    }
    static readonly string[] Extensions = { ".mp3", ".ogg", ".wav", ".flac" };
    static readonly Random Rng = new();
    static Il2Cpp.MusicService service;
    static string folder;          // folder chosen for the current game music type
    // One shuffled queue per folder, kept across matches, so every song plays once before any song repeats.
    static readonly Dictionary<string, List<string>> queues = new();
    static readonly MenuSequence menuSequence = new();
    static IntPtr system, sound, channel;
    // Base level under the game's Music slider. Osama, 7 Nov 2026: slider 50% should sound like 12% did at 0.5.
    const float volume = 0.086f;   // Osama 7 Nov: old 50% level (0.12 x 0.5) now sits at 70%
    static float slider = 1f, nextSliderRead;
    // Silence between battle songs (Osama, 7 Nov 2026: 2 minutes). The first song starts at once.
    const float BattleGap = 120f;
    const float CalmGap = 10f;    // Osama 7 Nov: 10 s between calm (Round 1) songs
    static string playingDir;     // folder of the song now playing (Battle or Battle/Calm)
    static float resumeAt;
    // Osama 8 Nov: victory and defeat music play once, then silence until the menu.
    static bool playedOnce;
    // Voice lines: UserData/FAMusic/Voice/<GROUP>/<Line>/ replaces event:/BrokenArrowGame/BA_Command/<GROUP>/<Line>.
    static readonly string VoiceRoot = Path.Combine(Root, "Voice");
    const float VoiceBase = 0.234f;   // Osama 7 Nov: the old 41% level (0.4 x 0.41) now sits at 70%
    static IntPtr voiceSound, voiceChannel;

    public override void OnInitializeMelon()
    {
        Directory.CreateDirectory(Root);

        Directory.CreateDirectory(PacksDir);
        var packs = Packs();
        pack = File.Exists(PackFile) ? File.ReadAllText(PackFile).Trim() : (packs.Contains("USA") ? "USA" : packs.FirstOrDefault() ?? GameMusic);
        if (pack != GameMusic && !packs.Contains(pack)) pack = GameMusic;

        // The game's FMOD library is in BrokenArrow_Data/Plugins/x86_64, which is not on the search path yet.
        // Loading it by full path first lets the DllImport below find the module that is already loaded.
        System.Runtime.InteropServices.NativeLibrary.Load(Path.Combine(MelonEnvironment.GameRootDirectory, "BrokenArrow_Data", "Plugins", "x86_64", "fmodstudio.dll"));
        Check(Fmod.FMOD_System_Create(out system, Fmod.Version), "System_Create");
        Check(Fmod.FMOD_System_Init(system, 4, 0, IntPtr.Zero), "System_Init");

        // The game starts music through PlayByType or through PlayByEvent with a music type.
        var post = new HarmonyMethod(typeof(Player).GetMethod(nameof(PlayByTypeAfter)));
        foreach (var m in typeof(Il2Cpp.MusicService).GetMethods().Where(m =>
                     (m.Name == "PlayByType" || m.Name == "PlayByEvent") && m.GetParameters().Any(p => p.Name == "musicType")))
        {
            HarmonyInstance.Patch(m, postfix: post);
            LoggerInstance.Msg($"FA_MUSIC hooked {m.Name}({string.Join(", ", m.GetParameters().Select(p => p.Name))})");
        }
        // The menu music starts through PlayByEvent(eventName, changeType, fadeInOut), with no music type.
        var byEvent = new HarmonyMethod(typeof(Player).GetMethod(nameof(PlayByEventAfter)));
        foreach (var m in typeof(Il2Cpp.MusicService).GetMethods().Where(m => m.Name == "PlayByEvent" && m.GetParameters().Length == 3))
            HarmonyInstance.Patch(m, postfix: byEvent);

        // Unit voice lines: AudioCommandSystem.PlayCommand skips playback when this returns an empty string.
        var voiceType = AccessTools.TypeByName("Il2CppBrokenArrow.AudioSystem.AudioCommand.AudioCommandsCollection");
        var voiceMethod = voiceType?.GetMethod("GetEventByCommand");
        if (voiceMethod != null && Directory.Exists(VoiceRoot))
        {
            HarmonyInstance.Patch(voiceMethod, postfix: new HarmonyMethod(typeof(Player).GetMethod(nameof(VoiceAfter))));
            LoggerInstance.Msg($"FA_MUSIC voice lines on: {Directory.GetDirectories(VoiceRoot, "*", SearchOption.AllDirectories).Length} folders");
        }

        // Diagnostic: log every music call so a missed start path shows in Latest.log.
        var log = new HarmonyMethod(typeof(Player).GetMethod(nameof(LogCall)));
        foreach (var m in typeof(Il2Cpp.MusicService).GetMethods().Where(m => m.Name is "PlayByEvent" or "PlayTEMP" or "Stop" or "SetIntensity"))
            HarmonyInstance.Patch(m, postfix: log);
        LoggerInstance.Msg($"FA_MUSIC ready: pack {pack}, packs [{string.Join(", ", packs)}], volume {volume}");
    }

    public static void PlayByTypeAfter(Il2Cpp.MusicService __instance, MusicType musicType)
    {
        service = __instance;
        TrackBattle((int)musicType);
        lastType = (int)musicType;
        var next = FolderFor(lastType);
        Melon<Player>.Logger.Msg($"FA_MUSIC game music {musicType} -> {(next == null ? "game music" : next)}");
        if (KeepThroughLoading(next)) return;
        Switch(next);
    }

    // Maps the last part of the FMOD event path, for example ".../Music_Hangar", to a music type.
    public static void PlayByEventAfter(Il2Cpp.MusicService __instance, string eventName)
    {
        var name = (eventName ?? "").Split('/').Last().ToLowerInvariant();
        int type = name.Contains("hangar") || name.Contains("menu") || name.Contains("intro") ? 20
            : name.Contains("loading") ? 40
            : name.Contains("victory") || name.Contains("win") ? 62
            : name.Contains("defeat") || name.Contains("lose") ? 61
            : name.Contains("draw") ? 63
            : name.Contains("multi") || name.Contains("battle") ? 50
            : -1;
        if (type < 0) return;
        service = __instance;
        TrackBattle(type);
        lastType = type;
        var next = FolderFor(type);
        Melon<Player>.Logger.Msg($"FA_MUSIC game event {name} -> {(next == null ? "game music" : next)}");
        if (KeepThroughLoading(next)) return;
        Switch(next);
    }

    // Shared slots (for example US_VEHICLE/Move) serve many units. A subfolder named after the unit's
    // selection event (for example Move/HUMVEE_TRANSP_Selection) wins over the shared clips.
    // Osama 7 Nov: move and attack orders speak about half as often. The first order after a quiet spell always speaks;
    // after that every second order stays silent.
    const float OrderQuiet = 6f;
    static float lastOrderLine = -100f;
    static bool skipNextOrder;
    static bool IsOrder(int c) => c is 1 or 2 or 3 or 4 or 5 or 6 or 27;   // attack, fire at position, move, move+attack, reverse, fast move, sprint

    // Clips for one event: <slot>/Spawn/ for a unit called in, then <slot>/<preset>/, <slot>/<selection event>/, <slot>/.
    static List<string> Pick(string evt, int cmd, string preset, string unit)
    {
        var parts = (evt ?? "").Split('/');
        if (parts.Length < 2) return new List<string>();
        var dir = Path.Combine(VoiceRoot, parts[^2], parts[^1]);
        if (cmd == 8 && Files(Path.Combine(dir, "Spawn")).Count > 0) return Files(Path.Combine(dir, "Spawn"));
        var clips = preset != null ? Files(Path.Combine(dir, preset)) : new List<string>();
        if (clips.Count == 0 && unit.Length > 0) clips = Files(Path.Combine(dir, unit));
        return clips.Count > 0 ? clips : Files(dir);
    }

    public static void VoiceAfter(Il2CppBrokenArrow.AudioSystem.AudioCommand.AudioCommandsCollection __instance, Il2CppBrokenArrow.AudioSystem.AudioCommand.AudioCommandType command, ref string __result)
    {
        try
        {
            if (!VoicePolicy.UseCustom(pack)) return;
            int cmd = (int)command;
            if (string.IsNullOrEmpty(__result) || system == IntPtr.Zero) return;
            if (IsOrder(cmd))
            {
                var now = UnityEngine.Time.unscaledTime;
                if (now - lastOrderLine > OrderQuiet) skipNextOrder = false;
                if (skipNextOrder) { skipNextOrder = false; __result = ""; return; }
                skipNextOrder = true;
                lastOrderLine = now;
            }
            var unit = (__instance?.Selection ?? "").Split('/').Last();
            var preset = PresetOf(__instance);
            var slot = __result;
            var clips = Pick(slot, cmd, preset, unit);
            // Osama 7 Nov: radar, fire at position, laser and weapons-free orders use the unit's attack lines when they have none.
            if (clips.Count == 0 && (cmd is 2 or 20 or 22 or 24) && !string.IsNullOrEmpty(__instance?.Attack))
                clips = Pick(slot = __instance.Attack, 1, preset, unit);
            var parts = slot.Split('/');
            unit = preset ?? unit;
            // Osama 9 Nov: a US line with no C&C clip stays silent; never fall back to the vanilla voice.
            if (clips.Count == 0) { if (__result.Contains("/BA_Command/US_")) __result = ""; return; }
            var file = NextVoice(clips);
            if (voiceChannel != IntPtr.Zero) Fmod.FMOD_Channel_Stop(voiceChannel);
            if (voiceSound != IntPtr.Zero) Fmod.FMOD_Sound_Release(voiceSound);
            voiceChannel = voiceSound = IntPtr.Zero;
            if (Fmod.FMOD_System_CreateSound(system, Encoding.UTF8.GetBytes(file + "\0"), 0x80 | 0x8 | 0x1, IntPtr.Zero, out voiceSound) != 0
                || Fmod.FMOD_System_PlaySound(system, voiceSound, IntPtr.Zero, 0, out voiceChannel) != 0) return;
            Fmod.FMOD_Channel_SetVolume(voiceChannel, VoiceBase * VoiceSlider());
            Melon<Player>.Logger.Msg($"FA_MUSIC voice {parts[^2]}/{parts[^1]} command {cmd} unit {unit} slider {VoiceSlider():0.00} -> {Path.GetFileName(file)}");
            __result = "";
        }
        catch (Exception e) { Melon<Player>.Logger.Warning("FA_MUSIC voice failed: " + e.Message); }
    }

    // Osama 9 Nov: no repeated lines. Each folder plays all its clips in shuffled order before any repeats,
    // and the same line never plays twice in a row (clips are shared across folders).
    static readonly Dictionary<string, List<string>> voiceBags = new();
    static string lastVoice = "";
    static string NextVoice(List<string> clips)
    {
        var key = Path.GetDirectoryName(clips[0]) ?? "";
        if (!voiceBags.TryGetValue(key, out var bag) || bag.Count == 0)
            voiceBags[key] = bag = clips.OrderBy(_ => Rng.Next()).ToList();
        int i = bag.FindIndex(f => Path.GetFileName(f) != lastVoice);
        if (i < 0) i = 0;
        var file = bag[i]; bag.RemoveAt(i);
        lastVoice = Path.GetFileName(file);
        return file;
    }

    static float VoiceSlider()
    {
        try
        {
            var studio = Il2CppFMODUnity.RuntimeManager.StudioSystem.handle;
            if (Fmod.FMOD_Studio_System_GetParameterByName(studio, Encoding.UTF8.GetBytes("Volume_Voice_Commands\0"), out _, out float v) == 0) return ToLinear(v);
        }
        catch { }
        return 1f;
    }

    public static void LogCall(System.Reflection.MethodBase __originalMethod, object[] __args)
    {
        Melon<Player>.Logger.Msg($"FA_MUSIC call {__originalMethod.Name}({string.Join(", ", __args.Select(a => a?.ToString()))})");
    }

    // With no Loading folder in the pack, the song that is playing carries on through the loading screen.
    static bool KeepThroughLoading(string next)
    {
        if (lastType != 40 || next != null || folder == null) return false;
        Melon<Player>.Logger.Msg("FA_MUSIC loading screen: current song continues");
        return true;
    }

    // Unit sound presets (Units.AudioPreset, for example UNIT_SOUND_PRESET_A-GMV) each point at a command collection.
    // A collection used by exactly one preset names that preset; a shared collection gives null.
    static Dictionary<IntPtr, List<string>> presets = new();
    static float presetScan;
    static string PresetOf(Il2CppBrokenArrow.AudioSystem.AudioCommand.AudioCommandsCollection c)
    {
        if (c == null) return null;
        if (!presets.ContainsKey(c.Pointer) && UnityEngine.Time.unscaledTime > presetScan)
        {
            presetScan = UnityEngine.Time.unscaledTime + 5f;
            presets.Clear();
            var lines = new List<string>();
            foreach (var p in UnityEngine.Resources.FindObjectsOfTypeAll<Il2CppBrokenArrow.AudioSystem.Presets.UnitSoundsPreset>())
            {
                var a = p.AudioCommands;
                if (a == null) continue;
                if (!presets.TryGetValue(a.Pointer, out var l)) presets[a.Pointer] = l = new List<string>();
                l.Add(p.name);
                lines.Add($"{p.name} | {a.name} | {a.Selection}");
            }
            try { File.WriteAllLines(Path.Combine(Root, "voice-presets.txt"), lines.OrderBy(x => x)); } catch { }
            Melon<Player>.Logger.Msg($"FA_MUSIC voice presets: {lines.Count} presets, {presets.Count} command sets");
        }
        return presets.TryGetValue(c.Pointer, out var names) && names.Count == 1 ? names[0] : null;
    }

    static void Switch(string next)
    {
        if (next == folder) return;
        StopTrack();
        if (next == null)
        {
            try { service?.CurrentInstance?.SetVolume(1f); } catch { }
        }
        folder = next;
        menuSequence.Reset();
        resumeAt = 0f;
        playedOnce = false;
    }

    // Parameters in 0..1 are linear; values outside that range are decibels (the game uses 20*log10 of the slider).
    static float ToLinear(float p) => p >= 0f && p <= 1f ? p : (float)Math.Pow(10, Math.Min(p, 0f) / 20);

    // Follows the game's Music slider twice a second.
    static void ReadSlider()
    {
        if (UnityEngine.Time.unscaledTime < nextSliderRead) return;
        nextSliderRead = UnityEngine.Time.unscaledTime + 0.5f;
        float music;
        try
        {
            var studio = Il2CppFMODUnity.RuntimeManager.StudioSystem.handle;
            if (Fmod.FMOD_Studio_System_GetParameterByName(studio, Encoding.UTF8.GetBytes("Volume_Music\0"), out _, out music) != 0) return;
        }
        catch { return; }
        var v = ToLinear(music);
        if (Math.Abs(v - slider) < 0.005f) return;
        Melon<Player>.Logger.Msg($"FA_MUSIC game music slider {music:0.###} dB -> {v:0.00}");
        slider = v;
        if (channel != IntPtr.Zero) Fmod.FMOD_Channel_SetVolume(channel, volume * slider);
    }

    static List<string> Packs() => Directory.Exists(PacksDir)
        ? Directory.GetDirectories(PacksDir).Select(Path.GetFileName).OrderBy(n => n).ToList()
        : new List<string>();

    static bool InMenu => lastType is 2 or 20 or 30;

    // Cycles USA -> Russia -> ... -> Game music on the main menu.
    public override void OnGUI()
    {
        if (!InMenu) return;
        var w = 260f;
        var x = UnityEngine.Screen.width - w - 20;
        var r = new UnityEngine.Rect(x, 20, w, 34);
        if (!UnityEngine.GUI.Button(r, $"Music: {pack}  (click to change)")) return;
        var options = Packs();
        options.Add(GameMusic);
        pack = options[(options.IndexOf(pack) + 1) % options.Count];
        if (!VoicePolicy.UseCustom(pack))
        {
            if (voiceChannel != IntPtr.Zero) Fmod.FMOD_Channel_Stop(voiceChannel);
            if (voiceSound != IntPtr.Zero) Fmod.FMOD_Sound_Release(voiceSound);
            voiceChannel = voiceSound = IntPtr.Zero;
        }
        lastOrderLine = -100f;
        skipNextOrder = false;
        File.WriteAllText(PackFile, pack + "\n");
        Melon<Player>.Logger.Msg("FA_MUSIC pack selected: " + pack);
        Switch(FolderFor(lastType));
    }

    // A situation folder (Battle, Menu, ...) wins. If it is empty, files directly in UserData/FAMusic are used.
    static string FolderFor(int type)
    {
        if (pack == GameMusic) return null;
        var root = Path.Combine(PacksDir, pack);
        string name = type switch
        {
            2 or 20 or 30 => "Menu",
            40 => "Loading",
            50 or 100 => "Battle",   // 100 = MiniGames: the deployment phase (Music_Paint)
            60 or 62 or 63 => "Victory",
            61 => "Defeat",
            _ => null,
        };
        if (name == null) return null;
        var sub = Path.Combine(root, name);
        if (Files(sub).Count > 0 || (name == "Menu" && Files(Path.Combine(sub, "First")).Count > 0)) return sub;
        return Files(root).Count > 0 ? root : null;
    }

    static List<string> Files(string dir) => Directory.Exists(dir)
        ? Directory.GetFiles(dir).Where(f => Extensions.Contains(Path.GetExtension(f).ToLowerInvariant())).ToList()
        : new List<string>();

    public override void OnUpdate()
    {
        if (system == IntPtr.Zero) return;
        if (folder != null)
        {
            ReadSlider();
            MuteGameMusic();
            int playing = 0;
            if (channel != IntPtr.Zero) Fmod.FMOD_Channel_IsPlaying(channel, out playing);
            var end = Path.GetFileName(folder);
            if (playing == 0 && channel != IntPtr.Zero && end is "Victory" or "Defeat")
            {
                StopTrack();
                channel = IntPtr.Zero;
                playedOnce = true;
                Melon<Player>.Logger.Msg($"FA_MUSIC {end} music finished: silence until the menu");
            }
            if (playing == 0 && !playedOnce)
            {
                if (channel != IntPtr.Zero && (Path.GetFileName(folder) == "Battle" || (Path.GetFileName(folder) == "Menu" && pack == "Black Hawk Down" && MenuSequence.CompilationFiles(pack, folder).Count == 0)))
                {
                    StopTrack();
                    var gap = Path.GetFileName(folder) == "Menu" ? MenuSequence.MenuGapSeconds(pack) : Path.GetFileName(playingDir) == "Calm" ? CalmGap : BattleGap;
                    resumeAt = UnityEngine.Time.unscaledTime + gap;
                    Melon<Player>.Logger.Msg($"FA_MUSIC song pause {gap:0} s");
                }
                if (UnityEngine.Time.unscaledTime >= resumeAt) PlayNext();
            }
        }
        Fmod.FMOD_System_Update(system);
    }

    static void MuteGameMusic()
    {
        try
        {
            service?.CurrentInstance?.SetVolume(0f);
            service?.TempInstance?.SetVolume(0f);
        }
        catch (Exception e) { Melon<Player>.Logger.Warning("FA_MUSIC mute failed: " + e.Message); service = null; }
    }

    static void PlayNext()
    {
        StopTrack();
        // Battle/Calm plays in deployment and Round 1; combat songs (Battle/) from Round 2.
        var dir = folder;
        var calm = Path.Combine(folder, "Calm");
        if (Path.GetFileName(folder) == "Battle" && Files(calm).Count > 0
            && (battleStart < 0 || UnityEngine.Time.time - battleStart < OpeningSeconds())) dir = calm;
        if (!queues.TryGetValue(dir, out var queue) || queue.Count == 0)
            queues[dir] = queue = Files(dir).OrderBy(_ => Rng.Next()).ToList();
        string file;
        var isMenu = Path.GetFileName(dir) == "Menu";
        var compilations = isMenu ? MenuSequence.CompilationFiles(pack, dir) : new List<string>();
        var orderedMenu = isMenu && compilations.Count == 0 && MenuSequence.IsOrderedPack(pack);
        var intro = isMenu && compilations.Count == 0 ? Files(Path.Combine(dir, "First")) : new List<string>();
        if (orderedMenu && intro.Count == 0) intro = Files(dir);
        var regular = Files(dir);
        if (orderedMenu)
        {
            var battleTracks = Files(Path.Combine(Path.GetDirectoryName(dir), "Battle"));
            if (battleTracks.Count > 0) regular = battleTracks;
            regular = regular.Where(f => !intro.Any(i => Path.GetFileName(i).Equals(Path.GetFileName(f), StringComparison.OrdinalIgnoreCase))).ToList();
        }
        if (compilations.Count > 0)
        {
            // Each complete mix is an independent equal-probability choice. Its gaps are embedded.
            file = compilations[Rng.Next(compilations.Count)];
        }
        else if (intro.Count > 0)
        {
            // Explicit menu opener once on entering this pack/menu; then the regular shuffled queue.
            file = menuSequence.Next(intro, regular, Rng);
        }
        else
        {
            // Packs with no designated opener keep their previous random menu behavior.
            if (Path.GetFileName(dir) == "Menu") queue = queues[dir] = Files(dir).OrderBy(_ => Rng.Next()).ToList();
            if (queue.Count == 0) { folder = null; return; }
            file = queue[0];
            queue.RemoveAt(0);
        }
        var remaining = intro.Count > 0 ? menuSequence.Remaining : queue.Count;
        // FMOD_CREATESTREAM | FMOD_2D | FMOD_LOOP_OFF
        if (Fmod.FMOD_System_CreateSound(system, Encoding.UTF8.GetBytes(file + "\0"), 0x80 | 0x8 | 0x1, IntPtr.Zero, out sound) != 0
            || Fmod.FMOD_System_PlaySound(system, sound, IntPtr.Zero, 0, out channel) != 0)
        {
            Melon<Player>.Logger.Warning("FA_MUSIC cannot play " + file);
            StopTrack();
            channel = IntPtr.Zero;
            return;
        }
        Fmod.FMOD_Channel_SetVolume(channel, volume * slider);
        playingDir = dir;
        Melon<Player>.Logger.Msg($"FA_MUSIC playing {Path.GetFileName(file)} from {Path.GetFileName(dir)}" + (battleStart >= 0 ? $" at battle {UnityEngine.Time.time - battleStart:0} s" : ""));
        try { File.AppendAllText(Path.Combine(Root, "music-history.txt"), $"{DateTime.Now:yyyy-MM-dd HH:mm:ss}  {pack}/{Path.GetRelativePath(Path.Combine(PacksDir, pack), dir)}  {Path.GetFileName(file)}  ({remaining} left before a repeat)\n"); } catch { }
    }

    static void StopTrack()
    {
        if (channel != IntPtr.Zero) Fmod.FMOD_Channel_Stop(channel);
        if (sound != IntPtr.Zero) Fmod.FMOD_Sound_Release(sound);
        channel = sound = IntPtr.Zero;
    }

    public override void OnApplicationQuit()
    {
        StopTrack();
        if (system != IntPtr.Zero) Fmod.FMOD_System_Release(system);
        system = IntPtr.Zero;
    }

    static void Check(int result, string call)
    {
        if (result != 0) throw new InvalidOperationException($"FA_MUSIC FMOD {call} failed with code {result}");
    }
}

static class Fmod
{
    // FMOD.VERSION.number in the game's FMOD wrapper (dump.cs).
    public const uint Version = 131345;
    const string Dll = "fmodstudio";
    [DllImport(Dll)] public static extern int FMOD_System_Create(out IntPtr system, uint headerVersion);
    [DllImport(Dll)] public static extern int FMOD_System_Init(IntPtr system, int maxChannels, uint flags, IntPtr extra);
    [DllImport(Dll)] public static extern int FMOD_System_Update(IntPtr system);
    [DllImport(Dll)] public static extern int FMOD_System_Release(IntPtr system);
    [DllImport(Dll)] public static extern int FMOD_System_CreateSound(IntPtr system, byte[] name, uint mode, IntPtr exinfo, out IntPtr sound);
    [DllImport(Dll)] public static extern int FMOD_System_PlaySound(IntPtr system, IntPtr sound, IntPtr group, int paused, out IntPtr channel);
    [DllImport(Dll)] public static extern int FMOD_Channel_IsPlaying(IntPtr channel, out int playing);
    [DllImport(Dll)] public static extern int FMOD_Channel_SetVolume(IntPtr channel, float volume);
    [DllImport(Dll)] public static extern int FMOD_Channel_Stop(IntPtr channel);
    [DllImport(Dll)] public static extern int FMOD_Sound_Release(IntPtr sound);
    [DllImport(Dll)] public static extern int FMOD_Studio_System_GetParameterByName(IntPtr system, byte[] name, out float value, out float finalValue);
}
