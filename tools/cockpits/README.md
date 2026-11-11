# Custom fighter cockpit policy

**The Build 5 candidate assigns native canopy materials to all 20 current custom fighter entries, in both armory and battle model copies. It preserves the existing interiors and frames. Native appearance is not yet verified.**

- F-22 donor (`US_F22_Glass`): J-20, J-20S, J-31, J-35, J-36, J-50 and YF-23.
- F-16V/F-16 donor (`US_F16_Glass`): J-10C, J-10S, J-11B, J-15, J-15D, J-16, J-16D, Su-30MKK, Su-47, F-14 and F-21.
- Su-57 donor (`!RU_SU-57glass`): Su-75 and Su-57D.

This is Osama’s model appearance policy, not a claim about real aircraft generations. Older J-8 aircraft, bombers, helicopters and unmanned aircraft are outside the fighter request. Future custom fighters must be added to this explicit policy before packaging; do not silently infer donor choice from filename alone.

`prepare.py` reads the complete SHA-pinned Build 4 archive. It identifies external canopy faces from their material, position and source alpha. This prevents a whole airframe atlas, canopy frame, HUD or navigation lamp from receiving the donor material. The J-20’s material named Cop_Glass is an internal pane: its exterior canopy is in the airframe atlas. Low-detail copies have separately verified material indices. The F-22 canopy uses the broad donor UV island; small sensor windows in its material are excluded. Geometry and non-canopy UV checks run against every prepared copy. No new skeleton or animation rig is created.

`Cockpits.cs` clones the native game material, preserving its shader, texture references, HDRP settings and keywords. It first searches loaded materials; if needed, it loads a matching donor prefab as an asset from an already-loaded bundle, without instantiating it. Only three named donors are permitted. Missing donors produce an explicit error; no guessed substitute is called a success. Donor tangents are recalculated on the selected canopy mesh.

## Reproduction and verification

Provide the retained local F-22 donor mesh JSON to `prepare.py --donor-mesh`; game assets and purchased models are not committed to this repository. The source donor is submesh 1 of the base F-22 body mesh from the installed units bundle. Retain the inspected donor dump with the task evidence.

```text
python tools/cockpits/prepare.py --base /path/PLA-TEST-Build-4.bamod --donor-mesh /path/donor-mesh.json --out /path/prepared
python tools/cockpits/package.py --base /path/PLA-TEST-Build-4.bamod --prepared /path/prepared --out /path/PLA-TEST-Build-5.bamod --zip /path/to/zip
```

Compile `releases/0.6/experimental-model-loader/FAModels.csproj` and `releases/0.6/source/runtime-qa/FreedomArrow.Runtime.csproj` against the pinned game assemblies before packaging. Run the pipeline and identity host checks. Packaging verifies every payload hash and rejects changes to gameplay constants, infantry files, weapons, audio or the existing model mappings.

An armory check must confirm the native donor lookup, shader appearance, canopy coverage and retained frames for each model; the battle copies need their own visual check. The offline blue-surface diagram proves region selection only. Do not report this candidate installed or rendered successfully from compilation or package checks alone. The current published profile and playtest lock remain unchanged until validated publication.

## Document change log

- 2026-11-10 23:16:39 PST (America/Los_Angeles) — Added the cockpit donor contract, reproducible preparation/package commands and native verification limits.
