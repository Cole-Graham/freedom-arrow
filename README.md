# freedom-arrow

Tools and data for a Broken Arrow gameplay mod. Unit, weapon, and ammo changes live in JSON constants. A Python pipeline reads the game's encrypted unit database, applies those constants, and writes a patched `data.unity3d` for local testing. Players install and launch the mod with [BAModManager](thirdparty-tools/BAModManager-main/README.md): the Mod Manager for development, and BAModLauncher for release.

The game is a Unity 6 IL2CPP title. The database is one `DataBaseCompiled` object inside `BrokenArrow_Data/data.unity3d`: 24 AES-256-CBC JSON tables. This project patches that object. BAModLauncher is what players press. It installs MelonLoader and this modpack, starts the game with Anti-Cheat disabled, and **Play vanilla with no mods** removes MelonLoader's `version.dll`.

Do not play ranked or quick match while MelonLoader is installed.

## Layout

| Path | What it is |
| --- | --- |
| `pipeline/` | Extract, patch, inject, rebase, and pack a `.bamod` |
| `mod/constants/` | Stable gameplay changes |
| `mod/manifest.json` | Game build the stable constants were last reconciled with |
| `mod/testing/constants/` | Testing gameplay changes |
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

Leave `write_game_bundle` false until you intend to copy a bundle over the game. `discover`, `decrypt`, `survey`, `il2cpp`, `apply`, `inject`, and `package` never write inside `game_root`. `hangar` does, and only when that flag is true.

Run commands from the repo root so Python can import `pipeline`:

```text
python -m pipeline decrypt
python -m pipeline apply
python -m pipeline inject
python -m unittest pipeline.tests.test_pipeline pipeline.tests.test_package
```

`decrypt` reads the live database (the `DataBaseCompiled` with the most units; smaller copies in the same file are mission snapshots and are left alone) and writes `cache/vanilla/<build-id>/`. The first run hashes `data.unity3d` and extracts `globalgamemanagers.assets`. Later runs reuse that snapshot.

`inject` repacks the whole archive into `dist/<channel>/data.unity3d`. On a current game that is several gigabytes and takes a few minutes. It also writes `dist/<channel>/channel.json` with the vanilla build id the bundle was built from.

## Changing the game

Edit `mod/constants/<table>.json`. Each file is one of the 24 tables. An empty object changes nothing. A constant names a row `Id` and the fields it sets, using the game's PascalCase names:

```json
{
  "1": { "Cost": 40 }
}
```

A list of rows with an `Id` field is also accepted. The pipeline rejects an unknown file, a missing `Id`, and a type change such as a number replaced by a string. Rows you do not mention stay as the original ciphertext, so an empty constants directory round-trips to the original object bytes.

Build and install the stable channel:

```text
python -m pipeline apply --channel stable
python -m pipeline inject --channel stable
```

`--channel` defaults to `stable`. Testing uses `mod/testing/constants/` and writes `dist/testing/`.

`python -m pipeline hangar` is the local check of a patched database: it installs `dist/stable/data.unity3d`, launches the game, and restores the previous file when the process exits. Set `write_game_bundle` first. Day-to-day play, MelonLoader install, and **Play vanilla with no mods** belong to BAModManager, not this command.

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

Each command writes `dist/<channel>/FreedomArrow-<version>.bamod`. The zip contains `mod.json` (`"type": "modpack"`) and the non-empty constant files under `UserData/FreedomArrow/constants/`. BAModManager installs those paths and skips anything else. The patched `data.unity3d` is not inside the package: it is several gigabytes, and the manager does not replace `BrokenArrow_Data`. When `mod/modpack.json` has repos, packaging also writes `dist/launcher.json`:

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
| `package --channel` | Write `dist/<channel>/FreedomArrow-<version>.bamod` for BAModLauncher |
| `rebase --channel` | Three-way merge of the previous snapshot, the new snapshot, and the constants |
| `update --channel` | Decrypt, rebase, apply, and inject |
| `hangar` | Install the stable bundle, launch, and restore on exit |

`python -m pipeline <command> --help` prints the flags. `--config` selects a file other than `config.YAML`.

## Third-party tools

`thirdparty-tools/BodkinToolkit` is an earlier editor whose write path hardcodes a PathID and drops JSON fields the schema does not name. Do not round-trip the game database through its YAML. The AES field order in `pipeline/tables.py` matches Bodkin's list; the lookup and the authoring format do not.

MelonLoader, Il2CppDumper, and ILSpy are vendored beside BAModManager. The manager downloads MelonLoader when a player presses PLAY. Il2CppDumper and ILSpy are for later UI and behaviour work.

## License

Apache License 2.0. See [LICENSE](LICENSE).
