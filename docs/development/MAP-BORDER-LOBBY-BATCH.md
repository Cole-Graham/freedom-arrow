# Map, border and lobby test batch

**Promoted to main 0.7 development as dev.56 (Lateralus, 12 November 2026: "push # 13 - 21 to the main dev build"). lat.24 implements Lateralus's requested map changes on the maintained dev.55 base. It is an isolated candidate, with no installation, native visual test or live-lobby verification performed.**

## Source and package

- Branch: `codex/batch/lateralus/map-borders-lobby`.
- Base: `codex/0.7-development`, `939658d500d4fee4a27c9ad7ac655e6f47d9e6c8`.
- Package: `FreedomArrow-0.7.0-devtest.lat.24.bamod`.
- SHA256: `897b7efcb15c0fc76cab4fa167a18a11d3559c5ea8cf19bd4cb19220147e14f0`.
- This is a complete gameplay candidate. It does not contain the separate PLA pack or replace shared model/music assets. Public dev.45/assets 0.1.14 and the main integration branch remain pinned.

## What changes

1. A constant-width border overlay follows native active PlayZoneBounds. It uses a 3-pixel opaque orange line and 7-pixel dark outline, cached native terrain heights, near-plane clipping and viewport clipping. It also draws native full-map bounds without an explicit zone. No gameplay boundary or objective material is changed. Sample count is capped at 192 per edge. Zone/controller disposal clears the cache; any rendering failure disables this feature for that controller.
2. Chkalovsk's existing inactive playable-zone object is selected via `head.spz`. Its bounds are X 0–9000, Z 0–4850.01636, with the north edge 1500 engine units beyond Alpha's centre. Airbase MapSettings confirms the full legal map is 9000×9000; 5000 was the authored zone depth, not the map size. All authored objectives and spawn positions remain.
3. Dead Center 1v1's three red spawns face toward the objective centroid. Each team's camera is placed at its spawn centroid, with its look-at tag 1200 engine units inward and height 700. Blue spawn facings, objectives and play area remain.
4. A bounded lobby repair retries the local unready FA scenario card's native deck fill/accessibility path after initialization. It runs at most once per frame, at half-second intervals, for at most 15 seconds/30 attempts. A working dropdown is left alone. Country/DLC/scenario checks remain; it sends no map-selection or readiness request and selects no deck. The initial metadata timing problem is a code-based hypothesis; this candidate has not demonstrated a live fix.
5. Highway of Death uses Lateralus's supplied Frontiers export and the exact name `[FA] [2v2] Highway of Death 0.1`. It has two slots per team, native A–G icons matching editor names, new per-team cameras and inward spawn facing. A/B/C/G score 2, F 3, D/E 6. FA conquest/deployment scripts and an offline Skirmish flavor are included. Objective UIDs 10031–10037 keep client-side weight resolution distinct from Chkalovsk's 31–37.
6. `[FA] [5v5] Airport 0.1` is Lateralus's 12 November export of his redesigned Airport, with his script, built by `scenarios/airport_5v5`. It replaces the vanilla-built `[FA] Airport 0.1`. Values: H and J 4; A and D 3; B, C, E, F, G and I 2. Five slots per team. The native size logic is removed: lobby Size option 53, Play Zone Small (uid 55), and nodes 22, 34–36, 187, 196–198, 210, 223, 225, 228, 229, 231, 232, 239, 245, 248, 249, 253, 257, 264, 265, 337 and their comments. Conquest node 330 now starts directly when the match is not matchmaking. Play Zone Large (uid 10, 9000×9000) is the only play area. Nodes 223/225/228/229 were the editor's "missing any target" warnings: they hid native zones 40 (Golf) and 46 (India) for medium and small lobbies, and those zones are not in the redesign. Zone labels Golf, Hotel, India and Juliett showed other names and now match. The Skirmish flavor has no deployment pause and bots in all 10 slots.
7. Every FA map's objectives use the vanilla 15-second capture time (`common.CAPTURE_SECONDS`, set in `write_flavor`). Dead Center 1v1, Chkalovsk and Highway were 5 seconds from their editor exports; the other maps were already 15 seconds. No other scenario byte changes.
8. lat.21 border fix. Lateralus tested lat.20 on 12 November: no change, only the vanilla orange wall. Measured in GameAssembly.dll: zero direct calls to `PlayableZone..ctor` (RVA 0x70F5A0), so the lat.18–20 constructor postfix never ran and the overlay had no zone. `add_OnZoneBoundsChanged` (0x70F6A0) has one direct caller, `MiniMapBehaviour.OnMissionLoaded`, and `SetPlayZone` (0x70F2F0) one, `PlayableZoneScript.OnActivatePlayableZone`. lat.21 takes the zone from postfixes on these two. `ContainsForPlayer` (7 callers, including target search) is not hooked, to avoid per-search cost. If `Camera.main` is null, the enabled screen camera with the highest depth is used. Not yet run in a game.
9. lat.22 border look. Lateralus tested lat.21 on 12 November (screenshots in the task thread): the line drew, but it was aliased, drawn over trees, units and the HUD, and he asked for white without the dark outline, maybe slightly transparent. lat.22 removes the IMGUI overlay. A MeshRenderer strip faces the camera and is rebuilt when the camera moves, so its width stays about 4 pixels. Its material is a runtime copy of the game's `ObjZone_Border` (HDRP/Unlit, transparent alpha blend, `_ZTestTransparent` 4 = LessEqual, read from the prefabsme bundle), with `_UnlitColor` white at alpha 0.8 and a 32-texel alpha ramp across the strip for soft edges. The renderer uses the objective-border renderer's layer when found (else 0), casts no shadows and writes no motion vectors. Terrain heights are sampled every 10 engine units (at most 1025 points per edge); the strip is lifted 1.5 units plus its half width. Host tests check the strip's screen width, direction, lift and fallbacks (7 cases). Expected trade-off: tall tree canopy now hides the line in forests. Not yet run in a game.
10. lat.23 maps. Lateralus confirmed the lat.22 border looks good and sent `[FA] [3v3] Baltiisk 0.1` and `[FA] [3v3] Dam 0.1` (12 November) to replace the vanilla-built Baltiisk and Dam. `scenarios/baltiisk_3v3` and `scenarios/dam_3v3` keep his scripts, cameras and play areas, like `airport_5v5`; the shared code is `common.prepare_authored` and `common.build_authored`. Values: Baltiisk A B C 2, D E F G 3, H I 4; Dam E F K L 2, A B G H 3, C D I J 4. Baltiisk's Hotel and India were labelled "Echo"; Dam's zones also listed capturing team 7, removed. Both have 5 slots per team although named 3v3. Baltiisk keeps a lobby dropdown named "Compensation" whose values are the native Auto/Medium/Small size; in his script it chooses only the native destruction goals (100 or 200), not the play area. `vanilla.py` and its helpers and the Baltiisk/Dam native pins are removed because no map uses them. Airport and the other maps build byte-identical to lat.22.
11. lat.24 time-up result. Lateralus (12 November): matches ended in a draw when neither side reached 300; a side with 10% more points should win. Before, at time up `Winner` (Mod.cs) let the native `ConquestMode.GetWinner(true)` decide, and that gave a draw below the score limit. Now `Ledger.TimeWinner` decides: score-limit winner, else `MarginWinner` (leader × 100 ≥ other × (100 + `TimeWinMarginPercent`), so any lead over 0 wins), else draw (`TeamSide.Neutral`). Offline `Winner` returns it to `OfflineTick` and skips the native check. Online, `QueueScoreLimitEnding` queues the margin winner at time up and the host sends `NetworkRoomService.SendEndGame`, as for a 300-point win; a draw sends nothing. Host tests: 5 new checks (73 total). Not yet run in a game; the online path races the server's own time-up and is unmeasured.

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

Import lat.24 through Mod Manager, then check the exact version label. Use the offline Local AI Skirmish path and verify its guard before a battle. Do not use multiplayer as an automated test.

- Check Chkalovsk at Alpha, Charlie and both spawn sides; confirm the border and legal movement agree.
- Check Highway's A–G symbols and weights, both team cameras, initial deployment and conquest scoring. Confirm the native active box clips the authored zone at Frontiers' full map edge.
- Check [5v5] Airport: whole-map play area for every lobby size, no Size option, all ten zone labels and values, and spawns outside the old small zone.
- Check that capturing a zone takes 15 seconds.
- Let a match run out of time below 300 with one side 10% or more ahead: that side wins. Under 10%: a draw. Logs show `time_up_result` (offline) or `score_limit_queued` with `timeUp` true (online).
- Check [3v3] Baltiisk and [3v3] Dam zone labels and values, both cameras, and the Skirmish bots.
- Check Dead Center from both teams; red reinforcements should arrive facing inward, and each camera should look toward the fight.
- Check the line at maximum/minimum zoom, top-down and oblique views, and on land/water. Verify active-zone changes and full-map fallback. Check HUD interference and frame cost.
- A human may verify their normally authorized mod lobby: without reselecting the map, check the host dropdown, then a joining client's dropdown. Compare allowed/forbidden country decks, ready-state lock and an empty deck library. No country or readiness restriction should be bypassed.
- Save the automatic test-log ZIP. Look for `playable_borders_installed`, `playable_borders_bounds`, and any `playable_borders_failed`; inspect `lobby_deck_refresh` and `lobby_deck_refresh_failed` for the UI repair.

## Document change log

- 2026-11-11 23:47:30 PST (America/Los_Angeles) — Recorded isolated lat.18 implementation, exact package hash, data/host checks, native evidence limits and the verification checklist.
- 2026-11-11 23:51:28 PST (America/Los_Angeles) — Superseded internal lat.18 with lat.19: run native accessibility before native fill so an empty/missing-map dropdown remains disabled. Map/border code unchanged.
- 2026-11-12 01:57:27 PST (America/Los_Angeles) — lat.20: [5v5] Airport 0.1 replaces [FA] Airport 0.1, size logic removed; 15-second capture time on every FA map.
- 2026-11-12 02:46:12 PST (America/Los_Angeles) — lat.21: border hook fix after Lateralus's lat.20 report; caller evidence from GameAssembly.
- 2026-11-12 03:09:31 PST (America/Los_Angeles) — lat.22: in-scene white border strip using the objective-border material, after Lateralus's lat.21 screenshots.
- 2026-11-12 04:04:59 PST (America/Los_Angeles) — lat.23: [3v3] Baltiisk and [3v3] Dam replace the vanilla-built maps; shared authored-map build; vanilla builder retired.
- 2026-11-12 04:47:28 PST (America/Los_Angeles) — lat.24: time-up margin win (10%), after Lateralus's draw report.
- 2026-11-12 04:49:28 PST (America/Los_Angeles) — Promoted as main dev.56 on codex/0.7-development; the batch branch is kept.
