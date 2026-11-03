# Cruise & Strategic Missiles (18_cruise_strategic.yml) — Real-World Effective Ranges

## Research Summary: Strategic Cruise Missile Systems
All values represent **maximum operational range** in meters for long-range cruise missile and strategic standoff systems.

---

## CRUISE MISSILE SYSTEMS

### AGM-86 ALCM (1 entry)

| Entry ID | System | Effective Range | Research |
|----------|--------|-----------------|----------|
| 303 | AGM-86D ALCM | 2400000 m | **AGM-86D ALCM**: 2400km effective range (Air-Launched Cruise Missile, Mach 0.48 turbofan, ~2400km maximum range, B-1B, B-52H; strategic standoff) |

### JASSM (1 entry)

| Entry ID | System | Effective Range | Research |
|----------|--------|-----------------|----------|
| 302 | JASSM | 370000 m | **JASSM**: 370km effective range (Joint Air-to-Surface Standoff Missile, Mach 0.65 turbofan, ~370km+ documented range, B-1B, B-2, F-15EX; modern standoff) |

### Kh-101/Kh-102 (2 entries)

| Entry ID | System | Effective Range | Research |
|----------|--------|-----------------|----------|
| 337 | Kh-101 | 3000000 m | **Kh-101**: 3000km effective range (Russian strategic cruise missile, turbofan, ~3000km+ range, Tu-160; supersonic Mach ~0.8-2.0 reported variant) |
| 453 | Kh-102 Nuke | 3000000 m | Kh-102 nuclear variant: 3000km effective (same missile platform with nuclear warhead, Tu-160; identical ballistic envelope) |

### Kh-555 (1 entry)

| Entry ID | System | Effective Range | Research |
|----------|--------|-----------------|----------|
| 338 | Kh-555 | 2500000 m | **Kh-555**: 2500km effective range (Russian cruise missile, turbofan, ~2500km range, Tu-160; export-controlled earlier variant) |

### Tomahawk (1 entry)

| Entry ID | System | Effective Range | Research |
|----------|--------|-----------------|----------|
| 35 | Tomahawk | 2500000 m | **Tomahawk BGM-109 Cruise Missile**: 2500km effective range (subsonic turbofan, variants 1600-2500km range, Arleigh Burke destroyers; use 2500km for BGM-109C/D variants) |

---

## STRATEGIC GRAVITY BOMBS

### B61 Nuclear Ordnance (1 entry)

| Entry ID | System | Effective Range | Research |
|----------|--------|-----------------|----------|
| 304 | B61-12 Nuclear | 20000 m | **B61-12 Thermonuclear Bomb**: 20km effective range (gravity-drop thermonuclear ordnance, standoff delivery range dependent on aircraft type and release altitude, typically released 10-30km from target for safety, B-1B, B-2, B-52H, F-117; conservative tactical standoff range) |

---

## NOTES ON DATA

1. **Strategic Range Classification**:
   - **Long-range cruise**: AGM-86 (2400km), Kh-101 (3000km), Kh-555 (2500km)
   - **Extended standoff**: JASSM (370km), Kh-102 (3000km)
   - **Subsonic cruise**: Tomahawk (2500km), AGM-86 (2400km)
   - **Strategic gravity**: B61-12 (tactical delivery range, 20km from release)

2. **Platform Variants**: Same missile maintains consistent strategic range
   - Kh-101/Kh-102: both 3000km (same platform, different warheads)
   - All bombers carry same missile types: consistent range per system

3. **Guidance System Impact**:
   - INS/TERCOM (Tomahawk): 2500km range
   - INS-only (AGM-86, Kh-series): 2400-3000km range
   - GPS-aided (JASSM): 370km+ range
   - Gravity bombs: platform-dependent delivery range

4. **Range Characteristics**:
   - **Subsonic cruise missiles**: 2000-3000km (8-10 hour flight time)
   - **Extended standoff**: 300-400km (tactical range)
   - **Gravity bombs**: 20km typical tactical standoff
   - **Strategic delivery**: 1600-3000km maximum range

5. **System Specifications**:
   - **AGM-86 ALCM**: Mach 0.48, 2400km, turbofan, air-launched
   - **JASSM**: Mach 0.65, 370km, turbofan, air-launched standoff
   - **Kh-101**: ~3000km, turbofan, strategic cruise
   - **Kh-102**: ~3000km (nuclear variant of Kh-101)
   - **Kh-555**: 2500km, turbofan, export variant
   - **Tomahawk**: Mach 0.48, 2500km, turbofan, sea-launched
   - **B61-12**: Thermonuclear, gravity-drop, 20km tactical standoff

---

## FILL COMMAND READY

Each entry needs one ground value per system (ground domain only; low_alt and high_alt remain at 0).

**Total corrections: 7 entries**
- AGM-86 ALCM: 2400000m
- JASSM: 370000m
- Kh-101: 3000000m
- Kh-102 Nuke: 3000000m
- Kh-555: 2500000m
- Tomahawk: 2500000m
- B61-12 Nuclear: 20000m
- Format: Integer meters
