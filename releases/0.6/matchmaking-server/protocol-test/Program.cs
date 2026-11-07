// Raw SignalR JSON client that talks like ArrowQueue's HubLink: direct WebSocket, 0x1e frames, no negotiate.
using System.Net.WebSockets; using System.Text; using System.Text.Json; using System.Collections.Concurrent;
var url = args.Length > 0 ? args[0] : "ws://127.0.0.1:8651/hubs/game";
int fails = 0; void Check(bool ok, string what) { Console.WriteLine((ok ? "PASS " : "FAIL ") + what); if (!ok) fails++; }
var a = await C.Open(url, "76561190000000001", "Alpha"); var b = await C.Open(url, "76561190000000002", "Bravo");
const string build = "fa-0.6-test";
var ha = await a.Invoke("HelloKeyed", a.Id, a.Name, build, "0.10.31", "", "k"); Check(ha.GetProperty("ok").GetBoolean(), "HelloKeyed ok");
await b.Invoke("HelloUnverified", b.Id, b.Name, build, "0.10.31", "FA 0.6.0-dev.11");
var snap = await a.Invoke("SubscribeDirectory", build); Check(snap.GetProperty("players").GetArrayLength() == 2, "directory snapshot has 2 players");
var online = await b.Invoke("GetOnlinePlayers");
var fb = online.EnumerateArray().First(x => x.GetProperty("player").GetProperty("steamId").GetString() == b.Id).GetProperty("player"); Check(fb.GetProperty("version").GetString() == "0.6.0-dev.11" && fb.GetProperty("pack").GetString() == "", "FA player shows FA version, no pack label"); Check(online.GetArrayLength() == 2 && online[0].GetProperty("player").GetProperty("name").GetString() != null, "GetOnlinePlayers 2 with names");
await a.Invoke("FindMatch", "1v1");
var mfa = await a.Wait("MatchFound"); var lobby = mfa.GetProperty("lobbyId").GetString()!; Check(lobby.Length > 0, "A MatchFound " + lobby);
var ra = await a.Invoke("JoinLobby", lobby); Check(ra[0].GetProperty("isHost").GetBoolean(), "A is host in roster");
var list = await b.Invoke("GetLobbyList", build); Check(list.GetArrayLength() == 1 && list[0].GetProperty("sameBuild").GetBoolean(), "B sees 1 same-build lobby");
await a.Invoke("ReportGameLobby", lobby, JsonSerializer.SerializeToElement(new { invite = new { ip = "1.2.3.4", password = "pw", md5 = "m", port = 7777, proxyPort = 0, instanceId = 1, lobbyType = 3 }, scenario = "TestMap", playerCount = 1, slotsA = 0, slotsB = 1 }));
await b.Invoke("FindMatch", "1v1");
var mfb = await b.Wait("MatchFound"); Check(mfb.GetProperty("lobbyId").GetString() == lobby, "B matched into A's lobby");
var rb = await b.Invoke("JoinLobby", lobby); Check(rb.GetArrayLength() == 2, "roster 2 players");
var jg = await b.Wait("JoinGameServer"); Check(jg.GetProperty("invite").GetProperty("ip").GetString() == "1.2.3.4", "B got host invite");
var pj = await a.WaitWhere("PlayerJoined", e => e.GetProperty("player").GetProperty("steamId").GetString() == b.Id); Check(pj.GetProperty("player").GetProperty("steamId").GetString() == b.Id, "A told B joined");
await b.Invoke("ConfirmJoined", lobby);
await a.Invoke("ReportStarted", lobby);
var ms = await b.Wait("MatchStarted"); Check(ms.GetProperty("lobbyId").GetString() == lobby, "B MatchStarted");
var sess = await b.Invoke("GetSessionState"); Check(sess.GetProperty("status").GetString() == "battle", "B status battle");
var upd = await a.Wait("DirectoryUpdated"); Check(upd.GetProperty("updates").GetArrayLength() >= 1, "directory updates arrive");
var inv = await a.Invoke("PartyAction", "invite", b.Id, null); Check(inv.GetProperty("party").GetProperty("members").GetArrayLength() == 1, "party created");
var bst = await b.Invoke("PartyAction", "state", null, null); var pid = bst.GetProperty("incoming")[0].GetProperty("partyId").GetString();
var acc = await b.Invoke("PartyAction", "accept", null, pid); Check(acc.GetProperty("party").GetProperty("members").GetArrayLength() == 2, "party accept → 2 members");
try { await a.Invoke("JoinOpenLobby", "nope"); Check(false, "error expected"); } catch (Exception e) { Check(e.Message.Contains("no_lobby"), "error code text: " + e.Message); }
await b.Close();
var gone = await a.WaitWhere("DirectoryUpdated", e => e.GetProperty("updates")[0].GetProperty("kind").GetString() == "player.removed"); Check(gone.ValueKind == JsonValueKind.Object, "player.removed on disconnect");
Console.WriteLine(fails == 0 ? "ALL PASS" : $"{fails} FAILED"); return fails;

sealed class C
{
    public string Id = "", Name = ""; ClientWebSocket ws = new(); int inv; 
    ConcurrentDictionary<string, TaskCompletionSource<JsonElement>> pending = new();
    List<(string t, JsonElement a)> events = new(); SemaphoreSlim evs = new(0);
    public static async Task<C> Open(string url, string id, string name)
    {
        var c = new C { Id = id, Name = name }; c.ws.Options.SetRequestHeader("User-Agent", "ArrowQueue/0.10.31");
        await c.ws.ConnectAsync(new Uri(url), default); await c.Send("{\"protocol\":\"json\",\"version\":1}");
        _ = c.Loop(); await Task.Delay(200); return c;
    }
    Task Send(string s) => ws.SendAsync(Encoding.UTF8.GetBytes(s + "\u001e"), WebSocketMessageType.Text, true, default);
    async Task Loop()
    {
        var buf = new byte[1 << 16]; var sb = new StringBuilder();
        while (ws.State == WebSocketState.Open)
        {
            WebSocketReceiveResult r; try { r = await ws.ReceiveAsync(buf, default); } catch { return; }
            sb.Append(Encoding.UTF8.GetString(buf, 0, r.Count));
            var all = sb.ToString(); int i;
            while ((i = all.IndexOf('\u001e')) >= 0)
            {
                var msg = all[..i]; all = all[(i + 1)..];
                if (msg.Length == 0) continue; var j = JsonDocument.Parse(msg).RootElement;
                int type = j.TryGetProperty("type", out var t) ? t.GetInt32() : 0;
                if (type == 3) { var id = j.GetProperty("invocationId").GetString()!; if (pending.TryRemove(id, out var tcs)) { if (j.TryGetProperty("error", out var er)) tcs.SetException(new Exception(er.GetString())); else tcs.SetResult(j.TryGetProperty("result", out var res) ? res.Clone() : default); } }
                else if (type == 1) { lock (events) events.Add((j.GetProperty("target").GetString()!, j.GetProperty("arguments").GetArrayLength() > 0 ? j.GetProperty("arguments")[0].Clone() : default)); evs.Release(); }
            }
            sb.Clear(); sb.Append(all);
        }
    }
    public async Task<JsonElement> Invoke(string m, params object?[] a)
    {
        var id = (++inv).ToString(); var tcs = new TaskCompletionSource<JsonElement>(); pending[id] = tcs;
        await Send(JsonSerializer.Serialize(new { type = 1, invocationId = id, target = m, arguments = a }));
        var done = await Task.WhenAny(tcs.Task, Task.Delay(5000)); if (done != tcs.Task) throw new Exception("timeout " + m); return await tcs.Task;
    }
    public Task<JsonElement> Wait(string t) => WaitWhere(t, _ => true);
    public async Task<JsonElement> WaitWhere(string t, Func<JsonElement, bool> f)
    {
        var until = DateTime.UtcNow.AddSeconds(5);
        while (DateTime.UtcNow < until)
        {
            lock (events) { var k = events.FindIndex(e => e.t == t && f(e.a)); if (k >= 0) { var e = events[k]; events.RemoveAt(k); return e.a; } }
            await evs.WaitAsync(200);
        }
        throw new Exception("no event " + t);
    }
    public Task Close() => ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", default);
}
