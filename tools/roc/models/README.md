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

## CM-12 converted, CM-26 out (27 November 2026, after midnight)

**CM-12 has its own ROC model now, and CM-26 is out of the ROC set (Shawn: "Use the current model called CM-11 for CM-12 cuz I checked the model is correct, remove CM-26 from the deck"). 25 cards have ROC models. Not yet in a game build.**

- **CM-12:** from `CM-12.zip` (cgmodel 680292; its file is named `CM11.fbx`, which Shawn confirmed is the right CM-12). Seller maps `_c` colour, `_n` normal, `_ao`, `_s` specular (turned into roughness 0.7 dull to 0.2 shiny), `_a` cut-outs (track, Browning, bullets and M60 are alpha MASK, `glb_alpha.py`). 9.3 m like the CM-11. Arsenal 119.9k triangles (from 147.6k), battle 59.1k, LODs 41.4k / 28.5k. Arsenal textures fitted to the budget: 7.1 Mpx.
- **CM-26:** it never had a card. It is no longer staged (`stage_roc.py`); its converted files stay in `veh/` only.
- **Hsiung Feng IIE size:** kept at 9.3 m as modelled (Shawn: "happy with Hsiung Feng IIE size for now").

## EC225 Super Puma in ROC SAR paint; HEMTT, Patriot PAC-2, PAC-3 MSE and RQ-7 cards (27 November 2026, after midnight)

**Five new ROC cards (units 5049-5053). The EC225 has its own model, repainted in the ROC Air Force SAR scheme from Shawn's two photos; the other four use the current Freedom Arrow models and data, as Shawn asked. Not yet in a game build.**

- **EC225:** Shawn's model (H225 game model, 46.5k triangles, 16.4 m), one 2048 sheet with AO / roughness / metal (`mga_orm`: R AO, G roughness, B metal). The 30 window parts shared the body material and its alpha map: `ec225_glass.py` gives them their own glass part and the body is OPAQUE; `tint_glass.py` makes them dark tinted (0.10, 0.12, 0.13, opacity 0.65). Battle uses the full model (46.5k, under the 60k cap), LODs 27.8k / 16.4k.
- **Paint (`livery_ec225.py`):** laid out in 3D from `uvpos.py` (body only: interior, rotors, gear and glass left out with `SKIP`). Sky blue cabin, dark blue engine deck and fin cap, white belly and tail boom, yellow tail-boom band, black nose radome; on both sides a red cross on a white disc behind the last window and the ROC roundel (blue disc, white 12-ray sun). Only the seller's navy / white / red livery texels change; a faint smooth noise keeps the paint from looking flat. The "2251" numbers are not drawn.

## New T91 rifle and Kestrel-1 launcher models (27 November 2026, ~01:00)

**Shawn's new T91 and Kestrel models replace the old T91 and give the Kestrel-1 its own model. Not yet in a game build; the Kestrel position in the hands is a first guess.**

- **T91:** `T91战斗步枪.FBX` (14.6k triangles, 0.95 m, one 1024 colour map `Hui.jpg`, no normal map). `wconv.py ... 2617 0,0,90 Hui.jpg -` (muzzle was -X) → 2,587 triangles, `famconv --length 0.953 --tex-max 1024`. Same file names (`w_roc_t91*`), so the 9 T91 hand rules are unchanged (offset `[0, -0.19, 0.19]`). The old T91 files are kept in `t91/old-1125/`.
- **Kestrel-1:** `火箭筒.obj` (cgmodel 732057, 229k triangles, 1.40 m, 4096 PBR TGA). `wconv.py ... 2617 0,0,-90` (muzzle +X; pistol grip behind the front grip) → 2,587 triangles, `famconv --length 1.40 --tex-max 1024`. The two loose rocket models are not used (the game's own projectile flies).
- **Kestrel hand rules (4):** slot `special` (FAModels' launcher slot), weapon 2900002 (Kestrel-1, from the ROC report), on Marine AT 5035, Marine 5038, Mech. Riflemen T112 5039 and Reserver Kestrel 5043. Offset `[0, -0.16, 0.07]` puts the pistol grip where the rifles' grip sits; adjust from in-game screenshots.
- `stage_roc.py` now stages every `w_roc_*` weapon. `roc-weapon-rules.json` (13 rules) is the copy in this folder.

## SF Scout from ROC SF 4 (ghillie), AN/TWQ-1 card (27 November 2026, ~02:00)

**SF Scout now uses Shawn's ROC SF 4 body: the ROC Infantry soldier in a ghillie suit, with a night-vision helmet and goggles. The ghillie's see-through strips are kept with a new cut-out option in the ROC FAModels. SF Section keeps the ROC SF 1 body (no ROC SF2 file was ever uploaded). AN/TWQ-1 Avenger card added (unit 5054). Not yet in a game build.**

- **Body `sf4`** (`roc_bodies.json`): ROC SF 4.blend (cgmodel 781683 family, 37.6k triangles, 9 meshes). Head, helmet, NVG and goggles rigid on Head; arms, coat and ghillie (`JiLiFu`) fitted with ArmFit; measured landmarks. `rig_roc.py` with `NORENDER=1` (no diagnostic renders on the deck); `ALPHA=1 pipe_body.sh sf4 rigs_sf4` keeps the alpha of the ghillie texture in the atlas (9.5 % of the sheet is see-through). LODs 27.9k / 7.0k / 3.0k.
- **Cut-out:** `infantry-bodies-roc.json` rule 5044 has `"cutout": true`; the ROC FAModels (`InfantryBodies.cs`) draws such bodies with alpha MASK, cutoff 0.5 (double-sided, as every FAModels material). Other bodies are unchanged.
- `stage_roc.py` stages only the bodies a rule uses, so the old `roc_sfscout` recolour is no longer shipped (kept in `inf/`).

## SF 4 ghillie sleeves on the arms; SF Section = ROC SF2 (27 November 2026, ~02:30)

- **Ghillie sleeves (Shawn: "make sure the arm and the hand in ROC SF 4 are align with the Ghillie suit's"):** the ghillie was modelled in a T-pose (sleeves level at z 1.45 m out to 0.80 m) while the soldier's arms hang in an A-pose. `ghillie_pose.py` bends each sleeve onto the arm's centre line (coat + arm slices) by arc length, keeping its cross-section, and writes `ROC SF 4 posed.blend`. Measured on the source: coat sleeve to ghillie 9.8 → 1.5 cm (median), forearm 28 → 3.9 cm, hand 36 → 12.6 cm (the hands come out of the sleeves). The arm landmarks were measured from the T-posed sleeves before; they now follow the real arms (hand at z 1.10 m instead of 1.51 m). Re-rigged and re-built (27.9k / 7.0k / 3.0k).
- **SF Section 5045 = ROC SF2** (`JGSF_soldier_01`, 10.6k triangles, Japanese-gunner style textures). The file is 1.62 m tall, so it is scaled to 1.83 m like the other ROC bodies (`scale` 0.01128). One mesh, fitted with ArmFit and measured landmarks; LODs 10.6k / 7.0k / 3.0k.

## TK-III cab fixed; CM-34 Desert and Mosaic paint (27 November 2026, ~02:30)

- **Tien Kung III cab (Shawn's screenshot: the cab looked open/broken):** the cab material (`chetou1`) was alpha BLEND, because its colour map carries the window cut-outs in its alpha (6.5 % of the sheet), so the whole cab drew as see-through and sorted wrongly. `canopy_split.py` moves the 30 window faces (alpha < 0.5) to their own glass part, the cab is OPAQUE (`glb_alpha.py`), and `tint_glass.py` makes the windows dark tinted glass (0.10, 0.12, 0.13, opacity 0.80). Rebuilt: 21.0k triangles (LODs 12.6k / 7.4k), 14.0 m, Arsenal textures 7.4 Mpx. Old files in `veh/x/tk3/pre-glass/`.
- **CM-34 paint (Shawn: "add more paint options to CM34"):** his folder has two more colour sets beside the default green: `SHAMO` (desert) and `MAISAIKE` (mosaic). They become the paint schemes `Dust` ("Desert") and `Mosaic` ("Mosaic camo"), 12 `@Scheme` textures (hull, wheels, gun; Arsenal and battle) at the shipped sizes, made with the same LANCZOS resizes as the default (the default matched its source exactly).

## CM-33 removed; weathering, camo and PBR infantry (27 November 2026, morning)

- **CM-33 removed (Shawn: "the CM-33 model quality is too poor, so just delete that unit"):** `roc.py` `REMOVED` takes the card out of the ROC spec and the Arsenal (`DisplayInArmory` false); its model rule is gone from `roc-models.json`. Transports are now CM-21, CM-32 and CM-34.
- **Weathering (`pipeline/weather_fam.py SLUG GLB LENGTH [K]`):** faded paint, crevice grime (AO), vertical streaks, dust on top faces, edge wear, small chips and mud below `MUD_TOP` m (mud keeps the surface detail and is written into the mask). It needs the texel position map from `pipeline/uvpos.py`. Applied to Tien Kung III, Thunderbolt 2000 and Land Sword II (M60A3/M110A2 look), CM-21, CM-22 and, lighter, the EC225. Unweathered textures stay in `veh/x/<slug>/pre-weather/`.
- **Camo (`pipeline/camo3d.py SLUG GLB LENGTH SPEC.json [SCHEME]`):** paints a 3D woodland or block pattern on the texels near the model's old camo colours and keeps their shading. Specs in `pipeline/camo/`. CM-22 has the CM-26 woodland colours (tracks skipped); CM-21 is redrawn in the same woodland.
- **CM-32:** the hull had no usable UVs and a flat cartoon colour. `cm32_uv.py` unwraps it to a 2048 sheet, `dilate_islands.py` fills the island gaps, and camo3d + weather_fam give Default (woodland), `Dust` ("Desert") and `Mosaic` schemes like the CM-34. No baked AO or normal detail yet (the source is untextured).
- **CM-21 transparency (Shawn: "check if the CM21 model has any transparency issues"):** the whole body material was alpha BLEND; it is OPAQUE now in all 4 material files. CM-32 Seat/Net/Text parts are OPAQUE too.
- **EC225 (Shawn: "looks like a toy"):** `livery_ec225.py` v2 adds per-part detail, panel cavities from the normal map and exhaust soot, then light weathering (K 0.45, `MUD_TOP` 0.5).
- **Infantry PBR (Shawn: follow the latest Chinese paratroopers):** `pipeline/infantry/atlas_pbr.py` builds all 7 ROC bodies with area-weighted atlas tiles, a PBR mask from ORM / roughness+metallic / GTA `_spec_` maps, AO in the colour and light sharpening. Old atlases in `inf/lod/old-pbr/` and `inf/fat/old-pbr/`.

## CM-32 v3 and the FBX pack (27 November 2026, ~04:00)

- **CM-32 v3:** the v2 previews showed near-white roof hatches and vision-block frames (the seller's `Interior_Color` material, colour 0.71) and mid-grey tyres (0.154). `cm32_uv.py` now puts the interior parts on the camo sheet too (58,486 painted faces) and makes the tyres rubber (0.03, rough 0.9); Seat, Net and Text stay OPAQUE (`glb_alpha.py`). Rebuilt with `finish_one.sh cm32 7.0 60000 31000` (60.9k / 32.4k, LODs 20.2k / 14.8k), new position map, the three schemes and weathering again. v2 files in `veh/x/cm32/v2/`.
- **Preview fix:** `render_fam_alpha.py` now multiplies a texture by its sub-mesh colour, as FAModels does (`_BaseColor` × map).
- **FBX pack for Shawn:** `export_fam_fbx.py MODEL.fam OUTDIR NAME` writes the Arsenal mesh as FBX with PNG textures (2048 from `tex_full/` where present; colour tints baked in; `_mask` split into Metallic/Roughness). Pack: Tien Kung III, Land Sword II, Thunderbolt 2000, EC225, CM-32 (+ Desert/Mosaic maps), on Sam's Drive, link-shared, file `1N3VgWNIATBO-fRq1u-zJBWpH54ueh0Cs`.
- **Infantry preview:** `infantry/render_fas_pbr.py` renders a `.fas` with its normal map and PBR mask.
- **Infantry atlas v2 (`atlas_pbr.py`):** the shelf packing left 23-42 % of each sheet empty. Tiles are now skyline-packed and then grown (largest surface first, 8 px steps) into the free space. Sheet use: reservist 58 → 85 %, infantry 66 → 94 %, infantry2 65 → 75 %, marine 75 → 89 %, marine SF 77 → 91 %, SF 4 77 → 99 %, SF2 71 → 70 % (two parts, no room to grow). No tile got smaller. All 7 bodies rebuilt and staged; v1 files in `inf/lod/old-pbr1/`.

## Infantry fixes from Shawn's in-game check; test build roc6 (27 November 2026, afternoon)

- **ROC Infantry black belly patch and Marine / Marine SF grey side flap:** both vests were rigid on Spine2. In the rifle stance the chest turns against the hips, so the vest's lower edge swung out (Marine: side strap by the arm; ROC Infantry: a gap showing the dark inside). `rig_roc.py` now has a `torso` rigid mode: body weights transferred from the game soldier, minus arm, hand and head bones (vest belly now Spine 93 % / Spine1 5 % instead of Spine2 100 %). Used for `SM_vestHeadGear` (infantry) and `s_m_y_marine_03_model_001` (marine, marinesf).
- **SF2 and Infantry 2 shoulder "wings":** the JGSDF vest shoulders and flaps stood up to 7 cm above the sleeves. `infantry/shoulder_flaps.py` presses everything above a shoulder line (sleeve top, sloping 2 % of the height up to the collar edge) toward it (K 0.15), on new `... shoulders.blend` sources; head, helmet, headset and collar unchanged.
- **Kestrel-1:** scale 0.75 on all 4 rules (units 5035, 5038, 5039, 5043).
- Rebuilt and staged: infantry, marine, marinesf, sf2, infantry2 (old files in `inf/lod/old-pbr2`, rigs in `inf/rigs_*.pre-1127`).

## Shawn's second and third in-game lists; test build roc7 (27 November 2026, afternoon)

- **CM-34 card:** `flatten` in roc.py: no custom-option rows (the 30mm "Dragoon" turret is the fixed weapon, SRAT/Trophy gone), 40 pts, name "CM-34 Clouded Leopard". Model turned 180° (`yaw` in roc-models.json; it faced backwards).
- **CM-32 rebuilt (`cm32_kitbash.py`):** CM-34 hull and wheels (turned 180°, CM-34 textures and Dust/Mosaic files), the CM-32's 3 rear antennas and tail box, and the vanilla Stryker ICV Mk19 station (prefab US_STRYKER_ICV_MK19: turret_0/weapon_0 part of mesh ICV, its pedestal, Mk19 gun; packed normal map unpacked) on the roof where the old station stood.
- **CM-22** uses the CM-21 model (alias in stage_roc.py). **M41D** ×1.4 (`scale`; it was 5.8 m with the gun, the real M41 is 8.2 m and 3.2 m wide).
- **CM-11 / CM-12 shadows:** their normal maps were DirectX-style. `normal_convention.py` (curl test; the M60A3 maps flipped by hand on 26 Nov read OpenGL) — green channel flipped for cm11/cm12. Other models that read DirectX (CM-34, M110A2, F-CK-1, TK-III, TB2000, EC225, Mirage, F-16A...) are listed for Shawn, not changed.
- **Glass:** Kung Feng VI, HF-IIE, Antelope and Land Sword II cabs use the vanilla 9K51 Grad glass (new FAModels cockpit token RU_BM_21_Grad_glass); Antelope door windows (`antelope_windows.py`) and Land Sword II windows (`split_windows.py`, boxes in camo/lsw2_windows.json) split from painted body faces; F-CK-1 windscreen (`fck1_windscreen.py`) and the C-130HE use the vanilla F-16 glass. Chung Hsiang II has no glass part.
- **Dust streaks:** `weather_fam.py STREAK=fine` (~5 cm wide, ~30 cm long, fainter) on TB2000, TK-III and Land Sword II.
- **F-16V:** Arsenal model gets the F-16A's landing gear and is lifted 0.62 m (`f16v_gear.py`); battle model unchanged (gear up).
- **EC225:** real ROC Blue Sky White Sun on both sides (`ec225_roundel.py`: 12 straight rays, ring and disc 30:17:15).
- **Infantry:** shoulders shaped to a smooth curve after rigging (`infantry/fas_shoulders.py`; Infantry 2 flatter, rise 0.015).

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
- 2026-11-27 00:05 PST (America/Los_Angeles) — CM-12 converted from Shawn's file; CM-26 removed from the ROC stage.
- 2026-11-27 00:33 PST (America/Los_Angeles) — EC225 converted and repainted in ROC SAR colours; 5 new cards noted.
- 2026-11-27 01:06 PST (America/Los_Angeles) — New T91 model; Kestrel-1 model and 4 launcher hand rules.
- 2026-11-27 01:46 PST (America/Los_Angeles) — SF Scout = ROC SF 4 ghillie body with cut-out; AN/TWQ-1 card.
- 2026-11-27 01:50 PST (America/Los_Angeles) — SF 4 ghillie sleeves bent onto the arms; SF Section = ROC SF2 body.
- 2026-11-27 02:15 PST (America/Los_Angeles) — TK-III cab glass fixed; CM-34 Desert and Mosaic paint schemes.
- 2026-11-27 03:36 PST (America/Los_Angeles) — CM-33 removed; weathering on TK-III, TB2000, LSW2, CM-21, CM-22, EC225; CM-22/CM-21 woodland; CM-32 UV + 3 schemes; CM-21 opaque; PBR infantry atlases.
- 2026-11-27 03:59 PST (America/Los_Angeles) — CM-32 v3 (interior parts on the camo sheet, rubber tyres); preview tint fix; FBX + PNG pack for Shawn.
- 2026-11-27 04:13 PST (America/Los_Angeles) — Infantry atlas v2: skyline packing with tile growth; 7 bodies rebuilt.

- 2026-11-27 14:38 PST (America/Los_Angeles) — Vest torso weights (infantry, marines), JP shoulder press, Kestrel 75 %; test build roc6.
- 2026-11-27 15:15 PST (America/Los_Angeles) — Second and third in-game lists (CM-34 card, CM-32 rebuild, glass, M41D, CM-22, CM-11 normals, F-16V gear, EC225 roundel, streaks); test build roc7.
