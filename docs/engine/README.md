# Engine combat math

How a detonation becomes health loss, a roof hit, or stress. The notes are the game methods in `ShellHitSystem`, `BattleSystemHelpers`, `StressSystem`, and `BuffDebuffSystem`, read from the installed binary. Stored radii are world units. The unit card prints twice that number: `HealthAOERadius` 50 is 100 m on the card.

- [Damage falloff](damage-falloff.md) scales raw damage by distance inside `HealthAOERadius` before armor.
- [Overpressure](overpressure.md) forces that already scaled hit onto top armor inside `OverpressureRadius`.
- [Stress](stress.md) adds blast stress and a share of the health lost, then Shocked and Panicked scale the unit until the bar recovers.
- [Target and ammunition selection](target-and-ammo-selection.md) scores each round and each target, and shows why a weapon fires at a target it can barely damage.
- [Missile flight](missile-flight.md) explains how start speed, burn time, acceleration, top speed and the 30% death speed set a missile's real reach, and how that compares with its table range.
- [Low altitude and air sight](low-altitude-and-air-sight.md) explains the Ground / Low / High states, which optics an air target is checked against, and the 15-unit forest layer that blocks sight lines above the visible trees.
- [Infantry casualty and weapon order](infantry-casualty-and-weapon-order.md) explains which soldier dies first (`SquadMembers.DeathPriority`, highest first, ties random) and what `SquadWeapons.Order`, `WeaponChannel` and `WeaponPriority` do for infantry (list order only; no fire priority).
- [Infantry ammunition](infantry-ammo.md) explains the squad ammo pool (`WeaponAmmunitions.Quantity` × carriers) and the Arsenal card number (× `Ammunitions.HUDMultiplier`).
