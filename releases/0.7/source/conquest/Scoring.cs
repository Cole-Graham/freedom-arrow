using System.Text.Json;

namespace FreedomArrow.Conquest;

// 0.4 crit rules (Osama, 5 November 2026). Targets are tanks and IFVs.
// Rear hit by a direct anti-tank weapon: red mobility.
// Front or side hit by a tank-gun sabot or HEAT round (100mm and up) doing at least CritDamage: yellow mobility plus one random yellow.
// dev.12: the same for a front or side hit by an ATGM doing at least AtgmCritDamage. Top-attack missiles are excluded.
public static class CritRule
{
    public const int Yellow = 1, Red = 2;
    const int Front = 0, Sides = 1, Back = 2, DirectShot = 10, Vehicle = 4, Kinetic = 1, Heat = 2;
    public static bool Target(int role) => role is 10 or 11;
    public static bool RearAntiTank(int trajectory, long targetType, float penetration, float minimum) =>
        trajectory is DirectShot or (>= 100 and <= 120) && (targetType & Vehicle) != 0 && penetration >= minimum;
    // Tank-gun ammunition names start with "Round" and the caliber; sabot rows say AP and HEAT rows say HEAT.
    public static bool TankGun(int trajectory, int armorTargeted, string name)
    {
        if (trajectory != DirectShot || armorTargeted is not (Kinetic or Heat) || name == null) return false;
        var words = name.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        return words.Length > 2 && words[0] == "Round" && int.TryParse(words[1], out int caliber) && caliber >= 100 && (words.Contains("AP") || words.Contains("HEAT"));
    }
    // ATGM names start with "Missile AT" or "Missile GLAT" (gun-launched).
    public static bool Atgm(int trajectory, int armorTargeted, bool topAttack, string name) =>
        trajectory is >= 100 and <= 120 && armorTargeted == Heat && !topAttack && name != null && (name.StartsWith("Missile AT ") || name.StartsWith("Missile GLAT "));
    // 0 none, 1 rear red, 2 yellow mobility plus one random yellow.
    public static int Kind(int side, float damage, float minimumDamage, bool rearAntiTank, bool tankGun, bool atgm = false, float atgmMinimumDamage = 0) =>
        damage <= 0 ? 0 : side == Back ? (rearAntiTank ? 1 : 0) :
        side is Front or Sides && ((tankGun && damage >= minimumDamage) || (atgm && damage >= atgmMinimumDamage)) ? 2 : 0;
    // The game reports Front below 45 degrees. A wider front arc turns a side hit inside the arc into a front hit.
    public static bool WidenFront(int side, float horizontalAngle, float frontArc) => side == Sides && Math.Abs(horizontalAngle) < frontArc;
}
public sealed class Settings
{
    public bool Enabled { get; set; } = true;
    public float FixedIncomePerMinute { get; set; } = 0;
    public int TestDurationSeconds { get; set; } = 0;
    public int TickSeconds { get; set; } = 30;
    public int SetupSeconds { get; set; } = 0;
    public int OnlineDeploySeconds { get; set; } = 0;
    public int OpeningDelaySeconds { get; set; } = 180;
    public int DefaultZoneWeight { get; set; } = 1;
    public string Scoring { get; set; } = "advantage";
    public string Contested { get; set; } = "exclude";
    public string Ending { get; set; } = "time_limit";
    public int ScoreLimit { get; set; } = 0;
    public string PhasePolicy { get; set; } = "native";
    public bool EnableDeveloperFixtures { get; set; } = false;
    // Runtime-only layer: never serialize synthetic weights into packaged/saved defaults.
    internal string FixtureMap;
    internal readonly Dictionary<int,int> FixtureWeights = new();
    public double MaximumSampleLatenessSeconds { get; set; } = 2;
    public bool ShowOverlay { get; set; } = true;
    public bool StateLog { get; set; } = false;
    public bool Crits { get; set; } = false;
    public float CritDamage { get; set; } = 9.3f;
    public float AtgmCritDamage { get; set; } = 8.9f;
    public float RearCritMinPenetration { get; set; } = 250;
    public float FrontArcDegrees { get; set; } = 45;
    public bool PilotRescue { get; set; } = true;
    public Dictionary<string, Dictionary<string, int>> MapZoneWeights { get; set; } = new();
    public static readonly JsonSerializerOptions Json = new() { WriteIndented = true, PropertyNameCaseInsensitive = true };

    public void Validate()
    {
        if (FixedIncomePerMinute != 0) EconomyWindow.PerSecond(FixedIncomePerMinute);
        if(TestDurationSeconds!=0 && (TestDurationSeconds<240||TestDurationSeconds>3600))throw new ArgumentException("TestDurationSeconds must be zero or 240..3600");
        if (TickSeconds < 1 || TickSeconds > 3600) throw new ArgumentException("TickSeconds must be 1..3600");
        if (SetupSeconds < 0 || SetupSeconds > 3600) throw new ArgumentException("SetupSeconds must be 0..3600");
        if (!(CritDamage > 0 && CritDamage <= 100)) throw new ArgumentException("CritDamage must be above 0 and at most 100");
        if (!(AtgmCritDamage > 0 && AtgmCritDamage <= 100)) throw new ArgumentException("AtgmCritDamage must be above 0 and at most 100");
        if (!(RearCritMinPenetration > 0)) throw new ArgumentException("RearCritMinPenetration must be above 0");
        if (!(FrontArcDegrees >= 45 && FrontArcDegrees <= 90)) throw new ArgumentException("FrontArcDegrees must be 45..90");
        if (OpeningDelaySeconds < 0 || OpeningDelaySeconds > 86400) throw new ArgumentException("OpeningDelaySeconds must be 0..86400");
        if (DefaultZoneWeight < 0 || DefaultZoneWeight > 100) throw new ArgumentException("DefaultZoneWeight must be 0..100");
        if (Scoring is not ("per_team" or "advantage")) throw new ArgumentException("Scoring must be per_team or advantage");
        if (Contested is not ("exclude" or "owner")) throw new ArgumentException("Contested must be exclude or owner");
        if (Ending is not ("time_limit" or "score_or_time")) throw new ArgumentException("Ending must be time_limit or score_or_time");
        if (Ending == "score_or_time" && (ScoreLimit < 1 || ScoreLimit > 1000000)) throw new ArgumentException("ScoreLimit must be 1..1000000 for score_or_time");
        if (Ending == "time_limit" && ScoreLimit != 0) throw new ArgumentException("ScoreLimit must be zero for time_limit");
        if (PhasePolicy is not ("native" or "continuous")) throw new ArgumentException("PhasePolicy must be native or continuous");
        if (!double.IsFinite(MaximumSampleLatenessSeconds) || MaximumSampleLatenessSeconds < 0 || MaximumSampleLatenessSeconds > 5)
            throw new ArgumentException("MaximumSampleLatenessSeconds must be finite, 0..5");
        if (MapZoneWeights == null) throw new ArgumentException("MapZoneWeights cannot be null");
        foreach (var map in MapZoneWeights)
        {
            if (string.IsNullOrWhiteSpace(map.Key) || map.Value == null) throw new ArgumentException("Invalid map weights");
            foreach (var zone in map.Value)
                if (!int.TryParse(zone.Key, out _) || zone.Value < 0 || zone.Value > 100)
                    throw new ArgumentException("Zone keys must be integer UIDs; weights must be 0..100");
        }
    }
    // A joining client may have no local scenario name. The exact zone IDs then identify a configured map.
    public string ResolveMap(string name, IEnumerable<int> uids)
    {
        if (name != OnlineUnknownMap) return name;
        var ids = uids.Select(i => i.ToString(System.Globalization.CultureInfo.InvariantCulture)).ToHashSet();
        var maps = MapZoneWeights.Where(m => m.Value.Keys.ToHashSet().SetEquals(ids)).Select(m => m.Key).ToList();
        if (maps.Count == 1) return maps[0];
        // Network and Skirmish flavors of the same authored map share zone IDs. Online joiners get the network name.
        var network = maps.Where(m => m.IndexOf("Skirmish", StringComparison.Ordinal) < 0).ToList();
        return network.Count == 1 ? network[0] : name;
    }
    public const string OnlineUnknownMap = "online scenario";
    const int RoundAnnouncementSeconds = 8;
    static string Clock(double seconds)
    {
        int left = (int)Math.Ceiling(seconds);
        return $"{left / 60}:{left % 60:00}";
    }
    // Online, the native clock reads one deployment short when the mode starts, then holds until it is correct.
    // Show the true time for that hold. Scoring keeps the native clock.
    public static double ShownElapsed(double elapsed, double startOffset, double secondsSinceStart) =>
        secondsSinceStart < startOffset ? secondsSinceStart : elapsed;
    // The setup phase pauses the game, so it uses wall-clock seconds and not the match clock.
    public static string SetupBanner(double remaining) => $"DEPLOYMENT  {Clock(remaining)}";
    // Round 1 has no scoring. Zones can still be captured.
    public string RoundAnnouncement(double elapsed)
    {
        if (OpeningDelaySeconds > 0 && elapsed < RoundAnnouncementSeconds) return "ROUND 1: NO SCORING";
        return OpeningDelaySeconds > 0 && elapsed >= OpeningDelaySeconds && elapsed < OpeningDelaySeconds + RoundAnnouncementSeconds ? "ROUND 2: ZONES SCORE" : null;
    }
    // The native phase bar: Round 1 fills over the opening, Round 2 over the rest of the match.
    public (string Text, float Progress) RoundBar(double elapsed, double duration)
    {
        if (elapsed < OpeningDelaySeconds) return ("ROUND 1: NO SCORING", (float)(elapsed / OpeningDelaySeconds));
        double scoring = Math.Max(1, duration - OpeningDelaySeconds);
        return ("ROUND 2: SCORING", (float)Math.Clamp((elapsed - OpeningDelaySeconds) / scoring, 0, 1));
    }
    public static string NextTickLabel(int points) => points > 0 ? "+" + points.ToString(System.Globalization.CultureInfo.InvariantCulture) : "";
    public string ZoneLabel(string map, int uid) => "+" + Weight(map, uid).ToString(System.Globalization.CultureInfo.InvariantCulture);
    public int Weight(string map, int uid) => FixtureMap == map && FixtureWeights.TryGetValue(uid,out int fixture) ? fixture : MapZoneWeights.TryGetValue(map, out var zones)
        && zones.TryGetValue(uid.ToString(System.Globalization.CultureInfo.InvariantCulture), out int value) ? value : DefaultZoneWeight;
}

// No game dependencies: this is the exact scoring code compiled into the mod and host tests.
public sealed class Zone
{
    public int Uid { get; }
    public int Owner { get; }
    public bool Contested { get; }
    public Zone(int uid, int owner, bool contested) { Uid = uid; Owner = owner; Contested = contested; }
}
public sealed class Award
{
    public double Scheduled { get; }
    public double Sampled { get; }
    public int Alpha { get; }
    public int Bravo { get; }
    public int TotalAlpha { get; }
    public int TotalBravo { get; }
    public Award(double scheduled, double sampled, int alpha, int bravo, int totalAlpha, int totalBravo)
    { Scheduled = scheduled; Sampled = sampled; Alpha = alpha; Bravo = bravo; TotalAlpha = totalAlpha; TotalBravo = totalBravo; }
}

public sealed class TickForecast
{
    public int AlphaHeld { get; }
    public int BravoHeld { get; }
    public int Alpha { get; }
    public int Bravo { get; }
    public TickForecast(int heldA,int heldB,int alpha,int bravo)
    {AlphaHeld=heldA;BravoHeld=heldB;Alpha=alpha;Bravo=bravo;}
}

public sealed class Ledger
{
    public Settings Config { get; }
    public string Map { get; }
    public double Duration { get; }
    public double Elapsed { get; private set; }
    public double NextTick { get; private set; }
    public int MissedTicks { get; private set; }
    public int Alpha { get; private set; }
    public int Bravo { get; private set; }
    public bool Finished { get; private set; }
    public bool ReachedScoreLimit => Config.Ending == "score_or_time" && Math.Max(Alpha, Bravo) >= Config.ScoreLimit && Alpha != Bravo;
    public int? ScoreLimitWinner => ReachedScoreLimit ? (Alpha > Bravo ? 0 : 1) : null;
    bool observed;
    public Ledger(Settings config, string map, double duration)
    {
        config.Validate();
        if (string.IsNullOrWhiteSpace(map)) throw new ArgumentException("Missing native map name");
        if (!double.IsFinite(duration) || duration <= 0 || duration > 86400) throw new ArgumentException("Invalid native match duration");
        Config = config; Map = map; Duration = duration;
        NextTick = config.OpeningDelaySeconds == 0 ? config.TickSeconds : config.OpeningDelaySeconds;
    }
    public TickForecast Forecast(IReadOnlyList<Zone> zones)
    {
        int a=0,b=0;
        foreach(var z in zones)
        {
            if(z.Contested&&Config.Contested=="exclude")continue;
            if(z.Owner==0)a=checked(a+Config.Weight(Map,z.Uid));
            if(z.Owner==1)b=checked(b+Config.Weight(Map,z.Uid));
        }
        int difference=a-b;
        return Config.Scoring=="advantage"?new(a,b,Math.Max(0,difference),Math.Max(0,-difference)):new(a,b,a,b);
    }
    public List<Award> Advance(double elapsed, IReadOnlyList<Zone> zones)
    {
        if (!double.IsFinite(elapsed) || elapsed < -0.01 || elapsed > Duration + 5) throw new ArgumentException("Invalid combat elapsed time");
        elapsed = Math.Clamp(elapsed, 0, Duration);
        if (observed && elapsed + 0.01 < Elapsed) throw new InvalidOperationException("Clock moved backwards; a new match must start a new ledger");
        // Online, the native clock can already be running when the scenario starts the mode.
        // Ticks keep the same absolute schedule, so every machine scores the same boundaries.
        if (!observed) while (NextTick + 0.00001 < elapsed) NextTick += Config.TickSeconds;
        if (zones.Select(z => z.Uid).Distinct().Count() != zones.Count) throw new ArgumentException("Duplicate zone UID");
        if (zones.Any(z => z.Owner is not (0 or 1 or 101))) throw new ArgumentException("Unknown zone owner");
        var awards = new List<Award>();
        if (Finished) return awards;
        elapsed = Math.Max(elapsed, Elapsed);
        if (elapsed + 0.00001 >= NextTick && NextTick <= Duration)
        {
            // Never fabricate historical ownership after a large clock jump or debugger pause.
            if (elapsed - NextTick > Config.MaximumSampleLatenessSeconds || elapsed + 0.00001 >= NextTick + Config.TickSeconds)
            {
                while (NextTick + 0.00001 <= elapsed) { NextTick += Config.TickSeconds; MissedTicks++; }
                Elapsed = elapsed; observed = true; Finished = elapsed >= Duration || ReachedScoreLimit;
                return awards;
            }
            // Sample current eligible ownership at this scheduled tick boundary.
            // Zone weight contributes every tick held; capture/weight edits award nothing immediately.
            var forecast=Forecast(zones);int a=forecast.Alpha,b=forecast.Bravo;
            int newA = checked(Alpha + a), newB = checked(Bravo + b);
            awards.Add(new(NextTick, elapsed, a, b, newA, newB));
            Alpha = newA; Bravo = newB; NextTick += Config.TickSeconds;
        }
        Elapsed = elapsed; observed = true; Finished = elapsed >= Duration || ReachedScoreLimit;
        return awards;
    }
}
