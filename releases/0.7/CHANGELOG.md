# Freedom Arrow 0.7 — draft changelog

**Gameplay0.7 is not released or installed. Continue playing0.6.0-dev.115. Music0.1.2 has been published in the combined asset pack independently; gameplay development continues separately.**

## New for 0.7

- **China battle music:** add `China - Mother Of All Weapons.mp3` (3:21) to the battle playlist. Found in the user-supplied unused China/GLA music collection, absent from asset pack 0.1.1. The staged file matches the source SHA256 and retains its original MP3 bytes. This is separate from track 011, the menu opener. See `music/china-battle-track.json`.

- **China menu music:** track 011 (existing `China theme 11.mp3`) plays first on entering the China menu playlist, then the remaining menu music. The old menu recording is `China theme 01 (menu).mp3`. Source for music component 1.3.10 is staged in `music/`; no new 0.7 package is built or installed.

- **Voices:** XM30 switches from its T-15 donor audio preset to the M2A3 Bradley preset (`UNIT_SOUND_PRESET_BRADLEY_ALL`). The final Bradley instruction supersedes the earlier Paladin wording. Abrams X retains `UNIT_SOUND_PRESET_ABRAMS`, the same assignment as existing Abrams, for the requested Crusader Tank lines. This queues the unit-to-voice assignment; audible clip identity and playback are not verified in this preparation.

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

## China music preparation evidence

The optional player now recognizes `Packs/<pack>/Menu/First/` as a designated opening queue. Packs without that folder retain their prior behavior, including USA selection. The marked track plays once on entry, then the regular menu queue; it starts first again after leaving/re-entering the menu or switching packs. China track 11 remains in the battle playlist too, since no battle removal was requested. Stage a byte-identical copy at the destination in `music/china-menu-track.json` before the next asset build. No audio binary is committed.

The candidate music DLL compiled with zero warnings/errors against the local game assemblies. Six host-side ordering scenarios passed: opener first, complete regular queue, no opener at refill, menu re-entry, opener-only playlist, and pack reset. Those checks do not prove audible FMOD playback in game. These initial staging checks did not change current files. Music0.1.2 was subsequently installed and published separately from gameplay; see music/RELEASE-0.1.2.md.

## Document change log

- 2026-11-09 16:59:06 PST (America/Los_Angeles) — Prepared the next-version branch, current play baseline, corrected naming decision and pending scale change.
- 2026-11-09 16:59:47 PST (America/Los_Angeles) — Queued XM30 at 190 points for the next update; current play build remains unchanged.
- 2026-11-09 17:01:29 PST (America/Los_Angeles) — Recorded the current dev.115 Abrams X smoke/jammer defect and read-only runtime-version evidence; root cause and fix remain open.
- 2026-11-09 17:07:33 PST (America/Los_Angeles) — Staged Bradley voices for XM30 and retained the existing Abrams voice assignment for Abrams X; no running-install changes.
- 2026-11-09 17:20:16 PST (America/Los_Angeles) — Staged China track 011 as menu opener and compiled/tested the optional first-track ordering component; no installation.
- 2026-11-09 17:21:20 PST (America/Los_Angeles) — Staged Mother Of All Weapons for China battle music; source hash and MP3 metadata checked; audible in-game playback remains untested.
- 2026-11-09 17:28:20 PST (America/Los_Angeles) — Published the combined music/model pack0.1.2; current gameplay stays dev.115.
