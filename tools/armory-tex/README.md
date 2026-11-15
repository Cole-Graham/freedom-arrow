# dev.10 batch (staged, not built)

Osama 14 Nov 2026 23:1x-23:3x PST after testing dev.9: "Hq-9 model looks fucked", "we over did some of the optimization for
tanks", "VT-5 looks really bad", "ZTZ-99A definitely doesn't look good", "J-20 / J-15D / J-35 textures look really bad",
"I think its really important for units to look good in the armory", "we can increase the load a bit".
- HQ-9 (m_hq22g_static.fam) back to the dev.8 mesh: the dev.9 cut faceted the round canisters (hq9-check/sheet.png).
- 259 armory textures remade colour-first (armory-tex2/plan.py, budget 30 Mpx per non-support armory model; colour maps
  stay at source size up to 2048, mask then normal maps shrink first). Plan: armory-tex2/plan_30.json; remake list fat_plan.json.
Support textures (support-tex) stay as in dev.9 ("fine for now").
Add every line of assets.txt as --asset over the dev.9 complete package.

## Revised 14 Nov 2026 23:5x PST (supersedes the 30 Mpx rule for VEH/Helo/Air)
Osama: "VEH, Helo and Air tab units need to look good, thats the priority, as long as they don't take me more than 0.3 seconds to load".
- 91 VEH/Helo/Air armory models (units.json CategoryType 2/5/6) back to source-size textures capped at 2048 (armory-tex3/plan.py):
  330 .fat taken from the dev.7 complete package (same sizes; dev.7 measured <= 0.29 s first load on his PC), 9 regenerated.
  CTL-181 (dev.7 0.37 s) keeps the colour-first 30 Mpx plan.
- 37 textures of other-tab models keep the colour-first 30 Mpx plan (armory-tex2).
- HQ-9 dev.8 mesh. assets.txt = 377 lines. Texture data for the changed files: 413 MB in dev.9 -> about 1.8 GB.
