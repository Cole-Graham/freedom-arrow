# Missile flight: range, burn time and speed

A missile has no fuel value. Its motor is `BurnTime`: the number of seconds it accelerates. The table ranges (`GroundRange`, `LowAltRange`, `HighAltRange`) only decide when a weapon may fire (see [Target and ammunition selection](target-and-ammo-selection.md#1-search-who-is-a-candidate)). Once the missile is launched, its speed fields decide how far it gets. It dies when it slows to 30% of `MaxSpeed` after burnout. A larger table range with the same motor lets a missile be fired from further away, but the missile does not fly further.

The addresses are for game build 1.2.2.1.

| Method | RVA |
| --- | ---: |
| `ProjectileSpawnerHelper.SpawnMissile` | `0x7DF4D0` |
| `BattleSystemHelpers.GetShellMuzzleSpeed(Entity, Ammunitions)` | `0x7D7C40` |
| `MissileStarterSystem.InternalUpdate` | `0x809730` |
| `RocketEngineSystem.IntenalUpdate` | `0x80B830` |
| `MissileGuidanceSystem.InternalUpdate` (speed death test at `0x8071AE`) | `0x806E90` |
| `SeekerSystem.InternalUpdate` | `0x827E40` |

## The fields

| `Ammunitions` field | Use |
| --- | --- |
| `MuzzleVelocity` | Added to the launcher's speed to give the start speed. It is 0 on every air-to-air missile. |
| `MainEngineIgnitionDelay` | Seconds from launch to motor start. |
| `Acceleration` | Speed gained per second while the motor burns. |
| `BurnTime` | Seconds that the motor burns, counted from ignition. |
| `MaxSpeed` | Top speed during the burn. It also sets the coast loss and the death speed. |
| `AimStartDelay` | Seconds from launch to the start of guidance. |
| `RotationSpeed`, `PreEgnitionRotationSpeed` | Turn rate after and before ignition. |

| `BattleSystemSettings` value | Setting |
| --- | ---: |
| `MISSILE_DECELERATION_PROPORTION` | 0.13 |
| `MISSILE_DEATH_SPEED_PROPORTION` | 0.3 |
| `MISSILE_GRAVITY_ACCELERATION_BEFORE_MOTOR_ACTIVATION` | 10 |
| `MISSILE_NO_TARGET_SUPPORT_TIME` | 2 |

## Flight, step by step

1. **Launch.** `SpawnMissile` sets the start speed with `GetShellMuzzleSpeed`:

   ```text
   v0 = MuzzleVelocity + launcherSpeed × cos(angle between the weapon's forward and the unit's forward)
   ```

   A jet that fires straight ahead gives its own speed to the missile. Fighter fly presets have `MaxSpeed` 225 and afterburner 315. `Fighter-Top` has 250 and 350.

2. **Before ignition.** `MissileStarterSystem` counts `TimeSinceLaunch`. The motor becomes active when the time reaches `MainEngineIgnitionDelay`, and guidance starts at `AimStartDelay`. Until ignition, `RocketEngineSystem` adds no speed. It only bends the velocity down by 10 units per second².

3. **Burn.** `RocketEngineSystem` runs this every frame while `TimeSinceActivation < BurnTime`:

   ```text
   speed = MaxSpeed                        if speed ≥ MaxSpeed
   speed = speed + Acceleration × dt       otherwise
   ```

   If `v0 + Acceleration × BurnTime` is less than `MaxSpeed`, the missile never reaches `MaxSpeed`. An AMRAAM fired from a jet at 225 burns out at 1025, not 1150.

4. **Coast.** After the burn:

   ```text
   speed = speed − MaxSpeed × 0.13 × dt
   ```

   The loss is a fixed amount per second, set by `MaxSpeed`. It does not depend on the speed at that moment.

5. **Death.** `MissileGuidanceSystem` sets the missile dead (`SetMissileDead`, reason 6) and removes its motor when:

   ```text
   TimeSinceActivation ≥ BurnTime  and  speed ≤ 0.3 × MaxSpeed
   ```

   A missile that burns out at full `MaxSpeed` coasts for `(1 − 0.3) / 0.13 = 5.4 s` and covers `3.5 × MaxSpeed` in that time.

`SeekerSystem` can also end the flight. For example, the target can leave the seeker's field of view, or the missile can stay without a target for more than 2 s (0 s for seeker type 50). The seeker's `MaxRange` is used as a search and lock distance. No missile component stores the distance flown, and none of the methods above compares it with the table range.

## Reach

Straight line, no turning, no gravity sag, no loft. `vb` is the speed at burnout.

```text
ignition:  d0 = v0 × MainEngineIgnitionDelay
burn:      vb = min(MaxSpeed, v0 + Acceleration × BurnTime)
           d1 = v0 × BurnTime + Acceleration × BurnTime² / 2                                when it never reaches MaxSpeed
           d1 = (MaxSpeed² − v0²) / (2 × Acceleration) + MaxSpeed × (BurnTime − t1),
                t1 = (MaxSpeed − v0) / Acceleration                                        otherwise
coast:     d2 = (vb² − (0.3 × MaxSpeed)²) / (2 × 0.13 × MaxSpeed)
reach      = d0 + d1 + d2
```

Example: AMRAAM fired from a jet at 225. `d0 = 112`, `vb = 1025`, `d1 = 2500` and `d2 = 3116`, so the reach is 5728 world units in 9.1 s.

What the reach means depends on the target:

- **A target flying toward the missile** shortens the distance, so a missile can be fired from further out.
- **A target flying away** has to be caught. The best launch distance against it is `max over t of (distance flown(t) − targetSpeed × t)`.

## Air-to-air missiles in 0.9 dev.44

Ranges are stored world units. The unit card shows twice the number. The launcher speed is 225, and the target in the last two columns flies at 225 in a straight line. All of these are calculated with the rules above and have not been measured in a game.

| Missile (motor) | Vanilla range | dev.44 range | Reach | Flight time | Fleeing target at 225 | Target closing at 225 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AIM-9 / R-73 / R-60 (600, 200, 3 s, no delay) | 1000 | 1000 | 3549 | 8.4 s | 1675 | 5436 |
| R-27T (600, 200, 3 s) | 1250 | 1750 | 3662 | 8.9 s | 1675 | 5661 |
| R-27ET (700, 200, 3 s) | 1500 | 2000 | 4099 | 8.9 s | 2101 | 6099 |
| AIM-7M / R-27ER (800, 200, 4 s) | 2500 | 3000 | 5287 | 9.9 s | 3062 | 7511 |
| AMRAAM / R-77-1 (1150, 200, 4 s) | 3500 | 4000 | 5731 | 9.1 s | 3694 | 7767 |
| PL-15 / PL-16 (AMRAAM motor) | new | 4500 | 5731 | 9.1 s | 3694 | 7767 |
| AIM-260 JATM, B-21 only, ammo 2001658 (AMRAAM motor) | new | 5500 | 5731 | 9.1 s | 3694 | 7767 |
| R-37 / AIM-174 / AIM-260 (1150, 300, 5 s); PL-17 and PL-21 are new rows with this motor and range | 4500 | 5500 | 8462 | 10.9 s | 6013 | 10911 |

The motor values are `MaxSpeed`, `Acceleration` and `BurnTime`. Every missile except the AIM-9 class has a 0.5 s ignition delay.

**What the mod changed.** 0.6 dev.52 (8 November) added 500 units of range to the nine vanilla missiles in the table (`air-range-contract.json`). PLA Build55 copied the AMRAAM for the PL-15 and PL-16, with 500 more range. No change touched `BurnTime`, `Acceleration`, `MaxSpeed`, `MainEngineIgnitionDelay` or `MuzzleVelocity`. Every motor value in dev.44 is the vanilla value.

**What that does.**

- Against a target that does not run, every missile can still reach its new range.
- Against a target that runs, these missiles now fire from further out than they can catch it:
  - AMRAAM, R-77-1, PL-12 and PL-15C catch a fleeing target out to about 3700, and they are fired out to 3500–4000.
  - PL-15 and PL-16 are fired out to 4500.
  - The B-21's JATM (2001658) is the largest gap: it is fired out to 5500. The F-22's AIM-260 (531) and the PL-17 have the R-37 motor and catch a fleeing target out to about 6000.
  - The R-27T is fired out to 1750 against a catch distance of about 1675. The AIM-7M and R-27ER are fired out to 3000 against about 3060.
- A missile that runs out of speed dies in flight.

**0.9 dev.45 batch (Lateralus, 19 November).** These AMRAAM-motor rows go to `BurnTime` 4.5 s: 89, 159, 920, 2016380, 2016390, 2011459, 2011471, 2016398 and 2017953. They then reach `MaxSpeed`, and the catch distance at 225 goes from 3694 to 4688. The B-21 JATM (2001658) takes the F-22 AIM-260 motor (`Acceleration` 300, `BurnTime` 5), so it catches to 6013. The J-8 PL-12 (2011537, range 3500) already catches its range and stays. The R-37 rows 312 and 921 go back to `DispersionHorizontalRadius` 1.0. All of this is calculated and has not been seen in a game.

**To give a missile more real reach,** raise `BurnTime` or `Acceleration` so that it burns for longer or reaches `MaxSpeed`, or raise `MaxSpeed`. The coast after burnout is always 5.4 s at most and `3.5 × MaxSpeed` long, so `MaxSpeed` sets the coast as well as the top speed.

## Reload while the missile flies

**Short answer:** a launcher reloads during the flight, except when its round has `PreventReloadWhileTracked` and `Seeker` 50 (terminal guidance) or 100 (semi-active). Then the reload timer stops until every missile the launcher guides has died: hit, shot down or out of speed. In 0.9.7l-dev.22, 103 ammunition rows have both, for example the TOW, Kornet, Konkurs, Metis, Hellfire and HJ-73. The CH-901 (ammo 2018448, `Seeker` 0, flag off) reloads during its flight.

*Read from GameAssembly 1.2.2.1 (Lateralus 26 Nov 2026, thread 1568104480459722894: "check if the reload of the next missile starts while the previous missile is in flight"). Not measured in a game.*

---

| Method | RVA |
| --- | ---: |
| `ShootingSystem.WeaponForceFire` (guidance set after `SpawnMissile`, `0x8100E0`) | `0x80E4C0` |
| `MagazineReloadingSystem.InternalUpdate` (reload stop, `0x7F4AB4`) | `0x7F4680` |
| `MissilesHelper.UpdateDeadMissileWeapon` (guidance removed, `0x80B58F`) | `0x80B4D0` |

1. **Launch.** After `SpawnMissile`, `WeaponForceFire` reads the round's `Seeker` (`Ammunitions` +0x108). For 50 or 100 it gives the weapon an `ActiveGuidanceComponent` (built from `Weapons.MultiTargetTracking` +0x5C and `SimultaneousTracking` +0x60) and adds the missile to it. Other seekers (0, 10 fire-and-forget, 200 SEAD, 300 laser) get none.
2. **Reload.** Every frame of a reload, `MagazineReloadingSystem` checks the selected round's `PreventReloadWhileTracked` (`Ammunitions` +0x130). If it is set and the weapon has an `ActiveGuidanceComponent`, the method returns before it adds the frame time to the reload. The reload starts again from where it stopped.
3. **Missile death.** `UpdateDeadMissileWeapon` removes the dead missile from the component. When no missile is left (`ActiveMissiles` 0), it removes the component, and the reload continues.

So for a launcher with one round in its magazine, one cycle is the flight plus the reload. An infantry squad's shared weapon reloads faster with more carriers alive (the frame time is multiplied by `UsingAliveSoldierCount`), but the flight is not shortened.

### DPM visualizer

From 26 Nov 2026 (Lateralus), the web DPM visualizer (`dpm-core.js` on freedomarrow.app) counts missile flight:

- **Flight time:** the straight line above, from a standing launch (launcher speed 0), for `TrajectoryType` 100, 110, 120, 200 and 600. A missile that cannot reach the distance shows "falls short" and the time to its death.
- **TTK:** plus the flight to the pinned distance (and the burn delay of a burning round).
- **DPM:** for a round that stops the reload, the flight to that distance is added to every magazine cycle. A squad's shared weapon divides only the reload by its carriers. Other rounds keep their DPM.
- **Pin panels:** "flight N s, the reload waits for it" or "reloads during the flight".

Calculated examples (0.9.7l-dev.22 data, theoretical, not yet proven in a game):

- Humvee TOW-2 (reload 5–6 s, magazine 1): DPM 114.6 at every range before; now 68.9 at 800 card m and 55.4 at 1,600 card m (TOW flight 3.6 s and 5.9 s).
- Blood Wolves CH-901: DPM unchanged (it reloads during the flight); TTK plus 5.2 s at 1,400 card m.
- HJ-73 / HJ-73D (`MaxSpeed` 100, `Acceleration` 30, `BurnTime` 4): the straight-line reach is about 600 world units (1,200 card m). The vehicle rows have a table range of 650 (Type 86, ammo 2010905) and 800 (ZBD-03 / ZLC-2000, ammo 2011153), so from about 1,200 card m their missiles die before they arrive.

## Not covered

- **Turning:** the pursuit path is longer than a straight line, and `RotationSpeed` limits the turn.
- **Loft:** `LoftAngle` and `LoftHeight` make a longer path.
- **Gravity:** the gravity on the speed vector before ignition is left out.
- **Speed units:** the figures assume that a plane's speed and a missile's speed are in the same units.
- **Launch rate while guiding:** whether `SimultaneousTracking` also stops a weapon with more than one round in its magazine from firing again was not traced.

## Document change log

- 2026-11-26 16:3x PST (America/Los_Angeles) — Added "Reload while the missile flies" (PreventReloadWhileTracked + Seeker 50/100 stop the reload until the missile dies), the DPM visualizer flight model, and the HJ-73 reach note (Lateralus).
