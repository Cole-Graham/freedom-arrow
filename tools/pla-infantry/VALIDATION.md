# PLA TEST Build2 — native armory validation

**All25 new infantry appearance cards were selected and rendered in the game on Vengeance. Each showed7 soldiers and accepted21 body renderers:525 successful applications,0 failures.** Screenshots were captured for every card and reviewed after the user-requested foot-height correction.

## What was checked

- Game: Unity6000.3.24f1; native GameAssembly SHA256 `12e7088369539b029a7bf0064062ce030a53b5189e7067420903f47b4281fddf`.
- Model loader: FAModels0.3.5;26 body rules (approved901 plus985–1009). Data receipt:23 tables,70,518 fields.
- Native armory selection uses the game's card callback. The opt-in helper records displayed unit ID, soldier count and renderer applications. Each screenshot also has an expected model-file binding checked in Latest.log.
- Coverage:25 configurations; all53 special-forces source mesh objects included. Separate woodland/desert regular models are included; the regular FBX's embedded rifle is omitted from the body because the squad equips its separate game weapon.
- Ground correction: new regular bodies use Y+0.00311m; new SF bodies use Y+0.01558m. These raise the first-pass bodies5.311cm/6.558cm. Native armory screenshots show boots at the paving after correction. Approved901 staysY−0.05m and existing weapon offsets remain intact.
- Offline:75 skinned LODs validated;3,646,438 vertex/index checks; normalized weights and all textures present.36 pipeline tests pass (one skipped), and6 profile selector tests pass.
- New cards keep the approved901 squad's50-point cost,7 members, weapon/ammunition data and abilities. All pre-existing database rows are asserted unchanged by the Build1-to-Build2 recipe.
- Archive SHA256: `904e2f51da19d95448327644813c1711ac1f45cfda0f39306befea5827acd3de`;3,477,938,532 bytes;7,932 payload entries checked in the isolated copy.
- [Raised-body native screenshot](https://discord.com/channels/1566969627743879208/1567745029781454889/1569809507255713834).
- Raw evidence is retained in the BA task directory `work/pla-infantry-configs-20261110/`: per-card screenshots/results, logs, source inventory, rig audit, alignment calculation and validation outputs.

## Limits

This verifies native armory appearance, idle poses, equipped weapon visuals and successful assignment of all three LOD meshes. It does not establish battle locomotion, firing/reload animation, all LOD transitions, terrain following, combat balance or frame time. The review used an isolated game/prefix; the main live install was not replaced. Source weights were transferred to the exact native40-bone donor; these are provisional fits that can still need hand/equipment refinements.

## Document change log

- 2026-11-10 12:30:14 PST (America/Los_Angeles) — Recorded all25 native armory checks, sole-height correction, archive identity, offline checks and measured limits.
