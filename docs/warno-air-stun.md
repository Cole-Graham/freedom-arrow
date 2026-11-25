# Air stun

A hit on a plane or a helicopter adds stun damage equal to the missile's written `SuppressDamages`. That number is not the suppress total the target feels. The engine adds `25 × PhysicalDamages` to suppress only, and it does not add that bonus to stun.

The stun bar is separate from the suppression bar. Crossing a cut on the stun bar raises the `Stunned` tag. Suppression still runs on its own bar and still applies the air-unit cohesion penalties. The forced plane evacuation that used to sit on the suppression bar is removed, so a stunned plane stays in the air under the stun tag.

## The stun bar

| | Plane | Helicopter |
| --- | ---: | ---: |
| Maximum (`MaxStunDamages`) | 255 | 100 |
| Regen per second | 1 | 1 |
| Pack | `packStun_Airplanes` | `packStun` |
| Cut | 0.70 | 0.99 |
| Stun damage that fires the pack | 178.5 | 99 |

Vanilla planes used a maximum of 9999 and regenerated 9999 a second, on the artillery stun pack, so missile stun did not stick. Vanilla helicopters used a maximum of 450 on `packStun`.

`packStun_Airplanes` is assigned to units tagged `Avion` whose menu icon is not `Texture_RTS_H_uav`. Its only effect, at the 0.70 cut, is `UnitEffect_Unit_Stunned`. Helicopters keep the shared `packStun`. That pack's 0.99 cut applies `UnitEffect_Unit_Stunned` and `UnitEffect_Infanterie_Cowering_Rampe`.

Putting the stunned effect on the suppression pack left planes stunned permanently: stun recovery only runs on the stun bar. The airplane pack exists so the tag clears when the stun bar falls back through 178.5.

## What the tag does

`UnitEffect_Unit_Stunned` raises the tag `Stunned` (`TagStunned`) and nothing else. The unit label draws the stun icon while that tag is up. The tag stays up while the stun bar remains on that cut, and it drops when regen carries the bar back under the cut.

`StunEffectDuration` is 3 seconds. Vanilla is 4.

On a plane the pack does not change speed, accuracy, or evacuation. The tag stays up until stun damage falls under 178.5. At 1 point a second, a 190 hit holds it for 11.5 seconds, a 240 hit for 61.5 seconds, a 265 hit for 86.5 seconds, and a 350 hit for 171.5 seconds.

On a helicopter the same tag is raised, and `UnitEffect_Infanterie_Cowering_Rampe` sets the speed multiplier to 0.30. The engine runs that as its own helicopter state (`SubUnitHelicoIsStunned`), and leaves it through `SubUnitHelicoEndStunned`. The tag stays up until stun damage falls under 99, so a 115 hit holds it for 16 seconds and a 350 hit holds it for 251 seconds.

## Resistance

Plane veterancy copies its suppress resistance onto stun. The modifier is a percentage of damage taken.

| Level | Stun damage taken |
| --- | ---: |
| Rookie | 0 |
| Trained | 0 |
| Veteran | −20% |
| Elite | −40% |

Helicopter veterancy is not copied onto stun. A helicopter takes the full written suppress as stun at every level.

A one-hit plane stun is written stun, after that resistance, of at least 178.5.

| Target | Written stun required |
| --- | ---: |
| Rookie or trained | 178.5 |
| Veteran | 223.2 |
| Elite | 297.5 |

## Written stun by physical damage

For an AA missile with no explicit `SuppressDamages`, the written value is the intended suppress minus `25 × PhysicalDamages`.

| Physical | Intended suppress | Written stun |
| ---: | ---: | ---: |
| 4 | 180 | 80 |
| 5 | 240 | 115 |
| 6 | 310 | 160 |
| 7 | 365 | 190 |
| 8 | 465 | 265 |
| 9 | 465 | 240 |

Five missiles set `SuppressDamages` to 350 after that standard, so their written stun stays 350. After elite resistance that is 210, which is still over 178.5.

## Missiles that stun a plane in one hit

Written 190 stuns a rookie or a trained plane (190 ≥ 178.5) and does not stun a veteran (`190 × 0.8 = 152`).

| Missile | Written stun |
| --- | ---: |
| `SAM_9M311_Tunguska` | 190 |
| `SAM_9M330_Tor` | 190 |
| `SAM_9M33M2` | 190 |

Each of those three also has a `_HAGRU` descriptor with the same written stun. `_HAGRU` is the plane-only copy.

Written 240 or 265 stuns a rookie, a trained plane, and a veteran. It does not stun an elite (`265 × 0.6 = 159`, `240 × 0.6 = 144`).

| Missile | Written stun |
| --- | ---: |
| `AA_R40RD1` | 265 |
| `AA_R40TD1` | 265 |
| `SAM_3M9M1` | 240 |
| `SAM_5V27D` | 240 |
| `SAM_9M336` | 240 |
| `SAM_9M38M1` | 240 |
| `SAM_I_Hawk` | 240 |

`SAM_3M9M1`, `SAM_5V27D`, `SAM_9M336`, `SAM_9M38M1`, and `SAM_I_Hawk` each have a `_HAGRU` twin at the same written stun.

Written 350 stuns every plane level, including elite.

| Missile | Written stun | After veteran | After elite |
| --- | ---: | ---: | ---: |
| `AA_AIM54_Phoenix` | 350 | 280 | 210 |
| `AA_R33_Vympel` | 350 | 280 | 210 |
| `AA_R37_Vympel` | 350 | 280 | 210 |
| `SAM_9M8M3` (Krug) | 350 | 280 | 210 |
| `SAM_BLOODHOUND` | 350 | 280 | 210 |

## Missiles that do not stun a plane in one hit

Physical 6 writes 160. One hit is under 178.5 at every veterancy (`160 × 0.6 = 96` on an elite). Two hits still clear it: a fresh plane takes 160 and then another 160, and the bar caps at 255; an elite takes 96 and then 96, which is 192, 13.5 above the cut. Regen between the two hits spends 1 point a second, so the second hit has to arrive before that margin is gone.

Physical 5 writes 115. Physical 4 writes 80. Neither reaches 178.5 in one hit. That is the Sidewinder L/M, Stinger, Igla, Strela, Rapier, Roland, Sparrow, and the other physical-4 and physical-5 AA missiles.

## Missiles that stun a helicopter in one hit

The helicopter cut is 99, and helicopter stun is not reduced by veterancy.

Every AA missile with physical damage 5, 6, 7, 8, or 9 stuns a helicopter in one hit. Written stun for those steps is 115, 160, 190, 265, and 240, and the five explicit missiles land at 350. All of those are at least 99, so the stun cut is crossed and the `Stunned` tag and the 0.30 speed multiplier come on.

Physical 4 writes 80 and does not stun a helicopter in one hit. That family is `AA_AIM9J_Sidewinder`, `AA_R13M`, `AA_R60M_Vympel`, `MANPAD_FIM43`, `MANPAD_Strela2M`, `MANPAD_Strela3`, `MANPAD_igla`, and the `SAM_Igla`, `SAM_Strela2`, and `SAM_FASTA_Strela2M` descriptors, including their `_HAGRU` twins.

SPAAG air bursts are not in this missile table. Their air ammo writes about two thirds of the ground suppress value so the same 178.5 plane cut lines up with the gun's old suppress timing.
