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

## Document change log

- 2026-11-25 03:4x PST (America/Los_Angeles) — T91 rifle converted; recipe and first grip offset.
