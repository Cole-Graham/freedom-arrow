# Transports and unit-swap loadouts

**Short answer.** The game does not support a unit-swap loadout (an option with `ReplaceUnitId`) on a unit that is used as a transport. The deck slot builds the main unit with `DeckSlotModel.GetUnitData`, which follows the swap to `Units.ReplaceUnit`. It builds the transport with `DeckSlotModel.GetTransportUnitData`, which does not follow it. So the shop counts the transport as the base unit, and the unit on the map is the swap unit. The two do not match.

Vanilla never does this. 53 of the 54 vanilla transport units have armory options, and every one of those options has `ReplaceUnitId` 0. They change `Turret0Id`, `ArmorId`, `MobilityId`, `MainSensorId` and `Ability1Id`–`Ability3Id` on the same unit instead. For example, the Stryker ICV "M2 HMG + Javelin" (+30) is a `Turret0Id` option, and the M2A3 Bradley Iron Fist APS (+25) is a type-6 protection option.

Source: the 1.2.2.1 game code (`work/game-1.2.2.1/GameAssembly.dll`, il2cpp dump `work/port-1.2.2.1/il2cppdump/dump.cs`), the vanilla tables and the 0.9.7 package data. The link from this mismatch to the reported symptoms is theoretical, not yet proven in a game.

---

## The case: Type 100 CSV (0.9.5 to 0.9.7)

In 0.9.7 the Type 100 CSV is only a transport. Unit 1416 is linked as a transport to 6 spec-18 cards (HJ-8E Team, QW-2 Team, QLZ-04 Team, Armored Scouts, Armored Sniper Pair, Forward Observers). Its loadout slot (modification 2020833, type 3) swaps the unit:

- Option 31360 "40 mm CT": `ReplaceUnitId` 1416.
- Option 31361 "40 mm CT + GL-5 APS", +40: `ReplaceUnitId` 1417.
- Option 31362 "9x CH-901", +60: `ReplaceUnitId` 1418.
- Option 31363 "9x CH-901 + GL-5 APS", +100: `ReplaceUnitId` 1419.

It is the only transport with unit swaps in vanilla or FA. Players reported the same availability bug on 0.9.5b, 0.9.6 and 0.9.7 (amok, Legendarybox, Distortion, SteelPlate, Nahcane, reported by Osama on 26 Nov 2026):

- The shop shows 0 left while the deck still has cards; one player with 2 cards saw 0 at the start of the match.
- A lost Type 100 is not replaced.
- It happens with one slot and one loadout.

SteelPlate's 0.9.7 log (`2026-11-26/76561199079463027/20261126-071728-4bba25`, Cold Harbor 4v4) shows one of his Type 100s (unit 1418, the CH-901 loadout) on the map from t = 244 s until it died at t = 2051 s. He had no second one up to the end of the snapshots at t = 2966 s. The log does not show his deck count.

The 24 Nov fix (`e28c7a7c`: the swap rows took the base `CategoryType`) was in 0.9.7, and the bug was still reported. So the category was not the cause.

## The code

`DeckSlotModel` keeps two cached units: `_loadedUnit` (0x40) and `_loadedTransportUnit` (0x48).

- `GetUnitData` (RVA 0x6EE6D0) calls `UnitsInfoService.CreateUnit(slot)`, which builds `UnitID` with `ModList`. If the result has `ReplaceUnit` (`Units` 0x110), it caches and returns `ReplaceUnit`.
- `GetTransportUnitData` (RVA 0x6EE650) calls `UnitsInfoService.CreateUnitAsTransport(slot)`, which builds `TransportID` with `TransportModList` and sets `OwnerInfantryID` (`Units` 0x40) to the slot's `UnitID`. It returns that unit. It does not read `ReplaceUnit`.

`Units.Equals` (RVA 0x2A22D0) compares `Id`, then `OwnerInfantryID`, then the applied options. So the transport card's unit (1416, owner = the infantry card, option 31362) and the swap unit (1418) are never equal.

The shop uses `Units` as the key in several places:

- `UnitStatistic.AddUnit` / `RemoveUnit` (Dictionary<Units, int> per player). `SpawnCommand.UpdateUnitStatistic` adds `IOrderedUnit.GetUnitData` and each cargo unit.
- `UnitStatistic.UnitUpdateEvent` → `ShopPanelUI.OnUnitUpdate` (RVA 0x37F4D0). It finds the first shop card whose unit, or whose transport, equals the event's unit and calls `ShopCardUI.SetUnitsOnMap(count)` on that card only.
- `ShopCardUI.SetUnitsOnMap` (RVA 0x379B70): left = total − on map − `DeckSynchronizer.GetPendingUnitCount(unit)` − `SpawnCommandWorker.GetInProgressCount(unit)`. The total is `TransportCount` when the card's unit has `OwnerInfantryID` > 0, else `Count`.

Because one side of these lookups uses the base transport unit and the other side can use the swap unit, the counts for a swapped transport can go wrong. Which exact path gives "0 left" was not traced to the end.

## How to give a transport loadouts

Use the vanilla pattern: options on the same unit, `ReplaceUnitId` 0.

- Weapons: a type-3 weapon-package option with `Turret0Id`.
- APS or jammer: a type-6 protection option with `Ability1Id`–`Ability3Id` (and `Turret0Id` if the turret changes).

On the US_M2A3 (Bradley) body, two FA turret rows that do not fill all 3 Bradley weapon slots fail with "Couldn't load unit" (see the 22 Nov notes on the ZBD-100). Options that point at turret rows with 3 weapons each, and one turret plus an APS-only option slot, loaded. Test a new transport loadout in the Arsenal on a test PC before it ships, and read `GameLogs`, not only the MelonLoader log.

## Document change log

- 2026-11-26 01:26 PST (America/Los_Angeles) — New page: transport unit-swap mismatch, from the Type 100 CSV availability reports.
