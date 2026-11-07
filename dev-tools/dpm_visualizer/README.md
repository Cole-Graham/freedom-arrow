# Broken Arrow DPM visualizer

Compare damage per minute vs range for Broken Arrow units and weapons. Expected DPM multiplies post-armor damage by the share of rounds that land in the target box (see Math). Check **Assume hits** to restore 100% hits. The range axis is **card metres** (world table range × 2), matching the targeting UI.

It only reads decrypted tables. It does not write the game, set `write_game_bundle`, or call `hangar` / `inject`.

## Setup

From the repository root:

```text
python -m pipeline decrypt
python -m pip install -r dev-tools/dpm_visualizer/requirements.txt
python run_dpm_visualizer.py
```

`decrypt` writes `cache/vanilla/<build-id>/`. Two buttons pick the data:

- **Load vanilla:** the newest `cache/vanilla/<build-id>/`.
- **Load Freedom Arrow (latest):** the newest `releases/<version>/` in your checkout. The button runs that release's `build_constants.py` first (about 1 s), so the data matches the files you have. It does not change the dev version. It needs the same Python packages as the build (`pycryptodome`). Pull the release branch first to get the newest build.

The last choice loads again at the next start. Rows that a release deletes (null in the overlay), such as removed squad members or retired options, are removed.

```text
$env:PYTHONPATH = "dev-tools"
python -m unittest discover -s dev-tools/dpm_visualizer/tests
```

## Tabs

- **Units:** the chart redraws by itself whenever a setting changes (units, loadouts, cost, armor, men, face, physical/stress, ammo, cover, check boxes); **Generate chart** still forces a redraw. Overlay several units against one armor face. Physical or stress. Cost-normalized DPM. Infantry RPG/ATGM weapons are omitted. Spread uses the target unit’s size, or a unit that wears the selected armor. Each comparison row has a **loadout** dropdown (weapon package × armor kit, or squad loadout). Armor, weapons, and the shown cost follow that loadout. With exactly two visible units, **Each vs the other's loadout** plots each line against the other unit’s selected plates; the checkbox is greyed out when more than two comparison rows are active.
- **Custom unit (bottom of the Units tab):** pick **From** (a unit) and its **Loadout**. The editor copies that loadout's cost, HP, armor row, armor values and weapons. Change any of them: pick another armor row or type armor values, change a weapon's count (guns, or men carrying it), pick another weapon + ammo, add or remove weapons. **Create / update** saves it under its name; picking a saved custom unit in **From** loads it back for editing. Add it as a compared unit to chart it. Its weapons always use the ammo you picked.
- **Armor menus (Target on both tabs, custom unit Armor row):** infantry armor is listed once per class (Armor Infantry, Shock, Elite) with a separate **Men** box, so any squad size works, including counts the game has no row for (for example a 10-man Elite). Armor comes from the class (every row of a class has the same armor), health is 5 per man, and the hit box is the game's squad box, 1 m + 0.5 m per man. Other armor rows are listed as before.
- **Cover (Target box on both tabs):** Open, Woods or Building, for infantry targets (rows with an infantry armor value). The values follow the loaded data: vanilla building 0.18 + 0.02 per soldier inside and no woods reduction; the mod's `game-config.json` (`BuildingDamageFloor`, `BuildingDamagePerSoldier`, `ForestDamageTaken`). Each round's `IgnoreCover` comes from the loaded tables, so the mod's ignore-cover changes count. Building: shells hit the building, so every round lands. Cover scales physical damage only; stress is not changed. The pinned-range panel lists each weapon's share through cover.
- **Weapons:** overlay ammo/weapon pairs. Sweep all four faces as extra lines. Clone and edit a weapon. Expected DPM uses the same spread-vs-size math as the Units tab. Pick a target unit for its box, or an armor row (kit plates use a unit that can wear them). Check **Assume hits** for 100% hits.

Click the chart to pin a range. The panel lists DPM, time-to-kill, card-metre range, penetration, and RoF. Selected rows, target armor, filters, profile customs, window size, and the active tab are saved to `user_data.json` and restored on the next launch.

## Math

- HEAT: `Damage * pen² / (pen² + armor²)`
- Kinetic: full damage at pen ≥ armor; zero at pen ≤ half armor; otherwise `max(0.1, 2 - 1/r)` of Damage
- Infantry / helicopters / value-armor rows always use the HEAT curve
- Penetration falls linearly from point-blank to `GroundRange`
- RoF uses magazine, burst, inter-shot, inter-burst, and reload midpoints
- Unguided hit chance: scale H×V spread from `DispersionMinimal` at 0 to full at `GroundRange`. The game (`ShootingSystem.AddBallisticDeviation`) draws `u` evenly in [-1, 1], then `v` evenly in [-(1 − |u|), 1 − |u|], and offsets the round by `(u × rx, v × ry)`. The hit chance is the share of those rounds inside a `width × height` box centred on the aim point. This is not the game's AI estimate `GetTargetAccuracy`, which overstates hits
- Target box (`HitDetectionSystem.GetUnitBox`): infantry are one square box of `1 + 0.5 × soldiers` metres (`InfantryConfig.BaseSquadSize` = 1), `Height` tall, for the full squad. In game, the box shrinks 0.5 m for each dead soldier, and soldiers die from the squad's health pool, not from hits on bodies. Vehicles use `min(Length, Width) × Height`
- Aim point at the box centre is assumed
- Building cover (`ShellHitSystem.DamageBuilding`): `M = clamp(floor + perSoldier × soldiers)`, damage × `(M + (1 − M) × IgnoreCover)`, no misses. Woods (FA `CoverDamage` hook): damage × `(1 − (1 − ForestDamageTaken) × (1 − IgnoreCover))`. How damage splits between several squads in one building is not modelled
- Seekers (`Seeker != 0`) use `DispersionHorizontalRadius` as accuracy (usually 1.0). ECM, decoys, stress, and moving-fire stabilizer are not applied
- Blast overlap after a miss is not modeled; a scattered HE round still counts as a miss here
