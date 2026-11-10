# Freedom Arrow 0.7 preparation

**Keep the running/public version on dev.115 and asset pack 0.1.1 while the group is playing. This branch prepares the next release without installing or publishing another playable build.**

## Prepared now

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

## Evidence limits

This is source and configuration preparation only. No 0.7 archive, game launch, installation or gameplay test occurred. The existing 15 installer-engine tests apply to dev.114/dev.115 and asset 0.1.1, not to a future 0.7 package.

## Document change log

- 2026-11-09 16:59:06 PST (America/Los_Angeles) — Prepared the next-version branch, current play baseline, corrected naming decision and pending scale change.
- 2026-11-09 16:59:47 PST (America/Los_Angeles) — Queued XM30 at 190 points for the next update; current play build remains unchanged.
