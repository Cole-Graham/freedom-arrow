# Broken Arrow modding toolkit (v3)

A set of small, single-purpose command-line tools for editing the Broken Arrow
unit/weapon/ammunition database. The toolkit is **self-contained**: everything
it reads or writes lives under `v3/`, and its third-party dependencies are
vendored into `v3/vendor/`. Nothing outside `/v3/` is required.

## Quick start

```
run.bat                 # Windows: opens the interactive menu (top-level entrypoint)
python menu/menu.py     # any platform
```

The menu drives every tool. To use a tool directly, call its front:

```
db/db.bat get units --id 3
extractor/extractor.bat decrypt
python import/import.py json
```

Every tool prints its own help with `?` (e.g. `db ?`).

## How it fits together

```
            bundle (data.unity3d)
                 |  extractor unpack / decrypt
                 v
            world/json/  --import-->  db (world/yaml/)  --export-->  world/json/
                 ^                       |  link / research / scale / bond
                 |  extractor encrypt / pack
                 v
            bundle (patched)
```

- **extractor** - bundle <-> JSON (decrypt, encrypt, pack, unpack).
- **import / export** - JSON <-> db (byte-exact round trip).
- **db** - storage + schema authority (the only thing that touches `yaml/`).
- **link** - derived `link_info` relationship blocks; graph walks.
- **research / scale** - real-world ranges -> balanced in-game ranges.
- **bond** - bridge-table mutations (weapon replacement) with consistency.
- **editor** - guided interactive unit editor; connected edits with clone-or-alter on shared parts.
- **diff / backup / check_patch** - diagnostics and snapshots.
- **actions** - `import_pipeline` and `export_pipeline` chain the above.
- **menu** - the interactive launcher (this is the entrypoint).

## Tools

| Folder | Kind | Purpose |
|---|---|---|
| `core/` | library | shared infra (args, prompts, IO, subprocess, paths). No CLI. |
| `menu/` | launcher | interactive top-level menu (`run.bat`). |
| `db/` | tool | field-level CRUD + schema; bulk `load`/`dump`. |
| `extractor/` | tool | bundle <-> JSON (decrypt/encrypt/pack/unpack). |
| `import/` | tool | JSON -> db. |
| `export/` | tool | db -> JSON. |
| `link/` | tool | compute/persist `link_info`; `walk` the graph. |
| `research/` | tool | research markdown -> ammo `real_world`. |
| `scale/` | tool | `real_world` -> `current` + `min_range`. |
| `bond/` | tool | bridge-table mutations (`replace`). |
| `editor/` | tool | guided interactive unit editor (specs/price/armor/mobility/optics/weapons/mods/abilities). |
| `diff/` | tool | row/id/field diff of two JSON trees. |
| `backup/` | tool | snapshot/restore JSON (light) and bundle (heavy). |
| `check_patch/` | tool | diagnose "my patch changed nothing". |
| `actions/` | pipelines | `import_pipeline`, `export_pipeline`. |
| `edit_unit/`, `edit_option/` | placeholder | interactive editors - not yet implemented. |

Each tool folder has its own `README.MD` with verbs and examples.

## Conventions

- **Single entry point per tool**: `<tool>/<tool>.py` (+ `<tool>.bat` on
  Windows), named exactly after the tool. Tools call other tools *only*
  through this front, via `core.proc`. No tool imports another tool's internals.
- **Self-contained**: world/data lives under `v3/world/` (`json/`, `yaml/`,
  `backups/`, `_workdir/`, `research/`); third-party deps in `v3/vendor/`
  (entry scripts prepend it to `sys.path`). The game's own `data.unity3d` is the
  one external operand - point at it with `--bundle`, `BA_GAME_ROOT`, or
  `v3/game_root.txt`; a copy at `v3/data.unity3d` is the default.

## Dependencies

Listed in `requirements.txt` (PyYAML, pycryptodome, UnityPy, attrs), vendored
into `v3/vendor/`. The vendored copy is platform-specific - on a new platform
re-vendor with:

```
pip install -r requirements.txt -t vendor
```

## Typical workflows

```
# Bundle -> editable db
python -m v3.actions.import_pipeline run        # or menu > Import pipeline

# Edit (examples)
bond/bond.bat replace --unit 3 --old-weapon 6 --new-weapon 270 --ammo 7
research/research.bat run && scale/scale.bat run
link/link.bat init

# Editable db -> patched bundle
python -m v3.actions.export_pipeline run        # or menu > Export pipeline
```
