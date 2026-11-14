# Freedom Arrow 0.8 — maps and conquest settings

**Map sources and zone values for 0.8 live here. `tools/pla-specs/package_0_8_next.py` rebuilds every map from them on each 0.8 build.**

- `scenarios/`: one package per map (layout, script changes, zone values), moved from the frozen `codex/0.7-development` at 0.7.0-dev.58 on 13 November 2026. `make_scenario.py` builds them all. The 16 maps that already existed build byte-identical to the 0.8.0-dev.31 package.
- `source/UserData/FAConquestPrototype/settings.json`: the conquest settings shipped in 0.8, including `MapZoneWeights`. The packager copies it and updates its hash pin in `compatibility.json`.
- A new map needs a package in `scenarios/`, a line in `make_scenario.py`, and its zone values in `settings.json`.

## Document change log

- 2026-11-13 02:46:43 PST (America/Los_Angeles) — Created: map sources moved from 0.7 dev.58, plus [5v5] Cold Harbor 0.1 (Lateralus).
- 2026-11-13 23:53:44 PST (America/Los_Angeles) — Lateralus batch: [5v5] Oil Rush, Airport and Cold Harbor 0.2 (new values; new Airport zones; Cold Harbor without Charlie). The 0.1 folders are retired by GUID.
