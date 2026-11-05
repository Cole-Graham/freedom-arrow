# Broken Arrow DPM visualizer

Compare damage per minute vs range for Broken Arrow units and weapons. Expected DPM multiplies post-armor damage by `GetTargetAccuracy` (spread vs the target box). Check **Assume hits** to restore 100% hits. The range axis is **card metres** (world table range × 2), matching the targeting UI.

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

- **Units:** overlay several units against one armor face. Physical or stress. Cost-normalized DPM. Infantry RPG/ATGM weapons are omitted. Clone a unit’s armor and cost. Spread uses the target unit’s size, or a unit that wears the selected armor.
- **Weapons:** overlay ammo/weapon pairs. Sweep all four faces as extra lines. Clone and edit a weapon.

Click the chart to pin a range. The panel lists DPM, time-to-kill, card-metre range, penetration, and RoF. Selected rows, target armor, filters, profile customs, window size, and the active tab are saved to `user_data.json` and restored on the next launch.

## Math

- HEAT: `Damage * pen² / (pen² + armor²)`
- Kinetic: full damage at pen ≥ armor; zero at pen ≤ half armor; otherwise `max(0.1, 2 - 1/r)` of Damage
- Infantry / helicopters / value-armor rows always use the HEAT curve
- Penetration falls linearly from point-blank to `GroundRange`
- RoF uses magazine, burst, inter-shot, inter-burst, and reload midpoints
- Unguided hit chance: scale H×V spread from `DispersionMinimal` at 0 to full at `GroundRange`, then `min(rx, width) × min(ry, height) / (rx × ry)` with `width = min(Length, Width)`
- Seekers (`Seeker != 0`) use `DispersionHorizontalRadius` as accuracy (usually 1.0). ECM, decoys, stress, and moving-fire stabilizer are not applied
- Blast overlap after a miss is not modeled; a scattered HE round still counts as a miss here
