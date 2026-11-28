# Loadout options can change a unit's stealth

**Short answer.** Yes. Every armory option (`Options` row) has a `StealthOverride` field. In battle the unit's stealth is `Units.CurrentStealth`: the `StealthOverride` of the first selected option whose value is above 0, or the unit's own `Stealth` when no selected option has one. A lower value is stealthier (detection range = optics × stealth × modifiers). Read from game code and vanilla data (game 1.2.2.1); not yet measured in a game with an FA option.

## Evidence

- `Units.get_CurrentStealth` (RVA `0x2A2C70`, 1.2.2.1) walks `Units.CurrentOptions` (field `0xF0`). It reads `Options.StealthOverride` (field `0x88`) and returns the first value above the threshold. Otherwise it returns `Units.Stealth` (field `0x98`).
- Vanilla uses it on 23 options, for example:
  - Stryker RV (stealth 0.8): M2 / Mk19 / M240 → 0.666; Bushmaster II (+25) → 1.0.
  - BRM-3K / BRDM-3: the gun turrets → 1.0; PRP radar turret → 0.666.
  - MDP-01 Termit helicopter (0.4): S-8 / Kornet / Igla pylons → 0.5. This is the only aircraft example.
  - Green Berets (0.333): base squad option → 0.4.
- Vanilla stealth values for aircraft: F-35A/B, F-22, B-2, F-117 0.571; Su-57 0.8; drones 0.8; 4th-generation fighters 1.0. No vanilla fighter option uses `StealthOverride`.

## Rules for using it

- One override wins: the first selected option with a value above 0. Put the override on one option of the loadout (for example the external-pylon option), not on several.
- The override replaces the unit's stealth; it does not multiply it.
- For an external-weapons ("beast mode") F-35 option: `StealthOverride` 1.0 makes it as visible as an F-16; 0.8 would match the Su-57.

## Document change log

- 2026-11-27 21:30 PST (America/Los_Angeles) — First version (Osama: "can a loadout on a fighter change the stealth of a plane? like we want to do a beast mode for the F-35").
