# Optional PLA infantry visual prototype

**FAModels 0.3.1 replaces body and weapon visuals for unit 901. It is installed separately; the core package does not include this optional DLL or source model files.**

## Details and evidence

The loader reads infantry-bodies.json (three FAS1 LOD files) and infantry-weapons.json. Skinned bodies reuse native bones, bind matrices, animations, weapon attachments and LOD groups. Body renderer lookup uses each InfantryData.ViewObject and MeshRenderers, rather than only the squad prefab root. Missing mappings keep the native renderer. Weapon rules retain native firing scripts and effects.

Bind visual rules to IDs from UserData/FreedomArrow/pla-infantry-prototype.json in the exact test package. Do not reuse IDs from an earlier candidate. Stats and ammo are defined by pla-infantry-contract.json, independently of these visual files.

Runtime logs confirmed seven body replacements across all three LODs in the initial test. The user reported hand-height and pouch problems. Local fitting now excludes gear from the arm adjustment and lowers upper-body geometry 4 cm while preserving sole contact. Revised fitting remains unverified in game. Weapon alignment, native firing effects and visibility still need inspection.

Build with the .NET SDK and -p:GameDir pointing to the existing generated MelonLoader assemblies. Keep paid/user-supplied models outside Git.

## Document change log

- 2026-11-09 14:23:06 PST (America/Los_Angeles) — Added optional skinned-body/weapon loader source, actual hook evidence and revised-fit limits.
