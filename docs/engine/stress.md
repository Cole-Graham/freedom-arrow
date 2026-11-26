# Stress

Suppression is the unit's stress bar. A hit adds blast stress plus a share of the health it removed. The bar clamps to `MaxStress`. At half the bar the unit is shocked, and at 80% it is panicked. Those two states scale aim, reload, dispersion, missile accuracy, and, for infantry, movement.

`BattleSystemHelpers.CalculateStressDamage` does the addition. `StressSystem.ApplyStressDamage` adds queued hits onto the current value. `BuffDebuffSystem.SetStressModifiers` reads the level and applies the row from `BuffConfig.StressModifiers`. The numbers below are that shipped asset.

## What a hit adds

```text
stressGain = stressFromBlast + MaxStress × (healthLoss / maxHealth)
stressFromBlast = StressDamage × stressFalloff × DoTModifier
```

`healthLoss` is the health damage after [falloff](damage-falloff.md) and armor. `maxHealth` is the target's full health. A hit that removes 10% of a 1000-stress unit's health also adds 100 stress, on top of the blast term.

`stressFromBlast` does not use armor. `StressDamage` is the ammunition field. `DoTModifier` is 1 on a normal impact. The falloff uses `StressAOERadius` the same way health uses `HealthAOERadius`:

```text
stressFalloff = 1                                          when NoDamageFalloff is set
stressFalloff = clamp(1 - distance / StressAOERadius, 0, 1)  when StressAOERadius > distance
stressFalloff = 0                                          when distance >= StressAOERadius
```

The radius is in world units. The card shows twice that number. Outside the stress radius the blast term is 0. A hit that still deals health damage inside the health radius still adds the health share. A hit inside the stress radius and outside the health radius adds only the blast term.

`ApplyStressDamage` sums the queued hits, adds them to the current value, and clamps the result to `MaxStress` and to at least 0. That apply step also clears the recovery timer.

524 units in the vanilla table have `MaxStress` 1000. 21 have 0, including the MQ-9. A 0 bar stays at 0 because the result is clamped to the bar.

## Worked hit

`StressDamage` 200, stored `StressAOERadius` 40 (80 m on the card), world distance 20, `DoTModifier` 1, health loss 2, max health 10, `MaxStress` 1000. Falloff is on.

```text
stressFalloff = 1 - 20/40 = 0.5
stressFromBlast = 200 × 0.5 = 100
health share = 1000 × (2 / 10) = 200
stressGain = 300
```

One such hit fills 300 of a 1000 bar, which is still under the shocked mark.

## Shocked and panicked

`StressSystem.SetStressLevel` compares the current value with two marks stored on the unit. `StressComponent` builds those marks as `MaxStress` times the `BuffConfig` multipliers. On the shipped asset the vehicle pair and the infantry pair are the same:

| Mark | Share of the bar | On a 1000 bar |
| --- | ---: | ---: |
| Shocked | 0.5 × MaxStress | 500 |
| Panicked | 0.8 × MaxStress | 800 |

Current stress at or above the panicked mark is level 2. Current stress at or above the shocked mark, and below panicked, is level 1. Below the shocked mark the level is 0.

`SetStressModifiers` multiplies the unit's combat channels by the `StressModifiers` row for that level. A factor above 1 lengthens that time or widens dispersion. A factor below 1 cuts missile accuracy or infantry speed. Calm is level 0 and is on the asset as well, because its infantry damage terms are already below 1.

Ground vehicles (`Type` 4), helicopters (`Type` 8), and ships (`Type` 32) use the general columns. Planes (`Type` 16) use the plane columns. Infantry (`Type` 2) use the infantry columns. Missile accuracy for everyone except planes uses the general missile column.

| Channel | Calm | Shocked | Panicked |
| --- | ---: | ---: | ---: |
| Aim time | 1 | 1.25 | 1.5 |
| Time between bursts | 1 | 1.25 | 1.5 |
| Reload | 1 | 1.25 | 1.5 |
| Dispersion | 1 | 1.15 | 1.52 |
| Missile accuracy | 1 | 0.85 | 0.55 |

| Plane channel | Calm | Shocked | Panicked |
| --- | ---: | ---: | ---: |
| Aim time | 1 | 1.5 | 2 |
| Time between bursts | 1 | 1.25 | 1.5 |
| Reload | 1 | 1.25 | 1.5 |
| Dispersion | 1 | 1.5 | 2 |
| Missile accuracy | 1 | 0.85 | 0.6 |

| Infantry channel | Calm | Shocked | Panicked |
| --- | ---: | ---: | ---: |
| Aim time | 1 | 1.5 | 2 |
| Time between bursts | 1 | 1.33 | 2 |
| Reload | 1 | 1.25 | 1.5 |
| Dispersion | 1 | 1.15 | 1.52 |
| Movement speed | 1 | 0.6 | 0.2 |
| Damage floor | 0.36 | 0.36 | 0.10 |
| Damage per soldier | 0.02 | 0.02 | 0.10 |

Infantry movement is multiplied by `MovementSpeedMultiplier` on that row. Shocked infantry move at 0.6 of their speed, and panicked infantry move at 0.2. Vehicles, helicopters, planes, and ships do not read that movement field in `SetStressModifiers`.

Infantry damage uses the floor and the per-soldier term:

```text
infantryDamageScale = clamp(InfantryDmgModFloor + count × InfantryDmgModPerSoldier, 0, 1)
```

`count` is the integer this path reads off the squad. The scale is applied when that path does not find an extra component on the unit. A squad of 7 soldiers is then:

| Level | Scale |
| --- | ---: |
| Calm | 0.36 + 7 × 0.02 = 0.50 |
| Shocked | 0.36 + 7 × 0.02 = 0.50 |
| Panicked | 0.10 + 7 × 0.10 = 0.80 |

The live Buff Config (path_id 52805) has the values above; an unused Buff Config object (52722) has 0.72/0.57/0.42 and 0.02/0.015/0.01. Lateralus's dev.26 Fletcher test (16 Nov 2026, 12 hits on a 12-man squad) matched the live values. The scale applies to hits under `StressDamageModThreshold` (36), and IgnoreCover blends it: `scale + (1 - scale) × IgnoreCover`. Freedom Arrow from the 0.9.0-dev.44 batch sets the floor to 1 and the per-soldier term to 0 on all three levels (`game-config.json` `InfantryOpenDamageFloor`/`InfantryOpenDamagePerSoldier`), so infantry outside buildings take full damage whatever their stress. Buildings, woods and IgnoreCover are unchanged. The wider cover rework is parked on branch `codex/batch/osama/cover-rework`.

Freedom Arrow's `game-config.json` replaces the two movement factors with shocked 0.7 and panicked 0.4. The other factors in these tables stay on the asset.

## Recovery

After the last stress is applied, `StressSystem.Update` drains the bar. The system sums the elapsed time it is given until that sum reaches 1 second, then runs one recovery step and subtracts that 1 second, so the step happens once per second. While queued stress is still waiting, the update applies the queue instead of recovering.

Each step adds 1 to a timer that counts seconds since the last apply, then subtracts from the bar:

```text
timer = timer + 1
stress = max(0, stress - (floor(timer) × StressRecoveryMultiplier + 1))
```

`StressRecoveryMultiplier` is 1 on the shipped `BuffConfig`, so the loss on second `n` is `n + 1`. The first quiet second removes 2. The next removes 3, then 4, and so on. `ApplyStressDamage` sets the timer back to 0, so a new hit restarts the count and the next quiet second removes 2 again.

A full 1000 bar, with no further hits:

| Seconds since the last stress | Removed this second | Stress left | Level |
| ---: | ---: | ---: | --- |
| 0 |  | 1000 | Panicked |
| 1 | 2 | 998 | Panicked |
| 19 | 20 | 791 | Shocked |
| 31 | 32 | 473 | Calm |
| 44 | 45 | 0 | Calm |

The level changes on the second the bar crosses the mark. At 19 seconds it falls through 800, so it is shocked. At 31 seconds it falls through 500, so it is calm. The bar is empty at 44 seconds.

A bar that has just reached panicked at 800 drops under 800 on the first quiet second (798) and is empty on second 39. A bar sitting on the shocked mark at 500 is under 500 on the first quiet second.

Freedom Arrow's `game-config.json` sets `StressRecoveryMultiplier` to 0.33 from 0.9.0-dev.36. `StressSystem` copies the value when the battle systems are built. The loss on second `n` is then `0.33 × n + 1`:

| Seconds since the last stress | Stress left | Level |
| ---: | ---: | --- |
| 0 | 1000 | Panicked |
| 32 | 793.8 | Shocked |
| 52 | 493.3 | Calm |
| 75 | 0 | Calm |

A bar that starts at 800 is empty on second 67. A bar that starts at 500 is empty on second 52.

## Exempting plane missiles from stress (feasibility, Lateralus 25 Nov 2026)

Proposal checked: remove the shocked/panicked missile accuracy, reload, time-between-bursts and aim-time debuffs for planes, only for Fire-and-forget (Seeker 10) and Terminal-guidance (Seeker 50) missiles. Read from code (1.2.2.1), not tested.

- **Where the debuffs live.** `BuffDebuffSystem.SetStressModifiers` (0x7EB380) writes one set of multipliers per unit into `BuffComponent` (`AimTimeModifier` 0x0, `TimeBetweenBurstsStressModifier` 0x8, `MagazineReloadTimeStressModifier` 0x10, `MissileAccuracyMultiplier` 0x38; obfuscated `GFloat`/`GAFloat`). Every weapon on the unit uses the same values, so a config change alone (the plane columns of `StressModifiers`) would also free guns, bombs, rockets, semi-active and SEAD missiles.
- **Missile accuracy: easy.** FA's `MissileHitChance.Chance` prefix already receives the round and the shooter's stress multiplier (`CalculateMissileHitChance`, 0x7D4130); it can use 1 instead for listed rounds. In 0.9.7-dev.15 data planes fire 38 Seeker 10/50 rounds; 3 of them (2016381, 2016975, 2017060) are also fired by non-plane units and need a shooter check or plane-only copies.
- **Aim time, bursts, reload: harder.** The per-weapon timer functions (`WeaponComponent.GenerateRandomAimTime` 0x82D520, `GenerateRandomTimeBetweenBursts` 0x82D9A0, `GenerateRandomMagazineReloadTime` 0x82D720, `GetAimTime` 0x82DAA0) have no direct callers (inlined), so they cannot be patched. Option: in FA's existing `ShootingSystem.InternalUpdate` hook (one weapon at a time), set the plane's three modifiers to 1 for a listed weapon and put them back afterwards, using the game's own `GFloat` conversion. Needs a trace that those modifiers are read only inside that update, and an in-game timing test.
- **Queued (missile accuracy only, Lateralus 25 Nov 16:1x):** `MissileHitChance.Chance` uses a stress multiplier of 1 for the 38 plane fire-and-forget / terminal-guidance rounds (`helicopter-range.json` `planeStressExempt`, built by `lateralus/plane_missile_stress_1125.py`). For the 3 rounds helicopters also fire (`planeStressShared`: PL-5E, PL-9, PL-10) it checks the shooter (`WarheadComponent.ShooterWeapon` -> unit Type 16) during the missile's roll; the AI's overkill score keeps the stress for them. Log line `FREEDOM_ARROW_PLANE_MISSILE_STRESS`. Aim time, bursts and reload are unchanged. Not tested in game.
- **Online.** Only the firing unit's own PC uses these values; the shots it then fires are sent as usual, so the other PCs stay in step.

## Document change log
- 2026-11-25 15:0x PST (America/Los_Angeles) — Added: feasibility of exempting plane fire-and-forget / terminal-guidance missiles from stress debuffs (Lateralus).
- 2026-11-25 16:2x PST (America/Los_Angeles) — Plane FF/TG missile accuracy exemption queued (Lateralus).
