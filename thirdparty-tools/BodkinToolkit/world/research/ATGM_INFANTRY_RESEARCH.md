# Infantry ATGMs (05_atgm_infantry.yml) — Real-World Effective Ranges

## Research Summary: Individual Weapon Systems
All values represent **effective range** (reliable combat engagement distance) in meters, sourced from military specifications and conservative where conflicts exist.

---

## SOVIET/RUSSIAN GUIDED MISSILES — 9M SERIES

| Entry ID | Ammunition | Weapon(s) | Research | Effective Range |
|----------|-----------|-----------|----------|-----------------|
| 95 | 9M113 | Konkurs Infantry | Konkurs (AT-5): 3000m effective range (man-portable variant, max 4000m vehicle) | **3000 m** |
| 557 | 9M113F | Konkurs-M Thermobaric | Konkurs-M: 3000m effective (thermobaric variant, same platform as HEAT) | **3000 m** |
| 578 | 9M113F | Konkurs UAV | Konkurs UAV variant: 3000m effective (same missile platform) | **3000 m** |
| 96 | 9M113M | Konkurs-M Infantry | Konkurs-M (improved): 3000m effective (guidance range up to 4000m with vehicle) | **3000 m** |
| 102 | 9M115 | Metis Infantry | Metis (AT-7): 1000m effective range (combat engagement distance) | **1000 m** |
| 523 | 9M131 | Metis-M Infantry | Metis-M: 1500m effective range (improved over original Metis) | **1500 m** |
| 98 | 9M131M | Metis-M1 Infantry | Metis-M1 (upgraded): 2000m effective range (further improved variant) | **2000 m** |
| 346 | 9M134 | Bulat (BMP-3 mounted) | Bulat: 3500m effective range (laser-guided, newer system) | **3500 m** |
| 114 | 9M111-2 | Fagot Infantry | Fagot (AT-4): 2000m maximum range (practical effective engagement) | **2000 m** |
| 395 | 9M111M | Fagot-M (improved) | Fagot-M (AT-4C): 2500m maximum range (improved motor, extended wire) | **2500 m** |

---

## AMERICAN GUIDED MISSILES — JAVELIN / TOW SERIES

| Entry ID | Ammunition | Weapon(s) | Research | Effective Range |
|----------|-----------|-----------|----------|-----------------|
| 44 | FGM-148 | Javelin Infantry | Javelin: 2500m qualified range (up to 4000m demonstrated) | **2500 m** |
| 508 | FGM-148 LWCLU | Javelin LWCLU | Javelin (Lightweight CLU variant): 2500m effective (same missile) | **2500 m** |
| 5 | BGM-71E | TOW-2A | TOW-2A: 3750m maximum range (3.75km effective) | **3750 m** |
| 52 | BGM-71F | TOW-2B | TOW-2B: 3750m effective range (same as TOW-2A) | **3750 m** |
| 458 | BGM-71 (BB) | TOW BunkerBuster | TOW-BB (bunker variant): 3750m range (same ballistic envelope) | **3750 m** |
| 345 | M47 Dragon III | Dragon III Infantry | M47 Dragon: 1000m effective range (1500m max, practical 1000m) | **1000 m** |

---

## EUROPEAN GUIDED MISSILES — SPIKE / MILAN / RBS SERIES

| Entry ID | Ammunition | Weapon(s) | Research | Effective Range |
|----------|-----------|-----------|----------|-----------------|
| 549 | Rafael Spike LR | Spike LR | Spike-LR: 4000m effective range (long-range variant) | **4000 m** |
| 485 | Rafael Spike SR | Spike-SR Disposable | Spike-SR: 1500m effective range (short-range variant) | **1500 m** |
| 596 | MBDA Milan ER | Milan ER Infantry | Milan ER: 3000m effective range (extended response variant) | **3000 m** |
| 572 | RBS 56 | RBS 56 (G-Wagen) | RBS 56 (Swedish Milan): 3000m effective (equivalent to Milan ER) | **3000 m** |
| 574 | IMI MAPATS | MAPATS (G-Wagen) | MAPATS: 3000m effective range (6000m max, conservative effective) | **3000 m** |

---

## NOTES ON DATA

1. **Conservative Approach**: Where military sources diverged, shorter/more conservative ranges were used
   - Example: Konkurs listed as 3000-4000m; used 3000m for man-portable variant
   - Example: MAPATS listed as 300-6000m; used 3000m as practical effective engagement range
   - Example: Javelin shows 2500m qualified vs. 4000m demonstrated; used 2500m

2. **Platform Variants**: Same missile platform (infantry, vehicle-mounted, UAV) uses unified effective range
   - Konkurs (all variants): 3000m (man-portable specification)
   - Javelin (infantry & LWCLU): 2500m (same FGM-148 missile)
   - TOW series (all variants): 3750m (BGM-71 platform)

3. **Generation Progression**: Later generation systems show extended ranges
   - Metis series: 1000m → 1500m → 2000m (generation progression)
   - Fagot series: 2000m → 2500m (Fagot → Fagot-M)
   - Spike variants: 1500m (SR) → 4000m (LR) → 8000m (ER, not in current list)

4. **Wire-Guided vs. Laser-Guided vs. Fire-and-Forget**:
   - Konkurs/Metis/Fagot: Wire-guided (tactical constraints on range)
   - Spike/MAPATS: Laser/beam-riding (greater standoff possible)
   - Javelin: Fire-and-forget (independent engagement after launch)

5. **Thermal vs. Optical Guidance**:
   - Night-capable systems (thermal CLU) may reduce practical range
   - Javelin maintains 2500m effective in all conditions due to fire-and-forget

---

## FILL COMMAND READY

Each entry needs one value per domain (Ground only; low_alt and high_alt remain 0).

**Total corrections: 21 entries**
- All values sourced from individual weapon system research
- No class defaults used
- Format: Integer meters (e.g., "4000", "2500", "1000")

