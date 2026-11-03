# Tank-Mounted Guns (09_tank_guns.yml) — Real-World Effective Ranges

## Research Summary: Individual Tank Gun Systems
All values represent **effective combat engagement range** in meters, based on practical combat doctrine and conservative estimates where sources diverged.

---

## SOVIET/RUSSIAN TANK GUNS

### 76mm Gun Systems (2 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 224 | D56TS HE | 76mm | 1500 m | Soviet 76mm (older T-34/T-44 series): ~1500m effective range (limited penetration vs modern armor) |
| 223 | D56TS HEAT | 76mm | 1500 m | D56TS HEAT variant: 1500m effective (same platform, chemical energy independent of distance) |

### 100mm Gun Systems (4 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 7 | 2A70 HE | 100mm | 2000 m | T-55AM2: 2A70 smoothbore, ~2000m effective (D-10 successor) |
| 500 | MT12 HE | 100mm | 2000 m | Recoilless gun 100mm: 2000m effective range |
| 499 | MT12 HEAT | 100mm | 2000 m | MT12 HEAT: 2000m effective (chemical warhead) |
| 501 | 2A70 AP | 100mm | 2000 m | 2A70 AP round: 2000m effective armor penetration range |

### 125mm Gun Systems (26 entries)

| Entry ID | Range | Research Notes |
|----------|-------|-----------------|
| 11, 238, 246, 124, 264, 239, 242, 139, 141, 48, 248 | 3000 m | 2A46/2A46M/2A46M1/2A46M5: T-72/T-80/T-90 smoothbore cannons, **3000m effective range** for kinetic and HEAT rounds (guided projectiles reach to 4000m but conservative estimate used) |
| 249, 247, 140, 243, 136, 137, 138, 142, 244, 37, 251 | 3000 m | 2A75/2A82/2A82-1M variants: Modern 125mm smoothbore, maintained 3000m effective (longer than predecessors but conservative doctrine range) |

---

## WESTERN TANK GUNS

### 105mm Gun Systems (7 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 505 | XM35 AP | 105mm | 1500 m | M68 / L7 NATO 105mm rifled gun: **1500m maximum doctrine effective range** (fire control accuracy limits beyond this) |
| 57 | M102 (AC-130) | 105mm | 1500 m | M102 airborne 105mm: 1500m effective (same ballistics as M68) |
| 24 | M68 HESH | 105mm | 1500 m | M68 HESH variant: 1500m effective (chemical warhead, accuracy-limited) |
| 253 | L7A1 APDS | 105mm | 1500 m | L7 APDS: 1500m effective (British variant) |
| 254 | L7A1 HE | 105mm | 1500 m | L7 HE: 1500m effective |
| 255 | M68 APDS | 105mm | 1500 m | M68 APDS: 1500m effective |
| 256 | M68 HE | 105mm | 1500 m | M68 HE: 1500m effective |

### 120mm Gun Systems (19 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 576-602 | Rh-120 (Leopard 2, Abrams) | 120mm | 2500 m | **Rh-120 NATO smoothbore standard**: 2500m practical effective range (fire control systems max at 3000m, conservative estimate) |
| | Leo2A8, M1A2, M1A3 | 120mm | 2500 m | All modern 120mm NATO variants: 2500m effective (DM53, M829A4 APFSDS rounds) |

### 165mm/152mm Gun Systems (1 entry)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 493 | M81E1 HESH | 165mm | 1500 m | M551 Sheridan 152mm gun (designated as 165mm in database): **2000m effective HESH range** (HE blast effect, limited armor penetration) |

---

## NOTES ON DATA

1. **Conservative Effective Range Approach**: Used practical combat doctrine maximums, not theoretical maximums
   - Example: 120mm NATO fire control max is 3000m; used 2500m for practical sustained fire
   - Example: 125mm guided projectiles reach 4000m; used 3000m for standard rounds
   - Example: 105mm rifled gun doctrine is 1500m max accuracy; applied conservatively

2. **Platform Variants**: Same gun maintains consistent effective range across platforms
   - 125mm 2A46/2A46M variants: all 3000m (T-72, T-80, T-90, PT-91, M-84)
   - Rh-120: all 2500m (Leopard 2A4-A8, M1 Abrams, M1A1-A3)
   - M68/L7: all 1500m (M48, M60, early M1)

3. **Generational Progression**: Later systems show improved effective ranges
   - 76mm: 1500m (older)
   - 100mm: 2000m (mid-gen)
   - 105mm: 1500m (limited by rifled design/fire control)
   - 120mm/125mm: 2500-3000m (modern smoothbore with advanced FCS)

4. **Ammunition Type Impact**: Chemical energy (HEAT/HESH) less range-dependent than kinetic
   - HEAT/HESH rounds: effective to stated range regardless of distance
   - AP/APFSDS rounds: penetration degrades with range, effective to conservative estimate
   - HE rounds: blast effect primary concern, effective range lower

5. **Guidance System Notes**:
   - APFSDS kinetic rounds: line-of-sight unguided (range-limited by fire control)
   - HEAT/HESH: shaped charge warhead (independent of kinetic energy)
   - Gun-launched guided projectiles: extended range (5km+, but not in this category)

---

## FILL COMMAND READY

Each entry needs one ground value per system (ground domain only; low_alt and high_alt remain at current values).

**Total corrections: 59 entries**
- 76mm systems: 1500m
- 100mm systems: 2000m
- 105mm systems: 1500m
- 120mm systems: 2500m
- 125mm systems: 3000m
- 165mm systems: 2000m
- Format: Integer meters (e.g., "3000", "2500", "1500")
