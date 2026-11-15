# dev.9 batch: support tab to vanilla level (Osama 14 Nov 2026 22:4x-22:5x PST)

"same level of textures and lod" / "estimate what vanilla has and pare it down" / 22:49 "looks good" (meshes) / "bring support textures down to near vanilla size too".

Add every line of `support-assets.txt` as `--asset` when the dev.9 batch is built (265 lines):
- 24 armory meshes from `support-lod/out/` cut to the matching vanilla unit's LOD0 triangles (max 3x per pass). 2.97M -> 1.57M triangles,
  168 -> 91 MB. Bones, sub-meshes and materials checked identical to dev.8 (24/24).
- 241 GPU textures from `support-tex/fat/` (plan `support-tex/plan_tex.json`): 38 support armory models at or under 6.3 Mpx each
  (vanilla: one 2048 colour + 1024 mask + 1024 normal). 677 -> 182 MB. Made from Assets 0.2.32 PNGs, BC7 25 / BC5 27, rows bottom-first.
  No texture is shared with a non-support model (checked against every .fam in dev.8).
Not done: PCL-181 still 134k triangles (Malva 39k); HQ-11 66k (Buk 52k). Before/after sheets: support-lod/sheet*.png, support-tex/sheet*.png.
`models.json` and `rend/` in this folder are the rejected battle-LOD armory trial (Osama: "not acceptable"). Do not use them; dev.9 starts from dev.8 models.json.
Approved by Osama 14 Nov 2026 22:59 PST ("looks good") for meshes and textures. Build only when Osama or Lateralus say the dev.9 batch is ready.
