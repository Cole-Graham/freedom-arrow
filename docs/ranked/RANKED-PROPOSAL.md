# Freedom Arrow ranked — proposal

Lateralus asked on 22 November 2026 for a proposal for our own ranked system, based on `docs/simple-elo.md`. It uses the vanilla Broken Arrow rank names and epaulet icons, plus a new Chinese Army set. Status: **proposal only; nothing is built.**

## Summary

- **Rating:** `simple-elo.md` exactly as written: start 1000, K 40, divisor 400, floor 600, win bonus below 1500.
- **Ranks:** vanilla has 20 ranks in each epaulet set. Ranks 1–18 are cut into Elo bands from 0 to 2170. Rank 19 is leaderboard places 2–3 and rank 20 is place 1 (players at 2170 or more), which is the `simple-elo.md` top-three rule.
- **Epaulet sets:** US Army, US Marines, Russian Army and Russian VDV use the vanilla icons. A new Chinese Army (PLA) set has 20 icons that we draw in the same style. The set only changes how a rank looks; every set has the same 20 ranks and the same Elo bands.
- **Hosting:** possible on what we already run. The ranked queue goes into FAQueue, our lobby server on the deck. It already has a find-match queue, lobby creation through the host's game, and match-result reports. Games stay on Broken Arrow's own servers, as today. The extra load is small (see Hosting).
- **UI:** a Ranked card on the Play screen (FA patch + menu-art splash), a Ranked menu (find match, your rank, recent results, rank ladder) and a Leaderboard that shows epaulets instead of #1, #2, #3. Mock-ups are in `docs/ranked/`.

---

## 1. Rank ladder

### How the bands are cut

- Rank 1 is 0–1000, so every new player starts there (`simple-elo.md`: Private covers everything through 1000).
- Ranks 2–17 split 1001–2169 into 16 bands. Each band is 12% wider than the one before (27 points at the bottom, 150 at the top), the same idea as the growing grade widths in `simple-elo.md`.
- Rank 18 is 2170 and above.
- Ranks 19 and 20 are not Elo bands. They go to leaderboard places 2–3 and place 1, and only to players at 2170 or above. Everyone else at 2170+ stays rank 18.
- The field average settles near 1500 (`simple-elo.md`), which is rank 12: Major in the US and Russian sets.

### All five sets

US Army and US Marines use the same vanilla names (`ui_rankname_lvlN_eng_base`); only the icons differ. Russian Army and Russian VDV share `ui_rankname_lvlN_rus_base`.

| Rank | Elo | US Army / US Marines | Russian Army / VDV | Chinese Army (new) |
| ---: | --- | --- | --- | --- |
| 1 | 0–1000 | Private | Ryadovoj | 列兵 (Private) |
| 2 | 1001–1027 | Private first class | Efrejtor | 上等兵 (Private first class) |
| 3 | 1028–1058 | Sergeant | Mladshij serzhant | 下士 (Corporal) |
| 4 | 1059–1092 | Staff sergeant | Serzhant | 中士 (Sergeant) |
| 5 | 1093–1131 | Sergeant first class | Starshij Serzhant | 上士 (Staff sergeant) |
| 6 | 1132–1174 | Master sergeant | Starshina | 四级军士长 (Master sergeant 4th class) |
| 7 | 1175–1222 | First sergeant | Praporshhik | 三级军士长 (Master sergeant 3rd class) |
| 8 | 1223–1276 | Sergeant major | Starshij praporshhik | 二级军士长 (Master sergeant 2nd class) |
| 9 | 1277–1336 | Second lieutenant | Mladshij lejtenant | 一级军士长 (Master sergeant 1st class) |
| 10 | 1337–1404 | First lieutenant | Lejtenant | 少尉 (Second lieutenant) |
| 11 | 1405–1480 | Captain | Kapitan | 中尉 (First lieutenant) |
| 12 | 1481–1565 | Major | Major | 上尉 (Captain) |
| 13 | 1566–1660 | Lieutenant colonel | Podpolkovnik | 少校 (Major) |
| 14 | 1661–1766 | Colonel | Polkovnik | 中校 (Lieutenant colonel) |
| 15 | 1767–1886 | Brigadier general | Brigadny`j general | 上校 (Colonel) |
| 16 | 1887–2019 | Major general | General major | 大校 (Senior colonel) |
| 17 | 2020–2169 | Lieutenant general | General lejtenant | 少将 (Major general) |
| 18 | 2170 and above | General | General polkovnik | 中将 (Lieutenant general) |
| 19 | 2170+ and leaderboard place 2–3 | General of the army | General armii | 上将 (General) |
| 20 | 2170+ and leaderboard place 1 | General of the armies | Marshal | 元帅 (Marshal) |

### Notes on the Chinese set

- These are the current PLA ranks: 2 enlisted ranks, 7 NCO ranks (the 2022 names: 下士, 中士, 上士, then 四级 to 一级军士长) and 10 officer ranks from 少尉 to 上将. Rank 20 is 元帅 (Marshal), a historical rank (1955), used like vanilla's Marshal and General of the armies.
- Because the PLA has 9 enlisted/NCO ranks where vanilla has 8, PLA officers start at rank 10 instead of 9. So the average player (rank 12) is 上尉 Captain in this set. The top three ranks line up exactly with `simple-elo.md`: 中将 Lieutenant general at 2170, 上将 General for places 2–3, 元帅 Marshal for place 1.
- Lateralus accepted officers starting at rank 10 (22 Nov).
- **Icons:** 20 new 72×128 sprites in the same flat style as `Epaulet_*_N` (the 2007-pattern PLA shoulder boards: NCO chevrons, officer stripes and stars, general pine branches). They are not drawn yet, and they must be checked against the official insignia before release.

### Vanilla assets used

- Icons: `Epaulet_USA_base_1..20` (US Army), `Epaulet_USA_1..20` (US Marines), `Epaulet_RUS_base_1..20` (Russian Army), `Epaulet_RUS_1..20` (Russian VDV), 72×128 each, from the game's sprite atlas. They were already extracted on the deck (asset ripper export, 7 Nov).
- The game has an `EpauletType` enum: UsaBase 1, UsaUSMC 2, RusBase 50, RusVDV 51, RusVMF 52 (unused). Each `EpauletData` is a sprite plus a rank-name key.
- **Default set (Lateralus: yes):** a player's FA epaulet set starts as the one they chose in vanilla: UsaBase → US Army, UsaUSMC → US Marines, RusBase → Russian Army, RusVDV → Russian VDV, and RusVMF (unused) → Russian Army. The PLA set has no vanilla equivalent, so players pick it themselves. Vanilla unlocks Marines and VDV through campaign missions; in FA ranked all five sets are free.

---

## 2. Rating rules

`simple-elo.md` as written, with these choices for our game:

- **Modes at launch (Lateralus, 22 Nov):** 1v1, 3v3 and 5v5. No 2v2.
- **Ladders (Lateralus: agreed):** a 1v1 ladder and one team ladder shared by 3v3 and 5v5, with a rating per player on each ladder.
- **Queueing as a party (Lateralus, 22 Nov):** players can queue together, using the parties FAQueue already has (the leader's search brings the members along).
  - **Two separate queues (Lateralus, 22 Nov: "1v1 should be a completely different queue"):**
    - **1v1 queue:** solo players only, 1v1 matches only, own 1v1 ladder.
    - **Team queue:** solos and parties. It forms a 3v3 or a 5v5, never a 1v1. A solo in the team queue never gets a 1v1. Parties of 4–5 get only 5v5. The matcher tries 5v5 first, so 10 waiting players make one 5v5 and not a 3v3 with 4 left over.
    - Measured on the test hub, 22 Nov: 2 team solos + 2 1v1 players → only the 1v1 pair is matched; 6 team solos → 3v3; 10 team solos → 5v5; a party of 2 in the 1v1 queue is refused.
  - **Matching:** the matchmaker fills each side with whole parties, never splitting one. It first looks for opponents with similar party sizes (a 5-stack against a 5-stack or a 4+1); after 3 minutes it accepts any mix. The two sides are balanced by average rating.
  - **Party rating:** the party's average rating is used for matching. Each member's own rating changes after the match, using the team averages (as above).
  - **Boost limit:** party members must be within 500 Elo of each other in ranked, so a high player cannot carry a new account up the ladder.
- **Team games:** the `simple-elo.md` "team rating" is the average of the players' ratings. Each player's change is split by their own rating (option C, Lateralus 22 Nov): a winner's share is K × (1 − expected score of their rating against the losers' average), a loser's share is K × (expected score against the winners' average), and each side's shares are scaled so the side's total equals the old same-for-all change × players. Favourites gain less and lose more; underdogs the reverse; the match adds no points. 1v1 is unchanged. A deserter on the winning team loses K × his expected score against the losers' average. The win bonus is computed from each winner's own rating before the match. The bonus is also scaled by the ladder average (full at 1400 or lower, 0 at 1500; `simple-elo.md`, Ladder-average scale).
- **What counts as a result:** the mod already reports each match (players, teams, map, winner, length) to FAQueue (`match-stats.jsonl`). A ranked result counts only when at least one report from each side agrees on the winner and the player list. If they disagree, the match is marked disputed, nothing changes and it is logged for admins.
- **Leavers:** a player who leaves before the end loses their own rating, as a loss. The rest of the match is scored normally.
- **Draws** (Freedom Arrow lead under 10% at time-out): no change.
- **Ranked rules are fixed:** FA conquest 300, 45 min, a ranked map pool per size, and the same FA build on every client. The server checks this before it starts the match. Starting pools are the FA maps played online so far:
  - [1v1] Dead Center, Kadaga, Jelgava, Klaipeda, Chernyakhovsky
  - [3v3] Baltiisk, Bay of Winds, Dam
  - [5v5] Airport, Oil Rush, Cold Harbor
- **Queue size for 5v5:** a 5v5 needs 10 players searching at the same time. With 30–70 players online, the Elo window has to widen faster for 5v5. Proposal: ±150 at first, any rating after 3 minutes, and teams balanced by total rating.
- **Seasons (Lateralus: yes):** each season keeps its final leaderboard and gives every player a badge with their best rank of that season. At the start of the next season everyone goes back to 1000. Length: 2 months (Lateralus, 22 Nov).

---

## 3. Hosting: possible, and cheap

**Recommended: FAQueue on the deck**, the lobby server that runs Mod lobbies today.

- **What it already does:**
  - `FindMatch(mode)` / `CancelFind` queues players.
  - The host's game creates the native lobby (`OpenExistingLobby`), and the others join through the game's own invite (`JoinGameServer`).
  - Parties are supported.
  - Match results already arrive in `match-stats.jsonl`.
  - Players reach it through `freedomarrow.app/hubs/*` (Cloudflare Worker → deck), which also works from mainland China.
- **Measured today:** the FAQueue process uses about 270 MB of memory and about 0.5% of one CPU core on average over 27 hours. That's with 33 players connected right now and a peak of 69.
- **What ranked adds:**
  - A ratings file (SQLite, a few MB for thousands of players).
  - A matching pass about once a second: pick pairs or teams by Elo, widening the window from ±100 to ±400 the longer someone waits.
  - Result checks when a match ends.
  - A leaderboard file written to R2 every 10 minutes. The website and the game read that file, so leaderboard views put no load on the deck.
- **Estimate:** under 20 MB more memory and well under 1% CPU at our numbers. Even 1,000 players searching at once is a small job for one process. The games themselves run on Broken Arrow's servers, as now.
- **Osama's PC (Vengeance):** not recommended as the host. It's off about half the day, and the queue has to be up whenever players are. It could be a cold backup.
- **Cloudflare only:** possible with Durable Objects (paid plan) and a rewrite of the queue. Not needed, because the deck already does this job.
- **Risks:**
  - If the deck is down, ranked is down. That's the same as Mod lobbies today.
  - Back up the ratings file to R2 every hour.

### Security (must have before launch)

- **Identity:** ranked must accept only verified Steam IDs. FAQueue has a keyed hello and an unverified hello today. Ranked needs real verification, for example a Steam ticket check or a one-time link through the website. Without it, someone can play under another player's ID.
- **Trust:** results need agreement from both sides (above). Disputes and odd patterns, such as repeat opponents or very short wins, go to the admin page.

---

## 4. Game client (runtime DLL)

- **Play screen:** a 5th card, "Ranked". It's added the same way we add the website banner and music-pack button today.
  - Art: the FA patch at the top, with the menu-art splash (the flag raising) as the background.
  - Text: "Test your skill against other players".
  - A small season tag. Mock-up: `docs/ranked/mock-1-play-card.jpg`.
- **Ranked menu**, with tabs **Ranked · Leaderboard · Rank ladder**. Mock-up: `mock-2-ranked-menu.jpg`.
  - **Find a ranked match:** mode (1v1 / 3v3 / 5v5), map pool, deck, region, a big FIND MATCH button with the patch, and the number searching.
  - **Your rank:** large epaulet, rank name, Elo, progress bar to the next rank, matches, win rate and best Elo, plus the epaulet set picker (US Army, US Marines, Russian Army, Russian VDV, PLA).
  - **Recent ranked matches:** W/L, map, opponent with their epaulet, Elo change.
  - **Rank ladder strip:** all 20 ranks with the Elo where each starts.
- **Leaderboard**, styled like vanilla. Mock-up: `mock-3-leaderboard.jpg`.
  - The list shows avatar, name and Elo. **The epaulet replaces #1, #2, #3**, in the set that player chose.
  - Your own rank sits in the header.
  - The profile panel shows the big epaulet, rank, Elo, progress, ranked statistics and the last 10 results.
- **Not changed:** the vanilla Elo and level in the top-right profile badge belong to Broken Arrow's own servers and stay as they are.

## 5. Work and order

1. **Server (FAQueue):** ranked queue, ratings store, result checks, leaderboard export, verified identity. About 2 days plus testing with 2 PCs.
2. **Client:** Ranked card, ranked menu, leaderboard. About 3–5 days, including in-game checks on Vengeance.
3. **PLA epaulet icons:** 20 sprites, about half a day, plus an insignia check.
4. **Website:** leaderboard page on freedomarrow.app (it reads the same R2 file). About half a day.
5. **Closed test:** team members only, ratings reset before public launch.

## Decisions (Lateralus, 22 November 2026)

- Modes at launch: 1v1, 3v3 and 5v5.
- Rank seasons: yes.
- PLA officers start at rank 10: accepted.
- The FA epaulet set defaults to the player's vanilla choice.

- Season length: 2 months.
- One shared team ladder for 3v3 and 5v5.
- Players can queue as a party; a party of 5 always plays 5v5.
- 1v1 is its own solo queue; the team queue only makes 3v3 or 5v5.

## Still open

- Nothing in the rules. Next step on your word: build the server side (FAQueue ranked queue) first, then the in-game menus.

## Ranked match flow (Lateralus 22 Nov: "go")

1. **Default deck.** Chosen in the ranked menu. The game reports to the lobby server whether it is a complete, valid deck. FIND MATCH is disabled (with the reason) until every group member has one; the group slots show a warning on members without one. Only the group leader can start the search; the server checks the decks too.
2. **Match found.** The normal Mod game flow: the host's game creates a private Scenario lobby with the server's map, everyone joins, and each player is moved to their team.
3. **Map revealed** in the lobby.
4. **Deck pick, 60 s** (server clock). Each player's default deck is selected at the start. Enemy deck info is hidden in the lobby. At the end, a player with no deck gets their default deck and is set ready.
5. **Reveal, 5 s**, then the host's game launches the match with the vanilla start call (`ChangeLobbyStatus(Launching)`) once everyone is ready.
- If not everyone has joined the game lobby within 90 s, the match is cancelled with no rating change.
- 1v1 works the same with one player per side.

## Document change log

- 2026-11-22 07:56 PST (America/Los_Angeles) — Proposal written for Lateralus: rank ladder (5 sets, 18 Elo bands + top 3), rating rules, hosting on FAQueue with measured load, client UI, mock-ups, work plan.
- 2026-11-22 08:01 PST (America/Los_Angeles) — Lateralus decisions: launch 1v1/3v3/5v5, seasons yes, PLA officers at rank 10, default set = vanilla epaulet. Map pools, 5v5 queue widening, season rules added.
- 2026-11-22 08:06 PST (America/Los_Angeles) — Lateralus: seasons 2 months, one team ladder for 3v3+5v5, party queueing (party size decides modes; 5-stack = 5v5; whole parties per side; 500 Elo boost limit).
- 2026-11-22 08:38 PST (America/Los_Angeles) — Lateralus: 1v1 is a separate solo queue; the team queue (solo or party) only makes 3v3/5v5. Test hub at freedomarrow.app/hubs/test.
- 2026-11-22 13:0x PST (America/Los_Angeles) — Lateralus: ranked match flow (default deck, 60 s hidden deck pick, reveal, automatic launch) added and built.
- 2026-11-22 13:4x PST (America/Los_Angeles) — Lateralus: win bonus scaled by the ladder average, so the ladder settles at 1500.
- 2026-11-22 14:0x PST (America/Los_Angeles) — Lateralus: option C per-player split for team games built (test hub).
