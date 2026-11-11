# Abrams X grey-panel material trial

**This trial gives the existing grey armour a stronger metallic response without increasing texture resolution. Only metallic/smoothness channels in two hull mask maps change. Gameplay remains dev.42.**

- Armory2048×2048, battle1024×1024; no additional textures or shaders.
- Grey paint is selected from the difference between approved green and silver colours, then gated by low colour saturation and medium brightness. This is a calculated texture classification, not a hand-labelled material-ID map.
- Grey metallic median rises from approximately0 to0.55; smoothness median rises from0.58 to0.65. These are texture values, not measured frame-time results.
- Pixels outside the selected grey regions remain identical in all channels. Occlusion/detail channels remain identical everywhere. Colour maps, normals, tracks, meshes, mapping and gameplay are preserved.
- Source/output hashes and pixel checks are in abramsx-grey-sheen-trial1.json. The generator requires the approved silver maps and previous green maps; installer rejects mismatched existing files and checks game closure.
- Preview is rendered in Blender. Native appearance and performance require a restart and game inspection.
- Unity HDRP channel reference: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/Mask-Map-and-Detail-Map.html

## Document change log

- 2026-11-10 17:54:55 PST (America/Los_Angeles) — Prepared the grey-only material trial, fixed2K/1K limits, pixel preservation checks and guarded backup/restore installer.
