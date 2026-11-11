Build 10 packaging: `python tools/cockpits/hide_package.py --base /path/PLA-TEST-Build-8.bamod --out /path/PLA-TEST-Build-10.bamod --zip /path/to/zip` after compiling FAModels 0.3.10 and Runtime 10.

**Current: PLA TEST Build 10.** Restore immediate stand-in hiding in the InitView postfix. Successful models still build completely before activation; on failure the partial model is removed, original renderers are restored and queued re-hide passes are cancelled. All Build 8 canopy materials, models, infantry, gameplay and audio are retained. Build 9 specialization work remains separate. Native transition verification is pending.

**Current: PLA TEST Build 8.** Source canopy glass now preserves specular reflections, uses metallic 0 and smoothness 0.95, with packed-map smoothness restricted to 0.90–0.98. Source textures/alpha, every mesh and other material settings remain as Build 7. These are chosen glass settings, not a claim to reconstruct the seller’s original shader. Native visual result is pending.

Rebuild the local complete pack with `python tools/cockpits/reflections_package.py --base /path/PLA-TEST-Build-7.bamod --out /path/PLA-TEST-Build-8.bamod --zip /path/to/zip` after compiling FAModels 0.3.9 and Runtime 8. Run `dotnet run --project tools/cockpits/finish-tests/FinishTests.csproj -c Release` for the actual finish helper’s host checks. These do not run Unity rendering. Earlier Build 7 instructions below are historical.

# Custom fighter cockpit policy

**Build 7 repairs a measured Build 5 failure: the unavailable F-22 donor stopped aircraft assembly halfway through. J-20, J-20S, J-31, J-35, J-36, J-50 and YF-23 now use their own source glass material, texture alpha and original UVs.** The F-16 and Su-57 donor assignments remain. Native repair appearance is pending.

Build 5's game log recorded `Cockpit donor unavailable: US_F22_Glass` for the affected PLA fighters. The old loader hid the stand-in first and stopped loading at the first failed material. It left only the pieces before that failure visible. This was not missing wheel/rudder texture data.

`prepare.py` splits only the selected glass faces. For source glass, it copies each original base/normal/mask image byte for byte to a distinct material filename, retains source vertex colours and all UVs, and enables alpha blending only for the glass. The untextured YF-23 glass retains its source colour/alpha. Some imported atlas materials had been marked OPAQUE even though their base images contained low-alpha canopy pixels; the repair enables that existing alpha on glass without making the hull transparent. No source image pixels are edited. Every source-model triangle, normal and UV is compared with the pinned Build 4 pack. Other model assignments and opaque surfaces are preserved.

The loader builds an inactive replacement before hiding the stand-in. On any failure it removes the incomplete replacement, restores originals and removes the queued re-hide passes. It logs a rejected replacement rather than presenting a partial aircraft as a success. Successful replacements still receive the original later-renderer visibility handling.

## Reproduction and verification

Use the retained native donor mesh JSON for the preparation command (the F-22 UV remapping path is no longer selected). Game assets and purchased models are not committed.

```text
python tools/cockpits/prepare.py --base /path/PLA-TEST-Build-4.bamod --donor-mesh /path/donor-mesh.json --out /path/prepared
python tools/cockpits/package.py --base /path/PLA-TEST-Build-4.bamod --prepared /path/prepared --out /path/PLA-TEST-Build-7.bamod --zip /path/to/zip
```

Compile FAModels 0.3.8 and PLA Runtime 7 against the pinned generated game assemblies before packaging. The complete pack verifies every payload hash and preserves gameplay, infantry offsets/skins, audio, weapons and model mappings. An armory check must still confirm complete aircraft, canopy opacity and the F-16/Su-57 donors. Battle copies require their own visual check. Public live lock and manifest remain unchanged. Build 6 belongs to separate specialization work.

## Document change log

- 2026-11-10 23:16:39 PST (America/Los_Angeles) — Added the cockpit donor contract, reproducible preparation/package commands and native verification limits.

- 2026-11-10 23:42:36 PST (America/Los_Angeles) — Replaced the failing F-22 donor policy with original source glass/UVs and documented complete-or-rejected model loading; retained Build 5 evidence as a measured regression.

- 2026-11-10 23:51:52 PST (America/Los_Angeles) — Added the opt-in Build 8 source canopy reflection finish and packed-map remaps; geometry/images unchanged and native appearance pending.

- 2026-11-11 00:14:36 PST (America/Los_Angeles) — Restored immediate hiding at Osama’s request, retaining failure recovery and approved Build 8 glass.
