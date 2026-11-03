# Mortars (11_mortars.yml) — Real-World Effective Ranges

## Research Summary: Individual Mortar Systems
All values represent **effective combat engagement range** in meters, based on indirect fire weapon specifications and practical maximum ranges.

---

## NATO MORTAR SYSTEMS

### 81mm Mortar Systems (2 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 133 | M252 HE | 81mm | 5700 m | **M252 81mm Medium Extended Range Mortar**: 5700m effective range (extended range system, 4500m minimum to 5935m maximum envelope) |
| 132 | M252 SMK | 81mm | 5700 m | M252 smoke variant: 5700m effective range (same ballistic platform as HE) |

### 120mm Mortar Systems (19 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 6 | M121 HE | 120mm | 7200 m | **M120/M121 120mm Heavy Mortar**: 7200m effective range (towed/vehicle-mounted, maximum 8900m with RAP, conservative estimate used) |
| 183 | Dilemma HE | 120mm | 7200 m | Dilemma variant: 7200m effective range (modernized system) |
| 187 | 2A80 Vena HEAT | 120mm | 7200 m | Vena HEAT round: 7200m effective range |
| 190 | 2A51 HE | 120mm | 7200 m | 2A51 system HE: 7200m effective (Soviet/Russian 120mm towed) |
| 191 | 2A51 HE-RAP | 120mm | 7200 m | 2A51 rocket-assisted: 7200m effective range |
| 404 | 2A51 HE-RAP | 120mm | 7200 m | 2A51 HE-RAP variant: 7200m effective |
| 406 | 2A51 HEAT | 120mm | 7200 m | 2A51 HEAT round: 7200m effective |
| 417 | 2A80 Vena HE | 120mm | 7200 m | Vena HE round: 7200m effective |
| 416 | 2A80 Vena HE-RAP | 120mm | 7200 m | Vena HE-RAP: 7200m effective |
| (remaining 10 entries) | Various | 120mm | 7200 m | All 120mm systems: unified 7200m effective range platform |

---

## SOVIET/RUSSIAN MORTAR SYSTEMS

### 82mm Mortar Systems (5 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 134 | 2B14 Podnos HE | 82mm | 4300 m | **2B14 Podnos 82mm Infantry Mortar**: 4300m effective range (standard man-portable system) |
| 410 | 2B9 Vasilek HE | 82mm | 4300 m | **2B9 Vasilek 82mm Gun-Mortar**: 4300m effective range (automatic weapon system, 4270m published) |
| 411 | 2B9 Vasilek RAP | 82mm | 4300 m | Vasilek rocket-assisted: 4300m effective (same platform as HE) |
| (remaining 2 entries) | Various | 82mm | 4300 m | All 82mm systems: unified 4300m effective range |

### 240mm Mortar Systems (2 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 71 | M240 HE | 240mm | 9700 m | **240mm M240 / 2S4 Tyulpan Heavy Mortar**: 9700m effective range (maximum range, 9650m for fragmentation round; minimum 800m) |
| 409 | M240 Guided | 240mm | 9700 m | M240 guided variant: 9700m effective range (same tube, guidance system independent of range) |

---

## NOTES ON DATA

1. **Conservative Effective Range Approach**: Used practical maximum ranges for indirect fire systems
   - Example: M252 envelope is 4500-5935m; used 5700m as practical extended range
   - Example: M120 reaches 8900m with rocket-assisted; used 7200m for standard HE rounds
   - Example: 240mm reaches 18000m with rocket-assisted; used 9700m for standard rounds

2. **Platform Variants**: Same mortar system maintains consistent effective range
   - M252: all variants 5700m (M252 HE, SMK, smoke)
   - M120/M121: all 120mm variants 7200m (vehicle-mounted, towed, HE, HEAT, RAP)
   - 2B14/Vasilek: all 82mm variants 4300m (infantry, gun-mortar, HE, RAP)
   - 240mm: all variants 9700m (HE, guided, fragmentation)

3. **Ammunition Impact**: Different munitions vary by range capability
   - Standard HE rounds: published effective range
   - Rocket-assisted projectiles (RAP): extended range capability (conservative estimate used)
   - Guided munitions: range independent of ballistic envelope (used standard max)
   - Smoke/illumination: same ballistic envelope as HE

4. **Indirect Fire Characteristics**:
   - Minimum ranges: 80-800m (safety arming distance)
   - Maximum ranges: 4300-9700m (fire planning envelope)
   - Effective ranges: practical combat engagement distance
   - High-angle fire (45-85° elevation) enables deep indirect engagement

5. **System Progression**:
   - 81mm NATO: 5700m (extended range medium mortar)
   - 82mm Soviet: 4300m (standard infantry mortar)
   - 120mm (both NATO/Soviet): 7200m (heavy direct support)
   - 240mm: 9700m (brigade-level indirect fire asset)

---

## FILL COMMAND READY

Each entry needs one ground value per system (ground domain only; low_alt and high_alt may remain at 0).

**Total corrections: 28 entries**
- 81mm systems: 5700m
- 82mm systems: 4300m
- 120mm systems: 7200m
- 240mm systems: 9700m
- Format: Integer meters (e.g., "9700", "7200", "5700", "4300")
