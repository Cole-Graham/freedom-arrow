# Freedom Arrow 0.8 — maps and conquest settings

**Map sources and zone values for 0.8 live here. `tools/pla-specs/package.py` rebuilds every map from them on each 0.8 build.**

- `scenarios/`: one package per map (layout, script changes, zone values), moved from the frozen `codex/0.7-development` at 0.7.0-dev.58 on 13 November 2026. `make_scenario.py` builds them all. The 16 maps that already existed build byte-identical to the 0.8.0-dev.31 package.
- `source/UserData/FAConquestPrototype/settings.json`: the conquest settings shipped in 0.8, including `MapZoneWeights`. The packager copies it and updates its hash pin in `compatibility.json`.
- A new map needs a package in `scenarios/`, a line in `make_scenario.py`, an entry in `maps.json` (its size and whether it is in the ranked pool), and its zone values in `settings.json`.
- `maps.json` is the one place a map's size is set (Lateralus 23 Nov 2026). The build checks every map against it and ships it as `UserData/FreedomArrow/maps.json`; the game and the ranked hub read sizes from that file, not from the [NvN] tag.

## ✅ Adding a map: what "add this map to the mod" means

**When Lateralus or Osama says "add this map to the mod", do every step below without being reminded. The build stops if a map breaks one of the checked rules** (Lateralus 23 Nov 2026: "Is it possible to automatically make sure all maps I ask you to add, always check all these things").

**What you do**

1. Put the editor export in `scenarios/<map>_<size>/` as `layout.bascr` and `meta.json`, with an `__init__.py` modelled on `coal_mountain_2v2` (the newest example).
2. Remove editor test units and waypoints with `C.remove_units_and_waypoints(objects, units=N, waypoints=N)` (exact counts, so a changed upload stops the build).
3. Remove the editor's Neutral and Spectators teams (`C.strip_editor_teams`).
4. Name the zones by letter and give them the requested values (`C.letter_zones`, plus `MapZoneWeights` in `source/UserData/FAConquestPrototype/settings.json` for both the online and the Skirmish name).
5. Turn only the spawns that face more than 45° away from the zones (`C.face_spawn_outliers`); keep the author's other facings, and say which spawns were turned.
6. Add one start camera per team (`C.add_team_cameras`).
7. Add the module to `make_scenario.py` and the map to `maps.json` (size, base name, ranked).
8. Build with `make_scenario.py`, read the built online and Skirmish files back, and report what was changed, what was kept, and anything odd (for example uneven spawn counts or a DLC requirement).
9. For a new version of an existing map: bump the version in the name, move its `MapZoneWeights` to the new names, and retire the old names by GUID in `mod/source/runtime-qa/Runtime.cs` (`RetiredScenarios`). The PvE copies in `pve.py` take their base map's zone values.
10. Add the change to the patch-notes draft with exact old → new values.

**What the build checks on every flavor of every PvP map** (`common.check_layout` and `write_flavor`, `make_scenario.registry`)

- Every zone neutralizes when contested (`forceNeutral`) and captures in 15 s (`CAPTURE_SECONDS`): both are set by the build.
- Every zone has a value, and no value is left for a zone that is gone.
- Each zone icon matches its letter (Alpha = A = 1).
- Zones are capturable by Alpha and Bravo only, and lie inside the active play area.
- No units and no waypoints on the map.
- One start camera per team.
- Each team's spawns are on its own side of the map; ground spawns are inside the play area.
- Spawns face within 45° of the centre of the zones.
- 5 open slots per team, the score limit of 300 in the description, native victory goals out of reach.
- The map is in `maps.json`, its [NvN] tag matches its size, and every size has a ranked map.
- Online maps that share a set of zone IDs have the same values (a joining client identifies its map by the zone IDs).

Maps that shipped before these checks and break one are listed by name in `common.py` (`SPAWN_FACING_KEPT`, `ZONE_ICON_KEPT`, `WAYPOINTS_KEPT`). Do not add a new map to those lists; fix the map instead.

## 🗺️ Map overviews on the website

**The FA maps page (<https://freedomarrow.app/tools/maps.html>) draws every map's play area, zones with their values, and spawns with their facing over the game's own map image.** It is rebuilt from the released package by `bin/ba-site-data` at each release, so a new map appears there when it ships.

- Layout: `team-site/build_maps.py` reads each online scenario's `.bascr` from the package (play area, zones, spawns).
- Background: `team-site/map_scenes.json` names one image per game scene: the tactical minimap from the scene's `mapsettings_assets_*.bundle`, or the lobby preview when the tactical one is not in the bundle (Coal Mountain, from the DLC 3 bundle). Each image covers the whole map (`MapSize` in the map settings): world X 0 to size left to right, Z 0 to size bottom to top. This was checked on 23 Nov 2026 by overlaying the Highway of Death and Dam zones.
- A map on a new game scene needs its image added to `map_scenes.json` (extraction scripts: `work/map-overviews-20261123`). Read only the map-settings objects from a bundle; never load `data.unity3d`.

## Document change log

- 2026-11-13 02:46:43 PST (America/Los_Angeles) — Created: map sources moved from 0.7 dev.58, plus [5v5] Cold Harbor 0.1 (Lateralus).
- 2026-11-13 23:53:44 PST (America/Los_Angeles) — Lateralus batch: [5v5] Oil Rush, Airport and Cold Harbor 0.2 (new values; new Airport zones; Cold Harbor without Charlie). The 0.1 folders are retired by GUID.
- 2026-11-23 12:5x PST (America/Los_Angeles) — [5v5] Airport, Oil Rush, Cold Harbor renamed [4v4]; maps.json map list added (Lateralus).
- 2026-11-23 21:3x PST (America/Los_Angeles) — [2v2] Coal Mountain 0.1 added; [2v2] Highway of Death 0.3 and [1v1] Dead Center 0.3 (new zone values); "Adding a map" checklist and the build checks behind it (Lateralus).
- 2026-11-23 21:2x PST (America/Los_Angeles) — Map overviews on the website: where the layout and background images come from.
- 2026-11-27 06:5x PST (America/Los_Angeles) — [1v1] Below the Mountain 0.1 added (End's Workshop map 3846746484, all zones +1); `C.add_team_cameras(ground=True)` puts a camera between a team's ground spawns (End).
- 2026-11-27 07:4x PST (America/Los_Angeles) — [1v1] Mountain 0.1 added (End's Workshop map 3846746372); End's +1 maps share `C.end_occ_spec`; ground-spawn cameras use spawn type 1 only.
- 2026-11-27 10:4x PST (America/Los_Angeles) — Lateralus: Mountain A-E 2, Below the Mountain A C E 2 / B D 4 (`end_occ_spec` takes per-map values); Mountain air spawns at the map edges.
- 2026-11-27 12:3x PST (America/Los_Angeles) — [2v2] Jelgavas Pils 0.1 added (Lateralus; A B 2 / C D 4; not in the ranked pool).
- 2026-11-28 09:5x PST (America/Los_Angeles) — [1v1] Jelgavas Pils 0.1 replaces [1v1] Jelgava (Lateralus; his 2v2 layout with a 5000 m wide playable zone; A B 2 / C D 4; ranked). Runtime.cs retires the installed Jelgava copies by GUID. The PvE Jelgava maps keep the old layout, so `jelgava_1v1` stays as their base and is no longer built on its own.
- 2026-11-28 10:1x PST (America/Los_Angeles) — The Russia PvE maps (PvE 1P RU and the four PvE AI RU) move from the old Jelgava layout to [1v1] Jelgavas Pils (Lateralus): same waves and AI cards, zones A B 2 / C D 4, names "RU Jelgavas Pils"; Runtime.cs retires the six old RU Jelgava copies by GUID. `jelgava_1v1` is no longer used by any build.
- 2026-11-28 10:2x PST (America/Los_Angeles) — `scenarios/jelgava_1v1` deleted (Lateralus: "yes delete the old source"); its spawn-facing exception in `common.py` removed with it.
- 2026-11-28 11:4x PST (America/Los_Angeles) — [1v1] Kadaga Military Base 0.1 replaces [1v1] Kadaga (Lateralus: new design, ranked, A B 3 / C D 4; DLC 2 as before). Runtime.cs retires the installed Kadaga copies by GUID. `kadaga_1v1` is no longer built.
- 2026-11-28 11:5x PST (America/Los_Angeles) — `scenarios/kadaga_1v1` deleted (Lateralus: "yes delete the old source folder").
