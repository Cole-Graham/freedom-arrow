# PLA TEST Build 13: assigned equipment, shared lift and recon gunships

**The complete equipment draft is assigned to five main specs. No ships, submarines, UUVs or White Emperor are playable. YJ-18 is a ground cruise-launcher prototype. Test retains only the 28 infantry appearance/rigging fixtures. Data and package checks pass; native behavior remains unverified.**

- 63,365 actual RowPlanner/reference checks; 127,234 planned writes across 24 tables. All equipment has a main-spec pool, all excluded cards have no pools, every rigging fixture remains Test-only, and transport capacities cover the linked squads.
- 160 equipment design records and 218 memberships; the six previous recon gunship plans now point to six actual new unit IDs. User design fields were preserved, and dependent formula checks found no errors.
- Main pool memberships: Airforce/Airborne 51, Armored 51, Rocket Force/Conscripts 69, Marines/SF 40, Motorized 47; Test 28. These are memberships, not unique model counts or final balance.
- The six recon versions retain parent weapons, sensor baseline and provisional cost. No recon stat bonus is invented. Gunships are excluded from troop-carrier choices, and the three transport-donor gunship capacities are cleared.
- YJ-18 uses native Iskander-K ground appearance, the two-cruise-missile weapon graph and donor statistics. Ballistic/ship weapon branches are absent from this unit. Final Chinese performance/art are not claimed.
- 7,977 payload hashes and 78 core hashes pass. All 7,895 compared shared assets match Build 12, including exact body/weapon bindings, all geometry, textures, cockpit finishes and music.
- Runtime 13 and FAModels 0.3.13 compile with zero warnings/errors. Russia/USA selector/spec controls and hidden unit cards are retained. No multiplayer test was performed; public LIVE dev.45 is unchanged.

## Historical Build 12 checks

# PLA TEST Build 12: equipment catalogue and Arsenal country controls

**Build 12 adds 102 named stand-ins from a pinned 157-entry model/description audit and retains the complete Build 11 content. Data and full-package checks pass. Native Arsenal filtering, deck creation and combat remain unverified after these changes.**

- 61,220 RowPlanner/reference checks across 24 tables; 123,252 planned writes. No default armor, carried-weapon/ammo graph or signed-short option-ID failure was found.
- Runtime 12 and FAModels 0.3.12 compile with zero warnings/errors. The identity helper accepts the 46 exact approved body IDs.
- 7,976 payload hashes and 77 core hashes pass. The linked Mod Launcher core accepts a fresh local-file installation with 7,977 files. This does not prove the Windows launcher GUI, download or PLAY flow.
- All Build 11 model geometry, textures, cockpit finish, music and approved alignment values are retained. The model map intentionally switches SR-5 to native HIMARS and reuses applicable bindings for new cards.
- 220 visible PLA units; spec memberships are Airforce/Airborne 17, Armored 24, Rocket Force 28, Marines/SF 28, Motorized 23 and Test 157. A shared ID remains one actual unit.
- Russia/USA country and spec controls remain visible, while all non-China unit DisplayInArmory flags are false. This addresses the single-country filter-mask collision diagnosed from Build 11 logs; native success has not yet been demonstrated.
- The equipment-only editable sheet has 174 current/draft equipment records plus six planned recon gunship records, with 219 spec memberships. Existing infantry is retained in-game and uses its own squad designer.
- A linked model or description permits a named donor stand-in; it does not establish ownership, local file availability, final weapons, final performance or distribution rights. No assets were purchased.
- The source catalogue is a dated snapshot. Subsequent human sheet edits must be reconciled by unit ID/name, without overwriting design fields. No LIVE merge or multiplayer test was performed.

## Historical Build 11 evidence

# PLA TEST Build 11: combined Build 9 and Build 10

**Build 11 retains all Build 9 branch/Test/infantry work and Build 10 immediate stand-in hiding. The complete archive and parent comparison pass. It is not installed and native behavior remains unverified.**

- 7,966 inherited Build 9 files compare byte-for-byte after excluding explicit version/manifest updates. Every gameplay table and repaired infantry asset is retained.
- Build 10 static models, cockpit configuration and music compare byte-for-byte. Its immediate-hide and failure-restoration loader source matches exactly except the version label.
- 7,975 payload hashes, 76 core hashes and 41,542 data/reference checks pass. Runtime 11 and FAModels 0.3.11 compile with zero warnings/errors.
- Linked Mod Launcher core accepts a fresh file install with 7,976 files in a disposable folder. Windows GUI, network download and PLAY remain untested.
- merge-provenance.json records both exact parent archive hashes and source commits. Run verify_merge.py against the pinned parent archives and Build 11 to reproduce the union check.
- This is a PLA-only candidate. Canonical installed Build 10 and the public LIVE dev.45 lock remain unchanged.

## Historical Build 9 evidence

**Data and complete-package checks passed. The user accepted the replacement arm fit in offline previews. Native Arsenal, deck creation, animation and combat are untested; this candidate is not installed.**

## Current checks

- 41,542 actual RowPlanner/reference checks across 24 tables; 76,210 planned field writes.
- 7,974 payload hashes and 75 core hashes verified. 7,861 inherited payloads are byte-identical to pinned canopy Build 8.
- The linked Mod Launcher core accepted a fresh local-file install with 7,975 files in a temporary fake game folder; Windows GUI, network download and PLAY remain untested.
- Both runtime plugins compiled with zero warnings and zero errors. The actual body-ID helper accepts all 44 intended body rules and rejects adjacent IDs.
- Branch pools: Airforce/SF 20, Armored 24, Rocket Force 28, Marines 27, Motorized 23, Test 52. These are card memberships, not finished unique model counts.
- All 25 infantry variants rebuilt at three LODs. 142 of 150 atlases remain byte-identical; eight lower-LOD atlases are repacked because their UV bounds changed. Source texture images are unchanged.
- The old fit visibly collapses sleeves in a controlled Blender bend. The replacement preserves arm thickness under the same pose. This is offline evidence, not a native animation result.
- Original body/weapon rules remain an exact prefix of the new binding files. Native weapon grip offsets and woodland helmet clearance are retained.
- All static models, cockpit configuration and aircraft canopy assets match the exact pinned Build 8 base. Vehicle combat statistics are unchanged by the branch draft.

## Reproduction

Use the SHA-pinned base in pla-specializations-contract.json. Run prepare.py with that archive and the pinned vanilla table snapshot. Run tools/pla-infantry/rig_configs.py against the supplied Type 21 source directory and BA_US_Ranger_Rifle1.glb donor, then atlas.py and stage_arm_payload.py. Compile Runtime 9 and FAModels 0.3.10, run row-tests and identity-tests, package with package.py, and verify with releases/0.6/verify.py. Assets remain external to source Git.

## Merge and install boundary

Keep canonical profile aliases and public dev.45 unchanged. Initial native tests use an isolated copy. Later LIVE integration must allocate collision-free graph IDs and omit the PLA-only country/card visibility rules. Existing PLA IDs 971, 972, 973 and 985 conflict with current LIVE units. No multiplayer test was performed and native country-4 support remains unverified.

## Historical internal candidate 6

The following was measured before the user requested Test and the arm repair; it is not the current package.

**Data and complete-package checks passed; native UI,deck creation and combat remain untested.**


-41,420 actual RowPlanner/reference checks pass across24tables.
-All7,935 payload hashes and73core hashes pass;7,907 existing payloads are byte-identical to Build5.
-Configured card pools:Airforce/SF33,Armored29,RocketForce34,Marines28,Motorized27. These include shared/additional existing prototypes and exclude transport-only cards and QA fixtures; they are not counts of finished unique units.
-Four existing unit IDs conflict with dev53:971(J31/F22dummy),972(WZ8/MiG29Kdummy),973(FH97A/Karatel),985(uniformfixture/BlackEagle). Fresh ID allocation is required at the later source merge.

## Mod Launcher file-import check

The linked upstream LauncherService/ModService installed the full package into a temporary fake game folder and selected PLA TEST Build6 with7,936 files. The test cleaned up its own files. This is a local-file/core compatibility check; Windows GUI,automatic download and PLAY remain untested.

## Reproduce

Prepare from the SHA-pinned complete Build5 with tools/pla-specs/prepare.py. Compile the runtime against the generated MelonLoader assemblies,run releases/0.6/row-tests/Tests.csproj against the pinned vanilla JSON and prepared source folder,then use tools/pla-specs/package.py with the complete Build5 archive and an available zip executable. Verify the output with releases/0.6/verify.py. Do not run the historical build_constants.py:it predates the approved comparison squads.

## Installation boundary

This candidate has not been installed. Use an isolated test copy or reconcile newer local live appearance overrides before any profile switch; its inherited Build4/5 model map predates the live Black Eagle and later appearance trials. Keep the current live install and canonical profile aliases unchanged.

## Document change log

- 2026-11-10 23:32:30 PST (America/Los_Angeles) — Recorded exact data/package checks and collision audit; native limits retained.

- 2026-11-10 23:34:48 PST (America/Los_Angeles) — Added measured launcher file-import result,reproduction path and installation preservation boundary.

- 2026-11-11 00:10:03 PST (America/Los_Angeles) — Recorded combined Build 9 checks, Test pool, arm repair and exact canopy base preservation; kept candidate 6 results historical.

- 2026-11-11 00:24:15 PST (America/Los_Angeles) — Added Build 11 exact parent-union checks and package validation; preserved Build 9/6 historical evidence.

- 2026-11-11 01:12:58 PST (America/Los_Angeles) — Recorded Build 12 catalogue, reference/package checks, equipment-only sheet scope and native UI limits.

- 2026-11-11 01:55:38 PST (America/Los_Angeles) — Added Build 13 assignment, exclusion, cruise-launcher, transport, recon and preservation evidence; native limits retained.
