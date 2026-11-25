# NLOS missiles (HJ-10, CTL-181, QN-502, CH-901)

> **Changed for 0.9.7 (Osama, 24 Nov 2026): the NLOS missiles now use the vanilla Iskander-K cruise guidance (Fire Position only), and the NLOS code is off.**
> - **Why:** in 0.9.6 every NLOS launch in Osama's log (20 launches, 17:08-17:13) was aimed at a ground spot. The code then locked each missile on the enemy nearest that spot (1-58 away) without checking that anyone saw it, and held the lock. To players, the launcher seemed to find and track targets nobody could see.
> - **Now (Osama 21:2x, "not the cruise" → back to cruise):** the rounds copy the vanilla Iskander-K cruise round 219: path 200, `Seeker` 0, `SeekerAngle` 0, `MaxSeekerDistance` 0, `CanReaquire` false, `LaserGuided` false, `TargetType` 1 (ground position only); speed, burn and turn equal the old HJ-10 values. The launchers stay `Type` 82 (cruise). They fire only on Fire Position orders, fly to the spot and dive. No laser homing: no vanilla cruise round is laser guided. The 17:4x Iskander-M (ballistic, laser) version shipped only in 0.9.7-dev.2/dev.3. Script: `tools/pla-specs/nlos_cruise_1124.py`.
> - **Laser = vanilla (Osama 21:4x "is that how lasers work in vanilla?"):** in the game, a laser-guided round looks for allied laser spots (`LaserDesignatorSystem.LaserSpots`) inside its own seeker cone (`LaserSeekerActivationSystem.InternalUpdate`, 1.2.2.1 `0x822980`): half-angle `SeekerAngle` × 0.5, reach `MaxSeekerDistance` (or `GroundRange` when `Seeker` ≠ 0), then `ActivateLaserSeeker` locks it on the spot. The Iskander-K copy set the cone to 0/0, so the rounds were blind to lasers. Each round now keeps its own cone (HJ-10 90°/800, QN-502 and CH-901 90°/700, CTL-181 90°/900) with `LaserGuided` on. No mod code is involved; the 21:3x laser_hold and custom-lock code were removed. Not yet seen in game.
> - **Turn rate (Osama 21:5x "can we increase missile agility? it seems to lock but it doesn't follow"):** `RotationSpeed` 45 → 120 °/s on all five rounds, the vanilla Hellfire (164) value. At 45 °/s a 300 u/s round turns on a ~380 u radius, and the laser lock in his 21:46-21:53 log came at 389-623 u. Not yet seen in game.
> - `nlos.json` lists no rounds, so `NlosTrait.cs` installs no hooks. The rest of this page describes 0.9.5-0.9.6 and is kept as history.
> - Not seen in game yet.

**Short answer.** NLOS needs two things. The data makes the missile fly a cruise path from a vertical launcher. The runtime hook `mod/source/runtime-qa/NlosTrait.cs` does the rest, driven by `UserData/FreedomArrow/nlos.json`. It lets the launcher fire at enemies that a friendly unit has spotted, with no line of sight of its own. It also keeps the missile locked on the target after the launcher loses sight of it. Data alone cannot do this: the game drops the lock when the missile has no line of sight.

- Read from: Freedom Arrow 0.9.5 (`gameplay/0.9.5`, `2f71d133`), Broken Arrow 1.2.2.1.
- A standalone copy of this code (a sample MelonLoader mod with stubs) and the full unit rows were prepared for focolate on 23 Nov 2026 (Osama's request): `work/nlos-for-focolate-20261123` on the deck.

---

## 🎯 Part 1: the data (what makes it a cruise missile)

These are the HJ-10 NLOS rows in 0.9.5. The CTL-181 and QN-502 use the same pattern.

**Launcher (`Weapons` row 2009619)**
- `Type` **82** (CruiseMissile). Not 80 (ATGM) or 81 (ATGMHE).
- `IsVerticalLauncher` **true**.
- `LowerVerticalAngle` -85, `UpperVerticalAngles` 30.
- `ShortGroundAttackBurst` 1, `NormalGroundAttackBurst` 2, `LongGroundAttackBurst` 2. These allow fire-position orders.
- `MagazineSize` 8, `AimTimeMin`/`Max` 1.0.

**Round (`Ammunitions` row 2009623)**
- `TrajectoryType` **200** (cruise path). It climbs, flies toward the target, then dives.
- `Seeker` 100, `SeekerAngle` 90, `MaxSeekerDistance` 800, `CanReaquire` true.
- `LaserGuided` **true**. With this, the missile follows a laser spot from a friendly designator.
- `GroundRange` 1000 (the unit card shows 2000 m), `MinimalRange` 100.
- `MuzzleVelocity` 50, `Acceleration` 50, `MaxSpeed` 300, `BurnTime` 20, `MainEngineIgnitionDelay` 1.0, `RotationSpeed` 45, `LaunchMarginAngle` 180.
- `TargetType` 37. That is the vanilla Javelin mask 36 plus bit 1 (fire at a ground position).
- `CanBeIntercepted` false.
- Damage: `Damage` 11, penetration 140, `IsTopArmorArmorAttack` true, `HealthAOERadius` 25, `OverpressureRadius` 5.

**Unit (`Units` row 936)**: an M6 Linebacker body, `Cost` 140. The weapon package has two options:
- "HJ-10 FNF" (default): a plain vanilla Javelin clone. It does not use the NLOS code.
- "HJ-10 NLOS (laser, 2000 m)", +20: the turret with the launcher above.

The NLOS code works only while the NLOS round is the selected round.

---

## 🧠 Part 2: the code (`NlosTrait.cs`)

Everything is driven by `nlos.json`:

- `fire_units` and `fire_weapons`: units with these launchers can shoot without their own line of sight.
- `ammunition`: rounds whose lock the code keeps.

### A. Firing without line of sight

- **Hook:** postfix on `FogOfWarWorker.IFogOfWarWorker.Update`. This runs once for each fog worker each frame.
- The game rebuilds each unit's `FogOfWarComponent.Shootable` list from that unit's own line of sight. After that, the hook adds enemies to the list of each NLOS unit. An enemy is added only when all of these are true:
  - any unit on the shooter's side sees it (the target's `FogOfWarComponent.VisibleTo`);
  - it is within `BattleSystemHelpers.GetAmmoShootingDistance` for the selected round;
  - the selected round is in `ammunition`;
  - the target's unit type is in the round's `TargetType` mask.
- The target list is cached for 0.5 s for each unit.

### B. Keeping the missile locked

- **`SeekerSystem.InternalUpdate` prefix:** finds the missile's target. It tries, in this order: the seeker target, then `OriginalTarget`, then the launcher's own target, then the unit nearest the laser spot (within 60). Each frame it then:
  - puts the target back if the seeker lost it (`MissilesHelper.SetNewTargetToMissile`, at most 20 times per missile);
  - sets `HasLOSOnCurrentTarget` and `HasVisionOnCurrentTarget` to true;
  - sets `LastTargetPosition` to the target's current position. Because of this, the missile follows a moving target even with no laser.
- **`SeekerSystem.DropCurrentTarget` prefix:** cancels drops for these reasons: no line of sight, not visible, too far, beyond seeker angle, shooter has no target, no laser spot (reason codes 5, 6, 7, 25, 26, 28). Any other reason, or a dead target, gives the missile back to the game.
- **Player re-guiding:** if the seeker switches to a different live target, the code keeps the new target.
- **Fire at a point with no unit there (`spotOnly`):** the code sets `LaunchHorizontalDistance` to the distance to the spot. After each seeker update it holds line of sight and vision off. It also keeps the missile on path 200 with seeker type 0. The missile then dives on the spot.

---

## ⚠️ Problems we found (this is why the code looks like this)

1. **A cruise round from a Type 81 launcher never fires.** In 0.9.4 the HJ-10 tried to fire 886 times and launched no missile. Use `Type` 82 with `IsVerticalLauncher` true.
2. **The cruise path needs `LaunchHorizontalDistance`.** The game sets it at launch from a unit target. A missile fired at a laser spot or at the ground has 0, and with 0 it flies level or climbs and never dives. The code sets it.
3. **`LaserGuided` true + cruise path.** About 3 s after launch, the game switches a laser-guided round to path 600 (laser missile) with seeker 300 (laser). With no target unit, it then flies straight and climbs. The code switches an empty-spot round back to path 200 with seeker 0. Locked rounds that switch still hit, so the code does not change them. No vanilla round uses path 200 with `LaserGuided` true.
4. **`Shootable` belongs to the whole unit, not one weapon.** Without the `TargetType` filter, every other weapon on the unit could also shoot without line of sight. In 0.9.5-dev.15 the QN-506's QN-201 and its guns did this.
5. **Do not put back a target that the game dropped for an allowed reason.** In 0.9.4 the old target was restored every frame and then dropped again, and the missiles flew erratically.
6. **Hook the fog worker, not `FogOfWarUnit.Update`.** That method ran about 7,500 times a second in a 5v5.
7. **Patch only methods that take `Entity`, `bool` or enum parameters.** A Harmony patch on a method with a `ref` to a non-blittable struct (`SetMissileDead(ref SeekerComponent)`) crashed the game natively.
8. **`Seeker` 100 in the ammo table is not the runtime `SeekerComponent.Type`.** On these rounds the runtime type was already 0.

---

## ✅ What we have seen in game

- **Laser spot on a vehicle:** player logs show the lock and hits. CTL-181: 11/11 in 0.9.5-dev.7 and 7/7 in dev.9. HJ-10: 8/8 in dev.32.
- **Fire at empty ground:** the hold in point 3 came in 0.9.5-dev.45, which is the same NLOS code as live 0.9.5. In Osama's dev.45 test log (22 Nov, 23:27–23:30 PST), all 22 missiles came down. The 8 fired with Fire Position at empty ground landed within 90 world units of the spot. The 14 fired at lased units landed within 75 of the target.
- **Not measured:** the frame-time cost of the fire hook in a full 5v5.

The CTL-181 (unit 1054, launcher 2018322, round 2018321) and QN-502 (unit 937, launcher 2009647, round 2009651) follow the same pattern. Their rounds use the same flight values. The QN-502 round has `TargetType` 1, so it fires only at ground positions and the laser spot.

## Document change log

- 2026-11-23 04:3x PST (America/Los_Angeles): first version, from 0.9.5 code and data and the 0.9.4-0.9.5 NLOS bug history.
- 2026-11-24 17:3x PST (America/Los_Angeles): 0.9.7 change at the top: NLOS rounds use vanilla cruise guidance and the NLOS code is off.
- 2026-11-24 17:5x PST (America/Los_Angeles): option A: Iskander-M guidance with optional laser and Type 83 launchers instead of Iskander-K cruise.
- 2026-11-24 21:3x PST (America/Los_Angeles): back to Iskander-K cruise guidance (Type 82 launchers, no laser) at Osama's correction; Iskander-M was dev.2/dev.3 only.
- 2026-11-24 21:4x PST (America/Los_Angeles): laser following on the cruise rounds (LaserGuided + laser_hold postfix).
- 2026-11-24 21:5x PST (America/Los_Angeles): laser following = vanilla seeker cone (LaserSeekerActivationSystem); custom laser code removed.
