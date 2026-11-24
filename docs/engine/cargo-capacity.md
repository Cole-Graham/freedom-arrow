# Cargo capacity: supply trucks and heavy-lift helicopters

**Short answer.** A unit's cargo capacity is `MobilityJson.HeavyLiftWeight` on the mobility row that the unit uses. A supply truck loads supply up to that number. A transport helicopter uses the same number for the vehicles it carries, and the supply and the carried vehicles share it. No ability or prefab sets it.

Which mobility row the unit uses depends on two things:
- **`UnitPropulsionsJson`** links the unit to its mobility rows.
- **The armory options:** an option with `MobilityId` ≠ 0 replaces the unit's mobility, and so also its cargo.

To change the cargo, change `HeavyLiftWeight` on the row the unit actually uses, after you check the options and which other units share that row.

Source: the 1.2.2.1 game code (`work/game-1.2.2.1/GameAssembly.dll`, il2cpp dump `work/port-1.2.2.1/il2cppdump/dump.cs`) and the 0.9.6-dev.6 package data. Nobody has measured the loaded amount in a game for this doc.

---

## Why changing the Shaanxi HMV3 Cargo took three tries (8–14 Nov 2026)

Osama asked for "Shaanxi HMV3 cargo should be 15000 max cargo" on 14 Nov 2026 ([message](https://discord.com/channels/1566969627743879208/1571014792016171120/1571067969650561098)). On 8 Nov he had asked for LMTV 4000 cargo. Both requests failed for reasons that were mistakes in the investigation, not limits of the game.

1. **8 Nov, LMTV 4000: wrong conclusion that the value is not in the data.** The cargo field is not in the `Units` row or in any ability row, and the search stopped there. The report said that "the game doesn't keep truck cargo in the data I can edit" ([message](https://discord.com/channels/1566969627743879208/1568809413958176912/1568824242798207099)). Osama then dropped the LMTV change. The field was on the **mobility** row all along.
2. **12 Nov, Build 66: the wrong pool.** A later search took the resupply ability (`AbilitiesJson.ResupplyPoints`, vanilla Light 250 / Medium 400 / Heavy 800) as "vehicle cargo" ([message](https://discord.com/channels/1566969627743879208/1567745029781454889/1570533939364241449)). Build 66 (PLA branch, `af0c0ed8`) gave the HMV3 Cargo a resupply ability with 15000 points. That is a separate supply pool (`ResupplyAbilityComponent.MaxSupplyPoints`) that an IFV-style unit hands out to units near it. It does not change how much supply the truck loads. So the truck still loaded the HEMTT amount.
3. **14 Nov 07:59: a third wrong conclusion.** The cargo was said to "come from the HEMTT vehicle model" and to need a code patch ([message](https://discord.com/channels/1566969627743879208/1571014792016171120/1571071997847535738)).
4. **14 Nov 08:34: the real mechanism** ([message](https://discord.com/channels/1566969627743879208/1571014792016171120/1571080776647319615)). The shop caps the loaded supply at `Units.HeavyLift`, which is `CurrentMobility.HeavyLiftWeight` (code below).
5. **14 Nov 08:36: the actual bug** ([message](https://discord.com/channels/1566969627743879208/1571014792016171120/1571081422960328816)). The HMV3 Cargo (unit 1247) already had the right mobility of its own: row 65 `Wheels LVSR` (the PLS), with `HeavyLiftWeight` 15000. But it had been made as a copy of the HEMTT, and so it had the HEMTT's two armory options:
   - "Flatbed multipurpose" (default) with `MobilityId` 108, `Wheels HEMMT Flatbed`, 9000.
   - "Armored troop transport" with `MobilityId` 231, `Wheels HEMMT Armored`, 4500.

   Whichever option was chosen, it replaced the unit's mobility. So the truck always loaded 9000 or 4500, and the 15000 on its own row never applied. The fix in 0.8.0-dev.101 (`e3384117`, script `archive/tools/pla-specs/apply_0_8_dev101.py`) set `MobilityId` to 0 on both options (options 24379 and 24380). The vanilla PLS has no such option either. The 15000-point resupply ability from Build 66 was removed in the same build.

**In one sentence:** the value was correct on the unit's own mobility row, but options copied from the HEMTT replaced that row. Before that was found, the investigation had looked for the value in the wrong places (unit row, abilities, prefab).

---

## How cargo works

### Data (tables)

- **`MobilityJson`**
  - `HeavyLiftWeight`: the cargo capacity. 0 means no cargo.
  - `Weight`: a different number (vanilla values 0–4000). The shop does not use it for cargo; see `Units.Weight` below.
  - Other fields are speeds, turn rate and so on. One mobility row can serve many units.
- **`UnitPropulsionsJson`** (`Id`, `UnitId`, `MobilityId`): the mobility rows a unit can use. Most trucks have two, a flatbed row and an armored row. For example, HEMTT 242 has 108 (9000) and 231 (4500).
- **`OptionsJson.MobilityId`** (armory option, through `ModificationsJson` → `UnitId`):
  - ≠ 0: when this option is chosen, the unit uses that mobility row, and so its `HeavyLiftWeight`.
  - 0: the option does not change the mobility.
  - Vanilla trucks put their armor choice on a "Custom_Slot_Armor" modification. For example, the HEMTT has option 586 Flatbed → 108 and option 587 Armored → 231.
- **Not cargo:** `AbilitiesJson.ResupplyPoints` (resupply ability) and the truck prefab. Seats are a separate limit (`InfSlotLimit` from `Units.GetInfantrySlots`). None of these sets the truck's supply load.

### Code (1.2.2.1)

- **`Units.get_HeavyLift`** (`0x2A2E20`): `return CurrentMobility?.HeavyLiftWeight ?? 0`.
  - It reads `Units.CurrentMobility` (`+0xE8`) and then `Mobility.HeavyLiftWeight` (`+0x30`).
  - `Units.get_Mobility` (`0x1B8820`) returns the same `CurrentMobility` field. The other mobility rows of the unit are in `Units.Mobilities` (`+0x120`).
- **`OrderedUnit..ctor(Units, IDeckSlotModel)`** (`0x371540`): when a unit is ordered in the shop, `HeavyLiftLimit.Max` = `Units.get_HeavyLift()`, and `InfSlotLimit.Max` = `GetInfantrySlots()`.
- **`OrderedUnit.AddSupply(ref int)`** (`0x3711B0`):
  - `left = max(0, HeavyLiftLimit.Max − HeavyLiftLimit.Current)` (`+0x34 − +0x30`).
  - The supply added is `min(requested, left)` (`IntClampMax`).
  - `HeavyLiftLimit.Current` grows by that amount.
- **`OrderedUnit.TryAddCargo((slot, Units))`** (`0x3713A0`):
  - **Seats:** for an infantry passenger (see Passengers below), it refuses the squad when its soldier count (`SquadMembers`) + `InfSlotLimit.Current` > `InfSlotLimit.Max` (`+0x38` / `+0x3C`).
  - **Weight, for every passenger:** if `HeavyLiftLimit.Max` > 0, it refuses the unit when `carried.Weight` (`Units.Weight`, `+0x94`, the `Weight` column of the `Units` table) + `Current` > `Max`. Otherwise it adds the weight to `Current`. Vanilla vehicles weigh 1000–27000 (HEMTT 21000, BTR-82 15000, Humvee 4000). Every vanilla infantry squad weighs 1.
  - So supply and carried vehicles take from **one** weight budget. A helicopter with a vehicle on board has less room for supply.
- The 1.2.2 build had the same logic at `0x2A3670` / `0x371DE0` / `0x371A50` / `0x371C40`. The addresses moved in 1.2.2.1; the method names did not.

### Which row is "current"

- **From the data and the HMV3 fix:** an option with `MobilityId` ≠ 0 decides the mobility row. If every chosen option has `MobilityId` 0, the unit keeps its own row (the HMV3 Cargo after dev.101).
- **Not traced in code:** exactly which row becomes `CurrentMobility` when none of a unit's options sets a mobility and the unit has more than one propulsion row. In vanilla, the flatbed rows have `IsDefault` = true. This doc does not prove whether the game always uses that flag.
- **Not checked:** whether an option's `MobilityId` must also be one of the unit's `UnitPropulsionsJson` rows. Vanilla always lists it. The FA Shaanxi SX2306 (below) does not.

---

## Passengers (seats) are not on the mobility row

**Short answer.** Seats are `Units.InfantrySlots`, a column of the transport's own `Units` row. The mobility row and the armory options do not change them. A squad needs one seat per soldier. Read from the 1.2.2.1 code and the vanilla tables; not measured in a game for this doc.

- **Data.** `UnitsJson.InfantrySlots`. Vanilla examples: HEMTT 27, KamAZ-6560 32, Ural-5323 24, MTVR 21, MTV 18, Ural-4320 16, LMTV 14, LVSR and M1075A1 PLS 0, CH-47 32, Mi-8MTV-5 21, Mi-26 85. `MobilityJson` and `OptionsJson` have no seat field, so a truck's Flatbed and Armored options have the same seats.
- **Code.** `Units.GetInfantrySlots` (`0x2A2520`) returns `InfantrySlots` (`Units +0x9C`). It returns 0 when the unit is itself infantry: `Type` Infantry (2), or `CategoryType` Infantry (1), or `CategoryType` Recon (0) with squad members. The shop sets `InfSlotLimit.Max` from it (`OrderedUnit..ctor`).
- **Which passengers use seats.** `TryAddCargo` checks seats for the same three cases (infantry type, infantry category, recon with squad members). It counts the squad's `SquadMembers` rows, one per soldier.
- **Passengers also use a little weight.** Each passenger also adds its `Units.Weight` to the heavy-lift budget when the transport has one. Infantry weighs 1, so a full truck of infantry uses about 1 of thousands.
- **To change seats:** edit `InfantrySlots` on the transport's `Units` row. Unlike mobility rows, a `Units` row belongs to one card. Copies made from it (for example the FA KamAZ-6560 Cargo, 0 seats) have their own value.

---

## How to change a unit's cargo

1. **Find every row the unit can use:**
   - its `UnitPropulsionsJson` rows (`UnitId` → `MobilityId`);
   - every armory option of the unit (`ModificationsJson.UnitId` → `OptionsJson.ModificationId`) with `MobilityId` ≠ 0.
2. **Decide which of those rows should change.** Usually that is the row of the default (flatbed) option and the unit's own propulsion row. A different value for the armored option is a separate decision.
3. **Check whether other units share the row.** Search `UnitPropulsionsJson` and `OptionsJson` for the same `MobilityId`.
   - **Not shared:** set `HeavyLiftWeight` on it.
   - **Shared, and the others must not change:** add a copy of the row with the new `HeavyLiftWeight` (`g.add('MobilityJson', MB[row], {'Name': ..., 'HeavyLiftWeight': N})`). Point only this unit's propulsion row and options at the copy. New rows must match the vanilla fields exactly (see the PLA RowPlanner rule).
4. **Or keep the unit's own row:** set the options' `MobilityId` to 0. That was the HMV3 Cargo fix.
5. **To remove cargo** (for example on gunship helicopters): use a copy of the mobility row with `HeavyLiftWeight` 0. Examples: Z-19 "PLA Heli Z-19 no cargo" 2018990 (0.8.0-dev.101 / 0.9.0-dev.14), Z-9WA and Z-20S (0.9.2-dev.1).
6. **Add a build check** that reads the value back from the package. The HMV3 check in `apply_0_8_dev101.py` is an example: `MB[65]['HeavyLiftWeight']==15000` and both options have `MobilityId` 0.

### Rows to watch (0.9.6-dev.6)

- **Row 65 `Wheels LVSR` (15000)** is shared by the LVSR (164), the M1075A1 PLS (241) and the HMV3 Cargo (1247). Changing it changes all three.
- **Row 41 `Wheels KAMAZ6560` (12000)** and **row 303 (6000)** are shared by the KamAZ-6560 (95) and the FA KamAZ-6560 Cargo (739).
- **Shaanxi SX2306 (1235, "PLA Shaanxi HMV3"), the same trap as before:**
  - Its own propulsion row is the FA copy 2015812 (`Wheels HEMMT Flatbed`, 9000).
  - But its two armory options still point at the vanilla HEMTT rows: 24374 Flatbed → 108 (9000, default) and 24373 Armored → 231 (4500).
  - So editing 2015812 alone does nothing in a game. Today both rows say 9000, so the card is correct, but the trap is still there.

### Values in 0.9.6-dev.6 (from the package data)

Trucks:
- **US:**
  - LVSR, M1075A1 PLS 15000
  - HEMTT 9000 / armored 4500
  - MTVR 6000 / 3000
  - MTV 4500 / 4500
  - LMTV 2000 / 2000
- **Russia:**
  - KamAZ-6560 and KamAZ-6560 Cargo 12000 / 6000
  - Ural-5323 8000 / 4000
  - Ural-4320 4000 / 2000
  - KamAZ VDV 3000
- **China:**
  - Shaanxi HMV3 Cargo 15000
  - Shaanxi SX2306 9000 / 4500
  - Shaanxi SX2220 and SX2220 Troop Truck 12000
  - Shaanxi SX2121 4500

Helicopters:
- Mi-26 20000
- Z-8L 16000
- CH-47 12500
- Mi-8MTV-5, Mi-8MTV-2, Mi-8 Cargo, Z-20, Z-20J 4000
- Mi-8AMTSh 3000

Recipe: `work/cargo-doc-20261123/survey.py <gameplay .bamod> <vanilla tables> <out.json>` lists every unit with cargo and its rows. The script is outside the repo.

## Document change log

- 2026-11-23 17:1x PST (America/Los_Angeles) — New doc (Lateralus asked why Osama had trouble changing cargo capacity and how it is configured). Why the HMV3 Cargo change failed, the 1.2.2.1 code path with RVAs, how to change it, shared rows and the Shaanxi SX2306 trap, current values.
- 2026-11-23 17:0x PST (America/Los_Angeles) — Added "Passengers (seats)" (Lateralus asked whether passengers are part of the mobility row: no, `Units.InfantrySlots`). Corrected the weight that carried units use: `Units.Weight`, not `MobilityJson.Weight`.
