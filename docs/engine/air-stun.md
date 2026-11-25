# Air stun (feasibility, Lateralus 25 Nov 2026)

**Short answer.** Broken Arrow has no stun state. It does have a stress bar on planes and helicopters, and that bar is already sent over the network. A WARNO-style air stun can be built on top of that bar: data and config alone give a weak version, and one small Freedom Arrow system gives the WARNO effects (helicopter slowed, plane weapons held, stun icon). Nothing is built.

---

**Details (read from code, 1.2.2.1 dump; not tested in a game):**
- **No stun in BA.** `dump.cs` has no stun component, tag or state. The closest system is stress (see [stress.md](stress.md)).
- **Air units have the bar.** In the 0.9.7-dev.15 data, 109 planes and 89 helicopters have `MaxStress` 1000; 18 planes and 3 helicopters (drones) have 0.
- **Hits already add stress to aircraft.** A hit adds `StressDamage × falloff + MaxStress × health removed / max health`. AA missiles carry `StressDamage` 144 to 668 (FA data).
- **What stress already does to aircraft.** Shocked (50% of the bar) and panicked (80%) scale aim time, time between bursts, reload, dispersion and missile accuracy. Planes have their own columns (panicked: aim ×2, dispersion ×2, missile accuracy ×0.6). Movement speed is read only for infantry.
- **Recovery.** FA `StressRecoveryMultiplier` 0.33: a full bar drops under 800 after 32 s and under 700 after 40 s. The rate is global (one value for all units).
- **Network.** `NetworkUnitValuesSync` carries `Stress` and `MaxSpeed` (with `RemoteUpdateStress` / `RemoteUpdateMaxSpeed`), so every PC sees the same stress value, and a unit's max speed set on its owner's PC reaches the others.
- **Hooks.** `StressSystem.ApplyStressDamage` (0x811530), `SetStressLevel` (0x8116E0) and `StressRecovery` (0x8117C0) have no direct native callers (inlined), so a Harmony patch on them would not run. A stun system has to read `StressComponent` (`CurrentStressValue` +0x18) itself, a few times a second for air units only.

**WARNO model (docs/warno-air-stun.md) against BA:**
- Separate stun bar (plane max 255, helicopter 100, regen 1/s): BA has one bar. Use the stress bar with its own stun cut, or keep a Freedom Arrow bar (harder online: it would have to be computed from hits on every PC).
- Stun tag and icon: Freedom Arrow can draw an icon from the synced stress value.
- Helicopter speed ×0.30: needs Freedom Arrow code (stress does not slow vehicles); `MaxSpeed` is synced.
- Plane: in WARNO a stunned plane cannot fire, takes no orders, and keeps flying its last course until the stun clears (Lateralus 25 Nov; the WARNO doc lists only the tag).
- Veterancy resistance: BA has no veterancy.

## Building the WARNO plane stun in BA (proposal)

- **Stun state:** an air unit is stunned while its synced stress is above a chosen cut (for example 70% of `MaxStress`). Every PC reads the same synced value.
- **No firing:** a prefix on `ShootingSystem.InternalUpdate` (the shooter's own firing path, already hooked by `SameUnitClaim.cs`) skips the weapons of a stunned air unit. Shots from it are then never sent (`NetworkShootService.Send`), so other PCs see nothing to replay. Missiles already in flight keep flying.
- **No orders:** the player's order path (`MainCommandSystem.AddCommandToQuery`, 0x78C220) has no direct native callers, so it cannot be patched reliably. Instead, stunned air units are taken out of the player's selection every frame and cannot be re-selected while stunned (local UI only, same result on every PC because no order is sent). The unit keeps its last command, so it flies its previous course.
- **Not checked yet:** which PC applies stress damage to a unit (the owner's or each PC's), whether a plane's own automatic actions (return to base when out of ammo or fuel) should stay allowed, and whether a control-group hotkey re-selects before the filter runs.

## Document change log

- 2026-11-25 12:3x PST (America/Los_Angeles) — Created: air stun feasibility against the WARNO model (Lateralus).
- 2026-11-25 12:4x PST (America/Los_Angeles) — WARNO plane stun effects corrected (no firing, no orders, keeps course) and a BA build plan added (Lateralus).
