# Engine combat math

How a high-explosive detonation becomes health loss on a vehicle. Both notes are the game methods in `ShellHitSystem` and `BattleSystemHelpers`, read from the installed binary. Stored radii are world units. The unit card prints twice that number: `HealthAOERadius` 50 is 100 m on the card.

- [Damage falloff](damage-falloff.md) scales raw damage by distance inside `HealthAOERadius` before armor.
- [Overpressure](overpressure.md) forces that already scaled hit onto top armor inside `OverpressureRadius`.
