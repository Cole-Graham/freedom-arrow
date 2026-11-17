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

## Stress

Stress uses the same shape with `StressAOERadius`, written to `StressAOEDamageModifier`. It does not go through the armor formula. `DealUnitDamage` sends `StressDamage × stressModifier × DoTModifier` to `BattleSystemHelpers.CalculateStressDamage`. A unit outside the health radius and inside the stress radius takes stress and no health damage.

## Buildings

`ShellHitSystem.DamageBuilding` is a separate call. It multiplies raw damage and `DoTModifier`, then the building cover share. It does not divide by `HealthAOERadius`. Infantry inside a building keep full raw damage into that cover share. The share itself is `Damage × (floor + (1 - floor) × IgnoreCover)`, with the floor and per-soldier term from the building config.
