# PLA TEST Build 9 validation

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
