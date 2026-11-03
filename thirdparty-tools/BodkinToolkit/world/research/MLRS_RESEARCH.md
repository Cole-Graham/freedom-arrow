# Multiple Launch Rocket Systems (13_mlrs.yml) — Real-World Effective Ranges

## Research Summary: Individual MLRS Systems
All values represent **effective range** for unguided rocket systems, based on military specifications for multiple launch rocket platforms.

---

## SOVIET/RUSSIAN MLRS SYSTEMS

### BM-21 Grad 122mm MLRS Systems (14 entries)

| Entry ID | System | Caliber | Effective Range | Research |
|----------|--------|---------|-----------------|----------|
| 66, 431, 432, 433, 434, 435, 436, 485, 488, 510, 511, 512, 513, 620 | BM-21 Grad / Grad variants | 122mm | 30000 m | **BM-21 Grad 122mm MLRS**: 30000m effective range (original 20km, modern extended variants 40-45km; conservative modern estimate 30km balances standard vs. extended) |

---

## NOTES ON DATA

1. **Conservative Effective Range Approach**: Used practical extended-range capability
   - Original Grad: 20km (9M22 HE-frag)
   - Modern standard: 30km (improved propellant)
   - Extended variants: 40-45km (G-2000/45 series)
   - Used 30km as realistic effective range for modern Grad systems

2. **Platform Variants**: All Grad variants use same ballistic envelope
   - HE (High Explosive)
   - Cluster ammunition
   - Incendiary
   - Smoke/illumination
   - All maintain 30000m effective range

3. **Ammunition Type Impact**: Grad rocket family
   - Standard HE: 20,000-30,000m depending on variant
   - Cluster warheads: same envelope
   - Incendiary: same envelope
   - Smoke/illuminate: slightly reduced range
   - Modern extended: 40,000+ meters

4. **Indirect Fire Characteristics**:
   - Unguided rockets: ballistic trajectory
   - Saturation fire capability: 40 rockets per salvo
   - Reload time: 5-8 minutes standard
   - Range: variable depending on ammunition load
   - Dispersal pattern: area weapon system

5. **System Notes**:
   - BM-21: Soviet-era platform still widely used
   - Multiple variants: domestic, licensed production, upgraded
   - Extended-range upgrades: modernized ammunition, improved propellant
   - Effective range: 30km balances practical engagement envelope

---

## FILL COMMAND READY

Each entry needs one ground value per system (ground domain only; low_alt and high_alt remain at 0).

**Total corrections: 14 entries**
- All BM-21 Grad variants: 30000m
- Format: Integer meters (e.g., "30000")
