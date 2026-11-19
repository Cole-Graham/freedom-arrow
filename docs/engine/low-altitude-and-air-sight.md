# Low altitude, air optics and line of sight

**Short answer.** Yes, there is an extra margin, and it comes from the forest. The game does not trace the sight line against the trees you see. It treats every forest cell of the map as a block of "forest" that reaches **15 world units (30 m on the card scale)** above the ground. A sight line that passes through that layer pays a vision cost. The cost is free for the first 21 steps and then rises with every further step. After about 50–60 steps (100–120 m) the line has used up most of a unit's air optics. Trees are not in the hard sight-line check at all. Only terrain and building colliders can cut a line outright.

What this means for anti-air: an AA unit at the edge of a wood, or behind one, often cannot see a helicopter or a low plane. Its sight line has to skim the top of that 15-unit forest layer for a long stretch, even when the camera shows a clear view over the real treetops. AA sees best when the first stretch of the line toward the target is over open ground, or from high ground where the line rises above 15 units over the trees quickly.

"Low altitude" is a game state, not a height you can see:

- **Helicopters are always Low.**
- **Planes are Low or High from their height**, with hysteresis between the 100 and 400 world-unit order heights.
- **Ground units are Ground.**

Each state uses its own optics value on the observer: ground, low-altitude or high-altitude optics.

Every claim below is marked **code** (read from the 1.2.2.1 binary), **data** (read from the 1.2.2.1 game data) or **calculated**.

---

## 1. What "low altitude" is

`AltitudeComponent.GlobalAltitudeLevel` (offset `0x18`) holds the state. The enum `GlobalAltitude` is `Ground = 0`, `Low = 1`, `High = 2` (code).

`AltitudeSystem.UpdateAltitudeLevel` (RVA `0x3C5170`) sets it every time `UpdateAltitudeLevelTime` passes `ResetUpdateTime` (code):

- **Helicopter** (`UnitHelicopterFlag`): always **Low**. The helicopter's real height and its fly mode do not change this state (code).
- **Plane** (`UnitAircraftComponent`): compares `AltitudeComponent.UnitAltitude` with a threshold set by `PlanesConfig.LowAltitude` and `PlanesConfig.HighAltitude` (code):
  - not High now: High when the height is above `Low + 0.4 × (High − Low)` (`LOW_TO_HIGH_ENTER_VALUE`);
  - High now: stays High while the height is above `Low + 0.3 × (High − Low)` (`HIGH_TO_LOW_ENTER_VALUE`), otherwise Low.
- **Ground units** are never set here, so they stay **Ground** (code).

`PlanesConfig` values in the game data are `HighAltitude = 400` and `LowAltitude = 100` world units. Their tooltips say "altitude above terrain" (data). That gives (calculated):

| Plane | Becomes High above | Drops to Low below |
| --- | ---: | ---: |
| World units | 220 | 190 |
| Card scale (×2) | 440 m | 380 m |

A plane ordered low (100) is Low. A plane ordered high (400) is High once it has climbed past 220. A plane diving through the band changes state at 190 on the way down (calculated).

`LabelDataComponent.IsLowAltitude` (`0x16`) and the label's low-altitude icon are the display side of the same state (code, field names only).

## 2. Which optics an air target is checked against

The unit's sensor row (`Sensors`) has three ranges: `OpticsGround`, `OpticsLowAltitude` and `OpticsHighAltitude` (data). Each observer's `FogOfWarComponent` keeps three matching vision distances: `DistanceGround` (`0x0`), `DistanceLowAlt` (`0x4`) and `DistanceHighAlt` (`0x8`) (code, field layout).

The target's altitude state picks which one applies: Ground, Low or High. Helicopters always use the low-altitude optics, and so do planes below the threshold above. This is inferred from the matching names and from weapon ranges, which pick Ground/Low/High range by the same `GlobalAltitudeLevel` (`BattleSystemHelpers.GetAmmoShootingDistance`, RVA `0x7D69B0`). The exact read in the vision code is **not traced yet**.

## 3. How the sight line is checked

Each observer runs `FogOfWarUnit` (`Update` RVA `0x6A2CC0`) on a timer. Each check of a target has two independent tests. **Both must pass** (code).

### 3a. Eye points

`FogOfWarHelper.TryGetEntityEyePoint` (RVA `0x69EFB0`): the eye is the unit's transform position plus `FogOfWarComponent.UnitColliderCenter` (`0x60`), the centre of the unit's collider (code). For a unit inside a building, the eye is a point of the building segment.

This means the observer looks from the middle of its hull, not from its sensor or turret top. The target is checked at the middle of its own collider (code).

### 3b. Hard block: a physics ray against terrain and buildings

A Unity `RaycastCommand` runs from eye to eye in a batch (`RaycastBatchService`). Its layer mask is built in the `FogOfWarUnit` constructor (RVA `0x6A37D0`) from **layer 8 and layer 11** (code).

In the 1.2.2.1 `TagManager` those layers are **8 = Terrain** and **11 = Buildings**. Layer 10 = Forest is **not** in the mask (data). So a hill or a building between the eyes blocks the line, and trees never do.

### 3c. Soft block: the vision-cost walk

`FogOfWarFilter.FilterCore` (RVA `0x69D110`) walks the same line in steps of 1 world unit (`FogOfWarConfig.FILTER_STEP_LENGTH = 1`) over the map's terrain grid (code). For each step it reads the cell's ground height and terrain type. Then:

1. `h` = height of the line above that cell's ground.
2. If `h` is above the terrain type's `Height`, the step costs **1**: open air.
3. Otherwise the step is inside that terrain type's layer. The type's step counter goes up by 1, and the step costs `Opacity + Multiplier × count`, at least 1.
4. The costs are added up, and smoke along the line is added after the walk (`SmokeHelper`).
5. The target is visible when the total is not more than the vision distance (`FilterTask.MaxVisionDistance`, `0x2C`).

Exceptions (code):

- `FilterTask.IgnoreTerrainCosts` (`0x28`) makes every step cost 1.
- `IgnoreForestCostOnly` (`0x29`) skips only forest.
- A target whose unit type is `Projectile` (128) skips the walk and costs the straight distance.

The terrain-type settings in the 1.2.2.1 `FowOfWarConfig` asset (data):

| Terrain type | Opacity | Multiplier | Height (layer top above ground) | Cover |
| --- | ---: | ---: | ---: | ---: |
| Vegetation (1) | 1 | 0 | 10 | 1 |
| Road (6) | 1 | 0 | 10 | 1 |
| HighSlopes (4) | 1 | 0 | 10 | 1 |
| Water (5) | 1 | 0 | 20 | 1 |
| Buildings (3) | 1 | 0 | 10 | 2 |
| **Forest (2)** | **−15** | **0.75** | **15** | 2 |
| Smoke (15) | 1 | 3 | 20 | 1 |

Other values: `MinimumDetectionDistance` 45, `MaxShootableForestDistance` 45, `LaserForestMaxRange` 45, `LaserOwnForestRange` 25 (data).

Only **forest** and **smoke** make a step cost more than 1. Vegetation, roads, slopes, water and the building grid all cost 1 per step, the same as open air. Buildings block only through the physics ray in 3b (data and code).

### 3d. The forest layer, worked out (calculated)

For the forest, step *k* inside the layer costs `max(1, −15 + 0.75k)`. Steps 1–21 cost 1 each. From step 22 the cost rises by 0.75 a step:

| Forest steps under the 15-unit layer | Card length | Vision cost used | Extra over open air |
| ---: | ---: | ---: | ---: |
| 20 | 40 m | 20 | 0 |
| 30 | 60 m | 62 | +32 |
| 40 | 80 m | 178 | +138 |
| 50 | 100 m | 369 | +319 |
| 60 | 120 m | 635 | +575 |
| 80 | 160 m | 1,393 | +1,313 |

Sensor low-altitude optics are mostly about 800–2,000 world units (data, sensor table). So a sight line that runs through roughly 60–80 world units of the forest layer is effectively blocked, even with a clear view over the real trees.

How long a line stays in the layer depends on the geometry. Take an AA eye about 1.5 units above the forest floor, and a target at height `H` and distance `D` on flat ground. The line stays under 15 units for the first `D × 13.5 / (H − 1.5)` units of its length. Example: a helicopter 25 units up at 600 units away keeps the line inside the layer for the first 345 units. If those 345 units are woods, the line is blocked. If the AA stands 60+ units clear of the tree line, only the far part of the line crosses forest. That part is higher than 15 units over the trees unless the target itself is low (calculated, flat-ground model).

This is the "extra margin above the trees": the forest blocks sight as if it were 15 world units (30 m) tall and grows denser the deeper the line goes into it. The tree models are not used.

## 4. Firing

The observer's shootable set (`FogOfWarComponent.Shootable`, `0x40`) is kept next to the visible set, and `FogOfWarHelper.IsTargetShootable` (RVA `0x69EB30`) takes a `FilterTask`. That suggests firing at air targets runs through the same filter result. Its exact rule is **not traced**.

## 5. Where the mod changes this

Freedom Arrow today changes only **Cover** for forest (3.0) and buildings (3.5), plus flash and spotted settings, through `DetectionConfig.cs` / `detection-config.json`. It changes no `Height`, `Opacity` or `Multiplier`, and no altitude thresholds (read from the mod source).

Ways to make AA placement easier (not implemented, not tested):

- **Lower the forest `Height`** (15 → e.g. 8–10) in the same `DetectionConfig` write, before `GenerateVisionData` copies the settings into `TerrainVisionData`. This moves the layer top closer to the visible treetops. It also changes ground vision through and over woods, for every unit.
- **Soften forest growth**: a smaller `Multiplier` (0.75) or a higher start (`Opacity` −15 → e.g. −30 gives 41 free steps). This also affects ground units.
- **Air-only rule**: a hook on `FogOfWarFilter.FilterCore` that uses a lower forest height when the target is a helicopter or plane. Ground vision stays unchanged. This needs code and a performance check, because the filter runs for every observer–target pair.
- **Plane altitude band**: `PlanesConfig.LowAltitude` / `HighAltitude` (100 / 400). This changes when planes count as Low, not the forest problem.

## 6. Not verified

- **Optics selection:** the exact code that picks `DistanceLowAlt` / `DistanceHighAlt` from the target's state, and any stealth, flash or spotted multipliers on it, is inferred, not traced.
- **Map grid:** the terrain-grid cell size per map (`MapMetaData`), and so how many grid cells one world-unit step crosses on each map.
- **Visible tree heights:** no tree heights were measured in a map, so the margin above the visible trees is not quantified in metres.
- **Helicopter heights:** actual helicopter flying heights were not read, so the worked example's 25 units is an example, not game data.
- **A grid flag:** the meaning of the cell flag `0x2` that skips the cost within 45 units (`MinimumDetectionDistance`) when the target is close.
- **In game:** none of this has been measured in a match.

## Document change log

- 2026-11-19 09:2x PST (America/Los_Angeles) — New doc: low altitude, air optics and line of sight (Lateralus's request).
