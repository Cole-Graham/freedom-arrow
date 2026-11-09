# Optional PLA infantry visual prototype

**FAModels 0.3.2 replaces body and weapon visuals for unit 901. It is installed separately; the core package does not include this optional DLL or source model files.**

## Details and evidence

The loader reads infantry-bodies.json (three FAS1 LOD files) and infantry-weapons.json. Skinned bodies reuse native bones, bind matrices, animations, weapon attachments and LOD groups. Body renderer lookup uses each InfantryData.ViewObject and MeshRenderers, rather than only the squad prefab root. Missing mappings keep the native renderer. Weapon rules retain native firing scripts and effects.

Bind visual rules to IDs from UserData/FreedomArrow/pla-infantry-prototype.json in the exact test package. Do not reuse IDs from an earlier candidate. Stats and ammo are defined by pla-infantry-contract.json, independently of these visual files.

Runtime logs confirmed seven body replacements across all three LODs in the initial test. The user reported hand-height and pouch problems. Local fitting now excludes gear from the arm adjustment and lowers upper-body geometry 4 cm while preserving sole contact. Revised fitting remains unverified in game. Weapon alignment, native firing effects and visibility still need inspection.

Build with the .NET SDK and -p:GameDir pointing to the existing generated MelonLoader assemblies. Keep paid/user-supplied models outside Git.

## Body placement correction — 9 November

**Version 0.3.2 adds a body-only world offset for the PLA test. Native weapon transforms remain fixed. The hand-centroid mesh pass was rejected after Sam showed distorted fingers and continued low rifle alignment. Restore the earlier body meshes, then test offset [0, -0.05, 0] metres. This new runtime path is compiled, not yet verified in game.**

Body rules accept a three-component finite offset, capped at 0.15 metres per axis and restricted to unit 901. Each body renderer uses visual-only child transforms of the original bones. LateUpdate converts the world offset into each native bone's local coordinates. All child rotations/scales remain identity. The native animation bones and weapon attachments remain in place; translating every visual bone equally translates the skinned body without separating palms and finger joints. Visual children are shared across LODs using the same native bone and are destroyed with their parent. No per-frame mesh copying is required.

Zero-offset rules retain the original bones. Old configurations without offset default to zero. This is an experimental fit control; root motion, animation timing, clipping, foot placement, scene cleanup and battle performance still need runtime checks. Lowering the whole body 5 cm also lowers boot soles by 5 cm, so slight ground clipping is an explicit test tradeoff. Do not call the posture or grip fixed based on compilation or matrix calculations.

## Approved positions — 9 November

**Sam approved the installed appearance: “looks good, lock in the positions.” Preserve this body/weapon fit as the baseline.**

The body-only offset is [0, -0.05, 0] m, with the earlier pre-regression body meshes and loader 0.3.2. Native weapon positions remain fixed. Custom offsets, scales, rotations, exact body/weapon files and loader hashes are pinned in approved-infantry-fit.json. The observed core version at approval was pla.infantry.7; the fit check does not require that core version, so unrelated gameplay updates may proceed.

Run `python3 check_approved_fit.py /path/to/broken_arrow` before/after future model installations. It is read-only and fails on changed rule files, body/weapon geometry or loader. A loader-only update can legitimately fail the hash check and must be reviewed before refreshing the baseline; do not overwrite this approval automatically. This is a recorded user visual approval, not independent verification of firing, resupply, movement or every animation.

## Document change log

- 2026-11-09 14:23:06 PST (America/Los_Angeles) — Added optional skinned-body/weapon loader source, actual hook evidence and revised-fit limits.
- 2026-11-09 15:32:11 PST (America/Los_Angeles) — Added body-only visual-bone translation, finger regression rollback and explicit runtime limits.
- 2026-11-09 15:47:15 PST (America/Los_Angeles) — Recorded Sam’s visual approval, pinned installed fit and added a read-only drift check.
