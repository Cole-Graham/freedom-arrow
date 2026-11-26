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

## 1b. Who sets a plane's flight altitude

**Summary:** the low/high hotkey only steers a plane while its change is pending. After that the plane holds the band it is in. A precision strike (cruise missiles) always flies its firing point at high altitude, whatever the hotkey says, so the plane climbs and then holds High (code, game 1.2.2.1).

---

- **Hotkey:** `AltitudeChangeAbilitySystem.ChangeAltitudeForPlane` writes `PlaneAltitudeSwitchComponent {IsChangePending = (GlobalAltitudeLevel != target), TargetAltitude = target}`. `GetTargetAltitude` (RVA `0x3C4C80`) returns `TargetAltitude` only while `IsChangePending`; otherwise it returns the current `GlobalAltitudeLevel` (code).
- **Normal flight:** `AircraftHelper.GetCurrentAltitude` (RVA `0x3A66B0`) gives `PlanesConfig.LowAltitude` (100) when the level is Low, else `AltitudeComponent.PlaneHighAltOverride` (`Nullable<float>`, `0xC`) if set, else `PlanesConfig.HighAltitude` (400). It is read by `FlyToPoint`, airstrike, airdrop and move-cancel code (code, direct callers).
- **Precision weapons:** `UnitBuilder.PlaneManeuverWeapons` (RVA `0x350A80`) sorts a plane's weapons into strafe, direct-fire, precision and bomb groups, using `Weapons.IsLowAltDirectWeapon` (`0x4E`) and `IsHighAltDirectWeapon` (`0x4F`). Cruise missiles (for example AGM-84 SLAM-ER and YJ-15, ammo `TrajectoryType` 200) have neither flag (data, 0.9.4 package; the exact sort rule is not traced).
- **The climb:** `PrecisionStrikeCommand.UpdateSteeringPoint` (RVA `0x77BDB0`) builds the firing `WaypointSinglePoint` at `PlaneHighAltOverride` if set, else `PlanesConfig.HighAltitude`. It does not read the hotkey. The strike lasts while the plane has `PrecisionStrikeComponent`. `CompleteStrike` (RVA `0x77A420`) then calls `FlyToPoint`, which uses the level-based altitude above, so a plane that is High after the strike stays High (code).
- **Other attack runs:** strafe and bombing runs (`AirstrikeCommand`, `AirAttackType` Strafe 1 / Bombing 2) and plane attack orders (`AttackCommand`) set `AirAttackComponent {StartAttackAltitude, ReturnPosition, TargetTooClose}` when they start and remove it on complete or cancel (the only direct callers of `Entity.Set/Remove<AirAttackComponent>`, plus save loading). `AirstrikeCommand.GetBombingAltitude` picks the run's band from the bomb type and the current level. How each run's altitude profile is flown is not traced (code).
- **Measured:** in Lateralus's ranked13 test logs (23 Nov 02:08–02:30 UTC) all 7 climbs out of the low band after an ordered descent came right after AGM-84 or YJ-15 launches, with `IsChangePending` false.
- **Not traced:** what brings some planes back to Low 7–12 s after a strike (6 of those 7 did). `PlaneHighAltOverride` is written at spawn (section 1c).

## 1c. Spawn altitude (Lateralus, 25 November 2026)

**Summary:** a plane appears at the spawn point's ground height plus its starting altitude, and that comes from its fly preset (`FlyPresets`, linked through its `Mobility` row). Most planes start High at 400 world units (800 m on the card). Presets with `LowAltitudeIsDefault` start Low at 100. Presets with `OverrideAltitude` use a higher "high" of `HighAltitude + (HighAltitude − LowAltitude) × OverrideAltitideRatio`: 595 with the 0.65 in the data. Helicopters spawn 8 units up. Freedom Arrow changes none of this (code, game 1.2.2.1; data 0.9.7-dev.15).

*Details:*

- **Starting state:** `UnitBuilder.InitAltitude` (RVA `0x344530`) builds `AltitudeComponent`. Helicopters (`Units.Type` 8) get `GlobalAltitudeLevel` Low. Planes (type 16) get Low if their preset's `LowAltitudeIsDefault` is set, else High. If `OverrideAltitude` is set it also writes `PlaneHighAltOverride = max(HighAltitude, HighAltitude + (HighAltitude − LowAltitude) × OverrideAltitideRatio)`; the upper clamp is `float.MaxValue` (code).
- **Spawn height:** `SpawnCommand.OnComplete` (RVA `0x331C50`, the inlined `GetUnitAltitude`, `0x331740`) adds to the spawn point's height: plane with `OverrideAltitude` → that override (595); else `LowAltitudeIsDefault` → `LowAltitude` (100); else `HighAltitude` (400). Helicopter → 8. Other units → 0. The base height is read from a grid at the spawn point, taken to be the map height (inferred) (code).
- **Afterwards:** a High plane flies at `PlaneHighAltOverride` if set, else 400 (`AircraftHelper.GetCurrentAltitude`, section 1b). So override presets cruise at 595 whenever they are High. They are Low at 100 like every other plane. The Low/High state switches at 220 going up and 190 going down (section 1).
- **`PlanesConfig`** (`HighAltitude` 0x18 = 400, `LowAltitude` 0x1C = 100, "altitude above terrain") is one shared setting for every plane. Per plane, only the fly preset fields above change the altitude. `OverrideAltitideRatio` is spelled that way in the game (data).
- **Presets in 0.9.7-dev.15 data:**
  - Start High at 400: AC130, Drone Fast/Medium/MediumPlus/Slow/VeryFast High, Static Drone, Fighter-Bomber, Fighter-F16, Fighter-Top and the FA fighter presets.
  - Start High, override 595: BigFast B1B, BigFast MiG31 (MiG-31 family, MD-22, WZ-8), BigFast Tu22 (Tu-22M3, H-6K), BigFast Tu160, BigSlow (B-2, B-21, B-52H, Tu-95, Tu-142), CAS F117.
  - Start Low at 100: CAS A10 (A-10C, L-39, J-5 and J-6W drones), CAS Yak38, CAS (Su-25s, AV-8Bs, EA-6B, Yak-130), Drone Slow Low (RQ-7, Forpost, Korsar, Jiutian), C27.
  - Start Low, and 595 when High: C130 (C-130J, KC-130J, MC-130H, Y-8), BigSlow (Cargo) (C-17, IL-76MD, An-26, AN-72P, Y-20, Y-20B, KJ-500, KQ-200).

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

### 3e. What the step's height is measured from, and the in-game LoS tool

The 15 units are added to the **map pixel height** (`MapPixel.Height`). The game does not use the rendered terrain. Pixels come from a baked map texture (`MapMetaData.ConvertPixel`, RVA `0x3CE610`). Each pixel holds a height and a terrain type (code).

That pixel height is not always the ground:

- Building pixels hold the roof height. The game has a separate "landscape" height that skips building pixels (`MapMetaData.GetInterpolatedTerrainHeight(..., includeBuildings, ...)` RVA `0x3CE880`; `FOWToolService.GetLandscapeHeightAt` RVA `0x6BC7C0`) (code).
- **Whether forest pixels hold the ground or the treetops is not verified.**

The in-game LoS tool (`FOWToolService.Filter`, RVA `0x6BBFB0`) runs the same model:

- the same `Height` / `Opacity` / `Multiplier` per terrain type;
- extra forest multipliers for drawing (`FOWToolConfig.MainLineForestVisibleMultiplier` `0xE0` and `GreenLineForestVisibleMultiplier` `0xE4`);
- `h` measured from the same pixel height (code).

Lateralus's screenshot (19 November) shows the tool's forest layer top at about two thirds of an 81 m helicopter height, about 27 world units above the ground. That is more than 15. If the tool draws its sticks from the landscape height to the pixel height + 15, the forest pixels would be about 12 units (24 m) above the ground, which is roughly treetop height. The forest layer would then reach about 15 units (30 m) **above the treetops**. This fits the observation but is **not verified**. Measuring pixel height against terrain height at forest points in a game would settle it.

The eye point (`UnitColliderCenter`) is read only by the vision code (`FogOfWarHelper.TryGetEntityEyePoint`, called from `FogOfWarUnit.AddFilterTasks` and `PreUpdate` and a debug drawer) and by the LoS tool (`FOWToolScript.InitializeUnitOptics` reads its height). No aiming, damage or hitbox code was found using it. This is from a scan of every function that fetches `FogOfWarComponent`; a whole-struct copy elsewhere cannot be ruled out entirely (code).

## 4. Firing: a stricter rule than seeing

`FogOfWarHelper.IsTargetShootable(FilterTask task, bool unitCheck)` (RVA `0x69EB30`) decides whether a unit may fire at a target (code):

1. If the unit's own sight line passed (`TargetVisible`, task `0x44`), it may fire.
2. Otherwise, when the target is seen by someone else on the team (the unit's visible set is not empty), it may fire only if:
   - its own line crosses **no smoke** (`SmokeTerrainDistance` ≤ 0.5, task `0x4C`); and
   - its own line has **at most `MaxShootableForestDistance` = 45 steps inside the forest layer** (`ForestTerrainSteps`, task `0x48`).
3. Otherwise it may not fire.

So a radar or another spotter can put an aircraft on the map, but a launcher whose own line runs through more than 45 world units (90 m on the card) of the forest layer still holds fire. The forest layer here is the same 15 units above the ground as in 3c. This rule ignores the target's height entirely. Only the stretch of the line that is low over trees counts (code; calculated meaning).

### Why the target's height is not the margin (calculated)

The forest layer is measured at every step of the line, from the ground under that step. The line starts at the launcher's eye, about 1–2 units up, and climbs slowly toward a distant aircraft. So a high aircraft far away still gives a line that is low over the trees near the launcher.

On flat ground, with the eye 1.5 units up and the target `H` above the launcher's ground at distance `D`, the line is inside the 15-unit layer for its first `13.5 × D / (H − 1.5)` units. Example: a forest belt starts 100 units in front of a Patriot and is 200 wide. Take a jet 100 units up (200 m on the card, the plane "low" order height):

| Jet distance | Line still in the layer up to | Forest steps | Fire at a team-spotted jet? |
| ---: | ---: | ---: | --- |
| 3,000 | 411 | 200 | no |
| 2,000 | 274 | 174 | no |
| 1,500 | 206 | 106 | no |
| 1,100 | 151 | 51 | no |
| 1,000 | 137 | 37 | yes |

In this example the Patriot can only fire once the jet is within about 1,050 units, even though the jet is 100 units up the whole time. A valley that puts the jet lower than the launcher's ground makes this worse. The physics ray in 3b also blocks a jet that is below a cliff edge.

## 5. Where the mod changes this

Freedom Arrow today changes only **Cover** for forest (3.0) and buildings (3.5), plus flash and spotted settings, through `DetectionConfig.cs` / `detection-config.json`. It changes no `Height`, `Opacity` or `Multiplier`, and no altitude thresholds (read from the mod source).

Ways to make AA placement easier (not implemented, not tested):

- **Lower the forest `Height`** (15 → e.g. 8–10) in the same `DetectionConfig` write, before `GenerateVisionData` copies the settings into `TerrainVisionData`. This moves the layer top closer to the visible treetops. It also changes ground vision through and over woods, for every unit.
- **Soften forest growth**: a smaller `Multiplier` (0.75) or a higher start (`Opacity` −15 → e.g. −30 gives 41 free steps). This also affects ground units.
- **Firing through woods**: raise `MaxShootableForestDistance` (45) in the same config write. Only units whose target is already spotted are affected, and this applies to every weapon.
- **Air-only rule**: a hook on `FogOfWarFilter.FilterCore` that uses a lower forest height when the target is a helicopter or plane. Ground vision stays unchanged. This needs code and a performance check, because the filter runs for every observer–target pair.
- **Plane altitude band**: `PlanesConfig.LowAltitude` / `HighAltitude` (100 / 400). This changes when planes count as Low, not the forest problem.

### 5b. Helicopter range and optics, and when the card shows the radar line

**Short answer:** each radar ability row is matched to a group in `UserData/FreedomArrow/helicopter-range.json`. While the radar is on, the group's `helicopterRangeMultiplier` replaces the low-altitude range multiplier against a helicopter, and `helicopterOpticsMultiplier` does the same for detection (every group is x1.25 today, Lateralus 21 Nov 2026). The detection bonus applies to every radar unit, so from 23 Nov 2026 (queued after 0.9.6-dev.6) the radar tooltip shows the helicopter lines for every unit with a radar (Lateralus: "its not only about extending their weapon range but also their optics range"). Before, it showed only for units with a weapon that can target helicopters (`heliUnits`).

**Radar tooltip shows range and optics (Lateralus 23 Nov 2026, queued after 0.9.6-dev.6):** vanilla lists only the range multipliers, so where a radar row's optics multiplier differs it was hidden (vanilla high altitude: SHORAD rows 58, 60, 62 and the China SHORAD-group rows optics x2.0 / range x1.0; long-range rows 59 and 123 optics x2.0 / range x3.0). The tooltip now shows three blocks, helicopter, low altitude and high altitude, each with its range and optics line. An optics = range build check was added and then withdrawn the same evening, once the tooltip showed both (Lateralus: "In that case just make the tool tip show both").

*Details (read from data and code, 23 Nov 2026; not checked in game):*
- `tools/pla-specs/lateralus/heli_range.py` `contract()` groups **every** row with `IsRadar` by the values the game copies into `RadarAbilityComponent`, so a new radar row gets a group by itself (rows with equal values must share multipliers; the build asserts this). `HeliRange.cs` finds the group from the live component.
- "Can target helicopters" = an ammunition used by the unit with `TargetType` flag `8`. Long-range SAM missiles have `TargetType` 1936 (no flag 8): S-300PM/V4, S-350, S-400, Buk M2/M3, IRIS-T SLM, and the China HQ-6A, HQ-9A, HQ-9B, HQ-11, HQ-12 and HQ-16. These units have the `Radar LongRange Static` row (59). Up to 0.9.6-dev.6 they had no tooltip line; the Patriots showed it only because of their M2 and M240 machine guns.
- China radar units (23 Nov 2026, codex/development 7e436b0f): SHORAD row 60 (HQ-7, HQ-7B, HQ-17, HQ-17A, HHQ-10, FK-2000, PGL-625, PGZ-04/04A/88/95); own rows in the SHORAD group (PGZ-09 and AFT-10 2009175, JRVG-1 2009943, LY-1 2019443); long-range row 59 (list above); ships row 70 `Radar LHA6`.
- Code: `HeliRangeCard.cs` `RadarGroup()` and the `SetUnitAbilities` postfix (the tooltip is built with `SetTraitItem` inlined).

### 5d. SA SHORAD, IR SHORAD and the radar icon label (Lateralus, 24 November 2026)

**Short answer:** radar-guided SAMs (a missile with `Seeker` 50 or 100 that can target planes) use rows 58/60/62 with low-altitude range and optics ×1.5. Units with only guns and/or heat-seeking missiles use their own "IR SHORAD" rows (range ×1.25, optics ×1.5). Helicopters stay ×1.25 on both. The card shows a label under the radar icon.

---

**Details** (`tools/pla-specs/lateralus/shorad_radar_1124.py`):
- **Why separate rows:** the game applies a unit's radar bonus to every weapon on the unit. `GetAmmoShootingDistance` (0x7D6330) and the search radius (`GetAmmoMaxShootingDistance`, 0x7D60C0) read only the round's five range fields, never its seeker. So a heat-seeking missile on a radar unit gets the bonus too. Read from the 1.2.2.1 code.
- **IR rounds on SA units** (AIM-9 on SLAMRAAM/NASAMS, Stinger on the Stryker M-SHORAD): compensated copies were tried and withdrawn on 24 Nov 22:0x (Lateralus). They now take the x1.5 SA radar like every other weapon on those units.
- **Burn time:** the radar-guided rounds of SA units burn longer so the catch range against a jet flying away at 225 grows by the same 20% as the range (calculated with the motor rules in `missile-flight.md`; not measured in a game).
- **Label:** `helicopter-range.json` radar groups carry `label` (SA / IR / LR) and `title` / `titleZh` (`heli_range.LABEL`, `heli_range.TITLE`). `HeliRangeCard.RadarLabel` swaps the card's radar icon (`InfocardConfig.Radar` sprite, `Ability_Radar`) for `FA_PLA_ABILITY_RADAR_SA` / `_IR` / `_LR` (`runtime-qa/icons`, seeded into `IconsLoader._sprites` by `ChinaUi.Seed`): the vanilla glyph with the letters cut out of the dish (Lateralus 24 Nov 20:2x: a text tag was still cut off at the card edge); the radar tooltip's title becomes "SA SHORAD Radar", "IR SHORAD Radar" or "Long-Range SAM Radar" (`TooltipData.TitleLocKey`). Both are picked by the radar values in `ActiveAbilities`. A first version put "SA SHORAD" under the icon; it was too big, ran off the card edge and covered the next ability (Lateralus, 24 Nov 18:4x). Ability rows have no icon field; the LSDW laser icon is done the same way (`Dazzler.cs`). The battle order button has no label yet.
- **Not verified in a game:** the label's position on the card, and all ranges above.

### 5e. Per-weapon radar use (Lateralus, 24 November 2026)

**Short answer:** on a radar unit, these rounds get **no** radar range bonus: Stinger, Igla-S, QW-2 (PGZ-95 / PGZ-04 / PGZ-04A), the Fletcher APKWS (laser) and machine guns (M2 12.7 mm, M240 7.62 mm; Lateralus 25 Nov). Everything else, including the AIM-9, the RIM-116 SeaRAM and HHQ-10 (both on SA radar from 25 Nov), the Hellfire SHORAD, the HJ-10, the LY-1 laser, the SM-6 and the M61 CIWS, keeps the radar. On the unit card, a weapon that uses the radar shows a plain radar icon in its trait row.

---

**Details:**
- **Lists:** `helicopter-range.json` `radarExempt` and `radarAmmo`, built by `tools/pla-specs/lateralus/radar_weapons_1124.py`. The rule is "every Seeker 10 round on a radar unit, except AIM-9 465, plus Fletcher 501"; the build checks the list is exactly these 8 rounds.
- **Range:** `HeliRange.Exempt` runs in the existing `GetAmmoShootingDistance` postfix. With the shooter's radar on, it recognises the radar term in the game's value (aircraft R × m; missiles 1.0 × R × m × m; fixed override v × m, e.g. HHQ-10 SEAD 1100) and replaces it with the value without radar. Helicopters get the round's helicopter range × 1. Ground targets and a switched-off radar are untouched.
- **Search radius:** not hooked. It only bounds the target search; each candidate still passes the per-target range above. So an exempt round may consider targets out to the radar-boosted radius but only fires within its own range.
- **Card:** `HeliRangeCard.WeaponTraitAfter`, a postfix on `UnitInfoCard.OnWeaponButtonSelected` (0x55B140), calls the game's `SetTraitItem` (0x55D4D0) with `InfocardConfig.Radar` and a tooltip with the unit's Low / High / helicopter multipliers. Weapons are matched to rounds by `WeaponListButton.TotalAmmoCount`.
- **Cost:** the check is one set lookup inside a hook already measured at 0.2–0.5 µs per call (22 Nov logs); the perf log line now also counts `radar-exempt` changes.
- **Not verified in a game.**

**Card icon wrong in 0.9.7-dev.13 (Lateralus, 25 November 2026).** The range lists were right; the card icon was wrong on 96 of 168 anti-air weapons of the 72 radar units. Two causes, both in the card hook:
- **The game hides the trait row.** `OnWeaponButtonSelected` (0x55B3F0–0x55B43E, code, 1.2.2.1) calls `_selectedWeaponTraits` (0x1A0) `.gameObject.SetActive(t)`, where `t` = AutoLoaded (0x48) or Silent (0x49) or CQC (0x4B) or IsRadarDependent (0x4C) or not CanShootOnTheMove (0x64). A weapon that fires on the move and has no other trait has a hidden row, so the icon our postfix adds is never seen. This hid it on 93 weapons that should show it (guns, Tor, HQ-17A, FK-2000, Hellfire SHORAD, ship SM-6 / CIWS).
- **`TotalAmmoCount` is not the selected weapon's rounds.** In the dev.13 log the PAC-3 MSE launcher listed `32,25,26,454,262,497` (Bradley, M-SHORAD and C-RAM rounds from earlier cards), and the M-SHORAD Stinger and M240 buttons listed the same `18,27`. The decision was nearly always "uses radar", so every weapon with a visible row showed the icon: Fletcher, MML Stinger and HHQ-10 (all must stop to fire).
- **The hook also went quiet** after the second Stryker M-SHORAD card at 09:23:09: no line for the 15 China cards opened afterwards. Its silent early returns (`_activeWeaponListButtons` null, no button matching the clicked object) are the likely place; not confirmed.
- **Vanilla has an unused per-weapon radar trait.** `Weapons.IsRadarDependent` (0x4C, a `weapons` column, set on 0 of 750 weapons), its own sprite `InfocardConfig.RadarDependent` (0x178) and text `ui_infocard_weapon_radar_dependent` (`TextWeaponIsRadarDependent`). Its getter (0x279250) is shared with 7 other getters and has no direct callers, so whether battle code reads the flag is not known.
- Full list: `work/radar-weapons-1124/full-audit-dev13.txt` (BA Codex work folder).
- **Radar only on loadouts with a radar weapon (Lateralus 25 Nov 09:17, queued after 0.9.7-dev.14).** A unit gets its one default ability row plus, per slot Ability1/2/3, the first chosen option's non-default row, so a per-loadout radar sits on the turret options (the M6 Linebacker pattern). Stryker M-SHORAD: SA radar 62 in slot 3 of the Stinger pod / Fletcher / Hellfire turrets, none on the M2 + Stinger turret. C-RAM: Phalanx IR 2021462, SeaRAM SA 62. MML: a new non-default copy of the static IR row on the AIM-9 and Hellfire turrets, none on the Stinger turret. HHQ-10: IR -> SA 60. Build check `radar_loadouts_1125.check`: every radar loadout must carry a radar weapon (it found these 6 loadouts on the dev.14 data).
- **Fix (0.9.7-dev.14):** the build writes `radarWeapons` (weapon ids) and checks that no weapon on a radar unit mixes radar and exempt rounds; the card decides by the selected weapon's id, switches the trait row on after adding the icon, and logs every early exit (`radar trait ...`, first 80).
- **Measured in 0.9.7-dev.14 (Lateralus's Skirmish log, 25 Nov):** the per-weapon range works in battle (`FREEDOM_ARROW_HELI_PERF` counted 285 and 372 radar-exempt range corrections per minute); the MML Stinger did not fire at 2465 m on an AH-64D.
- **Targeting reticle (rangefinder) did not follow it.** `TargetLineSystem.RefreshLocalTargetInfo` (0x4A6000, code, 1.2.2.1) does not call `GetAmmoShootingDistance`: it takes the target level's range (ammo +0xB0 / +0xB4 / +0xB8) x the shooter's radar modifier (+0x14 / +0x18) inline, and marks a round out of range when the distance is greater (0x4A6D89-0x4A6E05). So it ignored both the helicopter range and the radar exemption (MML Stinger: 1000 x 1.25 = 1250, shown as 2500 m, instead of 1000 / 2000 m). Fix queued: `HeliRangeReticle` postfix recomputes each round's max range with `GetAmmoShootingDistance` and resets the out-of-range flag. Rounds are matched by weapon + round name; not yet seen in game.

### 5c. Which optics value is the big number on the unit card

**Short answer.** The vanilla card shows **ground** optics for every unit except planes, which show **high-altitude** optics. Helicopter cards are no exception. Until 0.9.6 the FA card code showed **low-altitude** optics on helicopter cards, so a helicopter showed a higher number than the recon copy of the same helicopter with the same sensor. For example, the AH-64D Longbow showed 3200 m and the AH-64D Longbow Recon 2400 m (Lateralus, 23 Nov 2026). Fixed for the next build: the FA card now follows the vanilla rule. Helicopters show ground, planes show high altitude, and drones show whatever their category gets.

- **Vanilla (code, 1.2.2.1).** `UnitInfoCard.SetUnitStatistic` (`0x55F870`) takes the best sensor value with three selectors: ground (`Sensors +0x24`), low altitude (`+0x2C`) and high altitude (`+0x28`). The tooltip lists all three. The big number is the ground value, but high altitude when `CategoryType == Aircrafts (6)` (`cmp [unit+0x80], 6` at `0x5603C6`).
- **FA (`SpottingCap.CardAfter`).** It rewrites the number with the spotting cap on the ground value. From 0.4 dev.19 (`c10711a7`) it used the low-altitude value for `CategoryType == Helicopters (5)`. The comment there assumed that vanilla did the same; the code above shows that it does not. Recon helicopters are `CategoryType` Recon (0), so they always showed ground.
- **The tooltip was right before and after:** ground (capped), helicopter, low altitude and high altitude.
- **Planes (fixed the same day, Lateralus).** `CardAfter` also wrote the ground value on plane cards, so a plane with ground optics 0 showed "0 m" (for example the Mirage 2000D in the 23 Nov log). Plane cards (`CategoryType` Aircrafts) now show high-altitude optics, uncapped, as vanilla does. Example: the Mirage 2000D raw high 8000 shows 16000 m.
- **Drones (data, 0.9.6-dev.8).** 15 drones are `CategoryType` Recon (0), for example the MQ-9, RQ-4, Orion, Wing Loong, GJ-11, X-47B and Z-6B. They show ground optics like vanilla. FA raised their raw ground optics, and the spotting cap brings the card number back to the vanilla value: the MQ-9 has raw 5250, cap 2250, and shows 4500 m, the same as vanilla's 2250 × 2. 4 drones are `CategoryType` Aircrafts: the J-5 Drone, J-6W Drone, FH-97A and XQ-58A. They show high altitude, like planes.

## 6. Not verified

- **Optics selection:** the exact code that picks `DistanceLowAlt` / `DistanceHighAlt` from the target's state, and any stealth, flash or spotted multipliers on it, is inferred, not traced.
- **Map grid:** the terrain-grid cell size per map (`MapMetaData`), and so how many grid cells one world-unit step crosses on each map.
- **Visible tree heights:** no tree heights were measured in a map, so the margin above the visible trees is not quantified in metres.
- **Helicopter heights:** actual helicopter flying heights were not read, so the worked example's 25 units is an example, not game data.
- **A grid flag:** the meaning of the cell flag `0x2` that skips the cost within 45 units (`MinimumDetectionDistance`) when the target is close.
- **In game:** none of this has been measured in a match.

## Document change log

- 2026-11-19 09:2x PST (America/Los_Angeles) — New doc: low altitude, air optics and line of sight (Lateralus's request).
- 2026-11-19 09:5x PST (America/Los_Angeles) — Added pixel-height base, LoS tool model and the UnitColliderCenter reader scan.
- 2026-11-19 09:3x PST (America/Los_Angeles) — Traced the firing rule (IsTargetShootable: own line visible, or team-spotted with ≤45 forest-layer steps and no smoke); added the line-height example.
- 2026-11-22 18:5x PST (America/Los_Angeles) — Added section 1b: who sets a plane's flight altitude (hotkey pending rule, precision-strike climb to HighAltitude), from the altitude-arrow investigation.
- 2026-11-22 19:2x PST (America/Los_Angeles) — Section 1b: strafe, bombing and attack-order runs (`AirAttackComponent`) added beside precision strikes.
- 2026-11-23 16:3x PST (America/Los_Angeles) — Added section 5b: helicopter range radar groups and when the card shows the radar line (Lateralus asked about the HQ-11 tooltip).
- 2026-11-23 16:2x PST (America/Los_Angeles) — Section 5b: radar line for every radar unit; optics = range build check and the pending rows.
- 2026-11-23 16:4x PST (America/Los_Angeles) — Section 5b: tooltip shows range and optics per altitude; optics = range build check withdrawn.
- 2026-11-23 18:4x PST (America/Los_Angeles) — Added section 5c: card optics headline (vanilla ground, planes high; FA helicopter branch removed), from Lateralus's AH-64D / Recon screenshots.
- 2026-11-23 18:5x PST (America/Los_Angeles) — Section 5c: planes show high-altitude optics (Lateralus); drone categories and values.
- 2026-11-24 17:0x PST (America/Los_Angeles) — Added section 5d: SA / IR SHORAD radar rows, IR round copies, burn times and the card radar label (Lateralus).
- 2026-11-24 18:5x PST (America/Los_Angeles) — Section 5d: radar label is now a short SA / IR / LR tag in the icon corner; tooltip titles per radar type (Lateralus).
- 2026-11-24 20:3x PST (America/Los_Angeles) — Section 5d: radar type shown as letters cut out of the radar icon instead of a text tag (Lateralus).
- 2026-11-24 22:1x PST (America/Los_Angeles) — Section 5d: AIM-9 / Stinger copies withdrawn (Lateralus).
- 2026-11-24 22:4x PST (America/Los_Angeles) — Added section 5e: per-weapon radar use and the card's radar trait (Lateralus).
- 2026-11-25 07:42 PST (America/Los_Angeles) — Section 5e: why the dev.13 card radar icon was wrong (hidden trait row, pooled round list), and the unused vanilla IsRadarDependent trait (Lateralus).
- 2026-11-25 07:57 PST (America/Los_Angeles) — Section 5e: machine guns exempt from the radar; card fix for 0.9.7-dev.14 (Lateralus).
- 2026-11-25 08:22 PST (America/Los_Angeles) — Section 5e: dev.14 battle measurement; the targeting reticle computes range inline (fix queued) (Lateralus).
- 2026-11-25 09:21 PST (America/Los_Angeles) — Section 5e: radar only on loadouts with a radar weapon; HHQ-10 and SeaRAM use SA radar (Lateralus).
- 2026-11-25 22:3x PST (America/Los_Angeles) — Added section 1c: spawn altitude, fly preset override and low-default, and who writes `PlaneHighAltOverride` (Lateralus).
