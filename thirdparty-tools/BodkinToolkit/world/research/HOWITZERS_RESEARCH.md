# Howitzers & Artillery Guns (12_howitzers.yml) — Real-World Effective Ranges

## Research Summary: Individual Howitzer Systems
All values represent **effective combat engagement range** in meters for indirect fire artillery weapons, based on standard ammunition specifications (conservative estimates when sources varied between HE and RAP rounds).

---

## NATO HOWITZER SYSTEMS

### 105mm Howitzer Systems (6 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 37, 419, 427, 581, (2 more) | M101/M119 | 105mm | 18000 m | **M119A1/A2 105mm Towed Howitzer**: 18000m effective range (14000-19500m envelope, 19500m with RAP; M101A1: 11270m standard) |

### 155mm Howitzer Systems (14 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 425, 425, 537, (11 more) | M109/M777 | 155mm | 22000 m | **M109A5/A6 & M777 155mm Howitzer**: 22000m effective range (18000m baseline, 23500-30000m with RAP; conservative standard round estimate) |

---

## SOVIET/RUSSIAN HOWITZER SYSTEMS

### 122mm Howitzer Systems (2 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 174, 408 | 2A31 Gvozdika | 122mm | 18000 m | **2A31 Gvozdika 122mm Self-Propelled Howitzer**: 18000m effective range (15300m fragmentation, 21900m RAP; conservative estimate between variants) |

### 152mm Howitzer Systems (19 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 169, 413, (17 more) | 2A64/2S3 | 152mm | 20000 m | **2A64 & 2S3 Akatsiya 152mm Self-Propelled Howitzer**: 20000m effective range (17230-24700m depending on variant; 2S3: 17400m standard, 20500m RAP; 2S19: 24700m standard; conservative blended estimate) |

### 203mm Howitzer Systems (2 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 481, 565 | 2A44 Malka | 203mm | 25000 m | **2A44 Malka 203mm Heavy Howitzer**: 25000m effective range (extended range system, similar to 152mm heavy variants; 25000-28000m envelope) |

---

## NOTES ON DATA

1. **Conservative Effective Range Approach**: Used practical combat ranges where sources provided multiple variants
   - Example: 105mm ranges 14000-19500m; used 18000m as mid-range practical
   - Example: 155mm reaches 30000m with RAP; used 22000m for standard HE rounds
   - Example: 152mm variants span 17.2-24.7km; used 20000m as reasonable average

2. **Platform Variants**: Same howitzer system maintains consistent effective range
   - M119 variants: all 18000m (towed, modern fire control)
   - M109 variants: all 22000m (self-propelled, extended range)
   - 2S3/2A64 variants: all 20000m (Soviet platform)
   - 2A44 heavy: 25000m (superior range over lighter systems)

3. **Ammunition Type Impact**: Different munitions affect effective range
   - Standard HE rounds: quoted effective range
   - Cluster ammunition: same ballistic envelope as HE
   - Rocket-assisted projectiles (RAP): extended range (20-30% more)
   - Guided rounds (Excalibur): range independent of ballistic envelope

4. **Indirect Fire Characteristics**:
   - Maximum ranges: 14,000-30,000m depending on caliber and ammunition
   - Effective ranges: conservative firing distance for hit probability
   - Area targets: longer ranges viable with artillery procedures
   - Point targets: shorter ranges for direct accuracy

5. **Caliber Progression**:
   - 105mm NATO: 18,000m (light/towed)
   - 122mm Soviet: 18,000m (self-propelled medium)
   - 152mm Soviet: 20,000m (self-propelled medium-heavy)
   - 155mm NATO: 22,000m (self-propelled heavy)
   - 203mm Soviet: 25,000m (self-propelled heavy)

---

## FILL COMMAND READY

Each entry needs one ground value per system (ground domain only; low_alt and high_alt remain at 0).

**Total corrections: 43 entries**
- 105mm systems: 18000m
- 122mm systems: 18000m
- 152mm systems: 20000m
- 155mm systems: 22000m
- 203mm systems: 25000m
- Format: Integer meters (e.g., "25000", "22000", "20000", "18000")
