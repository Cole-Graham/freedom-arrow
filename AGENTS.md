# Agents

Read this before editing freedom-arrow. Human setup, command list, and the gameplay workflow are in [README.md](README.md). This file is how to work in the repo without damaging a local game install or committing game data.

## What this repo is

A Python 3.11+ pipeline plus the gameplay constants it applies. The game database is the `DataBaseCompiled` MonoBehaviour in `BrokenArrow_Data/data.unity3d`: 24 AES-encrypted JSON tables. Stable edits are `mod/constants/*.json`. Testing edits are `mod/testing/constants/*.json`. Empty `{}` means no change.

Run Python from the repo root so `import pipeline` works.

```text
python -m pip install -r pipeline/requirements.txt
python -m unittest pipeline.tests.test_pipeline pipeline.tests.test_package
```

Unit tests use temp directories and stub executables. They do not need the 7 GB bundle. Prefer them for any code change under `pipeline/`.

## Do this first

1. If `config.YAML` is missing, copy `config.template.YAML` and set `game_root` to a directory that contains `BrokenArrow_Data/data.unity3d`. The repo's own gitignored `BrokenArrow_Data/` is valid when `game_root` is the repo root.
2. Leave `write_game_bundle` false unless the user explicitly asked to install a bundle or launch the game.
3. Read `pipeline/cli.py` and `pipeline/channels.py` before adding commands. Stable follows `constants_dir` / `manifest_path` from config. Testing is always `mod/testing/constants` and `mod/testing/manifest.json`.

## Where to change things

| Task | Edit |
| --- | --- |
| A gameplay value | `mod/constants/<table>.json` or `mod/testing/constants/<table>.json` |
| Extract, encrypt, inject, rebase, package | `pipeline/` |
| Modpack id, version, GitHub repos | `mod/modpack.json` |
| Player install and Play vanilla | Do not reimplement. Use `thirdparty-tools/BAModManager-main` |
| Developer paths | `config.template.YAML` only. Never commit `config.YAML` |

A constant is an object keyed by row `Id`, values are the game's PascalCase fields:

```json
{ "1": { "Cost": 40 } }
```

Do not invent a second schema. Do not author the mod as Bodkin YAML. `thirdparty-tools/BodkinToolkit/import/translate.py` drops unknown fields. The committed source of truth is the constants JSON.

Field order is `pipeline/tables.py`. It must stay aligned with `thirdparty-tools/BodkinToolkit/extractor/crypto.py` `FIELD_ORDER`. Unity 6 inserts one empty string before those 24 fields; `pipeline/database.py` keeps that string in the object prefix so an empty patch returns the original bytes.

Lookup is by `m_Name == "DataBaseCompiled"`, then the candidate with the most unit rows. Do not hardcode PathID `15803`.

## Commands you may run

Safe without `write_game_bundle`:

```text
python -m pipeline discover
python -m pipeline decrypt
python -m pipeline apply --channel stable
python -m pipeline apply --channel testing
python -m pipeline package --channel stable
python -m pipeline package --channel testing
```

`decrypt` is cheap after the first snapshot exists. `apply` only writes under `cache/`. `package` writes a `.bamod` under `dist/<channel>/` and does not touch the game.

Ask before running these. They are slow or they write into the game directory:

| Command | Why it is gated |
| --- | --- |
| `inject` | Repacks the full archive into `dist/<channel>/data.unity3d` (several GB, a few minutes) |
| `update` | Decrypt, rebase, apply, and inject |
| `hangar` | Replaces the game's `data.unity3d`, launches `BrokenArrow.exe`, restores on exit. Requires `write_game_bundle: true` |

Do not set `write_game_bundle` to true yourself.

There is no launcher in this repo. Players use BAModLauncher from `thirdparty-tools/BAModManager-main`. Do not add a second Play / Play vanilla window. Stable and Testing are two GitHub repos in `mod/modpack.json` (`repo` and `testingRepo`), packaged as two `.bamod` files. Do not edit BAModManager unless the user asked for a change to that program.

`rebase` writes `cache/rebase-conflicts-<channel>.json` and does not move the manifest when there are conflicts. Do not pass `--accept` unless the user has reviewed that report and told you to keep the constants.

## Do not commit

These are gitignored and must stay that way:

- `config.YAML`
- `cache/` and `dist/`
- `BrokenArrow_Data/`
- `lat/` and `ai_working_dir/`

Do not commit decrypted tables, `data.unity3d`, bundle hashes of a local install, or a filled-in `game_root`. Game files are copyrighted and huge.

`thirdparty-tools/` is vendored. Do not reformat it, upgrade it, or fix Bodkin or BAModManager in place unless the user asked for that. New behaviour goes in `pipeline/`.

## Checks before you finish

- `python -m unittest pipeline.tests.test_pipeline pipeline.tests.test_package` passes.
- A change to constants or inject paths still round-trips an empty constants directory to the original MonoBehaviour bytes. That test is `IdentityTests` and `ApplyTests.test_empty_constants_round_trip_on_disk`.
- A change to packaging still produces a zip whose `mod.json` has `"type": "modpack"` and whose changed constants live under `UserData/FreedomArrow/constants/`. That test is `pipeline/tests/test_package.py`.
- You did not leave a one-off cost or probe script in `mod/constants/` or `mod/testing/constants/`. Those trees are the mod.

## Offline play

Day-to-day play goes through BAModManager or BAModLauncher. PLAY starts the game with Anti-Cheat disabled. **Play vanilla with no mods** is that program's button. It removes `version.dll`. Do not add a second implementation of that button. `hangar` remains only for trying `dist/stable/data.unity3d` locally.
