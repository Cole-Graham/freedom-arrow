# Make a Freedom Arrow 0.2 test version

**Change values in one of two files, set a new version, build, verify, install the `.bamod`, and read one log line.** Nothing here installs or launches the game for you. These steps were run on Linux; the Windows commands are not yet proven.

## What to edit

- `releases/0.3/detection-contract.json`: table values.
  - `optics_ground_tiers`: vanilla ground optics to new value. Six tiers: 500, 600, 700, 875, 1000, 1200.
  - `optics_ground_drones`: drone sensor rows 32, 33, 34. They do not follow the tiers, so change them yourself.
  - `stealth`: raw value per class. Raw is 1 / UI value, so UI 2.0 is 0.5.
  - `stealth_unit_values`: per-unit raw values that replace the class value.
  - `stealth_override_options`: per-option raw values.
- `releases/0.3/source/UserData/FreedomArrow/game-config.json`: starting points, forest damage taken, and the building damage floor and per-soldier values. Log lines: `FREEDOM_ARROW_START_POINTS`, `FREEDOM_ARROW_COVER_DAMAGE`, `FREEDOM_ARROW_BUILDING_DAMAGE`.
- `releases/0.3/source/UserData/FreedomArrow/detection-config.json`: config values, written when a battle loads. Each must be 1 to 10.
- `releases/0.3/vehicle-contract.json`: prices.

The verifier and row tests read these files, so tuning these values needs no test edit. A new kind of edit needs a matching change in `build_constants.py`, and usually in `verify.py` and `row-tests/Program.cs`.

## First-time setup (Windows, PowerShell, repository root)

Needs Python 3.11 or newer and the .NET 8 SDK. `GAME` is the install folder that contains `MelonLoader`. Launch the game once with MelonLoader first, so `MelonLoader/Il2CppAssemblies` exists.

```powershell
$env:PYTHONUTF8 = "1"
python -m venv .venv
.venv\Scripts\python -m pip install -r pipeline/requirements.txt
Copy-Item config.template.YAML config.YAML   # then set game_root in config.YAML
.venv\Scripts\python -m pipeline decrypt
```

`decrypt` writes `cache/vanilla/<build-id>/`. If a complete snapshot already exists for that build, `decrypt` keeps it and does not read the game again. A snapshot from an older pipeline can hold the wrong database copy.

The generator stops if any table differs from the 24 pins in `releases/0.1/source/UserData/FreedomArrow/compatibility.json`. If it stops:

1. Delete the snapshot and decrypt again. The cache is git-ignored and is rebuilt from the game.

   ```powershell
   Remove-Item -Recurse -Force cache/vanilla/<build-id>
   .venv\Scripts\python -m pipeline decrypt
   ```

2. A correct snapshot has 545 rows in `Units.json`. A stale one has 540, matches 6 of 24 pins, and has `Units` plaintext SHA-256 `47b65c72…`.
3. If a fresh snapshot still fails, the game build changed or its data is modified. Stop and report it. Do not bypass the check.

## Build a test version

```powershell
$env:PYTHONUTF8 = "1"
$GAME = "C:/Program Files (x86)/Steam/steamapps/common/broken_arrow"
$VANILLA = (Get-ChildItem cache/vanilla -Directory | Select-Object -First 1).FullName
.venv\Scripts\python releases/0.3/bump_version.py 0.2.0-dev.NN
.venv\Scripts\python releases/0.3/build_constants.py --vanilla-dir $VANILLA
.venv\Scripts\python releases/0.3/build.py --game-dir $GAME --dotnet dotnet
.venv\Scripts\python releases/0.3/verify.py
```

`build_constants.py` writes `constant-audit.json`, `source/UserData/FreedomArrow/constants/` and `deck-migration.json`. Git ignores them, so run it after every pull and every edit. `build.py` stops if the data is missing or for another version. A version bump still edits tracked files: commit it, or run `git restore releases/0.3 README.md` before you pull.

The archive is `releases/0.3/out/FreedomArrow-<version>.bamod`. It is git-ignored. Import it with the mod manager as usual, and do not copy it into `Mods`.

Use the next unused number, and check every remote branch first, because other branches also use numbers:

```powershell
git fetch origin
git grep -h '"version"' origin/codex/0.2-development origin/codex/0.2-split-test -- releases/0.3/mod.json
```

## Run the tests

```powershell
dotnet run --project releases/0.3/row-tests/Tests.csproj -c Release -- $VANILLA <payload>
dotnet run --project releases/0.3/economy-tests/Tests.csproj -c Release
.venv\Scripts\python -m unittest discover -s pipeline/tests
```

For `<payload>`, use `releases/0.3/build/payload/UserData/FreedomArrow`.

## Check that it worked in game

Read `MelonLoader/Latest.log` after a battle has loaded. Look for this line:

```text
FREEDOM_ARROW_DETECTION before {"apply":true,...,"after":{...}}
```

- `apply:true` and your `after` values mean the config was written.
- `apply:false` means the tables failed, so the config stayed vanilla. Look for `FREEDOM_ARROW_FAILED`.
- `FREEDOM_ARROW_DETECTION_FAILED` means the write failed and vanilla was kept.
- A correct log does not prove the range. The vision data is copied when the battle systems build, so measure in forest and in a building too.

Expected range, in displayed metres, for a target that is not firing or marked as spotted:

```text
range = 2 x optics x min(1.5, raw stealth / max(1, cover))
```

Example: 1450 optics, UI 2.0 infantry, forest cover 3 gives 483 m.

## Play with other people (dev.18, not yet run live)

Actual Arrow uses the same route: scenario lobbies, because the game's servers do not list them as anti-cheat protected. The mod checks that list and blocks hosting and joining if `Scenario` is added to it.

1. Every player installs the same `.bamod`. Compare the SHA-256. The mod does not detect a mismatch.
2. Launch through Steam with **Play Anti-Cheat Disabled**.
3. The host opens **Scenarios** on the play tab, picks `[FA] [2v2] Dead Center 0.1` or `[FA] [1v1] Dead Center 0.1` and creates a private lobby. F8 lists `[FA] [2v2] Dead Center Skirmish 0.1` and `[FA] [1v1] Dead Center Skirmish 0.1`.
4. The host invites the others. They join from the invite. The mod installs both scenarios for each player. If a joiner cannot get in, publish it to the Workshop from the host game; that step needs approval.
5. After the match, every player keeps `Latest.log`. Compare these lines:

```text
[LocalSkirmish] ONLINE_RULE: scenario lobby allowed
"match_started" with "online":true
"conquest_tick" lines: same scores on every machine
"economy_scope_prepared": perMinute 200
```

Stop and send the logs if a player disconnects or desyncs, the scores differ, or the server rejects anything.

- **Conquest scoring** needs a scenario that uses ConquestMode. On WarGoals scenarios it logs a fault and leaves native scoring running.
- **Unknown until a live match:** table sync between players, how the game's economy and deck-point reports treat our values, and who decides the final result.

## Rules

- Commit to `codex/0.2-development` and push when you commit. Fast-forward only; never force-push. Do not push to `main`.
- Online, use private scenario lobbies only. The mod blocks native Skirmish, ranked search and other lobby types, but do not try to get around that block.
- The tables and config apply in every battle mode, so all players need the same `.bamod`.
- Say which version and commit a test used, and attach `Latest.log`.

## Document change log

- 2026-11-04 19:24:04 PST (America/Los_Angeles) — Created the test-version guide for dev.14.
- 2026-11-04 19:29:55 PST (America/Los_Angeles) — Added the stale-snapshot recovery after a first Windows setup stopped on the pins.
- 2026-11-04 19:55:51 PST (America/Los_Angeles) — Added the dev.18 steps for play with other people in private scenario lobbies.
- 2026-11-04 20:21:00 PST (America/Los_Angeles) — Generated data is no longer in Git, so the guide now requires the generator after every pull and edit.
- 2026-11-04 21:28:04 PST (America/Los_Angeles) — Copied the guide for 0.3 and named the FA scenario.
- 2026-11-04 21:30:57 PST (America/Los_Angeles) — Added game-config.json.
- 2026-11-04 21:51:43 PST (America/Los_Angeles) — Added cover damage settings.
- 2026-11-04 22:10:01 PST (America/Los_Angeles) — Updated the cover damage settings.
