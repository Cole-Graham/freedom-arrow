# Freedom Arrow 0.7 preparation

**Keep the running/public version on dev.115 and asset pack 0.1.1 while the group is playing. This branch prepares the next release without installing or publishing another playable build.**

## Prepared now

- **China battle music:** add `China - Mother Of All Weapons.mp3` (3:21) to the battle playlist. Found in the user-supplied unused China/GLA music collection, absent from asset pack 0.1.1. The staged file matches the source SHA256 and retains its original MP3 bytes. This is separate from track 011, the menu opener. See `music/china-battle-track.json`.

- **China menu music:** track 011 (existing `China theme 11.mp3`) plays first on entering the China menu playlist, then the remaining menu music. The old menu recording is `China theme 01 (menu).mp3`. Source for music component 1.3.10 is staged in `music/`; no new 0.7 package is built or installed.

- **Voices:** XM30 switches from its T-15 donor audio preset to the M2A3 Bradley preset (`UNIT_SOUND_PRESET_BRADLEY_ALL`). The final Bradley instruction supersedes the earlier Paladin wording. Abrams X retains `UNIT_SOUND_PRESET_ABRAMS`, the same assignment as existing Abrams, for the requested Crusader Tank lines. This queues the unit-to-voice assignment; audible clip identity and playback are not verified in this preparation.

- `gameplay-overrides.json` stages XM30 unit 983 cost 220 → 190. Merge this into the future generator before building; it is not an independently installable patch.

- `baseline.json` records current versions, source commits, download links and archive hashes.
- `CHANGELOG.md` separates new 0.7 work from inherited fixes, deferred work and untested behavior.
- `assets/models.json` is the complete seven-unit live mapping with only XM30 scale changed: 0.70 → 0.77. Both armory and battle files use that mapping scale. Unit name and all other mappings remain unchanged.
- The baseline archive hash identifies the existing custom asset payload. The scale change requires a mapping update, not new meshes, textures or music.

## Build and deployment checklist

1. Continue work on this separate branch. Do not alter the PC install or current #build-install downloads during the play session.
2. Before a real candidate build, create the 0.7 build/version metadata from the dev.115 source. The inherited implementation is still under releases/0.6; this preparation does not pretend an already built 0.7 exists.
3. Keep gameplay ID `freedomarrow.gameplay` and asset ID `freedomarrow.assets.live`. Assets stay type `mod`, gameplay type `modpack`. Correct the stale 0.4 package display name when preparing 0.7 metadata.
4. Stage `assets/models.json` into an isolated asset input directory. Reuse existing asset binaries. Do not edit a live game's models.json while it is running. The current full-pack builder reads mappings from its staged game input.
5. Advance the asset package version only when building its actual update. Preserve playlist choice and keep PLA test assets outside the distributed live pack. The prototype ZIP delta updater is not a BAModManager package; do not advertise it as normal one-click installation.
6. Generate and verify gameplay tables, compare against the baseline, and confirm no accidental stat changes. Su-75 remains at 2 availability; XM30 remains named XM30.
7. Run installer replacement/coexistence checks with the candidate. Close the game before a later authorized installation. Preserve a rollback and verify installed hashes.
8. After installation, inspect XM30 in armory and battle for scale, ground contact, launcher clearance and effects alignment. Label observations separately from source/data checks. Follow the guarded offline Local AI Skirmish rules for a match.
9. Publish/install only when the group asks for the next update. Update the existing #build-install posts then; they continue to point at the current version now.
10. Finalize the changelog and sync the requested sheet/Bible/reports at the release batch boundary. No new release date is set.

## Open Abrams X defect

**Osama reports smoke and jammer absent during the current play session. This is unresolved, not fixed.** A read-only PC log check confirms dev.115 initialized at 16:50:24 and its whole-table application completed at 16:50:26. The packaged unit has intrinsic default smoke (1 charge), Trophy APS (2 charges) and ECM multiplier 0.7 (30% jammer). Those assignments do not prove that a spawned unit received usable abilities. The earlier data checks were insufficient proof of runtime behavior. Investigate initialization/selected options and model-component dependencies in an isolated run; do not blame an old PLA runtime or install a speculative change during play. See abramsx-defense-investigation.json.

## Evidence limits

This is source and configuration preparation only. No 0.7 archive, game launch, installation or gameplay test occurred. The existing 15 installer-engine tests apply to dev.114/dev.115 and asset 0.1.1, not to a future 0.7 package.

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
