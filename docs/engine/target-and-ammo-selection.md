# Target and ammunition selection

A weapon picks its target and its round in the same pass. For every target in range it finds the best round, scores that round against the target, and keeps the target with the highest score above 0. There is no minimum damage. A round that does any damage above 0 makes the target valid. Only the score comparison and the overkill check keep a weapon off a target that it can barely hurt.

The methods are in `TargetSearchHelper`, `BattleSystemHelpers` and `OverkillScoringSystem`. The addresses below are for game build 1.2.2.1. The code of each method is identical, instruction for instruction, to the earlier build that the 6000.3.24f1 dump describes. Only the addresses moved, by −0x680.

| Method | 1.2.2.1 RVA |
| --- | ---: |
| `TargetSearchHelper.GetSearchParameters` | `0x7E1710` |
| `TargetSearchHelper.TryAddTargetToCheckList` | `0x7E4D30` |
| `TargetSearchHelper.EvaluateTargets` | `0x7E0DF0` |
| `TargetSearchHelper.SelectTarget` | `0x7E4590` |
| `TargetSearchHelper.<SelectTarget>g__EvaluateTarget` | `0x7E5C60` |
| `BattleSystemHelpers.SelectBestShellForTarget` (with armor side) | `0x7DBCC0` |
| `BattleSystemHelpers.SelectBestShellForTarget` (side from geometry) | `0x7DC550` |
| `OverkillScoringSystem.CalculateWeaponOverkillScore` | `0x7F5C50` |
| `OverkillScoringSystem.CalculateOverkillScore` | `0x7F5850` |
| `OverkillScoringSystem.IsTargetOverkilled` | `0x7F78E0` |
| `AttackCommand.HasValidTargetAmmo` | `0x76A360` |

The settings come from the `BattleSystemSettings` asset. Both copies of the asset in the game files have the same values for these fields:

| Setting | Value | Used in |
| --- | ---: | --- |
| `MINIMAL_CHANCE_TO_KILL` | 0.8 | overkill check |
| `HP_LIMIT_WEAPON_SCORE` | true | score capped at the target's remaining health |
| `PRIORITIZE_ONE_SHOT_TARGETS` | true | finishing bonus |
| `PREVENT_GUIDED_OVERKILL` | true | guided rounds skip targets that other weapons already kill |
| `GUIDED_SELECTION_DAMAGE_TRESHHOLD` | 1.4 | guided against unguided round |
| `APS_GUIDED_SELECTION_DAMAGE_TRESHHOLD` | 5 | the same, against a target with active APS |
| `SEAD_SCORE_MULTIPLIER` | 0.99 | anti-radiation rounds |
| `PLANES_DAMAGE_SCORE_MULTIPLIER` | 1 | plane targets |

## 1. Search: who is a candidate

`GetSearchParameters` builds the weapon's search from the rounds it has loaded:

- The target mask is the OR of every loaded round's `TargetType`.
- The minimum range is the smallest `MinimalRange`.
- The maximum range is the largest `GetAmmoMaxShootingDistance`.

`TryAddTargetToCheckList` then removes a unit from the candidates when one of these is true:

- It is dead, or it is a supply object.
- Its type is not in the weapon's target mask. A Recon-category unit of type 16 (aircraft) whose fly preset has `LowAltitudeIsDefault` is tested as type 8 (helicopter). `SelectBestShellForTarget` uses the same rule.
- It is outside the squared minimum or maximum search range, or outside the search zone.
- It is a projectile (missile, cruise or ballistic missile, SEAD missile) and the shooter has no radar, or its radar is off. A ballistic missile is also refused outside the interception part of its flight.
- The shooter guides missiles and cannot guide another one onto it.
- No loaded round can reach it. The loop checks each round's `TargetType` against the target and its range against the distance.

This step does not look at damage. An M1A1 HC is a candidate for every weapon whose mask includes vehicles (bit 4) and that has range to it.

## 2. Round: which shell for this target

`EvaluateTargets` works through the candidates. First it gets the armor face from geometry (`GetArmorSideFromShotVector`, the same face test as in [Overpressure](overpressure.md#the-other-roof-path)). Then it calls `SelectBestShellForTarget` with that face.

For each round in the weapon's list, `SelectBestShellForTarget` skips the round when one of these is true:

- The round is disabled.
- It has no ammunition left and none is reserved in the magazine. A call can ignore this test.
- Its `TargetType` does not include the target's type.
- Its `Seeker` is 200 (anti-radiation) and the target has no active radar.
- The distance is under `MinimalRange` or over `GetAmmoShootingDistance` for that target. This is the range for ground, low altitude or high altitude.

Each round that is left gets a score:

```text
penetration = GetPenetrationForAmmunition(round, distance)
topAttack   = DoesAmmunitionUseTopArmorAttack(round, distance, range)
hitDamage   = CalculateHitDamage(target, round.Damage, round, penetration, topAttack, face)
score       = GetTargetAccuracy(round, target, distance) × hitDamage
```

A round with a score of exactly 0 is dropped. Guided rounds (`Seeker` > 0) and unguided rounds are ranked separately. If only one group has a round, that round wins. If both do, the guided round wins only when:

```text
bestGuided / bestUnguided ≥ 1.4      (5 against a target with an active APS)
```

The result also carries two flags:

- **Overkilled:** for a target that is not the unit's priority target, the result of `IsTargetOverkilled`.
- **Guided on a non-priority overkilled target:** set when `PREVENT_GUIDED_OVERKILL` is on, the target is not the priority target and it is overkilled.

If no round is left, the shell ID is −1.

Overpressure has no part in this score. The face is the geometric one, or Top only when the round itself has top attack. A round with `OverpressureRadius` above 0 still forces the roof when it hits a vehicle directly (see [Overpressure](overpressure.md#the-unit-the-shell-strikes)), but the selection does not expect that.

## 3. Score: how much the target is worth

`EvaluateTargets` removes a candidate when one of these is true:

| Reason (game debug text) | Test |
| --- | --- |
| "Can't select good shell for target" | shell ID < 0 |
| "Guided on non-priority overkilled" | that flag is set, and the target is not a SEAD missile aimed at this unit |
| "Can't kinematically hit the target" | `IsKinematicallyAbleToInterceptTarget` is false and the weapon does not guide missiles |
| "Non-positive overkill score" | own score ≤ 0 |

For each candidate that stays, the method also stores:

- **TimeToHit:** the turret rotation and aiming time (`CalculateWeaponRotationAndAimingTime`) plus the projectile time from `IsKinematicallyAbleToInterceptTarget`.
- **CanAim:** whether the target is inside the weapon's angles and a shot can be calculated.

The face for the score is Top when `DoesAmmunitionUseTopArmorAttack` or `IsTopAttackForcedByShooter` is true. Otherwise it is the geometric face. `CalculateWeaponOverkillScore` then works out:

```text
penetration = KE round:  GetPenetrationForAmmunition(round, distance + 10)
              otherwise: round.PenetrationAtGroundRange
hitDamage   = CalculateHitDamage(target, round.Damage, round, penetration, face == Top, face)
multiplier  = (Seeker 200 ? 0.99 : 1) × (target CategoryType 6, Aircrafts ? 1 : 1)
```

`CalculateOverkillScore` turns the damage into a value. `cost` is the target unit's `Cost`. `hp` and `maxHp` come from its health:

```text
finishing = maxHp / hp        when PRIORITIZE_ONE_SHOT_TARGETS and hitDamage > hp
          = 1                 otherwise
score     = min(cost × hp, cost × hitDamage × multiplier)     (HP_LIMIT_WEAPON_SCORE on)
ownScore  = finishing × score
```

Hit chance does not enter this score. It is returned beside the score as a separate value. Guided rounds replace it with the missile hit chance against the target's countermeasures.

After the removal test, `EvaluateTargets` changes the score:

```text
ownScore = ownScore − TimeToHit
ownScore += 500000     SEAD missile (type 256)
ownScore += 500000     again when that SEAD missile is aimed at this unit; its overkill flags are cleared
ownScore += 400000     other projectile types (128, 512, 1024)
```

## 4. Pick: which target wins

`SelectTarget` and its local function `EvaluateTarget` keep two best targets: one inside the weapon's angles and one outside them. Both start at a score of 0, and a target must beat that with a strict `>`. A target that the weapon cannot aim at is kept as the out-of-angles choice, so that the hull or turret can turn to it.

The first pass skips a target when one of these is true:

- Its shell ID ≤ 0.
- It cannot be hit kinematically.
- It is overkilled by other weapons.
- `PREVENT_GUIDED_OVERKILL` is on and its guided-overkill flag is set.
- The call has a current target level other than None, and the target is neither a priority target nor a projectile.

The first pass also removes the targets that cannot be hit kinematically. When it finds nothing, a second pass runs over the targets that are left, without the overkill skip. A weapon with nothing better to do therefore still fires at a target that other weapons already cover.

`IsTargetOverkilled` calls `GetCurrentScoreOnTarget`, which adds up the other weapons already on the target. It is true when both of these are true:

- The second returned value, the chance that those weapons kill the target, is 0.8 (`MINIMAL_CHANCE_TO_KILL`) or more.
- The first returned value, their combined score, is at least the target's current health times a factor stored on the target's `ShootPriorityComponent`.

## Overrides

- **Priority target (a player attack order):** when the last candidate in the list is the priority target, `SelectTarget` returns it at once, with no score comparison. `SelectBestShellForTarget` does not run the overkill check for it. It must still survive step 3, so it needs a round that does more than 0 damage.
- **Player attack order, validity:** `AttackCommand.HasValidTargetAmmo` accepts an order when any loaded round can target the unit type, has ammunition and is not anti-radiation. For a KE round it also checks that `DamageFormulaKinetic(Damage, PenetrationAtMinRange, target's lowest KE armor)` is above 0. It does not run a damage test for HE or HEAT rounds.
- **Current target is a priority target:** with target level Priority, `SelectTarget` returns no target from the list.
- **Missiles and projectiles:** the +400000 and +500000 bonuses put any projectile ahead of every ground target.
- **Finishing shots:** a hit that would kill the target multiplies its score by `maxHp / hp`.

## Example: JRVG-1 against an M1A1 HC from the front

0.9 dev.45 data, after its overpressure goes to 0. JRVG-1 (unit 952) has two rounds on one gun:

| Round | Ammo | TargetType | Damage | Penetration | Kind |
| --- | ---: | ---: | ---: | --- | --- |
| 76 mm AP | 2009951 | 36 (vehicle, ship) | 2.9 | 180 at 0, 120 at ground range | KE |
| 76 mm HE (proximity) | 2009953 | 63 (all ground and air) | 8 | 60 | HE |

M1A1 HC (unit 53, `Cost` 160, 14 HP): front KE 650, front HEAT 750, sides KE 120 and HEAT 200.

**Round choice from the front.** The AP round has penetration/armor = 180/650 = 0.28, below 0.5, so the KE formula gives 0 and the round is dropped. The HE round gives:

```text
8 × 60² / (60² + 750²) = 0.0509
```

That is above 0, so HE is the selected round.

**Score.**

```text
min(160 × 14, 160 × 0.0509) = 8.14
ownScore = 8.14 − TimeToHit
```

The weapon's aim time is 1.0 s. With a full turret turn at 360° per second and a 700-unit shot at 640 units per second, `TimeToHit` is at most about 2.6 s. That gives a final score of about 5.5, which is above 0. **The JRVG-1 does attack an M1A1 HC from the front when that tank is its best candidate.** The time figure is an estimate and has not been measured in a game.

**Break-even.** The tank stays a valid target while `160 × hitDamage > TimeToHit`. At 2.6 s, that needs more than 0.016 damage per hit. HE at 60 penetration gives 0.0237 against front HEAT 1100 and 0.0200 against the 1200 cap. A 1200-front tank needs a `Cost` of about 130 or more to stay valid, so every main battle tank front in the current data stays a target.

**What it costs the JRVG-1.** At 0.0509 per hit, 14 HP takes about 275 hits. The JRVG-1 carries 128 HE rounds. Its full load does about 6.5 HP to an M1A1 HC front.

**From the side.** The AP round gets 120 to 180 penetration against KE 120, so it does its full 2.9. HE gives `8 × 60² / (60² + 200²) = 0.66`. The AP round has the higher score and is the selected round.

**When anything else is in range,** the tank loses on score. One infantry squad, or any light vehicle that the HE round damages fully, is worth `cost × min(hp, damage)`, many times 8. The tank is picked only when it is the best candidate left, or when the player orders the attack.

Before dev.45, the same scoring applied. Selection did not know that the HE round would hit the roof, so it chose tanks as described above. Overpressure then turned each direct hit into `8 × 60² / (60² + 100²) = 2.12` health.
