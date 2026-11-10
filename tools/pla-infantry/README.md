# PLA infantry configuration test build

**PLA TEST Build2 adds25 comparison squads and fits the supplied Type21/special-forces meshes to the native Ranger skeleton. Keep the approved squad901 and its offsets.** All25 cards have now been checked in the native armory:7 soldiers,21 body applications and0 failures per card. This verifies appearance and idle poses; battle movement, firing, reloads and frame time remain untested.

## Reproduce

Use Blender5.2.3, the original extracted Ranger GLB, the supplied archive with SHA256 `933b61b7ba6fdf1bc29fe7140111866de542b93b138e54eee74a3b23153c59af`, and the complete Build1 package with SHA256 `ea2058ba5852df3b41a8dd9981ec9070d2bb4f223e10d39738631b03434a8364`.

1. Extract the two inner archives as source/regular and source/special. Run rig_configs.py in Blender with --source, --donor and --out. The contract lists25 card IDs985–1009. All53 special-forces mesh objects occur in at least one configuration. The regular model’s embedded QBZ191 is excluded from the body because the squad equips the separate game weapon.
2. Run atlas.py with the rig directory and output FAModels directory. It preserves source UVs by consolidating each object’s active UV layer before joining. Texture wrapping is baked into each atlas tile; every FAS uses one material. Source Photoshop links resolve to supplied TGA counterparts.
3. Build experimental-model-loader/FAModels.csproj against the pinned game assemblies. Loader0.3.5 permits the approved card901 and the25 comparison IDs. It keeps the original40 bone names/bind matrices and native weapon attachments.
4. Run verify_rigs.py with the rig and FAModels output directories. Run build_from_pack.py with --base, --vanilla, --rigs and --out. This recipe reads the pinned published Build1 data and asserts every existing row is unchanged. It appends only the comparison cards and their links. Do not replay the older balance history to assemble this package.
5. Install in an isolated game copy. Native startup must confirm the data applied and26 body rules loaded. Inspect every card and retain the body application/failure logs and screenshots.

The rig uses nearest-surface native weight transfer, maximum4 influences, normalized weights, a provisional14-degree shoulder fit and three decimated LODs. Heads, helmets and carriers use rigid head/torso weights. Equipment fit and weapon grips need human visual review. This is not a measured performance or combat-balance result.

## Test-copy review helper

No new user interface is added. A test-copy-only `UserData/FAModels/pla-review-unit.txt` request selects the matching native armory card and frames its squad. IDs are restricted to901 and985–1009; no battle is created. `pla-review-state.json` records the displayed card and applied/failed body renderers. Remove the request file for ordinary camera control. This file is never packaged.

## Document change log

- 2026-11-10 12:12:15 PST (America/Los_Angeles) — Recorded the25 configurations, pinned Build1 migration recipe, UV correction, rig method and isolated armory evidence requirements.

- 2026-11-10 12:29:01 PST (America/Los_Angeles) — Recorded the complete25-card native armory pass and user-requested ground correction: new regular bodies+0.00311m, SF+0.01558m; approved card901 remains−0.05m.
