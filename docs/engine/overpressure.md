# Overpressure

Overpressure turns a blast hit on a vehicle into a roof hit. The health damage is still the [falloff](damage-falloff.md) result. `OverpressureRadius` chooses the armor face. It does not add a second damage term and it does not restore damage that falloff already removed.

## When the flag is set

`Ammunitions.OverpressureRadius` is in world units, and the card shows twice that number. `DealAOEDamage` uses the same distance as health falloff: 3D distance from the detonation to the unit, minus that unit's radius, floored at 0.

```text
IsTargetOverpressured = OverpressureRadius > distance
```

The test is strict. A unit exactly on the overpressure radius keeps the face chosen from the impact. A unit past it does too. A unit outside `HealthAOERadius` already has a health modifier of 0, so the roof flag has no health to apply. On the rounds in this game the overpressure radius sits inside the health blast, so a unit inside the overpressure radius still has a positive health fraction.

`HitDamageInfo` starts with the flag clear. `DealAOEDamage` sets it on each nearby unit that passes the test.

## The unit the shell strikes

The unit that the shell hits directly does not get the distance test. `ShellHitSystem.InternalUpdate` builds its hit with:

```text
IsTargetOverpressured = OverpressureRadius > 0
```

The comparison register is 0 for the whole method (1.2.2.1 RVA `0x7fe0f0`: `movss xmm0,[ammo+0x98]; comiss xmm0,xmm7; seta`). `InternalUpdate` then adds that unit to the list that `DealAOEDamage` skips, so the blast does not test it again. The health fraction of a direct hit stays 1.

Result: every direct hit from a round with `OverpressureRadius` above 0 uses the roof, at full damage, from every angle. In vanilla this applies to direct-fire rounds such as the AC-130 105 mm (ammo 57), the S-24 (917, 918) and the S-25 (314). No vanilla anti-aircraft gun round has an overpressure radius.

## What the roof hit uses

`DealUnitDamage` forces the roof when any of these is set:

- `IsTargetOverpressured`
- `ForceTopAttack` on the hit
- `BattleSystemHelpers.DoesProjectileUseTopArmorAttack` for this ammunition and target

The call is then:

```text
CalculateHitDamage(target, baseDamage, ammo, penetration, forceTop = true, side = Top)
```

`baseDamage` is `rawDamage × healthModifier × DoTModifier` from the falloff step. `side` Top is armor-side value 3. High explosive resolves it with `DamageFormulaHEAT` against top armor:

```text
healthLoss = baseDamage × penetration² / (penetration² + topArmor²)
```

Top armor is much thinner than the side or rear plate, so the same base damage leaves a much larger health loss.

## The other roof path

With the flag clear, `BattleSystemHelpers.GetArmorSideFromShotVector` picks the face from the impact vector, in the target's local angles:

| Face | Value | Rule |
| --- | ---: | --- |
| Top | 3 | vertical angle below −30° (coming down steeper than 30° from horizontal) |
| Front | 0 | horizontal angle inside ±45° |
| Sides | 1 | horizontal angle from 45° through 135° |
| Rear | 2 | horizontal angle beyond 135° |

A bomb that falls onto the vehicle still hits the roof through this angle test. A blast beside the vehicle hits the roof only through overpressure, `ForceTopAttack`, or the ammunition top-attack flag. Those forced hits pass `forceTop` as well as side Top. A geometric roof hit passes side Top with `forceTop` clear.

## Same shell, three places

Stored `HealthAOERadius` 40 (80 m on the card), `OverpressureRadius` 20 (40 m on the card), `Damage` 12, penetration 50, top armor 20, side armor 80. Falloff is on. `DoTModifier` is 1.

| World distance | Card-scale distance | Health fraction | Face | Health loss |
| ---: | ---: | ---: | --- | ---: |
| 10 | 20 m | 0.75 | Top, overpressure | 7.76 |
| 30 | 60 m | 0.25 | Side, geometry | 0.84 |
| 40 | 80 m | 0 | none | 0 |

At 10, base damage is 9 and the roof formula is `9 × 50² / (50² + 20²) = 7.76`. At 30 the base damage is 3 and the side formula is `3 × 50² / (50² + 80²) = 0.84`. The distance from 10 to 30 costs both the falloff and the roof.

## Where the mod changes this

`OverpressureRadius` is an ammunition field. Setting it to 0 leaves `IsTargetOverpressured` clear for that round, so a near miss keeps the geometric face. In 0.6 dev.49 that is what unguided bombs (Mk 82/83/84, FAB, OFAB) do. `mod/source/conquest/BombRoof.cs` also clears a leftover `forceTop` on those bombs inside `CalculateHitDamage`, and leaves a geometric roof hit in place when the impact is steeper than 30°.

In 0.9 dev.45 the JRVG-1 76 mm proximity HE (ammo 2009953) goes from 4.5 to 0. Build 68 copied it from the Mark 45 127 mm naval HE, but the round kept direct fire and vehicle targets. Each direct hit on a tank therefore used the roof: `8 × 60² / (60² + 100²) = 2.12` health per hit on a main battle tank roof, against `0.66` on a 200 side.
