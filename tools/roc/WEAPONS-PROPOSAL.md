# ROC vehicle and aircraft weapons, 25-26 November 2026

**Done in the data (stage 3 of `roc.py`, not yet in a test build). Shawn answered the four questions on 26 November 00:5x: MQ-9B unarmed and a bit cheaper; Wan Chien copies the AGM-154 JSOW; the 76 mm gun and the rockets change only their round counts; the missiles keep their copied ranges.**

Each new ROC weapon is a renamed copy of the nearest vanilla weapon, with the vanilla values. The ROC cards shared their parents' turret rows, so every turret that changes is copied for the ROC card first; the live US units keep their rows. Checked: 6,403 batch checks; audit_mp_equipment 0 new faults; field types, swap prices, slot and mount checks 0; live rows identical with and without ROC (1,390 ROC rows).

## ✅ Result per card (built)

- **F-CK-1:** M61, TC-1, TC-2, Wan Chien (2 on the middle pylons, the F-16V's JSOW pylon), Mk82 and Mk82 Snakeye. Maverick, Rockeye and Mk84 removed.
- **F-5F:** M39A2 20 mm, AIM-9, Maverick, Mk82. AMRAAM, Rockeye and Mk84 removed.
- **F-16A:** M61, AIM-9, AIM-7 Sparrow (copy of the F-15C's AIM-7M in the AMRAAM slots), Mk82. Maverick, Rockeye and Mk84 removed.
- **Mirage 2000-5:** DEFA 554 30 mm (copy of GSh-30-1), MICA EM, MICA IR, Magic II on the wingtips. All air-to-ground options removed.
- **Antelope:** 4x TC-1L (copy of the SLAMRAAM's ground AIM-9) and the M3P. One pod option.
- **Land Sword II:** 4x or 6x TC-2. The AIM-9 option removed.
- **Tien Kung III:** TK-III (copy of PAC-3), plus the Patriot's MG and AGL options.
- **Kung Feng VI:** 45x 117 mm HE or 45x 117 mm WP (Grad copies). Cluster and incendiary removed.
- **Thunderbolt-2000:** 12x MK45 230 mm, 60x MK15 117 mm or 27x MK30 180 mm (in place of 227 mm HE, cluster and ATACMS).
- **M41D:** M32K1 76 mm (copy of the M68E1 105 mm): 42 HE, 21 AP. The Shillelagh option removed.
- **M110A2:** M201 203 mm HE. The guided-round option removed.
- **CM-11, CM-12, M60A3 TTS:** the M135 165 mm demolition-gun option removed.
- **CM-32:** T91 40 mm AGL (default) or M2. **CM-33:** T91 40 mm AGL. **CM-34:** Mk44 Bushmaster with the T74 coax (default). Javelin options removed.
- **Chung Hsiang II, MQ-9B:** unarmed. MQ-9B price 100 → 80; Chung Hsiang II keeps 50 (Shawn 26 Nov: both prices OK).
- **CM-22:** M30 107 mm in place of the M121 120 mm, with the 120 mm data. 107 mm HE damage 9.0 → 7.2 (−20 %, Shawn 26 Nov); smoke unchanged. Options: 35x 107mm smoke + 35x 107mm HE, or 70x 107mm smoke.
- **M1A2T (26 Nov evening, Shawn's sheet: "M1A2 SEP v3 (no APS)"):** the 3 APS options (Trophy APS, TUSK APS, TUSK2 APS) are removed from the ROC card. Default, TUSK armor and TUSK2 armor stay. Price 250 unchanged.
- **Hsiung Feng IIE (added 26 Nov evening, unit 5048):** HF-IIE, a renamed copy of the Iskander-K cruise missile (weapons 317/318, ammo 9M728), same range. Options: 2x HF-IIE (default) or 4x HF-IIE (+50). The ballistic Iskander-M HE and cluster options are removed. Price 225, as the Iskander.

## 📋 The proposal (25 November)

## ⚠️ Wrong now (parent loadouts that do not fit)

- **F-CK-1, F-5F, F-16A, Mirage 2000-5:** they all carry the F-16C loadouts: AMRAAM, Mk84 2000 lb, AGM-65H and Mk82. The F-5F and F-16A should not have AMRAAM.
- **CM-11, CM-12, M60A3 TTS:** they keep the M60A1's M135 165 mm demolition-gun option. Proposal: remove it.
- **Chung Hsiang II:** it carries the Forpost's Kornet and Kh-BPLA. The sheet says unarmed reconnaissance. Proposal: remove both.
- **MQ-9B:** it carries the MQ-9's AIM-9, Stinger, GBU-54 and Hellfire. The sheet says unarmed surveillance. Question for Shawn: unarmed, or keep the Reaper weapons?
- **Tien Kung III:** it carries the Patriot battery's MG and AGL as well as the PAC-3. Proposal: keep them, as on the Patriot.

## 🆕 New ROC weapons (renamed copies)

**Air-to-air**
- TC-1 Sky Sword I (IR): copy of AIM-9 Sidewinder (weapon 113).
- TC-2 Sky Sword II (active radar, BVR): copy of AIM-120 AMRAAM (118).
- MICA EM (active radar): copy of AMRAAM (118).
- MICA IR: copy of AIM-9 (113).
- Magic II (IR): copy of AIM-9 (113).

**Surface-to-air**
- TC-1L (Antelope): copy of the SLAMRAAM's ground-launched AIM-9 (621). This replaces the Avenger's Stinger pods.
- TC-2 (Land Sword II): copy of the SLAMRAAM's AMRAAM (619 / 620).
- TK-III (Tien Kung III): copy of PAC-3 (347 / 366).

**Air-to-ground**
- Wan Chien stand-off munition: no close vanilla match. Question for Shawn or Osama: which US glide weapon to copy.
- GBU-12 Paveway II: copy of GBU-54 500 lb (375).
- Mk82 500 lb: vanilla row, reused.

**Guns**
- M39A2 20 mm (F-5F, 2 guns) and DEFA 554 30 mm (Mirage): copies of the nearest vanilla aircraft cannon. I pick the row when I build, and name it in the report.
- M32K1 76 mm (M41D): no vanilla 76 mm tank gun. Proposal: copy the M68E1 105 mm (11) with lower penetration and damage. Shawn to give the values.
- T91 40 mm AGL (CM-32, CM-33): copy of the Mk19 (21).
- T74 7.62 mm (coax, door guns): the ROC T74 row that already exists (copy of the FN MAG, 643).
- CM-34 Mk44 30 mm: the Stryker parent already has the Bushmaster II (23) as an option. Proposal: make it the default.

**Rockets and artillery**
- Kung Feng VI: 117 mm HE and WP, 45 rounds. Copies of the Grad 122 mm HE (92) and smoke (712), with 45 rounds instead of 40.
- Thunderbolt-2000: MK15 117 mm × 60, MK30 180 mm × 27, MK45 230 mm × 12, as three loadout options. These replace the M270's 227 mm and ATACMS. Copies: Grad 122 mm for MK15, M269 227 mm (263) for MK30 and MK45.
- M110A2: the Malka's 203 mm (636) is kept and renamed M201.
- CM-22: the M1064's 120 mm mortar is kept. The sheet's 107 mm variant needs values.

## ✅ Unchanged (parent weapons already match the sheet)

AH-64E, F-16V, CM-21, CM-25, M1167, JLTV, M1A2T, M109A5, M109A7, OH-58D, CH-47SD, M142 HIMARS, UH-60M, C-130HE.

## ❓ Questions (answered 26 November, see the top)

1. MQ-9B: unarmed, or keep the Reaper weapons?
2. Wan Chien: which vanilla glide weapon to copy?
3. M41D 76 mm, CM-22 107 mm, Kung Feng and Thunderbolt rockets: real values, or copies with only the round count changed?
4. Do the ROC missiles keep the copied ranges (the "same class, same range" rule of the missile sheets), or do some deserve a change?

## Document change log

- 2026-11-25 14:5x PST (America/Los_Angeles) — First proposal, from Shawn's sheet and the vanilla parent weapons. Not built.
- 2026-11-26 01:04 PST (America/Los_Angeles) — Shawn's answers applied; stage 3 built in the data and checked.
- 2026-11-26 02:47 PST (America/Los_Angeles) — CM-22 107 mm (−20 % HE damage) done; MQ-9B and Chung Hsiang II prices confirmed by Shawn.
- 2026-11-26 20:09 PST (America/Los_Angeles) — Hsiung Feng IIE card and HF-IIE weapon added (Shawn 26 Nov 19:56).
- 2026-11-26 23:19 PST (America/Los_Angeles) — M1A2T APS options removed (sheet row 30).
