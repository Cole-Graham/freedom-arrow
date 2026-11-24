# Range of ground air defence against missiles (SEAD, cruise, ballistic)

**Short answer:** it depends on the missile, not on the SAM. When a missile is made targetable, the game gives it a fixed altitude level: SEAD and ordinary guided missiles are **Low**, ballistic missiles are **High**, and cruise missiles are **Low** unless the last digit of their `LoftHeight` is 5 or more (then **High**). A SAM's range against that missile is its `LowAltRange` or `HighAltRange` for that level (each falls back to `GroundRange` if 0), times the radar modifier for that level when its radar is on, times the anti-missile factor (`NonSeadProjectileRangeOverride` / `SeadProjectileRangeOverride`, else the BattleSystemSettings multiplier). The radar modifier is applied twice in that path; the target search radius applies it once, which likely caps the result (calculated, not measured).

*Details (read from GameAssembly 1.2.2.1 with the il2cpp dump; not measured in a game):*

## 1. The missile's altitude level

`ProjectileSpawnerHelper.MakeShellTargetable` (RVA `0x7DEB60`) builds a unit for an interceptable missile (unit `HealthComponent` 1.0 HP, `FogOfWarComponent`, `ShootPriorityComponent`, `CounterMeasuresComponent`) and sets `AltitudeComponent.GlobalAltitudeLevel` (`0x18`) once. From the round (`Ammunitions`):

| Round | Unit type set (`Units.Type`, `0x7C`) | GlobalAltitudeLevel |
| --- | --- | --- |
| `TrajectoryType` 300 (ballistic) | `BallisticMissile` 1024 | **High** (2) |
| `TrajectoryType` 200 (cruise) | `CruiseMissile` 512 | **High** if `LoftHeight % 10 >= 5`, else **Low** |
| other, `Seeker` 200 (anti-radiation) | `SEADMissile` 256 | **Low** (1) |
| other | unchanged (projectile) | **Low** (1) |

`AltitudeSystem.UpdateAltitudeLevel` only updates helicopters and planes, so a missile keeps this level for its whole flight, at any real height.

0.9.6 cruise rounds that are **High** (`LoftHeight` 2506): AGM-183A ARRW, Kh-47M2 Kinzhal, MAKO, YJ-21. All other cruise rounds (Tomahawk class, AGM-84, JASSM, Kh-101, CJ-10, Kh-32 with 1994, …) are **Low**.

## 2. Range against a target

`BattleSystemHelpers.GetAmmoShootingDistance(shooter, target, ammo)` (RVA `0x7D6330`):

```text
if target has <component at the first check>:   return LowAltRange     (earlier decode: airdrop)
base by target GlobalAltitudeLevel:
  Ground: GroundRange
  Low:    (LowAltRange  or GroundRange) × m      m = shooter radar RadarLowAltWeaponRangeModifier (radar on), else 1
  High:   (HighAltRange or GroundRange) × m      m = RadarHighAltWeaponRangeModifier (radar on), else 1
if target Units.Type & 0x780 (projectile / SEAD / cruise / ballistic):
  v = target is SEAD (seeker 200) ? ammo.SeadProjectileRangeOverride : ammo.NonSeadProjectileRangeOverride
  if v == 0: v = BattleSystemSettings.RANGE_MULTIPLIER_AGAINST_SEAD_PROJECTILES / _NON_SEAD_PROJECTILES
  range = v >= 100 ? v × m          (absolute range)
                   : v × base × m   (multiplier; base already holds m, so m is applied twice)
```

Callers include the target evaluation, shell selection, missile spawn and `IsKinematicallyAbleToInterceptTarget` (RVA `0x7D8DA0`, which calls it after `GetPredictedShootParametersToTarget`).

**Data in 0.9.6:** no round sets `NonSeadProjectileRangeOverride`. Two rounds set `SeadProjectileRangeOverride` = 1100 (an absolute range against SEAD missiles): vanilla ammo 465 `Missile AA AIM9 Ground` (SLAMRAAM 389, MML 393, NASAMS 508; FA does not change it) and FA ammo 2019358 `PLA HHQ-10 missile` (HHQ-10 1273, copied from 465). Every other round uses the settings multipliers 1.0 / 1.0 (13 Nov decode of BattleSystemSettings), so `range = base × m` = level range × m². Read from the released `FreedomArrow-0.9.6.bamod` (sha256 `98e0e962…`) merged over the 10 Nov vanilla tables.

## 3. The search radius

`GetAmmoMaxShootingDistance(shooter, ammo)` (RVA `0x7D60C0`) returns the largest of `GroundRange`, max(`LowAltRange × mLow`, `HighAltRange × mHigh`) and the anti-missile values built from that air maximum. With factor 1.0 that is max(Ground, Low × mLow, High × mHigh): the radar modifier once. If, as in the earlier decode, the target search uses this radius, the effective anti-missile range is min(level range × m², search radius) (calculated).

## 4. Worked examples (0.9.6 data, radar on, calculated)

- Long-range radar row 59 (Patriot, S-400, Buk, HQ-9, HQ-16, IRIS-T SLM): m = 2.0 low, 3.0 high. PAC-3 (Low/High 975): ballistic (High) 975 × 9 = 8775, search radius 2925 → about **2925** (5850 card m); SEAD or Low cruise 975 × 4 = 3900 → about **2925**. Radar off: 975 either way.
- SHORAD radar row 60 (Pantsir, Tor, FK-2000, HQ-17): m = 1.25 low, 1.0 high. Tor 9M331 (Low 1100, High 675): SEAD / Low cruise 1100 × 1.5625 = 1719, search 1375 → about **1375**; ballistic / Kinzhal / ARRW (High) **675**.
- AIM-9 ground round (ammo 465 / HHQ-10 2019358, Low 1050, High 775, SEAD override 1100) on SHORAD radar row 58/60 (m = 1.25 low): SEAD missile 1100 × 1.25 = 1375, search radius 1050 × 1.25 = 1312.5 → about **1312** (2625 card m); radar off 1100, search 1050 → about **1050**. Without the override it would be 1050 × 1.5625 = 1641, also cut to 1312, so the override changes little if the search radius applies. Cruise and ballistic missiles use the normal 1.0 path.
- Which missile types a SAM may shoot at all is its round's `TargetType` bits: 256 SEAD, 512 cruise, 1024 ballistic (`IsAntiProjectileSAM`, RVA `0x7D8920`).

## 5. Not verified

- Which component the first check in `GetAmmoShootingDistance` reads (airdrop in the earlier decode) and the name of the component compared with 200 for SEAD (read as the missile's seeker type).
- That the target search uses `GetAmmoMaxShootingDistance` in 1.2.2.1 (read in the earlier version).
- The BattleSystemSettings multipliers are from the 13 Nov decode (pre-1.2.2.1).
- Nothing here has been measured in a match.

## Document change log

- 2026-11-24 14:4x PST (America/Los_Angeles) — New: missile altitude levels, the anti-missile range formula and the search radius (Lateralus asked whether High or Low range is used).
- 2026-11-24 15:0x PST (America/Los_Angeles) — Corrected: two rounds do set `SeadProjectileRangeOverride` (1100: vanilla AIM-9 ground on SLAMRAAM/MML/NASAMS, FA HHQ-10); added their worked example (Lateralus asked for a unit with a factor other than 1.0).
