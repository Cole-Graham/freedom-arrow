# Damage falloff

A blast does less health damage as the target sits farther from the detonation. The fraction is applied to raw damage first. Armor, including an overpressure roof hit, runs on that reduced number.

`ShellHitSystem.InternalUpdate` does this for the unit the shell strikes. `ShellHitSystem.DealAOEDamage` does it again for every other unit inside the blast. Both write the fraction onto the hit as `HealthAOEDamageModifier`, and `ShellHitSystem.DealUnitDamage` multiplies it in before `BattleSystemHelpers.CalculateHitDamage`.

## Health fraction

`Ammunitions.HealthAOERadius` is the blast radius in world units. The card shows twice that (`50` stored is `100` m on the card). `distance` is in the same world units.

```text
healthModifier = 1                                          when NoDamageFalloff is set
healthModifier = clamp(1 - distance / HealthAOERadius, 0, 1)  otherwise, and only when HealthAOERadius > distance
healthModifier = 0                                          when distance >= HealthAOERadius
```

`NoDamageFalloff` is the ammunition flag that skips the curve and keeps full raw damage at every distance inside the hit. With the flag clear, damage is full at the detonation and reaches 0 at the stored radius. The comparison is strict: a unit sitting exactly on the radius gets no health damage from the blast.

For a nearby unit, `DealAOEDamage` measures the 3D distance from the detonation to the unit, subtracts a radius stored on that unit, and floors the result at 0. A detonation inside that per-unit radius is distance 0, so the health fraction is 1.

`HitDamageInfo` is built with this modifier at 1. The blast path overwrites it. `DealUnitDamage` then keeps the hit only when the modifier is greater than 0.

## What reaches the armor formula

On an ordinary hit the other two factors are 1. `DoTModifier` is the damage-over-time scale; a normal impact leaves it at 1. The value passed into `CalculateHitDamage` as base damage is:

```text
baseDamage = rawDamage × healthModifier × DoTModifier
```

`rawDamage` is the ammunition `Damage` stored on the hit. High explosive then uses `BattleSystemHelpers.DamageFormulaHEAT` against whichever face the hit selected:

```text
healthLoss = baseDamage × penetration² / (penetration² + armor²)
```

Kinetic ammunition uses `DamageFormulaKinetic` on the same `baseDamage`: full damage when penetration / armor is at least 1, no damage at or below 1/2, and `baseDamage × max(0.1, 2 - armor / penetration)` in between.

[Overpressure](overpressure.md) changes the face to top armor. It uses this `baseDamage` and does not put the fraction back to 1.

## Worked blast

Stored `HealthAOERadius` 40 (80 m on the card), `Damage` 12, penetration 50, top armor 20. `NoDamageFalloff` is clear and `DoTModifier` is 1.

| World distance | Card-scale distance | Health fraction | Base damage | HEAT vs top armor 20 |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 m | 1.00 | 12.0 | 10.34 |
| 10 | 20 m | 0.75 | 9.0 | 7.76 |
| 20 | 40 m | 0.50 | 6.0 | 5.17 |
| 30 | 60 m | 0.25 | 3.0 | 2.59 |
| 40 | 80 m | 0 | 0 | 0 |

`10.34 = 12 × 50² / (50² + 20²)`.

## Penetration over range

**Short answer:** only kinetic rounds lose penetration with range. HEAT rounds always use `PenetrationAtGroundRange`, at any distance. Rounds that target no armor have unlimited penetration.

*Details (read from GameAssembly 1.2.2.1, `GetPenetrationForAmmunition` 0x7D70B0 and `GetPenetrationForShell` 0x7D71D0; not measured in a game):*

```text
ArmorTargeted 0 (none):     penetration = float.MaxValue
ArmorTargeted 1 (Kinetic):  penetration = PenAtMin - (PenAtMin - PenAtGround) × distance / (refRange - MinimalRange)
ArmorTargeted 2 (HEAT):     penetration = PenetrationAtGroundRange
then clamped to >= 0
refRange = GetDispersionReferenceRange(): GroundRange, else LowAltRange, else HighAltRange, else 1000 (cached)
```

- 21 HEAT rounds in 0.9.6 have a different `PenetrationAtMinRange`, mostly aircraft cannons (GAU-8 150 → 75, GAU-12 120 → 60, most 30 mm plane guns 40 → 20). The game uses only their ground-range value.
- The DPM visualizer (Lateralus's `dev-tools/dpm_visualizer/calculations.py` `penetration_at_range` and the web copy `dpm-core.js` `DPM.pen`) interpolates every round from min-range to ground-range penetration, HEAT included, over `distance / GroundRange`. It differs from the game for those 21 HEAT rounds, and slightly for the 40 kinetic rounds with `MinimalRange` > 0 (the game divides by `GroundRange - MinimalRange`).

## Stress

Stress uses the same shape with `StressAOERadius`, written to `StressAOEDamageModifier`. That fraction scales the ammunition `StressDamage` only. `BattleSystemHelpers.CalculateStressDamage` then adds `MaxStress × (healthLoss / maxHealth)` as well. The levels, the shocked and panicked modifiers, and the recovery clock are in [Stress](stress.md). A unit outside the health radius and inside the stress radius takes the blast term and no health share.

## Infantry squads

An explosive applies one health fraction to the whole squad. How many soldiers are still alive changes that fraction inside a building, and it changes how large a target the squad is in the open.

The horizontal length, in the same world units as `distance`, is:

```text
squadSize = BaseSquadSize + 0.5 × livingSoldiers
```

`InfantryConfig.BaseSquadSize` is 1. `InitInfantry` computes it when the squad is created. `HealSquad` and `KillSquadSolders` compute it again from the soldiers still alive, so each soldier added or killed changes the length by 0.5. `InfantryUnitComponent` stores it, and the squad collider is set to `(squadSize, height, squadSize)`.

`HitDetectionSystem.GetUnitBox` uses that length for the width and the depth. The vertical size is `Units.Height`. A shell hits the squad when it meets that box. Seven living soldiers make a box 4.5 world units on a side, 9 m on the card scale. One living soldier is 1.5 world units, 3 m on the card. A blast that reaches the larger box misses a smaller squad.

For a squad already inside the blast, `DealAOEDamage` measures one distance and applies one health fraction to the squad's health pool (`Armors.MaxHealthPoints`).

The distance that enters the fraction is the 3D distance from the detonation to the squad center, minus the radius stored on that unit. A negative result becomes 0. Distance 0 makes the health fraction 1, so the armor formula receives the full raw `Damage`.

The squad in the rows below is seven living soldiers on the `Armor Infantry 7Men` row. Its health pool is 35, which is 5 per soldier. `GetArmorBySideAndType` returns `ArmorValue` whenever that value is above 0, and this row's `ArmorValue` is 6, so every face is armor 6. Its target box is 4.5 wide, 2.0 tall, and 4.5 deep: `1 + 0.5 × 7` on the two horizontal axes and `Units.Height` on the vertical. On the card that is 9 m × 4 m × 9 m. The radius subtracted from the center distance in these rows is 4.

The blast is the one above: `HealthAOERadius` 40, `Damage` 12, penetration 50.

| Center distance | Card-scale center | Distance used | Health fraction | Base damage | Health loss | Pool left of 35 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 6 m | 0 | 1.00 | 12.0 | 11.83 | 23.17 |
| 14 | 28 m | 10 | 0.75 | 9.0 | 8.87 | 26.13 |
| 24 | 48 m | 20 | 0.50 | 6.0 | 5.91 | 29.09 |
| 44 | 88 m | 40 | 0 | 0 | 0 | 35 |

`14 - 4 = 10`, and `1 - 10/40 = 0.75`. `3 - 4` is negative, so the distance used is 0 and the armor formula receives all 12. Health loss is `baseDamage × 50² / (50² + 6²)`. The "Distance used" column is the "World distance" column of the table above.

A two-soldier squad on `Armor Infantry 2Men` has a health pool of 10 and a box 2.0 wide, 2.0 tall, and 2.0 deep (4 m × 4 m × 4 m on the card). Its armor is also 6. At the same center, with the same stored radius, the first row removes the same 11.83 from that pool of 10.

## Buildings

`ShellHitSystem.DamageBuilding` is a separate call. It multiplies raw damage and `DoTModifier`, then one building cover share. It does not divide by `HealthAOERadius`. Infantry inside a building keep full raw damage into that share.

Inside a building the soldier count changes the damage taken. The blast keeps its full raw damage, and a larger squad keeps a larger share of it. When the squad is created, health per soldier is stored from the armor record and the squad roster:

```text
healthPerSoldier = Armors.MaxHealthPoints / squadMemberCount
```

For each squad in the building, `DamageBuilding` turns current health back into a soldier count, rounded to the nearest integer and capped at the soldiers still on that squad:

```text
soldiers = round(currentHealth / healthPerSoldier)
```

Those counts are added together, and that sum is the `soldiers` in the share:

```text
M = clamp(DamageModifierFloor + DamageModifierPerSoldier × soldiers, 0, 1)
share = M + (1 - M) × clamp(IgnoreCover, 0, 1)
```

The shipped `BuildingsConfig` has a floor of 0.18 and 0.02 per soldier. A building holding 7 soldiers and a weapon with `IgnoreCover` 0 keeps `0.18 + 0.02 × 7 = 0.32` of the raw damage. Two soldiers keep `0.22`. On the worked blast above (`Damage` 12), that is 3.84 before armor for 7 soldiers and 2.64 for 2 soldiers. `IgnoreCover` 1 keeps all 12.

Freedom Arrow's `game-config.json` sets the floor to 0.3 (`BuildingDamageFloor`, from 0.9.4-dev.5; 0.18 before) and `BuildingDamagePerSoldier` to 0, so `M` stays 0.3 for every squad size.

## Woods and open ground (Freedom Arrow)

Vanilla has no terrain factor. Freedom Arrow's `CoverDamage` hook multiplies the result of `CalculateHitDamage` (after the blast fraction and armor) for infantry standing on `TerrainType.Forest`:

```text
share = 1 - (1 - ForestDamageTaken) × (1 - IgnoreCover)
```

`ForestDamageTaken` is 0.55 in `game-config.json`. In the open, `InfantryOpenDamageFloor` 1 and `InfantryOpenDamagePerSoldier` 0 switch off vanilla's stress-based damage reduction, so infantry in the open take full damage at every stress level.

## Worked example: 155 mm HE on an 8-man squad

Every 152/155 mm howitzer HE round in 0.9.5b has `Damage` 12, penetration 45, `HealthAOERadius` 45 (90 m on the card) and `IgnoreCover` 0.357. Infantry armor is 6 (Elite 10); each soldier is 5 health. Penetration 45 against armor 6 keeps `45² / (45² + 6²)` = 98.3% of the base damage. Theoretical, from the code and data; not measured in a game.

| Where | Share | Direct hit | 22.5 world (45 m card) from the impact |
| --- | ---: | ---: | ---: |
| Open | 1 | 11.8 health (2.4 soldiers) | 5.9 (1.2) |
| Woods | 0.711 | 8.4 (1.7) | 4.2 (0.8) |
| Building | 0.3 + 0.7 × 0.357 = 0.550 | 6.5 (1.3) | 6.5 (1.3), no falloff |
