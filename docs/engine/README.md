# Engine combat math

How a detonation becomes health loss, a roof hit, or stress. The notes are the game methods in `ShellHitSystem`, `BattleSystemHelpers`, `StressSystem`, and `BuffDebuffSystem`, read from the installed binary. Stored radii are world units. The unit card prints twice that number: `HealthAOERadius` 50 is 100 m on the card.

- [Damage falloff](damage-falloff.md) scales raw damage by distance inside `HealthAOERadius` before armor.
- [Overpressure](overpressure.md) forces that already scaled hit onto top armor inside `OverpressureRadius`.
- [Stress](stress.md) adds blast stress and a share of the health lost, then Shocked and Panicked scale the unit until the bar recovers.
