# Model loader: clear canopy preset

FAModels 0.3.4 adds an opt-in canopy preset. It is compiled against the pinned game assemblies. The eight supplied material sidecars resolve to their mesh draw keys and preserve every opaque material. Final game appearance is pending.

Use `clearGlass: true`, `opacity: 0.025`, `alpha: "BLEND"`, `metallic: 0` and `smoothness: 0.95` on confirmed glass draws only. This uses neutral, low-opacity glass without its base/normal/metallic mask maps. Cockpit interiors and frames retain their original textures. Transparent fog, preserved opaque specular and double faces are disabled for the flagged draw. Other materials, including the approved B-21, are unchanged.

Build with the project's dotnet wrapper:

```sh
dotnet build FAModels.csproj -c Release -p:GameDir=/path/to/pinned/game
```

The separate normals tool accepts FAM models and writes new copies. It splits vertices only where needed for a 30-degree crease. It asserts identical triangle positions and UVs per corner. It changes no textures or attachment names. Requires NumPy.

```sh
python fix_panel_normals.py --source /path/to/models --output /path/to/candidate m_ztz100_cg m_ztz100_lo
```

For ZTZ-100 battle geometry, the mean normal/face angle on the largest faces falls from 24.4 to 2.2 degrees. A neutral shaded Blender comparison shows flatter panels. This is a geometry calculation and preview, not a game measurement.

Install only after closing the game, back up the old loader and affected model files, verify hashes, and restart. Check both armory and battle copies. Inspect canopy face orientation and compare the view against the vanilla F-15E under equal lighting. Low opacity cannot add missing cockpit geometry.

[How to Add New Units, section 13.15](https://docs.google.com/document/d/1k2zs6IMNMcyygotSppubcDCUbwtWK8KWTV-hk4jBTUg/edit) contains the public procedure.

Coverage check: enumerate every live aircraft in the model map, then inspect both its armory and battle sidecars. F-14, Su-47, Su-57D and YF-23 now use the clear preset in eight files. The YF-23 was missed in the first pass and retained dark30%-opacity glass with double faces; it was corrected after Osama's screenshot. Preserve the approved B-21 preset. A filename-only search is not a complete coverage check.

## Document change log

- 2026-11-09 23:04:20 PST (America/Los_Angeles) — Added versioned clear-canopy source, eight sidecars and normals correction recipe; stated pending runtime checks.
- 2026-11-09 23:39:56 PST (America/Los_Angeles) — Added YF-23 armory/battle material presets and mandatory coverage check; runtime appearance pending.
