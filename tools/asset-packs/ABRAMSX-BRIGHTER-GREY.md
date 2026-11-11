# Abrams X brighter mid-grey trial2

**The prior approved grey-sheen finish is saved with a restore script. This trial aims to brighten the mid-greys by reducing their metallic blend from approximately0.55 toward0.32, while retaining the same colour textures and smoothness. Black and very dark-grey pixels are excluded.**

The selector uses the approved green/silver colour difference, low saturation and medium brightness. Pixels with maximum RGB channel at or below0.32 are excluded; the adjustment fades in to full strength by0.40. These are calculated texture classifications, not semantic material IDs. Pixels outside selection and all occlusion/detail/smoothness channels are checked for exact preservation.

Only two material masks change. Armory2048² and battle1024² remain fixed. Tracks, normals, geometry, base colours and mapping stay unchanged. The Blender comparison is a preview; native lighting and frame time are unmeasured.

Generator: prepare_abramsx_brighter_grey.py. Hashed source/output recipe: abramsx-brighter-grey-trial2.json. Guarded installer refuses changed base assets and runs only with the game closed; it backs up the previous masks and asset receipt.

## Document change log

- 2026-11-10 18:08:13 PST (America/Los_Angeles) — Preserved the approved finish and prepared a reversible brighter-grey material trial with black/dark-grey exclusion and existing texture limits.
