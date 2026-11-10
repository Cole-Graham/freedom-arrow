# Separate gameplay and cosmetic assets

**Players install two independent BAModLauncher packages: Freedom Arrow gameplay, and Freedom Arrow Models and Music. Gameplay updates do not contain or replace the asset files.** The initial combined asset package contains only the seven promoted live-unit models, the music library and the existing voice assets. PLA preview models and infantry test data are excluded.

Close the game, use **BAModManager → Mods → + Add mods** for each `.bamod`, then launch through Steam on Linux. The assets have type `mod`, so they coexist with the main gameplay `modpack`; do not select assets as the primary launcher modpack. After the first asset installation, update only gameplay until an asset update is announced. Do not disable/uninstall the asset package as part of a gameplay update. Current prototype PCs already have the files and do not need to download them again.

The music loader defaults to USA if no saved playlist exists. The pack omits `pack.txt` and playback history, so later asset updates retain a player's selection. No geometry reduction, texture resizing or audio re-encoding happens during packaging; ZIP storage is lossless.

## Build the initial optional package

```bash
python tools/asset-packs/build.py GAME_ROOT FreedomArrow-Assets-0.1.0.bamod --version 0.1.0
```

The builder follows both armory/battle FAM dependencies, material sidecars and base/normal/mask textures; it includes model and music loaders separately from the gameplay core. It emits a manifest with SHA-256 hashes. Raw source archives, unrelated models and personal playback history are excluded. This tooling does not establish asset redistribution rights; current downloaded paid assets and soundtrack files are staged privately, not published by this command.

## Developer prototype updates

```bash
python tools/asset-packs/build.py GAME_ROOT asset-update.zip --version 0.1.1 --previous-manifest FreedomArrow-Assets-0.1.0.manifest.json
python apply_model_update.py asset-update.zip GAME_ROOT
```

A prototype delta contains only changed asset files plus its manifest and installer. **A delta ZIP is not a BAModLauncher package.** Keep this path for controlled prototype deployments. The updater requires the previous hashes, preserves unrelated model mappings and playlist choice, backs up every touched file, verifies the full new asset set, and prints a rollback command. It never writes gameplay constants. Files no longer referenced are retained rather than deleted.

The full combined package uses the ordinary launcher process. The delta updater is an optional developer tool; no claim of a tested Windows GUI installation is made.

## Validation

`python tools/asset-packs/test_pack.py` tests dependency closure, separation from PLA/gameplay data, exclusion of local playlist/history state, changed-file export, existing model mappings, saved playlist retention and rejection of an incorrect base. Actual model rendering, music playback and matchmaking still require game tests.

## Combined pack0.1.6

The approved live selection now includes Su-47, F-14 and YF-23 alongside the seven previous models. B-21 uses the approved gear-down4K armory and gear-up1K battle copies. FAModels0.3.4 supplies opt-in clean glass for F-14, Su-47 and Su-57D. Music1.4.1 and all5647 current voices match pack0.1.5 byte for byte. No PLA test models are added.

`approved-live-016.json` records the archive hash and exact source commits. The package manifest verifies5998 files. A new game launch is still needed to check canopy appearance. Unit portraits and cutout icons belong to the gameplay DLL; this pack does not set gameplay prices, pools or weapons.

## Combined pack0.1.7

Adds the omitted YF-23 clear-canopy preset to its armory and battle material sidecars. All other payload bytes match0.1.6. Loader0.3.4, geometry, cockpit textures, B-21, Music1.4.1 and all current voices are unchanged. Both material keys match their actual meshes; opaque entries are unchanged. Runtime appearance awaits a new model construction or game restart.

## Combined pack0.1.8

Adds F-21 Super Tomcat as an alias of the existing F-14 armory/battle model for gameplay dev.17. The F-14 name remains supported. All meshes, textures, loader, music and voices are byte-identical to0.1.7. Run `python tools/asset-packs/build_018_from_017.py /path/to/folder` with the verified0.1.7 archive in that folder to reproduce the pack. Actual model appearance awaits the next launch.

## Document change log

- 2026-11-09 16:27:30 PST (America/Los_Angeles) — Added independent combined live-model/music packaging, USA default policy and prototype delta workflow; retained gameplay installation method.

- 2026-11-09 16:45:58 PST (America/Los_Angeles) — Corrected asset type to a normal add-on in0.1.1; verified15 install/update checks against unchanged manager Core source using full real archives.
- 2026-11-09 23:12:57 PST (America/Los_Angeles) — Recorded pack0.1.6: ten live models, approved B-21, clean canopy loader and preserved1.4.1 audio/voices.
- 2026-11-09 23:41:30 PST (America/Los_Angeles) — Added YF-23 canopy correction to both copies; recorded unchanged payload and runtime limits.
- 2026-11-10 00:22:37 PST (America/Los_Angeles) — Added F-21 alias, pinned pack0.1.8 and recorded reproducible upgrade.
