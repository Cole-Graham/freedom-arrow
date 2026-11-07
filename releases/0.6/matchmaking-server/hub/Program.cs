// FAQueue: Freedom Arrow matchmaking hub for the unchanged ArrowQueue 0.10.31 client.
// Protocol read from the decompiled client (see ../PROTOCOL.md). The server only relays:
// presence, the lobby directory, and the host's native lobby invite. It never touches game data.
using System.Text.Json;
using Microsoft.AspNetCore.SignalR;

var b = WebApplication.CreateBuilder(args);
b.Services.AddSignalR(o => { o.EnableDetailedErrors = false; o.MaximumReceiveMessageSize = 256 * 1024; })
    .AddJsonProtocol(o => { o.PayloadSerializerOptions.PropertyNamingPolicy = null; });
b.Logging.AddSimpleConsole(o => { o.SingleLine = true; o.TimestampFormat = "HH:mm:ss "; });
var app = b.Build();
app.UseWebSockets();
app.MapGet("/health", () => Results.Json(Store.Health()));
app.MapHub<GameHub>("/hubs/game");
// ArrowQueue posts end-of-match statistics here (Freedom Arrow points its StatsServer at /hubs/stats). Kept on the deck only.
var statsFile = Path.Combine(AppContext.BaseDirectory, "..", "match-stats.jsonl");
app.MapPost("/hubs/stats/v1/match", async (HttpRequest r) =>
{
    using var sr = new StreamReader(r.Body); var body = await sr.ReadToEndAsync();
    if (body.Length > 512 * 1024) return Results.StatusCode(413);
    try { JsonDocument.Parse(body); } catch { return Results.BadRequest(); }
    lock (Store.Lock) File.AppendAllText(statsFile, body.ReplaceLineEndings(" ") + "\n");
    return Results.Json(new { ok = true });
});
var url = Environment.GetEnvironmentVariable("FAQUEUE_URL") ?? "http://127.0.0.1:8651";
app.Run(url);

sealed class Player
{
    public string Conn = "", SteamId = "", Name = "", Build = "", Version = "", Pack = "";
    public string Status = "menu";      // menu | searching | lobby | battle
    public string? LobbyId, SearchMode, PartyId;
    public bool Dir;                     // subscribed to directory updates
    public DateTime Since = DateTime.UtcNow;
    public object Identity() => new { steamId = SteamId, name = Name, buildHash = Build, version = Version, pack = Pack };
    public object Online() => new { player = Identity(), status = Status };
}

sealed class LobbyMember { public string SteamId = "", Name = ""; public int Team; public bool Host, Joined; }

sealed class Lobby
{
    public string Id = "", Mode = "5v5", Build = "", HostId = "", HostName = "", Scenario = "?", State = "gathering";
    public int Size = 10, PlayerCount, SlotsA = -1, SlotsB = -1;
    public JsonElement? Invite;
    public bool Open = true;
    public DateTime Created = DateTime.UtcNow;
    public readonly List<LobbyMember> Members = new();
    public HashSet<string> Banned = new();
    public bool Full => Members.Count >= Size;
    public object Row(string? viewerBuild) => new
    {
        lobbyId = Id, hostName = HostName, mode = Mode, scenario = Scenario, buildHash = Build,
        count = Math.Max(Members.Count, PlayerCount), size = Size, full = Full, state = State,
        sameBuild = viewerBuild == null || viewerBuild == Build, watchable = Invite != null,
        ageSec = (int)(DateTime.UtcNow - Created).TotalSeconds,
    };
    public object Roster() => Members.Select(m => new { steamId = m.SteamId, name = m.Name, team = m.Team, isHost = m.Host, joined = m.Joined, backfillPending = false }).ToArray();
    public object State_() => new { lobbyId = Id, status = State, scenario = Scenario, playerCount = Math.Max(Members.Count, PlayerCount), slotsA = SlotsA, slotsB = SlotsB, players = Roster(), invite = Invite };
}

sealed class Party
{
    public string Id = Guid.NewGuid().ToString("N")[..12], Leader = "";
    public readonly List<string> Members = new(), Invites = new();
}

static class Store
{
    public static readonly object Lock = new();
    public static readonly Dictionary<string, Player> ByConn = new();
    public static readonly Dictionary<string, Player> BySteam = new();
    public static readonly Dictionary<string, Lobby> Lobbies = new();
    public static readonly Dictionary<string, Party> Parties = new();
    public static long Revision;
    public static object Health()
    {
        lock (Lock) return new { ok = true, players = BySteam.Count, lobbies = Lobbies.Count, revision = Revision };
    }
    public static int Capacity(string? mode) => mode switch
    {
        "5v5" => 10, "4v4" => 8, "3v3" => 6, "2v2" => 4, "1v1" => 2, "test" => 1, _ => 10,
    };
}

sealed class GameHub : Hub
{
    readonly IHubContext<GameHub> _ctx;
    readonly ILogger<GameHub> _log;
    public GameHub(IHubContext<GameHub> ctx, ILogger<GameHub> log) { _ctx = ctx; _log = log; }

    // ---------- helpers (call under Store.Lock) ----------
    Player Me() => Store.ByConn.TryGetValue(Context.ConnectionId, out var p) ? p : throw new HubException("Call Hello before using this method.");
    static string Clip(string? s, int n) => string.IsNullOrEmpty(s) ? "" : (s.Length > n ? s[..n] : s);

    List<(string conn, string method, object arg)> _out = new();
    void To(Player p, string method, object arg) => _out.Add((p.Conn, method, arg));
    void ToLobby(Lobby l, string method, object arg)
    {
        foreach (var m in l.Members) if (Store.BySteam.TryGetValue(m.SteamId, out var p)) To(p, method, arg);
    }
    void Dir(string kind, string? steamId = null, object? player = null, string? lobbyId = null, Lobby? lobby = null)
    {
        long rev = ++Store.Revision;
        foreach (var p in Store.BySteam.Values.Where(x => x.Dir))
            To(p, "DirectoryUpdated", new { revision = rev, updates = new[] { new { revision = rev, kind, steamId, player, lobbyId, lobby = lobby?.Row(p.Build) } } });
    }
    async Task Flush()
    {
        List<(string conn, string method, object arg)> o; o = _out; _out = new();
        foreach (var (c, m, a) in o)
            try { await _ctx.Clients.Client(c).SendAsync(m, a); } catch (Exception e) { _log.LogWarning("send {m}: {e}", m, e.Message); }
    }
    void SetStatus(Player p, string st)
    {
        if (p.Status == st) return;
        p.Status = st;
        To(p, "PlayerStatusChanged", st);
        Dir("player.upsert", p.SteamId, p.Online());
    }
    void Remove(Player p, Lobby l, string reason)
    {
        var m = l.Members.FirstOrDefault(x => x.SteamId == p.SteamId);
        if (m == null) return;
        l.Members.Remove(m);
        p.LobbyId = null;
        SetStatus(p, "menu");
        if (m.Host || l.Members.Count == 0)
        {
            l.State = "closed";
            ToLobby(l, "MatchFailed", new { lobbyId = l.Id, reason = m.Host ? "host_left" : reason });
            ToLobby(l, "LobbyClosed", new { lobbyId = l.Id });
            foreach (var x in l.Members) if (Store.BySteam.TryGetValue(x.SteamId, out var xp)) { xp.LobbyId = null; SetStatus(xp, "menu"); }
            l.Members.Clear();
            Store.Lobbies.Remove(l.Id);
            Dir("lobby.removed", lobbyId: l.Id);
            _log.LogInformation("lobby {id} closed ({r})", l.Id, reason);
            return;
        }
        ToLobby(l, "PlayerLeft", new { lobbyId = l.Id, steamId = p.SteamId });
        if (l.State == "full") l.State = "gathering";
        ToLobby(l, "LobbyStateChanged", l.State_());
        Dir("lobby.upsert", lobbyId: l.Id, lobby: l);
    }
    void Join(Player p, Lobby l, bool host, int team = -1)
    {
        if (p.LobbyId != null && p.LobbyId != l.Id && Store.Lobbies.TryGetValue(p.LobbyId, out var old)) Remove(p, old, "moved");
        if (l.Members.All(x => x.SteamId != p.SteamId))
        {
            if (team < 0) team = l.Members.Count(x => x.Team == 0) <= l.Members.Count(x => x.Team == 1) ? 0 : 1;
            var m = new LobbyMember { SteamId = p.SteamId, Name = p.Name, Team = team, Host = host };
            l.Members.Add(m);
            ToLobby(l, "PlayerJoined", new { lobbyId = l.Id, player = new { steamId = m.SteamId, name = m.Name, team = m.Team, isHost = m.Host, joined = m.Joined, backfillPending = false } });
        }
        p.LobbyId = l.Id; p.SearchMode = null;
        SetStatus(p, "lobby");
        if (l.Full && l.State == "gathering") l.State = "full";
        Dir("lobby.upsert", lobbyId: l.Id, lobby: l);
    }
    Lobby NewLobby(Player host, string mode)
    {
        var l = new Lobby { Id = Guid.NewGuid().ToString("N")[..16], Mode = mode, Size = Store.Capacity(mode), Build = host.Build, HostId = host.SteamId, HostName = host.Name };
        Store.Lobbies[l.Id] = l;
        return l;
    }
    object PartyState(Player p)
    {
        Party? pt = p.PartyId != null && Store.Parties.TryGetValue(p.PartyId, out var x) ? x : null;
        object Member(string id) { Store.BySteam.TryGetValue(id, out var q); return new { steamId = id, name = q?.Name ?? id, status = q?.Status ?? "offline", version = q?.Version ?? "" }; }
        var incoming = Store.Parties.Values.Where(z => z.Invites.Contains(p.SteamId)).Select(z =>
        {
            Store.BySteam.TryGetValue(z.Leader, out var lp);
            return new { partyId = z.Id, fromSteamId = z.Leader, fromName = lp?.Name ?? z.Leader, size = z.Members.Count };
        }).ToArray();
        return new
        {
            party = pt == null ? null : new { id = pt.Id, leader = pt.Leader, members = pt.Members.Select(Member).ToArray(), invites = pt.Invites.Select(Member).ToArray(), search = (object?)null },
            incoming,
        };
    }
    void PartyNews(Party pt)
    {
        foreach (var id in pt.Members.Concat(pt.Invites).Distinct())
            if (Store.BySteam.TryGetValue(id, out var q)) To(q, "PartyChanged", PartyState(q));
    }

    // ---------- connection ----------
    public override async Task OnDisconnectedAsync(Exception? e)
    {
        lock (Store.Lock)
        {
            if (Store.ByConn.Remove(Context.ConnectionId, out var p) && Store.BySteam.TryGetValue(p.SteamId, out var cur) && cur == p)
            {
                if (p.LobbyId != null && Store.Lobbies.TryGetValue(p.LobbyId, out var l) && l.State != "starting") Remove(p, l, "left");
                Store.BySteam.Remove(p.SteamId);
                Dir("player.removed", p.SteamId);
                _log.LogInformation("bye {name} ({id})", p.Name, p.SteamId);
            }
        }
        await Flush();
        await base.OnDisconnectedAsync(e);
    }

    Task<object> Hello(string steamId, string name, string compat, string version, string pack)
    {
        if (string.IsNullOrWhiteSpace(steamId) || steamId.Length > 32) throw new HubException("bad_identity");
        lock (Store.Lock)
        {
            if (Store.BySteam.TryGetValue(steamId, out var old)) { Store.ByConn.Remove(old.Conn); old.Conn = Context.ConnectionId; old.Name = Clip(name, 64); old.Build = Clip(compat, 128); old.Version = Clip(version, 32); old.Pack = Clip(pack, 64); Store.ByConn[old.Conn] = old; }
            else
            {
                var p = new Player { Conn = Context.ConnectionId, SteamId = steamId, Name = Clip(name, 64), Build = Clip(compat, 128), Version = Clip(version, 32), Pack = Clip(pack, 64) };
                Store.ByConn[p.Conn] = p; Store.BySteam[steamId] = p;
                Dir("player.upsert", steamId, p.Online());
            }
            _log.LogInformation("hello {name} ({id}) build {b}", name, steamId, Clip(compat, 16));
        }
        return Task.FromResult<object>(new { ok = true });
    }
    public async Task<object> HelloKeyed(string steamId, string name, string compat, string version, string pack, string key) { var r = await Hello(steamId, name, compat, version, pack); await Flush(); return r; }
    public async Task<object> HelloUnverified(string steamId, string name, string compat, string version, string pack) { var r = await Hello(steamId, name, compat, version, pack); await Flush(); return r; }

    public async Task<object?> ReportPresence(string place, string pack)
    {
        lock (Store.Lock)
        {
            var p = Me(); p.Pack = Clip(pack, 64);
            var st = (place ?? "menu").ToLowerInvariant() switch { "battle" or "ingame" => "battle", "lobby" or "inlobby" => "lobby", _ => p.LobbyId != null ? "lobby" : p.SearchMode != null ? "searching" : "menu" };
            SetStatus(p, st);
        }
        await Flush(); return null;
    }

    public object GetSessionState()
    {
        lock (Store.Lock)
        {
            var p = Me();
            return new { status = p.Status, isSearching = p.SearchMode != null, lobbyId = p.LobbyId, party = PartyState(p) };
        }
    }

    public object GetOnlinePlayers() { lock (Store.Lock) return Store.BySteam.Values.Select(p => p.Online()).ToArray(); }

    public object GetLobbyList(string compat)
    {
        lock (Store.Lock) return Store.Lobbies.Values.Where(l => l.Open && l.State != "closed").Select(l => l.Row(compat == "?" ? null : compat)).ToArray();
    }

    public object SubscribeDirectory(string compat)
    {
        lock (Store.Lock)
        {
            var p = Me(); p.Dir = true;
            return new { revision = Store.Revision, players = Store.BySteam.Values.Select(x => x.Online()).ToArray(), lobbies = Store.Lobbies.Values.Where(l => l.Open && l.State != "closed").Select(l => l.Row(p.Build)).ToArray() };
        }
    }

    public async Task<object?> FindMatch(string mode)
    {
        mode = Clip(mode, 8);
        lock (Store.Lock)
        {
            var p = Me();
            if (p.LobbyId != null) throw new HubException("leave_lobby_first");
            p.SearchMode = mode;
            SetStatus(p, "searching");
            var l = Store.Lobbies.Values.Where(x => x.Open && x.State == "gathering" && !x.Full && x.Mode == mode && x.Build == p.Build && !x.Banned.Contains(p.SteamId))
                .OrderByDescending(x => x.Members.Count).FirstOrDefault();
            bool host = l == null;
            l ??= NewLobby(p, mode);
            Join(p, l, host);
            To(p, "MatchFound", new { lobbyId = l.Id, mode = l.Mode });
            // Group: the leader's search brings the members along (the client follows a MatchFound when it is not the leader).
            if (p.PartyId != null && Store.Parties.TryGetValue(p.PartyId, out var pt) && pt.Leader == p.SteamId)
                foreach (var id in pt.Members.Where(id => id != p.SteamId))
                    if (Store.BySteam.TryGetValue(id, out var q) && q.LobbyId == null && !l.Full) { Join(q, l, false); To(q, "MatchFound", new { lobbyId = l.Id, mode = l.Mode }); }
            _log.LogInformation("find {name} {mode}: {what} {id}", p.Name, mode, host ? "hosts" : "joins", l.Id);
        }
        await Flush(); return null;
    }

    public async Task<object?> CancelFind()
    {
        lock (Store.Lock) { var p = Me(); p.SearchMode = null; if (p.LobbyId == null) SetStatus(p, "menu"); }
        await Flush(); return null;
    }

    public async Task<object?> JoinOpenLobby(string lobbyId)
    {
        lock (Store.Lock)
        {
            var p = Me();
            if (!Store.Lobbies.TryGetValue(lobbyId ?? "", out var l) || l.State == "closed") throw new HubException("no_lobby");
            if (l.Banned.Contains(p.SteamId)) throw new HubException("not_available");
            if (l.Full) throw new HubException("lobby_full");
            Join(p, l, false);
            To(p, "MatchFound", new { lobbyId = l.Id, mode = l.Mode });
        }
        await Flush(); return null;
    }

    // Host already made the native lobby: register it and return the lobby id (string).
    public async Task<string> OpenExistingLobby(string mode, int team, JsonElement report)
    {
        string id;
        lock (Store.Lock)
        {
            var p = Me();
            Lobby l;
            if (p.LobbyId != null && Store.Lobbies.TryGetValue(p.LobbyId, out var cur) && cur.HostId == p.SteamId) l = cur;
            else { if (p.LobbyId != null && Store.Lobbies.TryGetValue(p.LobbyId, out var o)) Remove(p, o, "moved"); l = NewLobby(p, Clip(mode, 8)); Join(p, l, true, Math.Clamp(team, 0, 1)); }
            ApplyReport(l, report);
            id = l.Id;
            ToLobby(l, "LobbyStateChanged", l.State_());
            Dir("lobby.upsert", lobbyId: l.Id, lobby: l);
            _log.LogInformation("open lobby {id} by {name} {mode} {map}", l.Id, p.Name, l.Mode, l.Scenario);
        }
        await Flush(); return id;
    }

    static void ApplyReport(Lobby l, JsonElement r)
    {
        if (r.ValueKind != JsonValueKind.Object) return;
        if (r.TryGetProperty("invite", out var inv) && inv.ValueKind == JsonValueKind.Object) l.Invite = inv.Clone();
        if (r.TryGetProperty("scenario", out var s) && s.ValueKind == JsonValueKind.String) l.Scenario = Clip(s.GetString(), 128);
        if (r.TryGetProperty("playerCount", out var c) && c.TryGetInt32(out var ci)) l.PlayerCount = ci;
        if (r.TryGetProperty("slotsA", out var a) && a.TryGetInt32(out var ai)) l.SlotsA = ai;
        if (r.TryGetProperty("slotsB", out var bb) && bb.TryGetInt32(out var bi)) l.SlotsB = bi;
    }

    public async Task<object> JoinLobby(string lobbyId)
    {
        object roster;
        lock (Store.Lock)
        {
            var p = Me();
            if (!Store.Lobbies.TryGetValue(lobbyId ?? "", out var l) || l.State == "closed") throw new HubException("no_lobby");
            if (l.Members.All(x => x.SteamId != p.SteamId)) { if (l.Full) throw new HubException("lobby_full"); Join(p, l, false); }
            roster = l.Roster();
            if (l.Invite != null && l.HostId != p.SteamId) To(p, "JoinGameServer", new { lobbyId = l.Id, invite = l.Invite });
        }
        await Flush(); return roster;
    }

    public async Task<object?> ReportGameLobby(string lobbyId, JsonElement report)
    {
        lock (Store.Lock)
        {
            var p = Me();
            if (!Store.Lobbies.TryGetValue(lobbyId ?? "", out var l)) throw new HubException("no_lobby");
            if (l.HostId != p.SteamId) throw new HubException("not_host");
            bool first = l.Invite == null;
            ApplyReport(l, report);
            if (l.Invite != null)
                foreach (var m in l.Members.Where(m => !m.Host && (first || !m.Joined)))
                    if (Store.BySteam.TryGetValue(m.SteamId, out var q)) To(q, "JoinGameServer", new { lobbyId = l.Id, invite = l.Invite });
            ToLobby(l, "LobbyStateChanged", l.State_());
            Dir("lobby.upsert", lobbyId: l.Id, lobby: l);
        }
        await Flush(); return null;
    }

    public async Task<object?> ConfirmJoined(string lobbyId)
    {
        lock (Store.Lock)
        {
            var p = Me();
            if (Store.Lobbies.TryGetValue(lobbyId ?? "", out var l) && l.Members.FirstOrDefault(x => x.SteamId == p.SteamId) is { } m)
            {
                m.Joined = true;
                ToLobby(l, "LobbyStateChanged", l.State_());
            }
        }
        await Flush(); return null;
    }

    public async Task<object?> ReportStarted(string lobbyId)
    {
        lock (Store.Lock)
        {
            if (Store.Lobbies.TryGetValue(lobbyId ?? "", out var l))
            {
                l.State = "starting";
                ToLobby(l, "MatchStarted", new { lobbyId = l.Id });
                foreach (var m in l.Members) if (Store.BySteam.TryGetValue(m.SteamId, out var q)) { q.LobbyId = null; SetStatus(q, "battle"); }
                Store.Lobbies.Remove(l.Id);
                Dir("lobby.removed", lobbyId: l.Id);
                _log.LogInformation("lobby {id} started ({n} players, {map})", l.Id, l.Members.Count, l.Scenario);
            }
        }
        await Flush(); return null;
    }

    public async Task<object?> ReportFailed(string lobbyId, string reason)
    {
        lock (Store.Lock)
        {
            var p = Me();
            if (Store.Lobbies.TryGetValue(lobbyId ?? "", out var l)) Remove(p, l, Clip(reason, 64));
        }
        await Flush(); return null;
    }

    public async Task<object?> LeaveLobby(string lobbyId)
    {
        lock (Store.Lock)
        {
            var p = Me(); p.SearchMode = null;
            if (Store.Lobbies.TryGetValue(lobbyId ?? p.LobbyId ?? "", out var l)) Remove(p, l, "left");
            else if (p.LobbyId == null) SetStatus(p, "menu");
        }
        await Flush(); return null;
    }

    public async Task<object?> ReportReturnedToMenu()
    {
        lock (Store.Lock) { var p = Me(); if (p.LobbyId == null) { p.SearchMode = null; SetStatus(p, "menu"); } }
        await Flush(); return null;
    }

    public object? WatchLobby(string lobbyId, string compat)
    {
        lock (Store.Lock)
        {
            if (!Store.Lobbies.TryGetValue(lobbyId ?? "", out var l) || l.Invite == null) throw new HubException("not_watchable");
            return l.Invite;
        }
    }

    public async Task<object?> BanFromLobby(string lobbyId, string steamId)
    {
        lock (Store.Lock)
        {
            var p = Me();
            if (Store.Lobbies.TryGetValue(lobbyId ?? "", out var l) && l.HostId == p.SteamId && steamId != p.SteamId)
            {
                l.Banned.Add(steamId);
                if (Store.BySteam.TryGetValue(steamId, out var q)) { To(q, "LobbyBanned", new { lobbyId = l.Id }); Remove(q, l, "banned"); }
            }
        }
        await Flush(); return null;
    }

    public async Task<object> PartyAction(string action, string? to, string? partyId)
    {
        object result;
        lock (Store.Lock)
        {
            var p = Me();
            Party? pt = p.PartyId != null && Store.Parties.TryGetValue(p.PartyId, out var x) ? x : null;
            switch (action)
            {
                case "state": break;
                case "invite":
                    if (string.IsNullOrEmpty(to) || !Store.BySteam.ContainsKey(to)) throw new HubException("target_offline");
                    if (pt == null) { pt = new Party { Leader = p.SteamId }; pt.Members.Add(p.SteamId); Store.Parties[pt.Id] = pt; p.PartyId = pt.Id; }
                    if (pt.Leader != p.SteamId) throw new HubException("not_leader");
                    if (pt.Members.Count + pt.Invites.Count >= 5) throw new HubException("party_full");
                    if (!pt.Invites.Contains(to) && !pt.Members.Contains(to)) pt.Invites.Add(to);
                    PartyNews(pt); break;
                case "accept":
                    if (partyId == null || !Store.Parties.TryGetValue(partyId, out var ap) || !ap.Invites.Remove(p.SteamId)) throw new HubException("no_invite");
                    if (pt != null && pt != ap) Leave(p, pt);
                    ap.Members.Add(p.SteamId); p.PartyId = ap.Id; PartyNews(ap); break;
                case "decline":
                    if (partyId != null && Store.Parties.TryGetValue(partyId, out var dp)) { dp.Invites.Remove(p.SteamId); PartyNews(dp); }
                    break;
                case "kick":
                    if (pt == null || pt.Leader != p.SteamId) throw new HubException("not_leader");
                    if (to != null && pt.Members.Remove(to) | pt.Invites.Remove(to))
                    {
                        if (Store.BySteam.TryGetValue(to, out var kq)) { kq.PartyId = null; To(kq, "PartyChanged", PartyState(kq)); }
                        PartyNews(pt);
                    }
                    break;
                case "leave":
                    if (pt != null) Leave(p, pt);
                    break;
                default: throw new HubException("bad_action");
            }
            result = PartyState(p);
        }
        await Flush(); return result;
    }

    void Leave(Player p, Party pt)
    {
        pt.Members.Remove(p.SteamId); p.PartyId = null;
        if (pt.Members.Count == 0) { Store.Parties.Remove(pt.Id); return; }
        if (pt.Leader == p.SteamId) pt.Leader = pt.Members[0];
        PartyNews(pt);
    }
}
