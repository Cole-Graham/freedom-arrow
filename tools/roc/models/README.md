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
- **Not used:** AH-64E, F-16A, Mirage 2000, M60A3 TTS, CM-25 (War Thunder extracts; AH-64E, F-16A, Mirage and M60A3 were later converted from Shawn's own files, CM-25 stays vanilla); F-CK-1 (the .max import throws parts out of place); C-130HE (mesh named `SK_West_Transport_C130J_LOD0`, Osama to judge); Hsiung Feng IIE and Chung Xiang II (files not usable / not shared).
- **Known limits:** helicopter rotors are part of the body (no spin yet); the model files are not in git (work/roc-20261125/stage, 527 MB).

## Infantry bodies (25 November 2026)

**All 7 ROC bodies (6 sources plus the SF Scout recolour) are on the BA 40-bone soldier skeleton, with 3 LODs each (28k / 7k / 3k triangles at most). They cover all 14 ROC infantry cards. They are not yet in a game build.**

- ROC Reservist: Reserver 5042, Reserver Kestrel 5043.
- ROC Infantry: DMS Team 5034, Mech. Riflemen 5040.
- ROC Infantry 2: Mech. Riflemen T112 5039, SF Snipers 5046, SF Snipers M107 5047. The 51k-triangle M1 helmet is cut to about 4k first.
- ROC Marine: Marine AT 5035, Marine 5038, Reserve Marine 5041.
- ROC Marine SF: Marine Frogmen CQC 5036, Marine Frogmen 5037.
- SF Scout 5044: the ROC SF 1 body with the ROC Infantry camo on the uniform (Shawn, 25 Nov). `recamo_sf1.py` finds the large camo areas of SF 1's body texture and keeps the boots (`uv_zmask.py`: faces wholly below 0.20 m). Shawn found the first generated pattern odd, so `quilt_roc.py` now fills those areas with real ROC Infantry fabric: 320 px pieces from clean areas of the trousers and coat back, joined along minimum-difference seams (image quilting), with the baked fabric folds flattened. The pieces are scaled by texel density (trousers 1412, coat 1256, SF 1 1617 px/m). Fold shading comes from SF 1's Black texture. The vest, helmet and gloves are unchanged.
- SF Section 5045: Shawn wants the ROC SF2 body. That file is not in the models folder yet, so the rule points to the plain ROC SF 1 body as a stand-in.

Rules file: `infantry-bodies-roc.json`. FAModels on this branch reads every `infantry-bodies-*.json` beside `infantry-bodies.json` and approves the ROC block 5000-5999. A bad add-on file is skipped alone, so the PLA rules still load. The pinned `infantry-bodies.json` is not changed. The `roc_` file names are not counted by the `pla2_` payload check.

---

**Method** (`pipeline/infantry/`, run from the work folder with Blender 5.2.3):

1. `rig_roc.py KEY roc_bodies.json Ranger.glb OUT`: moves the source arms onto the native Ranger arms (ArmFit), copies the Ranger surface weights and makes head gear and vests rigid. It also renders `landmarks0/1.png` and `rest0/1.png`.
2. Landmarks: ROC Reservist and ROC SF 1 use their own arm bones. SF 1's bones lie on -Y in the FBX, so `bonerot [-90,0,0]` turns them upright. The other 4 bodies have no skeleton (ROC Infantry's helper empties all sit at 0,0,0). `lm_auto.py` measures the arm joints from the mesh, and the same measurement on the Ranger mesh is the target, so the two biases cancel.
3. Measured accuracy of `lm_auto.py` against real skeletons (`lm_validate.py`): wrist 1.5-2.8 cm, elbow 4.2-10.9 cm, shoulder 2.9-9.4 cm. Part of the shoulder difference is rig convention: the shoulder bone is at x = 0.149 m on SF 1 and 0.246 m on the Ranger.
4. SF 1's mesh has shape keys (`Basis`, `V_None`). With shape keys, Blender keeps the basis key and drops edits to the vertices, so SF 1's arm fit was silently lost and its arms stayed near a T-pose. `rig_roc.py` now clears shape keys first. SF 1 and SF Scout also use measured landmarks now, like the other skeleton-less bodies.
5. The GTA Marine hands hang below ArmFit's z > 0.86 m limit, which stretched them. Each side of the separate hand mesh (`hand_meshes`) now moves whole with the rigid hand transform.
6. `pipe_body.sh KEY RIGS`: atlas (`roc_` prefix), `decimate_fas.py` LODs, `_0_b` battle texture copies and `.fat` files.
7. `pose_sheet.sh KEY RIGS`: rest pose plus a test pose (arms, legs, head, spine).

## New models and fixes (26 November 2026)

**4 more cards have ROC models: AH-64E, F-CK-1, C-130HE and Chung Hsiang II (Shawn's 26 November uploads). The Antelope's 3 War Thunder-named textures are replaced by BA Codex's own. 20 vehicle and aircraft cards now have ROC models. They are not yet in a game build.**

- **AH-64E:** 30.1k triangles (battle 28.9k, LODs 17.3k / 9.8k), 16.4 m. The 8 Hellfires, 2 rocket pods and 2 Hellfire rails are dropped (the game draws stores on its own pylons). Rotors are static (Shawn: proceed).
- **F-CK-1:** from the new FBX (the .max import was unusable). 55.1k (battle 47.5k, LODs 28.4k / 14.2k), 14.21 m. TC-1, TC-2 and drop tanks dropped; landing gear kept, as on the F-16V (dropping it left open gear bays).
- **C-130HE:** 26.8k (LODs 16.0k / 9.4k), 29.79 m long, 39.7 m span. The mesh is the game's own C-130J (`ROC__Transport_C130J_LOD0`) with Shawn's ROC textures.
- **Chung Hsiang II:** 11.0k (LODs 6.6k / 3.8k), 6.6 m as modelled.
- **Antelope:** `antelope_own_tex.py` draws new headlight, cab-glass and wire-grille textures in the same layout (only the lamp positions are read from the old sheet). Old files are kept in `veh/ante_own/orig/`.
- **UH-60M and CM-21:** kept as converted (Shawn 26 November: proceed; the UH-60M rotor does not spin).

---

**Gotchas found on 26 November**
- `plane_prep.py` guesses "up" from the canopy. On the AH-64E and the F-CK-1 the cockpit sits below the model's middle, so both came out upside down; `UPSIGN=1` fixes it. It also takes the longest extent as the fuselage: use `LONG=1` for aircraft wider than long.
- `famconv.py` measures `--length` along the longer flat axis. The C-130 and the UAV were scaled by their wingspan (C-130: 22 m span) until `FCX=--turn` was passed through `finish_one.sh`.
- `fbx2glb.py` sets a material to BLEND when its colour map has an alpha channel, and it can pair a material with another material's opacity map. The AH-64E and F-CK-1 hulls looked hollow; `glb_alpha.py` sets them OPAQUE (canopy: MASK).
- `conv.py` (fat) skips files that already exist: move the old `.fat` away before rebuilding a texture.
- `stage_roc.py` now also stages the infantry bodies, `infantry-bodies-roc.json` and the T91 rifle, because it empties the stage folder first.

## M60A3 TTS, canopy glass and texture budget (26 November 2026, later)

**The M60A3 TTS has its ROC model (21 cards now). Aircraft canopies are clear glass. Armory textures of 13 models are fitted to the team budget. Not yet in a game build.**

- **M60A3 TTS:** from Shawn's new FBX (Substance textures). 9.44 m, Armory 91k / battle 53k triangles (LODs 36.6k / 25.3k). Textures fitted to the budget: Armory 134 → 11 MB, battle 33 → 3 MB.
- **Canopy glass (Shawn: "correct color (not a blue color) ... like glass"):** F-5F (its canopy was a solid deep-blue material), F-16V, UH-60M (`玻璃` windows were opaque) and F-CK-1 now use FAModels `clearGlass` (neutral, colour ignored). The F-CK-1 canopy shared the airframe texture and was only cut out; `canopy_split.py` moves the 660 see-through canopy faces to their own glass material.
- **LOD material files:** every ROC `_lo_static_l1/l2.fam` now has a `.mat.json` (a copy of the battle one), as the live models do; without it the glass settings were lost at distance.
- **Armory texture budget (Osama 24 Nov: about 1.5x vanilla = 9.4 Mpx colour + normal):** `tex_budget.py` shrinks in 3/4 steps the texture with the most pixels per square metre of surface it covers. Applied to Antelope, C-130HE, CM-11, CM-21, CM-26, CM-34, Land Sword II, M110A2, M41D, Thunderbolt-2000, Tien Kung III, UH-60M and M60A3. Fighters (F-CK-1, F-16V, F-5F) stay above vanilla detail, as the rule says. Battle textures were not changed (except the new M60A3); the battle budget is per role and a batch needs Osama's go.

---

**Gotchas**
- `fbx2glb.py` (shared tool) falls back to a sibling material's opacity map (M60A3: the body got the camo net's). `fbx2glb_roc.py` is a ROC copy that only takes a material's own opacity map; the shared tool is unchanged.
- Substance exports name files `<part>_Base_color.png` / `_Normal_DirectX.png`: copy them to `<material>_BaseColor.png` / `_Normal.png` and flip the normal's green channel (DirectX → OpenGL).
- `glass.py` now also handles untextured (colour-keyed) glass materials and Chinese names, and leaves coloured light lenses alone.

## F-16A and Mirage 2000-5, with 2 Mirage paint schemes (26 November 2026, afternoon)

**The F-16A and the Mirage 2000-5 have ROC models (23 cards now). The Mirage has 2 skins on the Arsenal paint button. CM-25 stays on its vanilla model (Shawn). Not yet in a game build; the paint add-on needs the ROC FAModels DLL.**

- **F-16A:** from Shawn's new FBX (modelled about 10x too large; scaled to 15.06 m). Arsenal 111k triangles (cut from 160k), battle 53.9k, LODs 32.2k / 19.1k. The 9 missiles are dropped; the landing gear stays, as on the F-16V and F-CK-1.
- **Mirage 2000-5:** 31.1k triangles (LODs 19.0k / 11.5k), 14.36 m. The MICA, fuel tanks, racks and ground plane are dropped. The file is upside down for `plane_prep.py`: `UPSIGN=1`.
- **Mirage skins (Shawn: "2 basecolor skins for Mirage 2000, make them options for the unit in game"):** Default = ROC_Mirage_01 (blue-grey), Grey camo = ROC_Mirage_02. Only the colour map changes. `m_roc_mirage_{static,lo_static}_tex0@GreyCamo.fat` is the second skin, made with the same LANCZOS resize famconv uses (the default matched its source exactly). The battle LODs share the battle texture, so they change with it.
- **Paint add-on:** `paint-schemes-roc.json` (here and in the stage) lists the ROC units with schemes. The ROC-branch FAModels reads `paint-schemes-*.json` add-ons next to the live `paint-schemes.json`; a bad add-on is skipped alone. Swatches are `paint/ROC_Mirage_2000_5@{Default,GreyCamo}.png`. The choice is local, as for the live schemes.
- **Glass:** both canopies use `clearGlass`. The F-16A's targeting-system material shares the interior texture, so that texture is stored twice (tex0 and tex4, 5.6 MB in the Arsenal); not fixed.
- Recipe: `pipeline/new6_raw.sh`, `pipeline/new6_finish.sh`, `pipeline/stage_roc.py` (paint section).

## Plane finish and vanilla F-16 glass, as on the French preview (26 November 2026, afternoon)

**All 7 ROC planes now use the finish of the French-preview Rafale and Mirage. The 5 fighters use the game's own F-16 canopy glass (Osama: "use the Rafale and mirage materials we have on the French preview ... on all the planes", "vanilla f-16 glass transplant from vanilla for all the fighters"). Not yet seen in game.**

- **Glass (F-16A, F-16V, F-5F, F-CK-1, Mirage 2000-5):** `cockpitDonor US_F16_Glass`, the same as the French Rafale and Mirage. Until the F-16 glass is in memory, the old clear glass is the `fallback`. The canopy UVs are squeezed into the vanilla F-16 glass patch (`glassuv.py`, u 0.003-0.145, v 0.928-0.998) in all 4 files of each plane, so the soap-film map shows as a faint tint, not waves. This replaces the clear glass of the morning. The F-5F's dark blue and green canopy colours no longer show (the donor ignores them). The C-130HE keeps clear glass (it is not a fighter).
- **Mirage 2000-5:** the same C5 FBX as the French Mirage 2000D (`m_mirage2k`, md5 1620dec6). Shawn's folder also has its metal and roughness maps (downloaded now), so the mask is built from them and used as painted (metallic 1 / smoothness 0 in the .mat.json, as `m_mirage2k`). Both paint schemes share it.
- **F-16A, F-16V:** the seller's specular maps (F-16A `combat_jet_alternative2_specular`, `combat_jet_interior_specular`; F-16V `F16_Body_Spec`) become the mask (metal and smoothness = normalised specular). The Rafale ranges apply: metal 0.35-0.45, smoothness 0.35-0.80.
- **F-5F, F-CK-1, C-130HE, Chung Hsiang II:** no metal or gloss maps came with them, so they get the Rafale's middle values on every part: metallic 0.40, smoothness 0.55. The F-5F's untextured parts had been metallic 1 / smoothness 1 (mirror-like).
- Originals: `veh/x/<slug>/pre-matfix/`. Recipe: `pipeline/plane_finish.py` (reads the originals, so a rerun does not squeeze the UVs twice). `render_fam_alpha.py` now shows the remaps and the donor glass (as a grey tint).

## Hsiung Feng IIE, weathered (26 November 2026, evening)

**The Hsiung Feng IIE has its ROC model and a new card (unit 5048, Iskander template, as Shawn's sheet says). Its textures have moderate mud low down and light wear high up (Shawn: "do not make it look too old or overly damaged"). Not yet in a game build.**

- **Source:** Shawn's FBX with 7 PBR texture sets (UE export: `lambertNN` / `WorldGridMaterial58` files; mapped to the FBX materials `standardSurface1_Inst*` by matching the textures packed in his .blend). UE normals are DirectX: green flipped. The ORM maps are split into AO, roughness and metallic. Two tiny `WorldGridMaterial` parts (UE grid placeholder) are dropped.
- **Size:** 9.3 m as modelled, 4 launch tubes. Arsenal 120k triangles (cut from 146k; 12 detailed wheels are about 100k), battle 49.7k, LODs 29.9k / 18.3k. Arsenal textures fitted to the budget: 8.0 Mpx. Battle textures not budgeted (needs Osama's go). No separate glass (the cab windows are painted).
- **Weathering (`pipeline/weather_hf2e.py`):** `pipeline/bake_geo.py` bakes per material, on Vengeance, the height and up-facing direction (and with `EDGE=1`, 2 cm bevel edges). Mud: full below about 0.25 m and gone by 0.9 m, with fractal noise, plus crevices (AO) below 1.3 m; the wheels get an even lighter coat; mud is rough and not metallic. Upper body (above about 0.8 m): bare metal on baked edges (about 1-2 % of the surface), small dark paint chips (about 1 %), and light dust on up-facing surfaces. Unweathered textures stay in `veh/x/hf2e/tex/`.
- **Lighter pass (Shawn 26 Nov 20:2x: "looks fine, but can be a bit lighter"):** mud opacity 0.72 → 0.55 (wheels 0.6 → 0.45), mud gone by 0.75 m instead of 0.9 m, worn metal 0.9 → 0.65, chips 0.7 → 0.5, dust 0.16 → 0.10. Mud now covers about 11 % of the main body (was 23 %). The first pass is kept in `veh/x/hf2e/texw-v1/`.
- **Cab glass, Woodland camo (Shawn 26 Nov 21:5x, with 2 reference photos):**
  - **Glass:** the cab windows were solid black texels (8.4 % of the cab sheet). `canopy_split.py` moves the 114 cab faces that sample pure black (max channel ≤ 14) to their own glass part; `tint_glass.py` gives it dark tinted glass (colour 0.10, 0.12, 0.13, opacity 0.82, smoothness 0.95, metallic 0.3) in all 4 files. FAModels takes the opacity from the part's colour, so the colour is written into the .fam files.
  - **Camo (paint button, scheme `Camo` = "Woodland camo"):** colours are the M60A3 body texture's own camo colours (medians of its green 57,66,50, brown 87,71,62 and dark grey 47,50,57). `uvpos.py` rasterises the world position of every texel from the UVs (CPU, no render), and `camo_hf2e.py` lays a 3D noise pattern on it (patches about 1-2 m on the model), so the camo runs across UV seams. Only texels near each sheet's main paint colour change (blue-grey body, white cab), scaled by their own brightness so panel lines and shading stay; wheel hubs go plain green as in the photo. The lighter mud and wear are applied on top with the same noise, so they match the default. 14 `@Camo` textures (Arsenal and battle), swatches `paint/ROC_Hsiung_Feng_IIE@{Default,Camo}.png`, listed in `paint-schemes-roc.json`.
  - **Size (open question):** the model's wheels are 0.61 m across; a real truck wheel (315/80R22.5) is about 1.07 m. So the model is about 0.57 of real size (9.3 m; the real tractor and trailer are about 16 m). Not changed until Shawn or Osama say.

## Document change log

- 2026-11-25 03:4x PST (America/Los_Angeles) — T91 rifle converted; recipe and first grip offset.
- 2026-11-25 04:4x PST (America/Los_Angeles) — 16 ROC vehicle/aircraft models converted overnight; pipeline and card links recorded.
- 2026-11-25 10:4x PST (America/Los_Angeles) — 6 ROC infantry bodies rigged with LODs; add-on body rules and FAModels ROC range recorded.
- 2026-11-25 11:2x PST (America/Los_Angeles) — SF Scout recoloured to ROC camo; SF Section waits for ROC SF2.
- 2026-11-25 13:5x PST (America/Los_Angeles) — SF Scout camo rebuilt from real ROC fabric; SF 1 arm-fit fix (shape keys); matte previews.
- 2026-11-26 02:51 PST (America/Los_Angeles) — AH-64E, F-CK-1, C-130HE and Chung Hsiang II converted; Antelope textures replaced; stage includes infantry and T91.
- 2026-11-26 03:11 PST (America/Los_Angeles) — M60A3 TTS converted; canopy glass fixed on 4 aircraft; LOD material files; Armory texture budget on 13 models.
- 2026-11-26 12:54 PST (America/Los_Angeles) — F-16A and Mirage 2000-5 converted; Mirage second skin as a paint scheme through a ROC paint add-on file.
- 2026-11-26 14:52 PST (America/Los_Angeles) — French-preview finish on all 7 ROC planes; vanilla F-16 glass on the 5 fighters.
- 2026-11-26 20:11 PST (America/Los_Angeles) — Hsiung Feng IIE converted and weathered; card 5048 added.
- 2026-11-26 20:30 PST (America/Los_Angeles) — Hsiung Feng IIE weathering made lighter (Shawn).
- 2026-11-26 22:08 PST (America/Los_Angeles) — Hsiung Feng IIE: dark tinted cab glass and optional Woodland camo (paint scheme); size question recorded.
