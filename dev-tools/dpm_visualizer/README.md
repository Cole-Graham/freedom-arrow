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

`decrypt` writes `cache/vanilla/<build-id>/`. The visualizer autoloads that folder. Optional overlay: `mod/constants`, `mod/testing/constants`, or `releases/0.2/source/UserData/FreedomArrow/constants`.

```text
$env:PYTHONPATH = "dev-tools"
python -m unittest discover -s dev-tools/dpm_visualizer/tests
```

## Tabs

- **Units:** overlay several units against one armor face. Physical or stress. Cost-normalized DPM. Infantry RPG/ATGM weapons are omitted. Clone a unit’s armor and cost. Spread uses the target unit’s size, or a unit that wears the selected armor. Each comparison row has a **loadout** dropdown (weapon package × armor kit, or squad loadout). Armor, weapons, and the shown cost follow that loadout. With exactly two visible units, **Each vs the other's loadout** plots each line against the other unit’s selected plates; the checkbox is greyed out when more than two comparison rows are active.
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
- Aim point at the box centre is assumed. Garrisoned infantry are not modelled: in game, shells hit the building section instead
- Seekers (`Seeker != 0`) use `DispersionHorizontalRadius` as accuracy (usually 1.0). ECM, decoys, stress, and moving-fire stabilizer are not applied
- Blast overlap after a miss is not modeled; a scattered HE round still counts as a miss here
