# Tank-Mounted ATGMs (10_tank_atgm.yml) — Real-World Effective Ranges

## Research Summary: Individual Tank ATGM Systems
All values represent **effective combat engagement range** in meters, based on military specifications for guided missiles fired from tank gun systems.

---

## SOVIET/RUSSIAN TANK-MOUNTED ATGMS

### 9M117 Arkan Family (2 entries)

| Entry ID | Missile | System | Effective Range | Research |
|----------|---------|--------|-----------------|----------|
| 8 | 9M117 | Arkan (baseline) | 5500 m | **Arkan/Bastion**: 9M117 laser beam-riding ATGM, **5500m effective range** (100m-6000m envelope, 5500m practical) |
| 197 | 9M117M | ArkanM (improved) | 5500 m | ArkanM variant: 5500m effective (same platform, upgraded guidance) |

### 9M119 Invar Family (4 entries)

| Entry ID | Missile | System | Effective Range | Research |
|----------|---------|--------|-----------------|----------|
| 72 | 9M119 | Invar (baseline) | 5000 m | **Invar/Svir/Refleks**: 9M119 laser-guided ATGM from 125mm gun, **5000m effective range** |
| 125 | 9M119M | InvarM (improved) | 5000 m | 9M119M variant: 5000m effective (upgraded tandem warhead) |
| 245 | 9M119M1 | InvarM1 T90M | 5000 m | InvarM1 for T-90M: 5000m effective (latest variant of Svir platform) |
| 250 | 9M119M1 | InvarM1 | 5000 m | InvarM1 variant: 5000m effective (modernized seeker, same guidance envelope) |

### 3UBK21 Sprinter (1 entry)

| Entry ID | Missile | System | Effective Range | Research |
|----------|---------|--------|-----------------|----------|
| 514 | 3UBK21 | Sprinter (latest-gen) | 8000 m | **Sprinter**: 3UBK21 for T-14 Armata 2A82-1M gun, **8000m effective range** (millimeter-wave SACLOS, 950mm penetration) |

---

## AMERICAN TANK ATGM

### MGM-51 Shillelagh (1 entry)

| Entry ID | Missile | System | Effective Range | Research |
|----------|---------|--------|-----------------|----------|
| 168 | MGM-51 | Shillelagh | 3000 m | **Shillelagh**: M13/MGM-51 from M81 gun (Sheridan/later variants), **3000m effective range** (MGM-51B/C extended-range model; original 2000m) |

---

## NOTES ON DATA

1. **Conservative Effective Range Approach**: Where sources provided ranges, used practical effective engagement distance
   - Arkan: listed as 100-6000m envelope; used 5500m as practical extended range
   - Invar: listed as 5000m maximum; used 5000m (direct specification)
   - Shillelagh: original 2000m, extended variants 3000m; used 3000m for modern combat capability
   - Sprinter: listed as 8000m, some sources claim 12000m max; used 8000m documented effective

2. **Platform Variants**: Same missile maintains unified effective range across platforms
   - Arkan/ArkanM: both 5500m (same laser guidance system on T-55, T-62, BMP-3)
   - Invar/InvarM/InvarM1: all 5000m (same 9M119 missile family from 2A45/2A46/2A46M guns)
   - Sprinter: single entry, T-14 Armata platform only

3. **Generational Progression**: Later systems show significantly extended ranges
   - Shillelagh: 2000m (original, 1960s-70s) → 3000m (extended-range B/C variants)
   - Arkan/Invar: ~5000-5500m (1980s-90s Russian development)
   - Sprinter: 8000m (2010s latest generation, significant leap in standoff capability)

4. **Guidance System Impact**: All tank ATGMs are laser or millimeter-wave guided
   - Laser beam-riding (Arkan, Invar): vulnerable to atmospheric obscuration, requires target tracking
   - SACLOS millimeter-wave (Sprinter): improved all-weather capability, longer engagement range
   - Shillelagh: SACLOS with semiactive guidance (limited by fire control system generation)

5. **Armor Penetration Capability**:
   - Arkan: 750mm RHAe after ERA
   - Invar: 900mm RHAe after ERA
   - Sprinter: 950mm RHAe after ERA (best penetration)
   - Shillelagh: ~600-700mm RHAe after ERA (older design)

6. **Engagement Envelope**:
   - Minimum ranges: 100-730m (arming distance, gun tube exit clearance)
   - Maximum ranges: 2000-8000m (as listed above)
   - Practical sustained fire: max range minus engagement time

---

## FILL COMMAND READY

Each entry needs one value per domain (ground only; low_alt and high_alt remain at current values or 0).

**Total corrections: 8 entries**
- Arkan variants: 5500m
- Invar variants: 5000m
- Shillelagh: 3000m
- Sprinter: 8000m
- Format: Integer meters (e.g., "8000", "5500", "5000", "3000")
