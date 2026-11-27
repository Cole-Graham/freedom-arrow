# Engine combat math

How a detonation becomes health loss, a roof hit, or stress. The notes are the game methods in `ShellHitSystem`, `BattleSystemHelpers`, `StressSystem`, and `BuffDebuffSystem`, read from the installed binary. Stored radii are world units. The unit card prints twice that number: `HealthAOERadius` 50 is 100 m on the card.

- [Damage falloff](damage-falloff.md) scales raw damage by distance inside `HealthAOERadius` before armor.
- [Overpressure](overpressure.md) forces that already scaled hit onto top armor inside `OverpressureRadius`.
- [Damage over time](damage-over-time.md): burning rounds deal no impact damage; their fire hits everything in `HealthAOERadius` every 0.5 s.
- [Stress](stress.md) adds blast stress and a share of the health lost, then Shocked and Panicked scale the unit until the bar recovers.
- [Target and ammunition selection](target-and-ammo-selection.md) scores each round and each target, and shows why a weapon fires at a target it can barely damage.
- [Missile flight](missile-flight.md) explains how start speed, burn time, acceleration, top speed and the 30% death speed set a missile's real reach, and how that compares with its table range, and when a launcher's reload waits for its missile.
- [Low altitude and air sight](low-altitude-and-air-sight.md) explains the Ground / Low / High states, which optics an air target is checked against, and the 15-unit forest layer that blocks sight lines above the visible trees.
- [Infantry casualty and weapon order](infantry-casualty-and-weapon-order.md) explains which soldier dies first (`SquadMembers.DeathPriority`, highest first, ties random) and what `SquadWeapons.Order`, `WeaponChannel` and `WeaponPriority` do for infantry (list order only; no fire priority).
- [Infantry soldiers with two weapons](infantry-dual-weapons.md): no shotgun switch; each weapon fires at its own rate × carriers, inside its own range, and a man aiming one weapon is skipped by the other for about 0.5 s.
- [Infantry ammunition](infantry-ammo.md) explains the squad ammo pool (`WeaponAmmunitions.Quantity` × carriers) and the Arsenal card number (× `Ammunitions.HUDMultiplier`).
- [NLOS missiles](nlos.md) explains the cruise-launcher data and the `NlosTrait` hook that lets the HJ-10, CTL-181 and QN-502 fire on spotted targets without line of sight and keep their lock, and the bugs that shaped it.
- [Cargo capacity](cargo-capacity.md) explains why a truck's supply and a helicopter's lift are `MobilityJson.HeavyLiftWeight` on the mobility row the unit actually uses (armory options with `MobilityId` replace it), why the HMV3 Cargo 15000 change failed three times, and how to change cargo safely.
- [Menu fly-in animation](ui-fly-in-animation.md) explains why a GalaxyUI card ends where it was before the layout ran (FlyFadeIn saves, flies, snaps back), and how the Play tab keeps layout and resting position together.
- [FAModels model loading](model-loading.md) explains when FAModels swaps a unit's model, how its detail levels (LOD0 most detailed) switch, and the 0.3.45 lightest-level-first loading with a 6 ms per-frame limit.
- [FAModels canopy glass](model-glass.md) explains borrowed cockpit glass (`cockpitDonor`), the stand-in used until the game loads it, and the 0.3.50 `preserveSpecular` option that keeps the stand-in reflective.
- [Transports and unit-swap loadouts](transport-unit-swaps.md) explains why a transport must not use `ReplaceUnitId` loadouts: the deck builds the transport without following the swap, so the shop counts a different unit from the one on the map (Type 100 CSV availability bug).

## Document change log

- 2026-11-24 13:50 PST (America/Los_Angeles) — Added the FAModels model loading page.
- 2026-11-25 18:5x PST (America/Los_Angeles) — Added the damage-over-time page.
- 2026-11-26 01:26 PST (America/Los_Angeles) — Added the transport unit-swap page.
- 2026-11-26 16:3x PST (America/Los_Angeles) — Missile flight entry: reload wait.
- 2026-11-26 21:4x PST (America/Los_Angeles) — Added the FAModels canopy glass page.
