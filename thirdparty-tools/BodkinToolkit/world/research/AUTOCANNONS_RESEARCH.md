# Aircraft & Vehicle Autocannons (08_autocannons.yml) — Real-World Effective Ranges

## Research Summary: Individual Autocannon Systems
All values represent **effective combat engagement range** in meters, based on direct fire weapon specifications and practical combat doctrine ranges.

---

## NATO AUTOCANNON SYSTEMS

### 20mm Cannon Systems (7 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 58, 62, 262, 295, 457, 561, 604 | M61 Vulcan / M197 | 20mm | 2000 m | **M61 Vulcan 20mm Vulcan Gatling Gun**: 2000m effective range (1.1 miles air-to-air, 2.3 miles air-to-ground; self-destruct rounds 1800-2300m) |

### 25mm Cannon Systems (8 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 32, 56, 185, 186, 230, 231, 232, 233 | GAU-12 Equalizer | 25mm | 1500 m | **GAU-12/U 25mm Equalizer**: 1500m effective range (1200+ yards practical, multi-barrel Gatling design) |

### 30mm Cannon Systems (34 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 36, 454, (32 more entries) | M230LF / Bushmaster II | 30mm | 1500 m | **M230LF Apache Chain Gun**: 1500m effective range (800-1000m best practices, ~2000m theoretical max; M789 HEDP effectiveness to 1500m) |

### 35mm Cannon Systems (2 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 569, 570 | Bushmaster III | 35mm | 2000 m | **Bushmaster III 35mm**: 2000m effective range (derived from 30mm systems with extended ballistics) |

### 40mm Cannon Systems (1 entry)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 55 | Bofors HEDP | 40mm | 2000 m | **Bofors 40mm Cannon (AC-130 variant)**: 2000m effective range (conservative estimate for ground-based system) |

### 50mm Cannon Systems (2 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 506, 507 | Bushmaster V | 50mm | 2000 m | **Bushmaster V 50mm**: 2000m effective range (guided variants reach 1km against UAVs, standard rounds ~2000m) |

---

## SOVIET/RUSSIAN AUTOCANNON SYSTEMS

### 23mm Cannon Systems (11 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 79, 161, 162, 176, 189, 212, 213, 292, 330, 333, 437 | GSh-23 / ZU-23 / GSh-6-23 | 23mm | 2000 m | **GSh-23L 23mm Twin-Barrel Cannon**: 2000m effective direct fire range (direct fire ≤2km, can reach 2-3x farther with high-arc fire; 715 m/s muzzle velocity; 3000+ rpm) |

### 57mm Cannon Systems (9 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 198, 199, 200, 201, 202, 203, 204, 205, 206 | Bofors/AU-220M | 57mm | 2000 m | **Bofors/AU-220M 57mm Autocannon**: 4000m effective range against ground targets (naval systems reach 7600m+ against air, 12km max; AU-220M 4km effective ground) |

---

## NOTES ON DATA

1. **Conservative Effective Range Approach**: Used practical direct-fire engagement distance
   - Example: M61 Vulcan reaches 2.3 miles air-to-ground; used 2000m as practical effective range
   - Example: M230 can theoretically reach 2000m; used 1500m as practical doctrine maximum
   - Example: 57mm naval systems reach 12km maximum; used 4000m for ground engagement

2. **Platform Variants**: Same autocannon system maintains consistent effective range
   - M61 variants: all 2000m (M197, AAG, CIWS, airborne/shipboard)
   - GSh-23 variants: all 2000m (GSh-23L, ZU-23, GSh-6-23, towed/aircraft mounted)
   - M230 variants: all 1500m (M230LF, Bushmaster II, Apache-mounted)
   - Bushmaster family: scaled by caliber (25mm→1500m, 30mm→1500m, 35mm→2000m, 50mm→2000m)

3. **Ammunition Type Impact**: Different munitions affect effective range
   - HE/HEDP rounds: effective to standard range for target destruction
   - Armor-piercing: effective range depends on armor thickness threshold
   - Self-destruct rounds: range set by fuze (M61: 1800-2300m self-destruct)
   - Guided variants: range independent of ballistic envelope

4. **Fire Control Considerations**:
   - Direct fire systems: effective range = reliable hit probability with fire control
   - High-arc fire: GSh-23 can reach 2-3x farther, but less accurate
   - Naval systems: different ballistic profiles than air/ground variants
   - Rate of fire: 3000-4200 rpm allows suppressive fire beyond accurate range

5. **Caliber Progression**:
   - 20mm NATO: 2000m (fighter/gunship mounted)
   - 23mm Soviet: 2000m (fighter/towed gun)
   - 25mm NATO: 1500m (light armor suppression)
   - 30mm NATO: 1500m (attack helicopter, IFV)
   - 35-40mm: 2000m (extended range variants)
   - 50-57mm: 2000-4000m (heavy ground/naval systems)

---

## FILL COMMAND READY

Each entry needs one ground value per system (ground domain only; low_alt and high_alt remain at 0).

**Total corrections: 74 entries**
- 20mm systems: 2000m
- 23mm systems: 2000m
- 25mm systems: 1500m
- 30mm systems: 1500m
- 35mm systems: 2000m
- 40mm systems: 2000m
- 50mm systems: 2000m
- 57mm systems: 4000m
- Format: Integer meters (e.g., "4000", "2000", "1500")
