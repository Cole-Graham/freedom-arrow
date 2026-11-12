# Map, border and lobby test batch

**lat.19 implements Lateralus's requested map changes on the maintained dev.55 base. It is an isolated candidate, with no installation, native visual test or live-lobby verification performed.**

## Source and package

- Branch: `codex/batch/lateralus/map-borders-lobby`.
- Base: `codex/0.7-development`, `939658d500d4fee4a27c9ad7ac655e6f47d9e6c8`.
- Package: `FreedomArrow-0.7.0-devtest.lat.19.bamod`.
- SHA256: `61b7e8e2b4b0d52c7cd0cad591adf43c52043376485a4d8787a3886eb449f323`.
- This is a complete gameplay candidate. It does not contain the separate PLA pack or replace shared model/music assets. Public dev.45/assets 0.1.14 and the main integration branch remain pinned.

## What changes

1. A constant-width border overlay follows native active PlayZoneBounds. It uses a 3-pixel opaque orange line and 7-pixel dark outline, cached native terrain heights, near-plane clipping and viewport clipping. It also draws native full-map bounds without an explicit zone. No gameplay boundary or objective material is changed. Sample count is capped at 192 per edge. Zone/controller disposal clears the cache; any rendering failure disables this feature for that controller.
2. Chkalovsk's existing inactive playable-zone object is selected via `head.spz`. Its bounds are X 0–9000, Z 0–4850.01636, with the north edge 1500 engine units beyond Alpha's centre. Airbase MapSettings confirms the full legal map is 9000×9000; 5000 was the authored zone depth, not the map size. All authored objectives and spawn positions remain.
3. Dead Center 1v1's three red spawns face toward the objective centroid. Each team's camera is placed at its spawn centroid, with its look-at tag 1200 engine units inward and height 700. Blue spawn facings, objectives and play area remain.
4. A bounded lobby repair retries the local unready FA scenario card's native deck fill/accessibility path after initialization. It runs at most once per frame, at half-second intervals, for at most 15 seconds/30 attempts. A working dropdown is left alone. Country/DLC/scenario checks remain; it sends no map-selection or readiness request and selects no deck. The initial metadata timing problem is a code-based hypothesis; this candidate has not demonstrated a live fix.
5. Highway of Death uses Lateralus's supplied Frontiers export and the exact name `[FA] [2v2] Highway of Death 0.1`. It has two slots per team, native A–G icons matching editor names, new per-team cameras and inward spawn facing. A/B/C/G score 2, F 3, D/E 6. FA conquest/deployment scripts and an offline Skirmish flavor are included. Objective UIDs 10031–10037 keep client-side weight resolution distinct from Chkalovsk's 31–37.

## Evidence and limits

- Runtime compilation: zero warnings/errors against the pinned generated game assemblies.
- Package verification: all 71 payload hashes and scenario metadata checks passed.
- Row/reference regression tests: 25,869 checks passed.
- Border screen clipping: 14 host cases passed, including viewport crossings, reversed segments, boundaries, non-finite inputs and distant coordinates.
- All 24 packaged gameplay constant files are byte-identical to dev.55. Existing AA speed/prediction/overkill, 15 helicopter flares and item #10's four AT4 carriers are retained.
- All 14 scenario archives are byte-identical across two separate generations. Network and offline variants have matching physical layouts.
- Raw source/evidence is kept in `work/map-borders-lobby-20261111` on BA Codex's workspace. Build commands use `--no-scenario-copy`; no game bundle or installed scenario was changed.

These are compilation, code/data and host-test results. They do not prove the native hooks fire, the visual is readable in HDRP, the overlay is clear around HUD panels, or the lobby symptom is fixed. No frame-time result is claimed. Native tests are pending.

## Test in the game

Import lat.19 through Mod Manager, then check the exact version label. Use the offline Local AI Skirmish path and verify its guard before a battle. Do not use multiplayer as an automated test.

- Check Chkalovsk at Alpha, Charlie and both spawn sides; confirm the border and legal movement agree.
- Check Highway's A–G symbols and weights, both team cameras, initial deployment and conquest scoring. Confirm the native active box clips the authored zone at Frontiers' full map edge.
- Check Dead Center from both teams; red reinforcements should arrive facing inward, and each camera should look toward the fight.
- Check the line at maximum/minimum zoom, top-down and oblique views, and on land/water. Verify active-zone changes and full-map fallback. Check HUD interference and frame cost.
- A human may verify their normally authorized mod lobby: without reselecting the map, check the host dropdown, then a joining client's dropdown. Compare allowed/forbidden country decks, ready-state lock and an empty deck library. No country or readiness restriction should be bypassed.
- Save the automatic test-log ZIP. Look for `playable_borders_installed`, `playable_borders_bounds`, and any `playable_borders_failed`; inspect `lobby_deck_refresh` and `lobby_deck_refresh_failed` for the UI repair.

## Document change log

- 2026-11-11 23:47:30 PST (America/Los_Angeles) — Recorded isolated lat.18 implementation, exact package hash, data/host checks, native evidence limits and the verification checklist.
- 2026-11-11 23:51:28 PST (America/Los_Angeles) — Superseded internal lat.18 with lat.19: run native accessibility before native fill so an empty/missing-map dropdown remains disabled. Map/border code unchanged.
