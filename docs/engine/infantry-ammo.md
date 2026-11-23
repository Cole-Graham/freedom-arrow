# Infantry ammunition: `WeaponAmmunitions.Quantity`, carriers and the card number

**Short answer.** A squad has one ammunition pool for each weapon. The pool is `WeaponAmmunitions.Quantity` × the number of soldiers who carry that weapon. The Arsenal card shows the pool × `Ammunitions.HUDMultiplier`. Read from the 1.2.2.1 code (`work/game-1.2.2.1/GameAssembly.dll`) and checked against one card in the game (below).

---

## Details

- **Data (code).** `LoadUnits.LoadAmmunitions` (`0x285C10`) puts each `WeaponAmmunitions` row (unit + weapon + ammunition) into the weapon's dictionary: `AmmunitionId → Quantity`. There is no multiplier at load time.
- **Battle (code).** `UnitBuilder.InfantryRecalculateAmmo` (`0x343A40`):
  1. For each weapon of the squad, it calculates `Quantity × soldiers carrying that weapon` (`imul` at `0x343D78`). Primary and special weapons both count. It adds the result into one entry per ammunition type (`AmmoAndSoldier`).
  2. It sets the weapon's `AmmunitionContainer` maximum to that total (`OverrideMaxAmmo`). The current amount is the total × the spawn ammo percent when that is below 100 (`OverrideAmmo`).
  3. The amount per soldier is the total ÷ the carriers (`GAInt` division, `0x34412C`). `InfantryDeathHealSystem.RecalculateSoldierWeaponAmmo` (`0x40DA10`) recalculates it when soldiers die or heal.
- **Arsenal card (code).** `UnitInfoCard.SetUnitWeaponList` (`0x561900`) groups the squad's weapons by weapon Id. The group size is the `xN` on the weapon button. `WeaponListButton.Init` (`0x57B450`) adds up `Quantity` over the group, which gives the same `Quantity × carriers`. `AmmoInfoExpansionPanel.Init` (`0x53D400`) shows that × `Ammunitions.HUDMultiplier` (field `+0x30`, `imul` at `0x53D9FC`).
- **HUDMultiplier values (data).** Vanilla: 1 on 527 ammunition rows, 3 on 53 (including MP5SD6 9x19mm, ammo 341), 5 on 14, 10 on 13, and others. The FA QCW-05 ammunition 2013350 copies ammo 341, so it is 3. QBU-191 ammunition 2004001 is 1.
- **Checked in the game (Lateralus, 22 Nov 2026, 0.9.4 card).** Beijing Swords (1187) QCW-05 showed `x2` and `x120`. Calculated: Quantity 20 × 2 carriers × HUDMultiplier 3 = 120.
- **Consequences.**
  - Equal `Quantity` means equal ammo per carrier. Card numbers are equal only when the carrier count and the HUDMultiplier are also equal.
  - Not checked: whether the in-battle HUD also multiplies by `HUDMultiplier`, and how many rounds one ammo unit fires.

## Rate of fire on the card

- **Formula (code).** `WeaponHelper.RateOfFireSecond` (`0x2BCE50`) gives rounds per second. The card shows it × 60. Calculate a cycle time for the minimum values and one for the maximum values, then use the average of the two: `MagazineSize ÷ ShotsPerBurstMax − 1` gaps × `TimeBetweenBursts` + `(MagazineSize − MagazineSize ÷ ShotsPerBurstMax)` × `TimeBetweenShotsInBurst` + `MagazineReloadTime`. The rate is `MagazineSize ÷` that average cycle.
- **Infantry cards (data + card).** Rifles show that rate × the ammunition's `HUDMultiplier`. The MP5SD6 is 15 × 3 = 45, and the QCW-05 card showed the same 45. The FA runtime (`CardLauncherRof`) changes only launcher cards.
- **Examples (calculated).** 5 rounds, 1 per burst, 4 s reload: DXL-4 (bursts 7.375–9.375 s) is 8.0 per minute, OSV-96 (11–12 s) is 6.0. Lateralus 22 Nov: the two swap their burst intervals, so the DXL-4 becomes 6 and the OSV-96 becomes 8 (`infantry_1122b.py`).

## Document change log

- 2026-11-22 17:4x PST (America/Los_Angeles) — New doc (Lateralus asked whether ammo is per soldier or per weapon). Battle pool, card formula and HUDMultiplier, with RVAs.
- 2026-11-22 17:5x PST (America/Los_Angeles) — Added the card rate-of-fire formula (Lateralus: DXL-4 / OSV-96 rate of fire).
