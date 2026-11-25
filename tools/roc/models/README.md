# ROC models

**ROC model files are ROC-only add-ons. They are not staged into the live Models & music; a ROC test installer copies them into `UserData/FAModels` and takes them out again.**

## T91 rifle (25 November 2026)

- **Source:** `Object001` in Shawn's `ROC Infantry.blend` (cgmodel 781683), textures `T_T65A2_Color.png` / `T_T65A2_Normal.png`. Shawn: "You can use T91 rifle from the infantry model called 'ROC Infantry'".
- **Recipe** (work/roc-20261125, the weapons-1125 pipeline):
  - `blender -b "ROC Infantry.blend" -P export_obj.py -- Object001 t65.fbx`
  - `blender -b -P weapons-1125/tools/wconv.py -- t65.fbx t91_v.glb 2617 0,-22.6,-90 T_T65A2_Color.png T_T65A2_Normal.png` (the seller scene tilts the rifle 22.6°; 2,617 = vanilla rifle budget, the AK-74M)
  - `famconv.py t91_v.glb models w_roc_t91 --length 0.9 --tex-max 1024` (and `w_roc_t91_lo`, same mesh), then `fat-all/conv.py`.
- **Result:** 2,587 triangles, 1024 px, 0.9 m, muzzle +Z like `w_qbz191`.
- **Hand rules:** every ROC squad carrying T91, T91K1, T91 CQC or T65K2 as its main gun (9 rules in roc3). Weapon IDs are read from the built package, never typed by hand. Offset `[0, -0.19, 0.19]` is a first guess from the QBZ-191 / QCQ-171 grips; adjust from in-game screenshots.

## Vehicles, planes and helicopters (25 November 2026, overnight)

- **Pipeline:** `pipeline/` (copied from work/roc-20261125/tools). FBX: `batch_veh.sh` (fbx2glb + famconv); .blend: `blend2glb.py`; .max: `max2glb.py` + `texlink.py`; jets/helicopters: `plane_prep.py` (drop stores/gear, nose +X, up +Z, `UPSIGN=1` when the guess is upside down); then `finish_one.sh SLUG LENGTH ARMORY_MAX BATTLE_MAX` (armory 2048 px / battle 1024 px .fam, cuts with battle-lod/lod2.py, glass, LOD1 60 % / LOD2 35 %, .fat); `stage_roc.py` builds the ROC-only model set.
- **Card links:** `roc-models.json` (models.json entries keyed by ROC card Name). 16 cards: CM-34, CM-33, CM-22, CM-11, CM-21, CM-32, M41D, Antelope, Thunderbolt-2000, Kung Feng VI, Tien Kung III, Land Sword II, F-16V, F-5F, M110A2, UH-60M (S-70C file). CM-26 converted, no card.
- **Not used:** AH-64E, F-16A, Mirage 2000, M60A3 TTS, CM-25 (War Thunder extracts); F-CK-1 (the .max import throws parts out of place); C-130HE (mesh named `SK_West_Transport_C130J_LOD0`, Osama to judge); Hsiung Feng IIE and Chung Xiang II (files not usable / not shared).
- **Known limits:** helicopter rotors are part of the body (no spin yet); the model files are not in git (work/roc-20261125/stage, 527 MB).

## Document change log

- 2026-11-25 03:4x PST (America/Los_Angeles) — T91 rifle converted; recipe and first grip offset.
- 2026-11-25 04:4x PST (America/Los_Angeles) — 16 ROC vehicle/aircraft models converted overnight; pipeline and card links recorded.
