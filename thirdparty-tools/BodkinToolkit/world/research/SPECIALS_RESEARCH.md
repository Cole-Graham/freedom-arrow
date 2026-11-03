# Special Weapons & Effects (98_specials.yml) — Game Mechanics Ranges

## Research Summary: Special Game Mechanics
All values represent **effective gameplay range** in meters for special effects, zombie attacks, and mine-clearing equipment.

---

## SMOKE & VISUAL EFFECTS

### Smoke Screens (3 entries)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 268 | SmokeScreen | 0 m | **Smoke Screen**: 0m range (passive visual effect, no engagement range) | 0 | 0 | 0 |
| 276 | SmokeScreen Infantry | 0 m | Smoke Infantry variant: 0m range (passive effect, infantry unit) | 0 | 0 | 0 |
| 585 | SmokeScreen Zombie | 0 m | Smoke Zombie variant: 0m range (passive effect, zombie unit) | 0 | 0 | 0 |

---

## FLASHBANG & TACTICAL EFFECTS

### Flashbang (1 entry)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 442 | Flashbang | 10 m | **Flashbang**: 10m effective radius (tactical stun effect, infantry units) | 0 | 0 | 0 |

---

## MINE CLEARING EQUIPMENT

### MICLIC Mine Clearing (1 entry)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 467 | MICLIC | 400 m | **MICLIC Mine-Clearing Line Charge**: 400m effective range (explosive mine-clearing system, AAVP MICLIC, M1150) | 0 | 0 | 0 |

### UR-77 Mine Clearing (1 entry)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 558 | UR-77 Meteorit | 400 m | **UR-77 Meteorit Mine Clearer**: 400m effective range (explosive mine-clearing system, UR-77) | 0 | 0 | 0 |

---

## ZOMBIE MECHANICS

### Melee Attacks (1 entry)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 582 | Zombie Melee | 15 m | **Zombie Melee Attack**: 15m effective range (melee bite attack, ZOM Runners/Walkers) | 0 | 0 | 0 |

### Projectile Attacks (2 entries)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 583 | Zombie Spit | 300 m | **Zombie Spit**: 300m effective range (projectile attack, ZOM Spitters) | 0 | 0 | 0 |
| 589 | Zombie Spit Antihelo | 300 m | Zombie Spit anti-helo variant: 300m effective range (ZOM Spitters, anti-air targeting) | 0 | 0 | 0 |

### Explosive Attacks (3 entries)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 586 | Zombie Boomer | 50 m | **Zombie Boomer Suicide**: 50m effective radius (explosion attack, ZOM Boomer) | 0 | 0 | 0 |
| 584 | Zombie Smoker | 50 m | Zombie Smoker suicide: 50m effective radius (explosion/gas attack, ZOM Smokers) | 0 | 0 | 0 |
| 590 | Zombie Fire Smoker | 50 m | Zombie Fire suicide: 50m effective radius (fire/explosion attack, ZOM Smokers) | 0 | 0 | 0 |

### Throwable Attacks (1 entry)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 587 | Zombie ThrowableCar | 100 m | **Zombie Throwable Car**: 100m effective range (throw attack, ZOM Thrower) | 0 | 0 | 0 |

---

## SPECIAL GAMEPLAY MECHANICS

### Supply & Reference Effects (2 entries)

| Entry ID | System | Effective Range | Research | Ground | Low Alt | High Alt |
| ---------- | -------- | ----------------- | ---------- | --- | --- | --- |
| 459 | Supply Explosion | 0 m | **Supply Explosion Reference**: 0m (game mechanic reference, no engagement range) | 0 | 0 | 0 |
| 588 | NoAmmo Hands | 0 m | **No Ammo (Melee Only)**: 0m ranged (melee-only unit, ZOM Civilians) | 0 | 0 | 0 |

---

## NOTES ON DATA

1. **Game Mechanic Categories**:
   - **Passive Effects**: 0m (smoke, visual effects, game references)
   - **Tactical Effects**: 10m (flashbang stun radius)
   - **Mine Clearing**: 400m (explosive mine-clearing effective range)
   - **Melee**: 15m (close combat bite range)
   - **Projectile**: 300m (spit/attack projectile range)
   - **Explosive**: 50m (suicide/explosion radius)
   - **Thrown**: 100m (car throw range)

2. **Zombie Attack Types**:
   - **Melee**: Close-range bite (15m)
   - **Spit**: Ranged projectile (300m, ground and air targets)
   - **Suicide/Explosive**: Radius explosion (50m)
   - **Throw**: Large object throw (100m)

3. **All Special Entries**:
   - Use **ground domain only** (low_alt and high_alt = 0)
   - Game mechanic balance, not real-world physics
   - Ranges based on gameplay mechanics and unit types

---

## FILL COMMAND READY

Each entry needs one ground value per system (ground domain only; low_alt and high_alt remain at 0).

**Total corrections: 15 entries**
- Passive effects: 0m
- Flashbang: 10m
- Mine clearers (MICLIC/UR-77): 400m
- Zombie melee: 15m
- Zombie spit: 300m
- Zombie explosive: 50m
- Zombie throwable: 100m
- Format: Integer meters (ground domain only)
