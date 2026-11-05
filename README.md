# freedom-arrow

**Unreleased 0.3 development:** [build instructions and changes](releases/0.3/README.md). 0.2 stays on `codex/0.2-development`.

**0.2 development:** [build instructions, included changes and held work](releases/0.2/README.md). The dev.29 data candidate is built offline; recon and card splits remain incomplete, and in-game acceptance is pending. Its release build uses `releases/0.2/build.py`, not the generic channel package command. Lateralus's optics/stealth/noise cleanup is preserved.

**Prepared 0.1 candidate:** [download, scope and source](releases/0.1/README.md) · [Linux deployment](docs/releases/0.1-linux.md). This review branch keeps detection, stealth and concealment vanilla; revised live acceptance and multiplayer remain unverified.

Tools and data for a Broken Arrow gameplay mod. Gameplay changes live in JSON constants. A MelonLoader plugin inside the `.bamod` applies those constants when the game loads. Players install and launch the mod with [BAModManager](thirdparty-tools/BAModManager-main/README.md): the Mod Manager for development, and BAModLauncher for release.

The game is a Unity 6 IL2CPP title. The database is one `DataBaseCompiled` object inside `BrokenArrow_Data/data.unity3d`: 24 AES-256-CBC JSON tables. BAModLauncher is what players press. It installs MelonLoader and this modpack, starts the game with Anti-Cheat disabled, and **Play vanilla with no mods** removes MelonLoader's `version.dll`.

Do not play ranked or quick match while MelonLoader is installed.

## Layout

| Path | What it is |
| --- | --- |
| `pipeline/` | Extract, patch, inject, rebase, and pack a `.bamod` |
| `runtime/FreedomArrow/` | MelonLoader plugin that applies constants and formulas |
| `mod/constants/` | Stable gameplay changes to the 24 tables |
| `mod/manifest.json` | Game build the stable constants were last reconciled with |
| `mod/formulas/` | Stable injected formulas, one file per game method |
| `mod/testing/constants/` | Testing gameplay changes |
| `mod/testing/formulas/` | Testing injected formulas |
| `mod/testing/manifest.json` | Game build the testing constants were last reconciled with |
| `mod/modpack.json` | Modpack id, version, and GitHub repos for Stable and Testing |
| `config.template.YAML` | Committed config template |
| `thirdparty-tools/BAModManager-main/` | BAModManager and BAModLauncher source |
| `thirdparty-tools/` | Also vendors Bodkin, MelonLoader, Il2CppDumper, and ILSpy |
| `BrokenArrow_Data/` | Local game data. Gitignored |
| `cache/` | Vanilla snapshots and launcher backups. Gitignored |
| `dist/` | Patched bundles. Gitignored |

## Onboarding

You need Python 3.11 or newer, and a Broken Arrow install that contains `BrokenArrow.exe` and `BrokenArrow_Data/data.unity3d`. A copy of `BrokenArrow_Data` in the repo root is valid when `game_root` is the repo root.

From the repo root:

```text
python -m pip install -r pipeline/requirements.txt
copy config.template.YAML config.YAML
```

On Linux or macOS, `cp config.template.YAML config.YAML`.

Edit `config.YAML` and set `game_root` to the install directory. Quote the path. Forward slashes work on Windows and Linux. Examples are in the template. `config.YAML` is gitignored. Every pipeline command stops if it is missing.

Leave `write_game_bundle` false until you intend to copy a bundle over the game. `discover`, `decrypt`, `survey`, `il2cpp`, `apply`, and `package` never write inside `game_root`. `inject` writes `dist/`, not the game. `hangar` writes inside `game_root`, and only when that flag is true.

Build the plugin before packaging:

```text
dotnet build runtime/FreedomArrow/FreedomArrow.csproj -c Release
dotnet run --project runtime/FreedomArrow.Tests/FreedomArrow.Tests.csproj -c Release
```

The console checks load the real plugin and exercise registration, generated hook calls, and encrypted table preparation. They do not start Unity or prove native hooks or combat behavior. The plugin and console checks target .NET 6, matching the bundled MelonLoader host.

Run commands from the repo root so Python can import `pipeline`:

```text
python -m pipeline decrypt
python -m pipeline apply
python -m pipeline inject
python -m unittest pipeline.tests.test_pipeline pipeline.tests.test_package
```

`decrypt` reads the live database and writes `cache/vanilla/<build-id>/`. When an object has `MainBuildDatabase` and level 2, that object is the live database. Otherwise the one with the most units is used, and every candidate path id and unit count is printed. The first run hashes `data.unity3d` and extracts `globalgamemanagers.assets`. Later runs reuse that snapshot.

`inject` repacks the whole archive into `dist/<channel>/data.unity3d`. On a current game that is several gigabytes and takes a few minutes. It also writes `dist/<channel>/channel.json` with the vanilla build id the bundle was built from.

## How constants are written

This section is the authoring shape. The cost object is an example of that shape. It is not a catalogue of mechanics.

A constant file names the place the game or the plugin actually applies the change. A number is a new literal. A string names something that already exists: a field, a return value, a component, or an enum. Do not add a key the game or the hook does not have.

**Existing table data.** `mod/constants/<table>.json` is one of the 24 database tables. An empty object changes nothing. The example sets one field on one row:

```json
{
  "1": { "Cost": 40 }
}
```

A list of rows with an `Id` field is also accepted. The pipeline rejects an unknown file, a missing `Id`, a type change, and a foreign key that does not point at a row. Rows you do not mention stay as the original ciphertext, so an empty constants directory round-trips to the original object bytes.

**Serialized config edits are not implemented.** `mod/configs/<ClassName>.json` and `mod/testing/configs/<ClassName>.json` are reserved for a future ScriptableObject application path. Packaging rejects JSON files there. If JSON files are already installed under `UserData/FreedomArrow/configs`, plugin startup reports the unsupported input and leaves gameplay hooks uninstalled. Reading fields from `dump.cs` or decoding a config asset does not apply edits to that asset.

**Code at a method.** `mod/formulas/<Class>/<Method>.json` names a game method and the parameters its hook reads. The file has `method`, `change`, and `parameters`. `change` is `after`, `before`, `inside`, or `instead`. Only `after` is accepted today. The other three are rejected until a hook implements them.

This file shape is one `after` hook. No hook is registered until a class is added to `FormulaHost`.

```json
{
  "method": "Game.OtherClass.OtherMethod",
  "change": "after",
  "parameters": {
    "scale": 1
  }
}
```

`parameters` are the values for that hook. A new method is a new file plus a hook. `package` checks the envelope only.

Day-to-day and release are `package`, then BAModManager or BAModLauncher PLAY. The plugin applies whatever constants and formulas are in the package. **Play vanilla** stays the manager's button.

```text
python -m pipeline package --channel stable
python -m pipeline package --channel testing
```

`decrypt`, `apply`, and `rebase` are the offline checks. `apply` merges constants and checks links without touching the game. `inject` and `hangar` are diagnostics. `hangar` still requires `write_game_bundle`: it installs `dist/stable/data.unity3d`, launches the game, and restores the previous file when the process exits.

## BAModManager

Source is in [thirdparty-tools/BAModManager-main](thirdparty-tools/BAModManager-main/README.md). It builds two programs. The Mod Manager is for development. BAModLauncher is what players get. Both already have **PLAY** and **Play vanilla with no mods**. Stable and Testing on the launcher are two GitHub repos, each publishing a `.bamod`.

Build them from that directory with the .NET 8 SDK:

```text
build.bat
build_launcher.bat owner/freedom-arrow owner/freedom-arrow-testing
```

`build.bat` writes the Mod Manager zip. `build_launcher.bat` with two `owner/repo` arguments writes a launcher whose Stable and Testing buttons follow those repos. Fill `repo` and `testingRepo` in [mod/modpack.json](mod/modpack.json) with the same names before you publish.

Pack the mod for either channel:

```text
python -m pipeline package --channel stable
python -m pipeline package --channel testing
```

Each command writes `dist/<channel>/FreedomArrow-<version>.bamod`. The zip contains `mod.json` (`"type": "modpack"`), `Mods/FreedomArrow.dll`, the non-empty constant files under `UserData/FreedomArrow/constants/`, and formula files under `UserData/FreedomArrow/formulas/`. BAModManager installs those paths. The patched `data.unity3d` is not inside the package: it is several gigabytes, and the manager does not replace `BrokenArrow_Data`. When `mod/modpack.json` has repos, packaging also writes `dist/launcher.json`:

```json
{ "modpack": "owner/freedom-arrow", "testing": "owner/freedom-arrow-testing" }
```

Put that file next to `BAModLauncher.exe` if you are using the generic launcher instead of `build_launcher.bat`. Publish each `.bamod` as a GitHub release asset. The tag must match `version` in `mod/modpack.json` (`v0.1.0` for version `0.1.0`). PLAY downloads a newer release when the tag is newer than the installed modpack. Keep `id` unchanged across versions.

Drag the `.bamod` onto BAModManager to confirm it installs before you publish it. PLAY in either program starts the game with Anti-Cheat disabled. **Play vanilla with no mods** removes `version.dll` and starts the normal game.

## After a game update

Steam replacing `data.unity3d` is expected. Keep the previous vanilla snapshot in `cache/` until the new one is reconciled.

```text
python -m pipeline update --channel stable
python -m pipeline update --channel testing
```

`update` decrypts the new bundle, rebases that channel's constants, applies them, and injects. A constant is kept when the game did not change that field. When both sides changed it, the row disappeared, or the field's type changed, rebase writes `cache/rebase-conflicts-<channel>.json` and leaves the manifest on the old build. Read the report, edit the constants, then either run `rebase` again or, after you have decided to keep your values, run:

```text
python -m pipeline rebase --channel stable --accept
```

`--accept` records the new build id and leaves the constants in place.

## Commands

| Command | What it does |
| --- | --- |
| `discover` | Find `DataBaseCompiled` by name and record path id, script, and build id |
| `decrypt` | Write the 24 JSON tables and their original ciphertext |
| `survey` | Catalog cover, forest, stealth, and suppression values into `cache/survey/<build-id>/report.json`. Reads the bundle only |
| `il2cpp` | Dump `GameAssembly.dll` from `game_root` and write cover-config fields and values to `cache/il2cpp/<build-id>/configs.json` |
| `apply --channel` | Merge that channel's constants onto the vanilla snapshot |
| `inject --channel` | Repack `dist/<channel>/data.unity3d` and `channel.json` |
| `package --channel` | Write `dist/<channel>/FreedomArrow-<version>.bamod`, including `Mods/FreedomArrow.dll` |
| `rebase --channel` | Three-way merge of the previous snapshot, the new snapshot, and the constants |
| `update --channel` | Decrypt, rebase, apply, and inject |
| `hangar` | Install the stable bundle, launch, and restore on exit |

`python -m pipeline <command> --help` prints the flags. `--config` selects a file other than `config.YAML`.

## Third-party tools

`thirdparty-tools/BodkinToolkit` is an earlier editor whose write path hardcodes a PathID and drops JSON fields the schema does not name. Do not round-trip the game database through its YAML. The AES field order in `pipeline/tables.py` matches Bodkin's list; the lookup and the authoring format do not.

MelonLoader, Il2CppDumper, and ILSpy are vendored beside BAModManager. The manager downloads MelonLoader when a player presses PLAY. Il2CppDumper and ILSpy are for later UI and behaviour work.

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Document change log

- 2026-11-04 16:54:02 PST (America/Los_Angeles) — Added an unreleased0.2 development/build pointer and explicit recon/card/runtime limits; preserved the0.1 candidate and upstream cleanup.
- 2026-11-04 17:30:00 PST (America/Los_Angeles) — Updated the development pointer to dev.4.
- 2026-11-04 17:54:19 PST (America/Los_Angeles) — Updated the development pointer to dev.5.
- 2026-11-04 18:01:47 PST (America/Los_Angeles) — Updated the development pointer to dev.6.
- 2026-11-04 18:07:58 PST (America/Los_Angeles) — Updated the development pointer to dev.7.
- 2026-11-04 18:11:00 PST (America/Los_Angeles) — Updated the development pointer to dev.8.
- 2026-11-04 18:26:32 PST (America/Los_Angeles) — Updated the development pointer to dev.9.
- 2026-11-04 18:37:44 PST (America/Los_Angeles) — Updated the development pointer to dev.10.
- 2026-11-04 19:05:03 PST (America/Los_Angeles) — Updated the development pointer to dev.11.
- 2026-11-04 19:11:24 PST (America/Los_Angeles) — Updated the development pointer to dev.12.
- 2026-11-04 19:24:04 PST (America/Los_Angeles) — Updated the development pointer to dev.14.
- 2026-11-04 19:37:31 PST (America/Los_Angeles) — Updated the development pointer to dev.16.
- 2026-11-04 19:42:51 PST (America/Los_Angeles) — Updated the development pointer to dev.17.
