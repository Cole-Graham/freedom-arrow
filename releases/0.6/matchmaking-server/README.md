# FAQueue — Freedom Arrow matchmaking hub

A small ASP.NET Core 8 SignalR hub that speaks the protocol of ArrowQueue 0.10.31 (ActualArrow's matchmaking mod, shipped unchanged in 0.6). It keeps the online list, the lobby directory and groups, and passes the host's native lobby invite to the players who join. It does not touch game data. Match statistics that ArrowQueue posts are kept in `match-stats.jsonl` beside the app.

Now (7 November 2026, Osama): runs on Sam's deck as the user service `faqueue` on 127.0.0.1:8651, published through Tailscale Funnel at `https://cyberdeck.tailf7ad82.ts.net/hubs/game`. Move it to a proper server when friends of friends play; then change the address in `source/runtime-qa/ThirdPartyGuard.cs`.

Players are not verified: anyone with the mod and the address can sign in with any Steam id.

## Run

```
dotnet publish hub -c Release -o app
FAQUEUE_URL=http://127.0.0.1:8651 dotnet app/FAQueue.dll
```

## Test (two fake ArrowQueue players)

```
dotnet run --project protocol-test -c Release -- ws://127.0.0.1:8651/hubs/game
```

Expect `ALL PASS` (17 checks).

## Undo on the deck

```
systemctl --user disable --now faqueue && rm ~/.config/systemd/user/faqueue.service && systemctl --user daemon-reload
sudo tailscale funnel --https=443 --set-path /hubs off
```
