// Freedom Arrow ranked (Lateralus 22 Nov 2026; docs/ranked/RANKED-PROPOSAL.md, docs/simple-elo.md).
// Modes r1v1 / r3v3 / r5v5 through the normal FindMatch call. Ladders: "1v1" and "team" (3v3 + 5v5 share one).
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
    public double Best { get; set; } = Ranked.Start;
    public DateTime Last { get; set; }
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
    public string Id = "", Mode = "", Ladder = "", LobbyId = "", Map = "";
    public List<string>[] Teams = { new(), new() };
    public DateTime Created = DateTime.UtcNow;
    public DateTime? Started;
    public string State = "lobby";   // lobby | battle | rated | disputed | cancelled | unrated
    public readonly Dictionary<string, (string side, string winner, string key, JsonNode report)> Votes = new();
}

static class Ranked
{
    // simple-elo.md
    public const double Start = 1000, K = 40, Div = 400, Floor = 600, BonusTarget = 1700, DeadZone = 200;
    // 20 ranks: 1-18 by Elo band, 19 = places 2-3 and 20 = place 1 among players at 2170+ (RANKED-PROPOSAL.md, section 1)
    static readonly int[] BandStart = { 0, 1001, 1028, 1059, 1093, 1132, 1175, 1223, 1277, 1337, 1405, 1481, 1566, 1661, 1767, 1887, 2020, 2170 };
    public static readonly Dictionary<string, (int size, string ladder, string[] pool)> Modes = new()
    {
        ["r1v1"] = (1, "1v1", new[] { "Dead Center", "Kadaga", "Jelgava", "Klaipeda", "Chernyakhovsky" }),
        ["r3v3"] = (3, "team", new[] { "Baltiisk", "Bay of Winds", "Dam" }),
        ["r5v5"] = (5, "team", new[] { "Airport", "Oil Rush", "Cold Harbor" }),
    };
    const double PartySpread = 500, OneSidedWaitMin = 30;

    public static int Season = 1;
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

    public static bool IsRanked(string? mode) => mode != null && Modes.ContainsKey(mode);

    public static void Init(IHubContext<GameHub> ctx, ILogger log, string dir)
    {
        _ctx = ctx; _log = log; _dir = dir; Directory.CreateDirectory(dir);
        var cfg = Path.Combine(dir, "config.json");
        if (File.Exists(cfg)) Season = JsonNode.Parse(File.ReadAllText(cfg))?["season"]?.GetValue<int>() ?? 1;
        else File.WriteAllText(cfg, JsonSerializer.Serialize(new { season = Season, length = "2 months (Lateralus 22 Nov 2026)" }));
        foreach (var lad in Ladders.Keys.ToArray())
        {
            var f = RatingsFile(lad);
            if (File.Exists(f)) foreach (var r in JsonSerializer.Deserialize<List<RankedRating>>(File.ReadAllText(f)) ?? new()) Ladders[lad][r.SteamId] = r;
        }
        _log.LogInformation("ranked season {s}: {a} 1v1 and {b} team ratings loaded from {d}", Season, Ladders["1v1"].Count, Ladders["team"].Count, dir);
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
    public static double Bonus(double winnerRating)
    {
        var d = BonusTarget - winnerRating;
        return d <= DeadZone ? 0 : 1 - Math.Exp(-d / (DeadZone / 2));
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
    // Called from FindMatch for r1v1/r3v3/r5v5. Returns an error code or null.
    public static string? Enqueue(Player p, string mode)
    {
        var (size, ladder, _) = Modes[mode];
        Party? pt = p.PartyId != null && Store.Parties.TryGetValue(p.PartyId, out var x) ? x : null;
        if (pt != null && pt.Leader != p.SteamId) return "not_leader";
        var ids = pt?.Members.ToList() ?? new List<string> { p.SteamId };
        // Party size decides the modes: 1v1 solo only; 4-5 players only 5v5; never more than a team.
        if (ids.Count > size || (size == 1 && ids.Count > 1)) return "party_too_big";
        if (ids.Count >= 4 && size != 5) return "party_needs_5v5";
        foreach (var id in ids)
        {
            if (!Store.BySteam.TryGetValue(id, out var q)) return "member_offline";
            if (q.LobbyId != null) return "leave_lobby_first";
            if (q.Build != p.Build) return "member_build_differs";
        }
        var ratings = ids.Select(id => Get(ladder, id, Store.BySteam[id].Name).Rating).ToList();
        if (ratings.Max() - ratings.Min() > PartySpread) return "party_spread_over_500";
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
    static double Window(RankedEntry e)
    {
        var (size, _, _) = Modes[e.Mode];
        var t = e.WaitSec;
        if (t >= 180) return double.MaxValue;                     // any rating after 3 minutes
        var b = size == 5 ? 150 : 100;
        return b * (1 + t / 60);
    }

    static void Tick()
    {
        try
        {
            lock (Store.Lock)
            {
                foreach (var mode in Modes.Keys) while (TryMatch(mode)) { }
                ResolveTimeouts();
                if (_dirty) Save();
                if ((DateTime.UtcNow - _lastExport).TotalSeconds >= 60) Export();
            }
            Flush();
        }
        catch (Exception e) { _log?.LogError("ranked tick: {e}", e); }
    }

    static bool TryMatch(string mode)
    {
        var (size, ladder, pool) = Modes[mode];
        foreach (var anchor in Queue.Where(e => e.Mode == mode).OrderBy(e => e.Since).ToList())
        {
            var w = Window(anchor);
            var cand = Queue.Where(e => e.Mode == mode && e.Build == anchor.Build && e != anchor && Math.Abs(e.Rating - anchor.Rating) <= Math.Max(w, Window(e)))
                .OrderBy(e => e.Since).Take(11).Prepend(anchor).ToList();
            if (cand.Sum(e => e.Members.Count) < 2 * size) continue;
            var best = BestSplit(cand, size, anchor.WaitSec >= 180);
            if (best == null) continue;
            Create(mode, ladder, pool, best.Value.a, best.Value.b);
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

    static void Create(string mode, string ladder, string[] pool, List<RankedEntry> a, List<RankedEntry> b)
    {
        foreach (var e in a.Concat(b)) Queue.Remove(e);
        var host = Store.BySteam[a[0].Leader];
        var map = pool[Random.Shared.Next(pool.Length)];
        var l = new Lobby { Id = Guid.NewGuid().ToString("N")[..16], Mode = mode, Size = 2 * Modes[mode].size, Build = host.Build, HostId = host.SteamId, HostName = host.Name, Open = false };
        var m = new RankedMatch { Id = l.Id, Mode = mode, Ladder = ladder, LobbyId = l.Id, Map = map };
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
            Send(Store.BySteam[id], "MatchFound", new { lobbyId = l.Id, mode, ranked = true, scenario = map, team = m.Teams[0].Contains(id) ? 0 : 1, host = host.SteamId });
        Append("match", new { id = m.Id, mode, ladder, map, teams = m.Teams, ratingA = a.Average(e => e.Rating), ratingB = b.Average(e => e.Rating) });
        _log?.LogInformation("ranked match {id} {mode} on {map}: {a} vs {b}", m.Id, mode, map, string.Join(",", m.Teams[0].Select(Name)), string.Join(",", m.Teams[1].Select(Name)));
    }
    static string Name(string id) => Store.BySteam.TryGetValue(id, out var q) ? q.Name : id;

    // ---------- lobby lifecycle hooks (from GameHub) ----------
    public static void OnStarted(Lobby l)
    {
        if (!Matches.TryGetValue(l.Id, out var m) || m.State != "lobby") return;
        m.State = "battle"; m.Started = DateTime.UtcNow;
        if (!m.Map.Equals(MapName(l.Scenario), StringComparison.OrdinalIgnoreCase) && !Modes[m.Mode].pool.Contains(MapName(l.Scenario), StringComparer.OrdinalIgnoreCase))
        { m.State = "unrated"; Append("unrated", new { id = m.Id, reason = "map_not_in_pool", scenario = l.Scenario }); }
        Append("started", new { id = m.Id, scenario = l.Scenario });
    }
    public static void OnLobbyClosed(Lobby l)
    {
        if (Matches.TryGetValue(l.Id, out var m) && m.State == "lobby") { m.State = "cancelled"; Append("cancelled", new { id = m.Id }); Matches.Remove(m.Id); }
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
        Append("report", new { id = m.Id, steam, side, winner, key });
        TryResolve(m, false);
    }
    static void ResolveTimeouts()
    {
        foreach (var m in Matches.Values.Where(x => x.State == "battle" && x.Votes.Count > 0).ToList())
            if ((DateTime.UtcNow - m.Started!.Value).TotalMinutes > 45 + OneSidedWaitMin) TryResolve(m, true);
        foreach (var m in Matches.Values.Where(x => x.State == "battle" && x.Votes.Count == 0 && (DateTime.UtcNow - x.Started!.Value).TotalHours > 3).ToList())
        { m.State = "unrated"; Append("unrated", new { id = m.Id, reason = "no_reports" }); Matches.Remove(m.Id); }
    }
    static void TryResolve(RankedMatch m, bool timedOut)
    {
        // Each hub team must report one native side (Alpha/Bravo) consistently.
        string? SideOf(int t) { var s = m.Teams[t].Where(m.Votes.ContainsKey).Select(id => m.Votes[id].side).Distinct().ToList(); return s.Count == 1 ? s[0] : s.Count == 0 ? null : "?"; }
        var sa = SideOf(0); var sb = SideOf(1);
        var winners = m.Votes.Values.Select(v => v.winner).Distinct().ToList();
        if (sa == "?" || sb == "?" || (sa != null && sa == sb) || winners.Count > 1)
        { Close(m, "disputed", new { sa, sb, winners }); return; }
        var w = winners[0];
        if (w is not ("Alpha" or "Bravo")) { Close(m, "unrated", new { reason = "draw", winner = w }); return; }
        if (sa != null && sb != null) { Rate(m, sa == w ? 0 : 1); return; }
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
        var changes = new Dictionary<string, double>();
        foreach (var r in W) { var c = baseChange * (1 + Bonus(r.Rating)); r.Rating += c; r.Wins++; r.Best = Math.Max(r.Best, r.Rating); r.Last = DateTime.UtcNow; changes[r.SteamId] = c; }
        foreach (var r in L) { var before = r.Rating; r.Rating = Math.Max(Floor, r.Rating - baseChange); r.Losses++; r.Last = DateTime.UtcNow; changes[r.SteamId] = r.Rating - before; }
        _dirty = true;
        Close(m, "rated", new { winTeam, deserted, avgW = rw, avgL = rl, baseChange, changes });
        foreach (var (id, c) in changes)
            if (Store.BySteam.TryGetValue(id, out var q)) Send(q, "RankedResult", new { matchId = m.Id, ladder = lad, change = Math.Round(c, 2), rating = Math.Round(Get(lad, id).Rating, 2), win = m.Teams[winTeam].Contains(id) });
    }
    static void Close(RankedMatch m, string state, object detail)
    {
        m.State = state; Matches.Remove(m.Id);
        Append(state, new { id = m.Id, mode = m.Mode, detail });
        _log?.LogInformation("ranked match {id}: {state}", m.Id, state);
    }

    // ---------- views ----------
    public static object Me(string steamId) => Ladders.Keys.ToDictionary(lad => lad, lad =>
    {
        var r = Get(lad, steamId); var place = Place(lad, steamId);
        return (object)new { rating = Math.Round(r.Rating, 2), level = Level(lad, r.Rating, place), place, wins = r.Wins, losses = r.Losses, best = Math.Round(r.Best, 2) };
    });
    public static object Board(string ladder, int top = 200)
    {
        var s = Sorted(ladder);
        return new
        {
            season = Season, ladder, updated = DateTime.UtcNow, players = s.Count,
            rows = s.Take(top).Select((r, i) => new { place = i + 1, steamId = r.SteamId, name = r.Name, rating = Math.Round(r.Rating, 1), level = Level(ladder, r.Rating, i + 1), wins = r.Wins, losses = r.Losses }).ToArray(),
        };
    }
    public static object QueueInfo() => Modes.Keys.ToDictionary(k => k, k => Queue.Where(e => e.Mode == k).Sum(e => e.Members.Count));

    // ---------- storage ----------
    static void Save()
    {
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
