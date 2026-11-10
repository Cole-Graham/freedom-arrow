# Freedom Arrow 0.7 — draft changelog

**Not released or installed. Continue playing 0.6.0-dev.115 with Models and Music 0.1.1. Development continues separately for the next update.**

## New for 0.7

- **XM30 price:** 220 → 190 points. Staged gameplay override for unit 983; not applied to the current play build.

- **XM30 model:** increase armory and battle visual size by 10% compared with the current size. Mapping scale changes from 0.70 to 0.77. The unit remains named XM30; the proposed XM-50 rename was withdrawn.
- **Su-75:** retain 2 availability. The brief request for 1 was withdrawn; this is not a new balance change.

These are staged decisions, not in-game results. Meshes, textures and weapons have not been re-exported, compressed or moved. Visual size and clearance still need a game check after installation is authorized.

## Carried forward from the current baseline

These are existing features, not new 0.7 changes:

- The dev.114 artillery corrections retained in dev.115: 40 mm damaging-artillery penetration floor, TOS damage 11 with normal impact handling, and the corrected X-47B card.
- Live added units and their current data: Abrams X, B-21, X-47B, Su-57D, Su-75, Karatel and XM30. PLA test units remain outside the live gameplay build.
- Gameplay and combined models/music remain separate packages. Gameplay updates preserve installed assets. USA remains the default playlist for new installations; existing choices are retained.
- Cosmetic model/music loaders are excluded from the gameplay matchmaking identifier by source logic. This was not proved through an online match.

The inherited 0.6 history remains in ../0.6/source/UserData/FreedomArrow/release-notes.md. That historical document contains older and superseded entries; it is not a fresh net-change claim. The reconciliation and history audit reports identify final values and known limits.

## Open Abrams X defect

**Osama reports smoke and jammer absent during the current play session. This is unresolved, not fixed.** A read-only PC log check confirms dev.115 initialized at 16:50:24 and its whole-table application completed at 16:50:26. The packaged unit has intrinsic default smoke (1 charge), Trophy APS (2 charges) and ECM multiplier 0.7 (30% jammer). Those assignments do not prove that a spawned unit received usable abilities. The earlier data checks were insufficient proof of runtime behavior. Investigate initialization/selected options and model-component dependencies in an isolated run; do not blame an old PLA runtime or install a speculative change during play. See abramsx-defense-investigation.json.

## Not included or promised

- Lateralus's queued batch, including helicopter 15% flare strength and 15 flares, remains separate. Do not silently merge it into this release.
- Plane refund/respawn rework remains proposal work in the other thread.
- Separate visible 3-second TOS fire remains unimplemented. A per-map 100-point 1v1 score limit remains a future note.
- No new proof of APS, smoke, jammer, scoring synchronization, music playback or model rendering is supplied by this preparation.

## Document change log

- 2026-11-09 16:59:06 PST (America/Los_Angeles) — Prepared the next-version branch, current play baseline, corrected naming decision and pending scale change.
- 2026-11-09 16:59:47 PST (America/Los_Angeles) — Queued XM30 at 190 points for the next update; current play build remains unchanged.
- 2026-11-09 17:01:29 PST (America/Los_Angeles) — Recorded the current dev.115 Abrams X smoke/jammer defect and read-only runtime-version evidence; root cause and fix remain open.
