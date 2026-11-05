# Make a Freedom Arrow 0.2 test version

**Change values in one of two files, set a new version, build, verify, install the `.bamod`, and read one log line.** Nothing here installs or launches the game for you. These steps were run on Linux; the Windows commands are not yet proven.

## What to edit

- `releases/0.2/detection-contract.json`: table values.
  - `optics_ground_tiers`: vanilla ground optics to new value. Six tiers: 500, 600, 700, 875, 1000, 1200.
  - `optics_ground_drones`: drone sensor rows 32, 33, 34. They do not follow the tiers, so change them yourself.
  - `stealth`: raw value per class. Raw is 1 / UI value, so UI 2.0 is 0.5.
  - `stealth_unit_values`: per-unit raw values that replace the class value.
  - `stealth_override_options`: per-option raw values.
- `releases/0.2/source/UserData/FreedomArrow/detection-config.json`: config values, written when a battle loads. Each must be 1 to 10.
- `releases/0.2/vehicle-contract.json`: prices.

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
.venv\Scripts\python releases/0.2/bump_version.py 0.2.0-dev.NN
.venv\Scripts\python releases/0.2/build_constants.py --vanilla-dir $VANILLA
.venv\Scripts\python releases/0.2/build.py --game-dir $GAME --dotnet dotnet
.venv\Scripts\python releases/0.2/verify.py
```

The archive is `releases/0.2/out/FreedomArrow-<version>.bamod`. It is git-ignored. Import it with the mod manager as usual, and do not copy it into `Mods`.

Use the next unused number, and check every remote branch first, because other branches also use numbers:

```powershell
git fetch origin
git grep -h '"version"' origin/codex/0.2-development origin/codex/0.2-split-test -- releases/0.2/mod.json
```

## Run the tests

```powershell
dotnet run --project releases/0.2/row-tests/Tests.csproj -c Release -- $VANILLA <payload>
dotnet run --project releases/0.2/economy-tests/Tests.csproj -c Release
.venv\Scripts\python -m unittest discover -s pipeline/tests
```

For `<payload>`, use `releases/0.2/build/payload/UserData/FreedomArrow`.

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

## Rules

- Commit to `codex/0.2-development` and push when you commit. Fast-forward only; never force-push. Do not push to `main`.
- Never take a modded client online. The tables and config apply in every battle mode.
- Say which version and commit a test used, and attach `Latest.log`.

## Document change log

- 2026-11-04 19:24:04 PST (America/Los_Angeles) — Created the test-version guide for dev.14.
- 2026-11-04 19:29:55 PST (America/Los_Angeles) — Added the stale-snapshot recovery after a first Windows setup stopped on the pins.
