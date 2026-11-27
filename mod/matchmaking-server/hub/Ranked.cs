// Freedom Arrow ranked (Lateralus 22 Nov 2026; docs/ranked/RANKED-PROPOSAL.md, docs/simple-elo.md).
// Two queues through the normal FindMatch call (Lateralus 22 Nov: "1v1 should be a completely different queue"):
//   r1v1  = solo players only, 1v1 matches, ladder "1v1";
//   rteam = solos and parties of up to 4, 2v2, 3v3 or 4v4 matches (never 1v1), ladder "team" (0.9.6, Lateralus 23 Nov 2026; was 3v3/5v5).
// The match format (1v1 / 2v2 / 3v3 / 4v4) is chosen when the match forms. The map pools come from the map list maps.json (see LoadMaps).
// The queue matches whole parties, creates a closed lobby with fixed teams and sends MatchFound, so the ArrowQueue client
// runs its normal host/join flow. Results come from the clients' end-of-match stats posts (who = sha256("arrow-stats|"+steamId)).
// A match is rated only when both sides report the same winner, or when every player of the silent side is a deserter.
// Everything is called under Store.Lock; messages are queued in Out and sent by Flush() after the lock.
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.AspNetCore.SignalR;

sealed class RankedRating
{
    public string SteamId { get; set; } = "";
    public string Name { get; set; } = "";
    public double Rating { get; set; } = Ranked.Start;
    public int Wins { get; set; }
    public int Losses { get; set; }
    public int Draws { get; set; }
    public double Best { get; set; } = Ranked.Start;
    public DateTime Last { get; set; }
    public List<RankedRecent> Recent { get; set; } = new();   // newest first, at most 10 (ranked menu "recent matches")
}

sealed class RankedRecent
{
    public DateTime T { get; set; }
    public string Format { get; set; } = "";
    public string Map { get; set; } = "";
    public string Vs { get; set; } = "";
    public bool Win { get; set; }
    public bool Draw { get; set; }
    public double Change { get; set; }
    public double VsRating { get; set; }
}

sealed class RankedEntry   // one queued unit: a solo player or a whole party
{
    public string Mode = "", Ladder = "", Build = "", Leader = "";
    public List<string> Members = new();
    public double Rating;
    public DateTime Since = DateTime.UtcNow;
    public double WaitSec => (DateTime.UtcNow - Since).TotalSeconds;
}

sealed class RankedMatch
{
    public string Id = "", Mode = "", Format = "", Ladder = "", LobbyId = "", Map = "";
    public List<string>[] Teams = { new(), new() };
    public DateTime Created = DateTime.UtcNow;
    public DateTime? Started, FirstVote;
    public string State = "lobby";
    // Lobby phases (Lateralus 22 Nov): join (everyone enters the game lobby, 90 s) -> deck (60 s, enemy decks hidden) -> reveal (5 s) -> launch.
    public string Phase = "join";
    public DateTime PhaseUntil = DateTime.UtcNow.AddSeconds(Ranked.JoinSec);   // lobby | battle | rated | disputed | cancelled | unrated
    public readonly Dictionary<string, (string side, string winner, string key, JsonNode report)> Votes = new();
}

static class Ranked
{
    // simple-elo.md
    public const double Start = 1000, K = 40, Div = 400, Floor = 600, BonusTarget = 1700, DeadZone = 200;
    // 20 ranks: 1-18 by Elo band, 19 = places 2-3 and 20 = place 1 among players at 2170+ (RANKED-PROPOSAL.md, section 1)
    static readonly int[] BandStart = { 0, 1001, 1028, 1059, 1093, 1132, 1175, 1223, 1277, 1337, 1405, 1481, 1566, 1661, 1767, 1887, 2020, 2170 };
    // Largest first: Tick tries them in this order, so 8 searching players make one 4v4, not a 3v3 plus 2 waiting.
    // These pools are the fallback for a hub without maps.json; LoadMaps replaces them from the list.
    public static readonly Dictionary<string, (int size, string ladder, string[] pool)> Formats = new()
    {
        ["4v4"] = (4, "team", new[] { "Airport", "Oil Rush", "Cold Harbor" }),
        ["3v3"] = (3, "team", new[] { "Baltiisk", "Bay of Winds", "Dam" }),
        ["2v2"] = (2, "team", new[] { "Dead Center", "Chkalovsk Airbase", "Highway of Death" }),
        ["1v1"] = (1, "1v1", new[] { "Dead Center", "Kadaga", "Jelgava", "Klaipeda", "Chernyakhovsky" }),
    };
    // Lateralus 23 Nov 2026: map size from data, not the [NvN] tag ("its super important the game can clearly keep track of which version
    // belongs to which game size"). maps.json is the file the build ships as UserData/FreedomArrow/maps.json (copy it to the ranked dir or
    // set FAQUEUE_MAPS when the hub is deployed). Exact scenario name -> (size, base) for every multiplayer map, ranked or not.
    // Lateralus 27 Nov 2026 ("How can we address these gaps?"): the hub re-reads maps.json within a minute when the file changes, so a new
    // ranked pool needs no restart. A file that does not parse keeps the last good list.
    static Dictionary<string, (string size, string bas)> MapList = new(StringComparer.Ordinal);
    static string _mapsPath = ""; static DateTime _mapsStamp; static int _mapsTick;
    // Team formats smaller than the largest wait this long for more players (Lateralus 23 Nov 2026: "the 20 s gather time is ok").
    public const double GatherSec = 20;
    const int MaxTeam = 4;
    public static readonly string[] Queues = { "r1v1", "rteam" };
    // Test hub only (FAQUEUE_RANKED_ALL=1): the unchanged client's 1v1 search joins r1v1, and 2v2-5v5 searches join rteam.
    public static bool AllRanked;
    public const double JoinSec = 90, DeckSec = 60, RevealSec = 5;
    const double PartySpread = 500, OneSidedWaitMin = 30;

    public static int Season = 1;
    // Season name shown in game (Lateralus 22 Nov 2026: "set the season to Season Alpha instead of Season Test"); config.json "name"
    public static string SeasonName = "Alpha";
    // last ranked deck each player reported (SetRankedDeck); a new hub session after a reconnect starts from it (Lateralus 22 Nov: 'deck invalid' after ArrowQueue's reconnect)
    public static readonly Dictionary<string, (bool ok, string name)> Decks = new();
    static string _dir = "";
    static IHubContext<GameHub>? _ctx;
    static ILogger? _log;
    static Timer? _timer;
    static readonly Dictionary<string, Dictionary<string, RankedRating>> Ladders = new() { ["1v1"] = new(), ["team"] = new() };
    public static readonly List<RankedEntry> Queue = new();
    public static readonly Dictionary<string, RankedMatch> Matches = new();
    static readonly List<(string conn, string method, object arg)> Out = new();
    static bool _dirty;
    static DateTime _lastExport = DateTime.MinValue;

    public static bool IsRanked(string? mode) => mode is "r1v1" or "rteam";
    public static string? QueueFor(string mode) => IsRanked(mode) ? mode : !AllRanked ? null : mode == "1v1" ? "r1v1" : mode is "2v2" or "3v3" or "4v4" or "5v5" ? "rteam" : null;
    static string LadderOf(string queue) => queue == "r1v1" ? "1v1" : "team";
    // Formats an entry can play: 1v1 queue -> 1v1; team queue -> 2v2, 3v3 or 4v4 with room for the whole party (a party of 4 plays 4v4 only).
    static bool Fits(RankedEntry e, int size) => e.Mode == "r1v1" ? size == 1 : size > 1 && e.Members.Count <= size;
    public static void LoadMaps(string path)
    {
        try
        {
            if (!File.Exists(path)) { _log?.LogWarning("ranked maps: {p} not found; built-in pools, map size from the name tag", path); return; }
            var stamp = File.GetLastWriteTimeUtc(path);
            var rows = JsonNode.Parse(File.ReadAllText(path))!["maps"]!.AsArray();
            var pools = new Dictionary<string, List<string>>();
            var list = new Dictionary<string, (string size, string bas)>(StringComparer.Ordinal);
            foreach (var r in rows)
            {
                if (r!["skirmish"]!.GetValue<bool>()) continue;
                string name = r["name"]!.GetValue<string>(), size = r["size"]!.GetValue<string>(), bas = r["base"]!.GetValue<string>();
                list[name] = (size, bas);
                if (r["ranked"]!.GetValue<bool>()) (pools.TryGetValue(size, out var l) ? l : pools[size] = new()).Add(bas);
            }
            MapList = list; _mapsStamp = stamp;
            foreach (var f in Formats.Keys.ToArray())
                if (pools.TryGetValue(f, out var p) && p.Count > 0) Formats[f] = (Formats[f].size, Formats[f].ladder, p.ToArray());
                else _log?.LogWarning("ranked maps: no {f} map in {p}; built-in pool kept", f, path);
            _log?.LogInformation("ranked maps: {n} maps from {p}; pools {pools}", MapList.Count, path, string.Join("; ", Formats.Select(f => f.Key + ": " + string.Join(", ", f.Value.pool))));
        }
        catch (Exception e) { _log?.LogError("ranked maps: {p} unreadable ({e}); {n} maps from the last good list kept", path, e.Message, MapList.Count); }
    }
    // The exact multiplayer scenario of a format and base map from maps.json, or null (the client then matches by name).
    static string? ScenarioFor(string format, string bas) => MapList.FirstOrDefault(x => x.Value.size == format && x.Value.bas.Equals(bas, StringComparison.OrdinalIgnoreCase)).Key;

    public static void Init(IHubContext<GameHub> ctx, ILogger log, string dir)
    {
        _ctx = ctx; _log = log; _dir = dir; Directory.CreateDirectory(dir);
        var cfg = Path.Combine(dir, "config.json");
        if (File.Exists(cfg)) { var c = JsonNode.Parse(File.ReadAllText(cfg)); Season = c?["season"]?.GetValue<int>() ?? 1; SeasonName = c?["name"]?.GetValue<string>() ?? SeasonName; }
        else File.WriteAllText(cfg, JsonSerializer.Serialize(new { season = Season, name = SeasonName, length = "2 months (Lateralus 22 Nov 2026)" }));
        foreach (var lad in Ladders.Keys.ToArray())
        {
            var f = RatingsFile(lad);
            if (File.Exists(f)) foreach (var r in JsonSerializer.Deserialize<List<RankedRating>>(File.ReadAllText(f)) ?? new()) Ladders[lad][r.SteamId] = r;
        }
        _log.LogInformation("ranked season {s} ({n}): {a} 1v1 and {b} team ratings loaded from {d}", Season, SeasonName, Ladders["1v1"].Count, Ladders["team"].Count, dir);
        _mapsPath = Environment.GetEnvironmentVariable("FAQUEUE_MAPS") is { Length: > 0 } mp ? mp : Path.Combine(dir, "maps.json");
        LoadMaps(_mapsPath);
        _timer = new Timer(_ => Tick(), null, 1000, 1000);
    }
    static string RatingsFile(string ladder) => Path.Combine(_dir, $"season-{Season}-{ladder}.json");

    // ---------- ratings ----------
    public static RankedRating Get(string ladder, string steamId, string name = "")
    {
        var l = Ladders[ladder];
        if (!l.TryGetValue(steamId, out var r)) { r = new RankedRating { SteamId = steamId, Name = name }; l[steamId] = r; }
        if (name != "") r.Name = name;
        return r;
    }
    // Ladder-average gate (Lateralus 22 Nov): the bonus is meant to lift the field to an average of 1500. Per winner alone it never
    // stops (half the field is always under 1500, simulated mean 1779 after 400 matches each), so it is scaled by how far the ladder
    // average is under 1500: full while the average is at or below 1400, falling to 0 at 1500.
    public const double GateFull = 1400, GateEnd = 1500;
    public static double Bonus(double winnerRating, double ladderMean)
    {
        var d = BonusTarget - winnerRating;
        var b = d <= DeadZone ? 0 : 1 - Math.Exp(-d / (DeadZone / 2));
        return b * Gate(ladderMean);
    }
    public static double Gate(double ladderMean) => Math.Clamp((GateEnd - ladderMean) / (GateEnd - GateFull), 0, 1);
    // average rating of every player with at least one rated match this season (1000 = start while the ladder is empty)
    public static double LadderMean(string ladder)
    {
        var rated = Ladders[ladder].Values.Where(r => r.Wins + r.Losses > 0).ToList();
        return rated.Count == 0 ? Start : rated.Average(r => r.Rating);
    }
    public static double Expected(double a, double b) => 1 / (1 + Math.Pow(10, (b - a) / Div));
    public static int Level(string ladder, double rating, int place)
    {
        if (rating >= 2170 && place == 1) return 20;
        if (rating >= 2170 && place is 2 or 3) return 19;
        var f = Math.Floor(rating); int lv = 1;
        for (int i = 0; i < BandStart.Length; i++) if (f >= BandStart[i]) lv = i + 1;
        return lv;
    }
    static List<RankedRating> Sorted(string ladder) => Ladders[ladder].Values.Where(r => r.Wins + r.Losses > 0).OrderByDescending(r => r.Rating).ThenBy(r => r.SteamId).ToList();
    static int Place(string ladder, string steamId) { var s = Sorted(ladder); var i = s.FindIndex(r => r.SteamId == steamId); return i < 0 ? 0 : i + 1; }

    // ---------- queue ----------
    // Called from FindMatch for r1v1/rteam. Returns an error code or null.
    public static string? Enqueue(Player p, string mode)
    {
        var ladder = LadderOf(mode);
        Party? pt = p.PartyId != null && Store.Parties.TryGetValue(p.PartyId, out var x) ? x : null;
        if (pt != null && pt.Leader != p.SteamId) return "not_leader";
        var ids = pt?.Members.ToList() ?? new List<string> { p.SteamId };
        // 1v1 is solo only; a team party is at most 4 (the largest team format, 4v4).
        if (ids.Count > (mode == "r1v1" ? 1 : MaxTeam)) return "party_too_big";
        foreach (var id in ids)
        {
            if (!Store.BySteam.TryGetValue(id, out var q)) return "member_offline";
            if (q.LobbyId != null) return "leave_lobby_first";
            if (q.Build != p.Build) return "member_build_differs";
        }
        var ratings = ids.Select(id => Get(ladder, id, Store.BySteam[id].Name).Rating).ToList();
        if (ratings.Max() - ratings.Min() > PartySpread) return "party_spread_over_500";
        // every member needs a valid ranked default deck (Lateralus 22 Nov); the FA client reports it with SetRankedDeck
        foreach (var id in ids) if (!Store.BySteam[id].RankedDeckOk) return "deck_invalid:" + Store.BySteam[id].Name;
        // leave cooldown (Lateralus 22 Nov): any member still cooling down blocks the search
        foreach (var id in ids) { var left = CooldownLeft(id); if (left > 0) return "cooldown:" + Store.BySteam[id].Name + ":" + (int)Math.Ceiling(left); }
        Dequeue(p.SteamId);
        Queue.Add(new RankedEntry { Mode = mode, Ladder = ladder, Build = p.Build, Leader = p.SteamId, Members = ids, Rating = ratings.Average() });
        foreach (var id in ids) { var q = Store.BySteam[id]; q.SearchMode = mode; Status(q, "searching"); }
        _log?.LogInformation("ranked queue {mode}: {name} ({n} players, {r:0})", mode, p.Name, ids.Count, ratings.Average());
        return null;
    }
    public static bool Dequeue(string steamId)
    {
        var e = Queue.FirstOrDefault(x => x.Members.Contains(steamId));
        if (e == null) return false;
        Queue.Remove(e);
        foreach (var id in e.Members) if (Store.BySteam.TryGetValue(id, out var q) && q.LobbyId == null) { q.SearchMode = null; Status(q, "menu"); }
        return true;
    }
    static double Window(RankedEntry e, int size)
    {
        var t = e.WaitSec;
        if (t >= 180) return double.MaxValue;                     // any rating after 3 minutes
        var b = size == 4 ? 150 : 100;
        return b * (1 + t / 60);
    }

    static void Tick()
    {
        try
        {
            lock (Store.Lock)
            {
                if (++_mapsTick % 60 == 0 && File.Exists(_mapsPath) && File.GetLastWriteTimeUtc(_mapsPath) != _mapsStamp) LoadMaps(_mapsPath);
                foreach (var f in Formats.Keys) while (TryMatch(f)) { }   // 4v4 first, so a full 8 is not split into 3v3 + 2 waiting
                ResolveTimeouts();
                Phases();
                if (_dirty || _metDirty) Save();
                if ((DateTime.UtcNow - _lastExport).TotalSeconds >= 60) Export();
            }
            Flush();
        }
        catch (Exception e) { _log?.LogError("ranked tick: {e}", e); }
    }

    static bool TryMatch(string format)
    {
        var (size, ladder, pool) = Formats[format];
        foreach (var anchor in Queue.Where(e => Fits(e, size)).OrderBy(e => e.Since).ToList())
        {
            if (size > 1 && size < MaxTeam && anchor.WaitSec < GatherSec) continue;   // give a bigger team game the first 20 s
            var w = Window(anchor, size);
            var cand = Queue.Where(e => Fits(e, size) && e.Build == anchor.Build && e != anchor && Math.Abs(e.Rating - anchor.Rating) <= Math.Max(w, Window(e, size)))
                .OrderBy(e => e.Since).Take(11).Prepend(anchor).ToList();
            if (cand.Sum(e => e.Members.Count) < 2 * size) continue;
            var best = BestSplit(cand, size, anchor.WaitSec >= 180);
            if (best == null) continue;
            Create(anchor.Mode, format, ladder, pool, best.Value.a, best.Value.b);
            return true;
        }
        return false;
    }

    // Whole parties on each side, both sides exactly `size`, anchor (cand[0]) on side A. Cost: rating gap between the side averages,
    // plus a party-shape penalty before 3 minutes (prefer a 5-stack against a 5-stack or a 4+1, Lateralus 22 Nov), minus a wait bonus.
    static (List<RankedEntry> a, List<RankedEntry> b)? BestSplit(List<RankedEntry> cand, int size, bool anyShape)
    {
        int n = cand.Count; double bestCost = double.MaxValue; (int a, int b) bestMask = (0, 0);
        for (int ma = 1; ma < (1 << n); ma += 2)   // bit 0 = anchor always on side A
        {
            if (Players(cand, ma) != size) continue;
            int rest = ((1 << n) - 1) & ~ma;
            for (int mb = rest; mb > 0; mb = (mb - 1) & rest)
            {
                if (Players(cand, mb) != size) continue;
                double ra = Avg(cand, ma), rb = Avg(cand, mb);
                double shape = anyShape ? 0 : 100 * Math.Abs(MaxParty(cand, ma) - MaxParty(cand, mb));
                double wait = 0; for (int i = 0; i < n; i++) if (((ma | mb) >> i & 1) == 1) wait += cand[i].WaitSec;
                double cost = Math.Abs(ra - rb) + shape - wait / 10;
                if (cost < bestCost) { bestCost = cost; bestMask = (ma, mb); }
            }
        }
        if (bestCost == double.MaxValue) return null;
        List<RankedEntry> Pick(int m) => Enumerable.Range(0, n).Where(i => (m >> i & 1) == 1).Select(i => cand[i]).ToList();
        return (Pick(bestMask.a), Pick(bestMask.b));
    }
    static int Players(List<RankedEntry> c, int m) { int s = 0; for (int i = 0; i < c.Count; i++) if ((m >> i & 1) == 1) s += c[i].Members.Count; return s; }
    static int MaxParty(List<RankedEntry> c, int m) { int s = 0; for (int i = 0; i < c.Count; i++) if ((m >> i & 1) == 1) s = Math.Max(s, c[i].Members.Count); return s; }
    static double Avg(List<RankedEntry> c, int m)
    {
        double s = 0; int k = 0;
        for (int i = 0; i < c.Count; i++) if ((m >> i & 1) == 1) { s += c[i].Rating * c[i].Members.Count; k += c[i].Members.Count; }
        return s / k;
    }

    static void Create(string mode, string format, string ladder, string[] pool, List<RankedEntry> a, List<RankedEntry> b)
    {
        foreach (var e in a.Concat(b)) Queue.Remove(e);
        var host = Store.BySteam[a[0].Leader];
        var map = pool[Random.Shared.Next(pool.Length)];
        var l = new Lobby { Id = Guid.NewGuid().ToString("N")[..16], Mode = mode, Size = 2 * Formats[format].size, Build = host.Build, HostId = host.SteamId, HostName = host.Name, Open = false };
        var m = new RankedMatch { Id = l.Id, Mode = mode, Format = format, Ladder = ladder, LobbyId = l.Id, Map = map };
        Store.Lobbies[l.Id] = l; Matches[m.Id] = m;
        int team = 0;
        foreach (var side in new[] { a, b })
        {
            foreach (var id in side.SelectMany(e => e.Members))
            {
                var q = Store.BySteam[id];
                l.Members.Add(new LobbyMember { SteamId = id, Name = q.Name, Team = team, Host = id == host.SteamId });
                m.Teams[team].Add(id);
                q.LobbyId = l.Id; q.SearchMode = null; Status(q, "lobby");
            }
            team++;
        }
        l.State = "full";
        foreach (var id in m.Teams.SelectMany(t => t))
            Send(Store.BySteam[id], "MatchFound", new { lobbyId = l.Id, mode, format, ranked = true, scenario = map, scenarioName = ScenarioFor(format, map), team = m.Teams[0].Contains(id) ? 0 : 1, host = host.SteamId });
        Append("match", new { id = m.Id, mode, format, ladder, map, teams = m.Teams, ratingA = a.Average(e => e.Rating), ratingB = b.Average(e => e.Rating) });
        _log?.LogInformation("ranked match {id} {format} on {map}: {a} vs {b}", m.Id, format, map, string.Join(",", m.Teams[0].Select(Name)), string.Join(",", m.Teams[1].Select(Name)));
    }
    static string Name(string id) => Store.BySteam.TryGetValue(id, out var q) ? q.Name : id;

    // ---------- lobby lifecycle hooks (from GameHub) ----------
    public static void OnStarted(Lobby l)
    {
        if (!Matches.TryGetValue(l.Id, out var m) || m.State != "lobby") return;
        m.State = "battle"; m.Started = DateTime.UtcNow;
        // 0.9.6: a map in maps.json must be of the match's size and in its pool; any other map keeps the name rule below.
        if (MapList.TryGetValue(l.Scenario ?? "", out var listed))
        {
            if (listed.size != m.Format) { m.State = "unrated"; Append("unrated", new { id = m.Id, reason = "map_wrong_size", scenario = l.Scenario, format = m.Format, size = listed.size }); }
            else if (!Formats[m.Format].pool.Contains(listed.bas, StringComparer.OrdinalIgnoreCase)) { m.State = "unrated"; Append("unrated", new { id = m.Id, reason = "map_not_in_pool", scenario = l.Scenario }); }
        }
        else if (!m.Map.Equals(MapName(l.Scenario), StringComparison.OrdinalIgnoreCase) && !Formats[m.Format].pool.Contains(MapName(l.Scenario), StringComparer.OrdinalIgnoreCase))
        { m.State = "unrated"; Append("unrated", new { id = m.Id, reason = "map_not_in_pool", scenario = l.Scenario }); }
        // Lateralus 22 Nov 2026 20:1x: Dead Center is installed as [1v1] and [2v2]; MapName drops the size tag, so a 1v1 on the 2v2 map was rated.
        // A map whose size tag is not the match format is unrated (maps without a tag keep the old rule).
        else if (SizeTag(l.Scenario) is string tag && !(tag == "5v5" ? "4v4" : tag).Equals(m.Format, StringComparison.OrdinalIgnoreCase))   // 0.9.5b clients still have [5v5] maps
        { m.State = "unrated"; Append("unrated", new { id = m.Id, reason = "map_wrong_size", scenario = l.Scenario, format = m.Format }); }
        Append("started", new { id = m.Id, scenario = l.Scenario });
    }
    public static void OnLobbyClosed(Lobby l)
    {
        if (Matches.TryGetValue(l.Id, out var m) && m.State == "lobby") { m.State = "cancelled"; Append("cancelled", new { id = m.Id }); Matches.Remove(m.Id); }
    }
    // "[FA] [2v2] Dead Center 0.2" -> "2v2"; null when the name has no size tag
    public static string? SizeTag(string? scen)
    {
        var x = System.Text.RegularExpressions.Regex.Match(scen ?? "", @"\[(\dv\d)\]");
        return x.Success ? x.Groups[1].Value : null;
    }
    // "[FA] [1v1] Dead Center 0.2" -> "Dead Center"
    public static string MapName(string? scen)
    {
        var s = System.Text.RegularExpressions.Regex.Replace(scen ?? "", @"^\[FA\]\s*", "");
        s = System.Text.RegularExpressions.Regex.Replace(s, @"^\[\dv\d\]\s*", "");
        return System.Text.RegularExpressions.Regex.Replace(s, @"\s+\d+(\.\d+)+$", "").Trim();
    }
    public static string Who(string steamId)
    {
        var h = SHA256.HashData(Encoding.UTF8.GetBytes("arrow-stats|" + steamId));
        return Convert.ToHexString(h, 0, 8).ToLowerInvariant();
    }

    // ---------- results ----------
    public static void OnStats(string body)
    {
        JsonNode? r; try { r = JsonNode.Parse(body); } catch { return; }
        var who = (string?)r?["who"]; var winner = (string?)r?["fight"]?["WinnerTeam"]; var side = (string?)r?["myTeam"]; var key = (string?)r?["matchKey"];
        if (who == null || winner == null || side == null) return;
        var m = Matches.Values.Where(x => x.State == "battle").FirstOrDefault(x => x.Teams.SelectMany(t => t).Any(id => Who(id) == who));
        if (m == null) return;
        var steam = m.Teams.SelectMany(t => t).First(id => Who(id) == who);
        m.Votes[steam] = (side, winner, key ?? "", r!);
        m.FirstVote ??= DateTime.UtcNow;
        Append("report", new { id = m.Id, steam, side, winner, key });
        TryResolve(m, false);
    }
    static void ResolveTimeouts()
    {
        foreach (var m in Matches.Values.Where(x => x.State == "battle" && x.Votes.Count > 0).ToList())
            if ((DateTime.UtcNow - m.Started!.Value).TotalMinutes > 45 + OneSidedWaitMin) TryResolve(m, true);
            // both sides reported but a flagged deserter could not be matched yet: settle 10 minutes after the first report
            else if (m.FirstVote is DateTime f && (DateTime.UtcNow - f).TotalMinutes > ReportWaitMin) TryResolve(m, false, settle: true);
        foreach (var m in Matches.Values.Where(x => x.State == "battle" && x.Votes.Count == 0 && (DateTime.UtcNow - x.Started!.Value).TotalHours > 3).ToList())
        { m.State = "unrated"; Append("unrated", new { id = m.Id, reason = "no_reports" }); Matches.Remove(m.Id); }
    }
    const double ReportWaitMin = 10;
    static void TryResolve(RankedMatch m, bool timedOut, bool settle = false)
    {
        // Each hub team must report one native side (Alpha/Bravo) consistently.
        string? SideOf(int t) { var s = m.Teams[t].Where(m.Votes.ContainsKey).Select(id => m.Votes[id].side).Distinct().ToList(); return s.Count == 1 ? s[0] : s.Count == 0 ? null : "?"; }
        var sa = SideOf(0); var sb = SideOf(1);
        var winners = m.Votes.Values.Select(v => v.winner).Distinct().ToList();
        if (sa == "?" || sb == "?" || (sa != null && sa == sb) || winners.Count > 1)
        { Close(m, "disputed", new { sa, sb, winners }); return; }
        var w = winners[0];
        // Draw (Lateralus 22 Nov: "use your draw proposal"): rated like half a win when both sides reported; else unrated as before.
        if (w is not ("Alpha" or "Bravo"))
        {
            if (sa != null && sb != null) { if (!settle && Unmatched(m)) return; RateDraw(m); return; }
            if (!timedOut) return;
            Close(m, "unrated", new { reason = "draw_one_side_reported", winner = w }); return;
        }
        if (sa != null && sb != null)
        {
            // Wait for more reports while the game flags deserters we cannot yet tell apart from players whose report is still coming.
            if (!settle && Unmatched(m)) return;
            Rate(m, sa == w ? 0 : 1); return;
        }
        if (!timedOut) return;
        // One side silent: rate only if every silent-side player is a deserter in the reporting side's own report.
        var reported = sa != null ? 0 : 1; var repSide = sa ?? sb!;
        var silentSide = repSide == "Alpha" ? "Bravo" : "Alpha";   // players[].team is "Alpha"/"Bravo" (TeamId is always 0)
        var rep = m.Votes.Values.First().report;
        var silent = rep["players"]?.AsArray().Where(p => (string?)p?["team"] == silentSide && !((bool?)p?["bot"] ?? false)).ToList() ?? new();
        if (silent.Count > 0 && silent.All(p => (bool?)p?["Deserter"] == true)) Rate(m, repSide == w ? reported : 1 - reported, deserted: true);
        else Close(m, "unrated", new { reason = "one_side_reported" });
    }
    static void Rate(RankedMatch m, int winTeam, bool deserted = false)
    {
        var lad = m.Ladder;
        var W = m.Teams[winTeam].Select(id => Get(lad, id, Name(id))).ToList();
        var L = m.Teams[1 - winTeam].Select(id => Get(lad, id, Name(id))).ToList();
        double rw = W.Average(r => r.Rating), rl = L.Average(r => r.Rating);
        double baseChange = K * (1 - Expected(rw, rl));
        double mean = LadderMean(lad), gate = Gate(mean);   // before this match's changes
        var changes = new Dictionary<string, double>();
        void Note(RankedRating r, bool win, List<RankedRating> other, double c)
        {
            var top = other.OrderByDescending(o => o.Rating).First();
            r.Recent.Insert(0, new RankedRecent { T = DateTime.UtcNow, Format = m.Format, Map = m.Map, Vs = other.Count == 1 ? top.Name : top.Name + " +" + (other.Count - 1), VsRating = Math.Round(other.Average(o => o.Rating), 1), Win = win, Change = Math.Round(c, 2) });
            if (r.Recent.Count > 10) r.Recent.RemoveRange(10, r.Recent.Count - 10);
        }
        // Deserters (Lateralus 22 Nov; vanilla 1.1 counts a player still disconnected at the end as a deserter, and 1.0.10 stopped
        // deserters gaining Elo): a player the game itself flags as Deserter never gains - on the winning team he takes the loss.
        var deserters = Deserters(m);
        var pre = W.Concat(L).ToDictionary(r => r.SteamId, r => r.Rating);
        // Per-player split, option C (Lateralus 22 Nov): each player's share comes from his own rating against the enemy team's average
        // (a favourite gains little and loses much, an underdog the reverse); each side's shares are then scaled so the side's total is
        // the team pot, baseChange x players. So the match moves the same total as before and adds no points. 1v1 is unchanged.
        var share = Shares(W, rl, L, rw, baseChange);
        foreach (var r in W)
        {
            // a deserter on the winning team takes the loss he would have taken had his team lost: his own expected score x K
            if (deserters.Contains(r.SteamId)) { var b0 = r.Rating; r.Rating = Math.Max(Floor, r.Rating - K * Expected(r.Rating, rl)); r.Losses++; r.Last = DateTime.UtcNow; changes[r.SteamId] = r.Rating - b0; continue; }
            var c = share[r.SteamId] * (1 + Bonus(r.Rating, mean)); r.Rating += c; r.Wins++; r.Best = Math.Max(r.Best, r.Rating); r.Last = DateTime.UtcNow; changes[r.SteamId] = c;
        }
        foreach (var r in L) { var before = r.Rating; r.Rating = Math.Max(Floor, r.Rating - share[r.SteamId]); r.Losses++; r.Last = DateTime.UtcNow; changes[r.SteamId] = r.Rating - before; }
        foreach (var r in W) Note(r, !deserters.Contains(r.SteamId), L, changes[r.SteamId]);
        foreach (var r in L) Note(r, false, W, changes[r.SteamId]);
        _dirty = true;
        _rateNumbers = W.Concat(L).ToDictionary(r => r.SteamId, r => (pre[r.SteamId], r.Rating));
        foreach (var d in deserters) Offend(d, "deserted");
        Close(m, "rated", new { winTeam, deserted, deserters, avgW = rw, avgL = rl, baseChange, ladderMean = mean, bonusGate = gate, shares = share, changes });
        foreach (var (id, c) in changes)
            if (Store.BySteam.TryGetValue(id, out var q)) Send(q, "RankedResult", new { matchId = m.Id, ladder = lad, change = Math.Round(c, 2), rating = Math.Round(Get(lad, id).Rating, 2), win = m.Teams[winTeam].Contains(id) && !deserters.Contains(id) });
    }
    // Draw = score 0.5 (standard Elo): raw_i = K (0.5 - E(r_i, enemy average)), a favourite loses a little and an underdog gains a
    // little; each side is then shifted (not scaled: raws can have both signs) so its total is the team-average draw change x players,
    // so the match adds no points. Equal teams of equal players: 0. No win bonus. A deserter takes his loss (K E(own, enemy avg)).
    static void RateDraw(RankedMatch m)
    {
        var lad = m.Ladder;
        var T = m.Teams.Select(t => t.Select(id => Get(lad, id, Name(id))).ToList()).ToList();
        var avg = T.Select(t => t.Average(r => r.Rating)).ToList();
        var deserters = Deserters(m);
        var pre = T.SelectMany(t => t).ToDictionary(r => r.SteamId, r => r.Rating);
        var change = new Dictionary<string, double>();
        for (int i = 0; i < 2; i++)
        {
            double oe = avg[1 - i], pot = T[i].Count * K * (0.5 - Expected(avg[i], oe));
            var raw = T[i].Select(r => K * (0.5 - Expected(r.Rating, oe))).ToList();
            double shift = (raw.Sum() - pot) / T[i].Count;
            for (int j = 0; j < T[i].Count; j++) change[T[i][j].SteamId] = deserters.Contains(T[i][j].SteamId) ? -K * Expected(T[i][j].Rating, oe) : raw[j] - shift;
        }
        for (int i = 0; i < 2; i++)
            foreach (var r in T[i])
            {
                var b0 = r.Rating; r.Rating = Math.Max(Floor, r.Rating + change[r.SteamId]); change[r.SteamId] = r.Rating - b0;
                if (deserters.Contains(r.SteamId)) r.Losses++; else r.Draws++;
                r.Best = Math.Max(r.Best, r.Rating); r.Last = DateTime.UtcNow;
                var other = T[1 - i]; var top = other.OrderByDescending(o => o.Rating).First();
                r.Recent.Insert(0, new RankedRecent { T = DateTime.UtcNow, Format = m.Format, Map = m.Map, Vs = other.Count == 1 ? top.Name : top.Name + " +" + (other.Count - 1), VsRating = Math.Round(avg[1 - i], 1), Win = false, Draw = !deserters.Contains(r.SteamId), Change = Math.Round(change[r.SteamId], 2) });
                if (r.Recent.Count > 10) r.Recent.RemoveRange(10, r.Recent.Count - 10);
            }
        _dirty = true;
        _rateNumbers = pre.ToDictionary(k => k.Key, k => (k.Value, k.Value + change[k.Key])); _isDraw = true;
        foreach (var d in deserters) Offend(d, "deserted");
        Close(m, "rated", new { draw = true, deserters, avgA = avg[0], avgB = avg[1], changes = change });
        foreach (var (id, c) in change)
            if (Store.BySteam.TryGetValue(id, out var q)) Send(q, "RankedResult", new { matchId = m.Id, ladder = lad, change = Math.Round(c, 2), rating = Math.Round(Get(lad, id).Rating, 2), win = false, draw = !deserters.Contains(id) });
    }
    // Option C shares (before any change of this match): winner i raw = K(1 - E(r_i, loser avg)), loser j raw = K E(r_j, winner avg),
    // each side scaled to baseChange x its player count.
    public static Dictionary<string, double> Shares(List<RankedRating> W, double rl, List<RankedRating> L, double rw, double baseChange)
    {
        var res = new Dictionary<string, double>();
        void Side(List<RankedRating> side, Func<RankedRating, double> raw)
        {
            var v = side.Select(raw).ToList(); double sum = v.Sum(), pot = baseChange * side.Count;
            for (int i = 0; i < side.Count; i++) res[side[i].SteamId] = sum > 0 ? v[i] * pot / sum : baseChange;
        }
        Side(W, r => K * (1 - Expected(r.Rating, rl)));
        Side(L, r => K * Expected(r.Rating, rw));
        return res;
    }
    // Hub players flagged Deserter by the game's end-of-match statistics. Reports name players only by in-match uid; a reporter's own
    // uid is myUid. So: on each side, the silent players (no report) are deserters when the reports flag at least that many non-reporting,
    // non-bot players of that side as Deserter. A reporter flagged Deserter (left, then reported) is matched by uid directly.
    static bool Unmatched(RankedMatch m)
    {
        var mine = new HashSet<int>(m.Votes.Values.Select(v => (int?)v.report["myUid"] ?? -1));
        bool flagged = m.Votes.Values.Any(v => (v.report["players"]?.AsArray() ?? new JsonArray()).Any(p => p != null && (bool?)p["Deserter"] == true && !((bool?)p["bot"] ?? false) && !mine.Contains((int?)p["uid"] ?? -1)));
        return flagged && m.Teams.Sum(t => t.Count(id => !m.Votes.ContainsKey(id))) > Deserters(m).Count;
    }
    static HashSet<string> Deserters(RankedMatch m)
    {
        var res = new HashSet<string>();
        var reporterUid = new Dictionary<int, string>();
        foreach (var (steam, v) in m.Votes) if (v.report["myUid"]?.GetValue<int>() is int u) reporterUid[u] = steam;
        var flagged = new Dictionary<string, HashSet<int>>();   // side -> uids flagged Deserter that did not report
        foreach (var v in m.Votes.Values)
            foreach (var p in v.report["players"]?.AsArray() ?? new JsonArray())
            {
                if (p == null || (bool?)p["Deserter"] != true || ((bool?)p["bot"] ?? false)) continue;
                int uid = (int?)p["uid"] ?? -1; string side = (string?)p["team"] ?? "";
                if (reporterUid.TryGetValue(uid, out var st)) { res.Add(st); continue; }
                (flagged.TryGetValue(side, out var set) ? set : flagged[side] = new HashSet<int>()).Add(uid);
            }
        for (int t = 0; t < 2; t++)
        {
            var side = m.Teams[t].Where(m.Votes.ContainsKey).Select(id => m.Votes[id].side).FirstOrDefault()
                       ?? (m.Teams[1 - t].Where(m.Votes.ContainsKey).Select(id => m.Votes[id].side).FirstOrDefault() is string o ? (o == "Alpha" ? "Bravo" : "Alpha") : null);
            var silent = m.Teams[t].Where(id => !m.Votes.ContainsKey(id)).ToList();
            if (side != null && silent.Count > 0 && flagged.TryGetValue(side, out var f) && f.Count >= silent.Count) res.UnionWith(silent);
        }
        return res;
    }
    // Per-player result of each player's latest ranked match, for the end screen (Lateralus 22 Nov: "end of match screens don't show any
    // ELO gain or loss for each player"). Unrated/disputed/cancelled matches list the players with no change and the reason.
    public static readonly Dictionary<string, object> LastResult = new();
    static Dictionary<string, (double before, double after)>? _rateNumbers; static bool _isDraw;
    static void Close(RankedMatch m, string state, object detail)
    {
        var nums = _rateNumbers; _rateNumbers = null; var draw = _isDraw; _isDraw = false;
        var players = m.Teams.SelectMany((t, ti) => t.Select(id => (id, ti))).Select(x =>
        {
            var r = Ladders[m.Ladder].GetValueOrDefault(x.id);
            var n = nums != null && nums.TryGetValue(x.id, out var v) ? v : ((double before, double after)?)null;
            return new { steamId = x.id, name = r?.Name ?? Name(x.id), team = x.ti, before = Math.Round(n?.before ?? r?.Rating ?? Start, 1), after = Math.Round(n?.after ?? r?.Rating ?? Start, 1), change = n == null ? 0 : Math.Round(n.Value.after - n.Value.before, 1) };
        }).ToList();
        var res = new { matchId = m.Id, ladder = m.Ladder, format = m.Format, map = m.Map, outcome = state, draw, detail = state == "rated" ? null : detail, at = DateTime.UtcNow, players };
        foreach (var t in m.Teams) foreach (var id in t) LastResult[id] = res;
        m.State = state; Matches.Remove(m.Id);
        Append(state, new { id = m.Id, mode = m.Mode, format = m.Format, detail });
        _log?.LogInformation("ranked match {id}: {state}", m.Id, state);
    }

    // ---------- views ----------
    public static object Me(string steamId) => MeLadders(steamId);
    public static object Extra(string steamId) { PenaltyReset(); var pe = Penalties().GetValueOrDefault(steamId); return new { cooldownSec = (int)Math.Ceiling(CooldownLeft(steamId)), offences = pe?.Count ?? 0, lastOffence = pe?.Why.LastOrDefault() ?? "", nextReset = NextReset(), lastResult = LastResult.GetValueOrDefault(steamId) }; }
    static Dictionary<string, object> MeLadders(string steamId) => Ladders.Keys.ToDictionary(lad => lad, lad =>
    {
        var r = Ladders[lad].TryGetValue(steamId, out var x) ? x : new RankedRating { SteamId = steamId };   // a lookup never adds a player
        var place = Place(lad, steamId);
        return (object)new { rating = Math.Round(r.Rating, 2), level = Level(lad, r.Rating, place), place, wins = r.Wins, losses = r.Losses, best = Math.Round(r.Best, 2),
            draws = r.Draws, recent = r.Recent.Select(x => new { t = x.T, format = x.Format, map = x.Map, vs = x.Vs, vsRating = x.VsRating, win = x.Win, draw = x.Draw, change = x.Change }) };
    });
    public static object Board(string ladder, int top = 200)
    {
        var s = Sorted(ladder);
        return new
        {
            season = Season, seasonName = SeasonName, ladder, updated = DateTime.UtcNow, players = s.Count,
            rows = s.Take(top).Select((r, i) => new { place = i + 1, steamId = r.SteamId, name = r.Name, rating = Math.Round(r.Rating, 1), level = Level(ladder, r.Rating, i + 1), wins = r.Wins, losses = r.Losses,
                best = Math.Round(r.Best, 1), last = string.Concat(r.Recent.Take(10).Select(x => x.Win ? 'W' : 'L')) }).ToArray(),
        };
    }
    // The player's own search, for the ranked page's status line (Lateralus 22 Nov: show when the matchmaker widens the rating gap):
    // seconds waited and, per format the search can still make, the allowed rating gap now (null = any rating, after 3 minutes).
    public static object? SearchInfo(string steamId)
    {
        var e = Queue.FirstOrDefault(x => x.Members.Contains(steamId));
        if (e == null) return null;
        var gaps = Formats.Where(f => Fits(e, f.Value.size)).ToDictionary(f => f.Key, f => { var w = Window(e, f.Value.size); return w == double.MaxValue ? (int?)null : (int)Math.Round(w); });
        return new { waitSec = (int)e.WaitSec, anyAfterSec = 180, gaps };
    }
    public static object QueueInfo() => Queues.ToDictionary(k => k, k => Queue.Where(e => e.Mode == k).Sum(e => e.Members.Count));
    // The player's open ranked match (for the FA client: the host loads this map), or null.
    public static object? MatchOf(string steamId)
    {
        var m = Matches.Values.FirstOrDefault(x => x.State is "lobby" or "battle" && x.Teams.Any(t => t.Contains(steamId)));
        return m == null ? null : new { id = m.Id, lobbyId = m.LobbyId, mode = m.Mode, format = m.Format, ladder = m.Ladder, map = m.Map, scenarioName = ScenarioFor(m.Format, m.Map), state = m.State, team = m.Teams[0].Contains(steamId) ? 0 : 1,
            phase = m.Phase, phaseLeftMs = Math.Max(0, (int)(m.PhaseUntil - DateTime.UtcNow).TotalMilliseconds), host = Store.Lobbies.TryGetValue(m.LobbyId, out var l) ? l.HostId : "" };
    }
    public static object GroupDecks(Player p)
    {
        var ids = p.PartyId != null && Store.Parties.TryGetValue(p.PartyId, out var pt) ? pt.Members.ToList() : new List<string> { p.SteamId };
        return ids.ToDictionary(id => id, id => Store.BySteam.TryGetValue(id, out var q) ? (object)new { ok = q.RankedDeckOk, deck = q.RankedDeck } : new { ok = false, deck = "" });
    }
    // join -> deck when the host's game lobby exists and every other player confirmed joining; deck -> reveal -> launch on the clock.
    // A join that is not complete in 90 s cancels the match (no rating); the players go back to the menu.
    static void Phases()
    {
        foreach (var m in Matches.Values.Where(x => x.State == "lobby").ToList())
        {
            if (!Store.Lobbies.TryGetValue(m.LobbyId, out var l)) continue;
            var now = DateTime.UtcNow;
            if (m.Phase == "join")
            {
                if (l.Invite != null && l.Members.All(x => x.Host || x.Joined)) { m.Phase = "deck"; m.PhaseUntil = now.AddSeconds(DeckSec); Append("phase", new { id = m.Id, phase = m.Phase }); }
                else if (now > m.PhaseUntil)
                {
                    Append("cancelled", new { id = m.Id, reason = "join_timeout", missing = l.Members.Where(x => !x.Host && !x.Joined).Select(x => x.SteamId) });
                    foreach (var x in l.Members.Where(x => !x.Host && !x.Joined).ToList()) Offend(x.SteamId, "did_not_join");
                    foreach (var x in l.Members) if (Store.BySteam.TryGetValue(x.SteamId, out var q)) { Send(q, "MatchFailed", new { lobbyId = l.Id, reason = "ranked_join_timeout" }); Send(q, "LobbyClosed", new { lobbyId = l.Id }); q.LobbyId = null; Status(q, "menu"); }
                    l.State = "closed"; l.Members.Clear(); Store.Lobbies.Remove(l.Id); Matches.Remove(m.Id);
                }
            }
            else if (m.Phase == "deck" && now > m.PhaseUntil) { m.Phase = "reveal"; m.PhaseUntil = now.AddSeconds(RevealSec); Append("phase", new { id = m.Id, phase = m.Phase }); }
            else if (m.Phase == "reveal" && now > m.PhaseUntil) { m.Phase = "launch"; m.PhaseUntil = now; Append("phase", new { id = m.Id, phase = m.Phase }); }
        }
    }

    // ---------- leave cooldowns (Lateralus 22 Nov) ----------
    // Leaving or disconnecting from a ranked lobby before launch, not joining it within 90 s, or being flagged Deserter by the game
    // at the end: 1st time 5 minutes, 2nd 1 hour, 3rd and later 24 hours without ranked. Every player's count goes back to 0 at the
    // same time every day (FAQUEUE_RANKED_RESET_UTC, hour in UTC, default 0 = 16:00 PST); a cooldown that is running keeps running.
    public sealed class Penalty { public int Count { get; set; } public DateTime Until { get; set; } public List<string> Why { get; set; } = new(); }
    static Dictionary<string, Penalty>? _pen; static DateTime _penEpoch;
    static string PenFile => Path.Combine(_dir, "penalties.json");
    static int ResetHour => int.TryParse(Environment.GetEnvironmentVariable("FAQUEUE_RANKED_RESET_UTC"), out var h) && h is >= 0 and < 24 ? h : 0;
    static DateTime LastReset(DateTime now) { var t = now.Date.AddHours(ResetHour); return now >= t ? t : t.AddDays(-1); }
    public static DateTime NextReset() => LastReset(DateTime.UtcNow).AddDays(1);
    static Dictionary<string, Penalty> Penalties()
    {
        if (_pen != null) return _pen;
        try { if (File.Exists(PenFile)) { var j = JsonNode.Parse(File.ReadAllText(PenFile)); _penEpoch = (DateTime?)j?["epoch"] ?? default; _pen = j?["players"].Deserialize<Dictionary<string, Penalty>>(); } } catch { }
        return _pen ??= new();
    }
    static void SavePenalties() { try { File.WriteAllText(PenFile, JsonSerializer.Serialize(new { epoch = _penEpoch, resetHourUtc = ResetHour, players = Penalties() })); } catch (Exception e) { _log?.LogError("penalties save: {e}", e.Message); } }
    static void PenaltyReset()
    {
        var all = Penalties(); var last = LastReset(DateTime.UtcNow);
        if (_penEpoch >= last) return;
        foreach (var p in all.Values) { p.Count = 0; p.Why.Clear(); }
        foreach (var k in all.Where(x => x.Value.Until < DateTime.UtcNow).Select(x => x.Key).ToList()) all.Remove(k);
        _penEpoch = last; SavePenalties();
    }
    public static double CooldownLeft(string id) { PenaltyReset(); return Penalties().TryGetValue(id, out var p) ? Math.Max(0, (p.Until - DateTime.UtcNow).TotalSeconds) : 0; }
    public static void Offend(string id, string why)
    {
        PenaltyReset();
        var all = Penalties(); if (!all.TryGetValue(id, out var p)) all[id] = p = new Penalty();
        p.Count++; p.Why.Add(why);
        var d = p.Count == 1 ? TimeSpan.FromMinutes(5) : p.Count == 2 ? TimeSpan.FromHours(1) : TimeSpan.FromHours(24);
        var until = DateTime.UtcNow + d; if (until > p.Until) p.Until = until;
        SavePenalties();
        Append("penalty", new { id, why, count = p.Count, until = p.Until });
        _log?.LogInformation("ranked cooldown {id}: {why}, offence {n}, until {u:u}", id, why, p.Count, p.Until);
        if (Store.BySteam.TryGetValue(id, out var q)) Send(q, "RankedCooldown", new { why, offences = p.Count, until = p.Until, seconds = (int)d.TotalSeconds });
    }
    // a player left (or dropped out of) a ranked lobby: an offence only before the launch phase (after it the game itself runs the match)
    public static void OnRankedLeave(Lobby l, string id)
    {
        if (Matches.TryGetValue(l.Id, out var m) && m.State == "lobby" && m.Phase is "join" or "deck" or "reveal") Offend(id, "left_lobby_" + m.Phase);
    }

    // ---------- storage ----------
    // "Recently played with" for the ranked group invite list (Lateralus 22 Nov): the last 30 players met in any started hub lobby.
    sealed class Met { public string Id { get; set; } = ""; public string Name { get; set; } = ""; public DateTime T { get; set; } }
    static Dictionary<string, List<Met>>? _met;
    static string MetFile => Path.Combine(_dir, "recent-players.json");
    static Dictionary<string, List<Met>> MetAll()
    {
        if (_met != null) return _met;
        try { _met = File.Exists(MetFile) ? JsonSerializer.Deserialize<Dictionary<string, List<Met>>>(File.ReadAllText(MetFile)) : null; } catch { }
        return _met ??= new();
    }
    static bool _metDirty;
    public static void NotePlayed(Lobby l)
    {
        var ids = l.Members.Select(m => (m.SteamId, m.Name)).ToList();
        var all = MetAll();
        foreach (var (a, _) in ids)
        {
            if (!all.TryGetValue(a, out var list)) all[a] = list = new();
            foreach (var (b, name) in ids.Where(x => x.SteamId != a))
            {
                list.RemoveAll(m => m.Id == b);
                list.Insert(0, new Met { Id = b, Name = name, T = DateTime.UtcNow });
            }
            if (list.Count > 30) list.RemoveRange(30, list.Count - 30);
        }
        _metDirty = true;
    }
    public static object RecentPlayers(string steamId) =>
        (MetAll().TryGetValue(steamId, out var list) ? list : new()).Select(m => new { steamId = m.Id, name = Store.BySteam.TryGetValue(m.Id, out var q) ? q.Name : m.Name, t = m.T, online = Store.BySteam.ContainsKey(m.Id) }).ToArray();

    static void Save()
    {
        if (_metDirty) { try { var tmp = MetFile + ".tmp"; File.WriteAllText(tmp, JsonSerializer.Serialize(MetAll())); File.Move(tmp, MetFile, true); _metDirty = false; } catch (Exception e) { _log?.LogWarning("recent players: {e}", e.Message); } }
        foreach (var (lad, d) in Ladders)
        {
            var f = RatingsFile(lad); var tmp = f + ".tmp";
            File.WriteAllText(tmp, JsonSerializer.Serialize(d.Values.Where(r => r.Wins + r.Losses > 0).ToList()));
            File.Move(tmp, f, true);
        }
        _dirty = false;
    }
    static void Export()
    {
        foreach (var lad in Ladders.Keys)
        {
            var f = Path.Combine(_dir, $"leaderboard-{lad}.json"); var tmp = f + ".tmp";
            File.WriteAllText(tmp, JsonSerializer.Serialize(Board(lad)));
            File.Move(tmp, f, true);
        }
        _lastExport = DateTime.UtcNow;
    }
    static void Append(string kind, object o) =>
        File.AppendAllText(Path.Combine(_dir, $"season-{Season}-ledger.jsonl"), JsonSerializer.Serialize(new { t = DateTime.UtcNow, kind, data = o }) + "\n");

    // ---------- messages ----------
    static void Send(Player p, string method, object arg) => Out.Add((p.Conn, method, arg));
    static void Status(Player p, string st)
    {
        if (p.Status == st) return;
        p.Status = st;
        Send(p, "PlayerStatusChanged", st);
        long rev = ++Store.Revision;
        foreach (var q in Store.BySteam.Values.Where(x => x.Dir))
            Send(q, "DirectoryUpdated", new { revision = rev, updates = new[] { new { revision = rev, kind = "player.upsert", steamId = p.SteamId, player = p.Online(), lobbyId = (string?)null, lobby = (object?)null } } });
    }
    public static void Flush()
    {
        List<(string conn, string method, object arg)> o;
        lock (Store.Lock) { o = new(Out); Out.Clear(); }
        foreach (var (c, m, a) in o)
            _ = _ctx?.Clients.Client(c).SendAsync(m, a).ContinueWith(t => { if (t.Exception != null) _log?.LogWarning("ranked send {m}: {e}", m, t.Exception.InnerException?.Message); });
    }
}
