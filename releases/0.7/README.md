# Freedom Arrow 0.7.0-dev.5 — development candidate

**This candidate carries forward dev.115 and changes XM30 to190 points with Bradley voice assignment. Install the companion combined asset pack0.1.3 for XM30 scale0.77 (10% larger than0.70) and the China music update.** No PLA test data is included.

## Defense correction from0.7 dev.1

The native loader selects only the first default ability row. Abrams X previously loaded APS alone; its smoke and ECM rows were separate defaults. XM30 smoke/APS already shared one row, but its ECM was separate. Both units now use one combined default profile. Latest instruction: Abrams X smoke1/APS2/ECM30%; XM30 smoke1/APS2/no ECM. IDs are preserved. Old separate profiles remain linked but non-default. Source/native-control-flow finding; not yet an in-game result.

## Changes from dev.115

- XM30:220 →190 points; same name, weapons, armor, defenses and availability.
- XM30 voice preset: T-15 → M2A3 Bradley. Abrams X retains the existing Abrams preset for the requested Crusader voice lines.
- Companion assets0.1.3: XM30 scale0.70 →0.77; China011 first in the menu, then remaining menu tracks; Mother Of All Weapons added to China battle music. New installs default to USA; existing playlist choice retained.
- Package display name corrected from the stale0.4 label to0.7.

## Carried forward

All other dev.115 data/settings are intended to remain unchanged, including40 mm damaging-artillery penetration floor, TOS damage11 with normal impact, JATM11 km and existing live added units. Su-75 availability remains2. Lateralus's queued branch is separate and is not silently included.

## Known issue and evidence limits

**This candidate corrects the identified first-default ability-selection bug: Abrams X and XM30 now each have one combined default defense profile; Abrams X has30% ECM and XM30 has none. In-game behavior still needs confirmation.** All claimed checks are offline package/data/compile or installer checks until a game result is explicitly recorded. Music playback, XM30 appearance and voice playback need runtime checks. Separate3-second TOS fire remains unimplemented.

## Install

Close the game. In BAModManager > Mods > + Add mods, import the gameplay0.7 candidate and the combined Models and Music0.1.3 pack, confirming replacement. Keep both enabled and ActualArrow disabled. Windows: manager PLAY. Linux: close manager and launch through Steam. A full restart is required. Do not import assets as the main gameplay modpack.


## Network option-ID correction candidate

The native network sends selected option IDs as signed 16-bit values. The old custom IDs exceeded32767 and were truncated, which can remove selected weapons from spawned units despite working in the editor. This candidate maps241 custom options into20000–20240 and migrates saved full-width or already narrowed selections. XM30’s two weapon choices now use20239 and20240. Weapon stats, ammunition, prices, defenses and all other gameplay tables remain unchanged from dev.3. Both players need the same corrected gameplay build.

Host checks cover all option IDs, both XM30 weapon choices and exact table comparison. Live network firing and the separately reported crash remain unverified. Current public gameplay/PC hold stays dev.3 until the candidate is deployed.

## Abrams X autoloader correction

Abrams X now has an exclusive main-gun row with AutoLoaded=true and a5–6 second base reload. It is linked to the intrinsic default turret; gun damage, penetration, aim time, ammunition and other Abrams variants remain unchanged. Network-safe options and saved-deck migration remain included. Solo/editor and network loadout paths are checked offline; live firing intervals, crew/stress effects and a human network retest remain unverified. Candidate only; public gameplay hold remains unchanged.

## Document change log

- 2026-11-09 17:31:05 PST (America/Los_Angeles) — Prepared the authorized0.7 candidate; latest instruction supersedes the previous dev.115 play-session hold. Hold again after this update.
- 2026-11-09 17:45:14 PST (America/Los_Angeles) — Corrected native first-default defense selection; runtime confirmation pending.
- 2026-11-09 17:48:20 PST (America/Los_Angeles) — Latest correction: XM30 one smoke and no ECM; Abrams X retains one smoke, two APS and30% ECM.

- 2026-11-09 18:39:15 PST (America/Los_Angeles) — Prepared network-safe option IDs and saved-selection migration; no live firing or crash fix claim.

- 2026-11-09 19:13:43 PST (America/Los_Angeles) — Added Abrams X exclusive autoloader5–6-second specification, intrinsic linkage and validation gates.
