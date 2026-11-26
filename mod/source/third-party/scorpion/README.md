# SCORPION mechanics (focolate): staged, not in any build

**Short answer:** the "experimental features" branch (`codex/batch/osama/experimental-features`, Osama 25 Nov 2026) holds focolate's SCORPION mechanics exactly as delivered, away from the live build.
- **Not wired in:** nothing in the packager, the payload manifest or the batch scripts loads these files yet.
- **Live build untouched:** `codex/development` does not contain them.
- **Reason:** Osama asked for them to be kept on their own branch away from the live build (25 Nov 2026).

## Contents (sha256, first 16 hex)
- **`bundle-1.0.1/`:** SCORPION three-mechanism bundle 1.0.1, the `.bamod` contents unchanged (package sha256 eb716863…f5c9).
  - **EG18 1.0.3:** `Mods/EG18.dll` 46269d5a79cb16ae and `UserData/EG18/card.json` 84e3dda8feaea265.
    - It is a radar-suppression aircraft, unit 13800.
  - **Split Patriot 1.1.7:** `Mods/SplitPatriot.dll` 1bd7b02458549e5b and `UserData/SplitPatriot/card.json` 744702313ad26db1.
    - It adds separate radar units 14200 and 14201 and radar ability 14200.
  - **LoiteringMunition 2.0-net-alpha.3:** `Mods/LoiteringMunition.dll` 21cd6aa7d42a9377, plus `unit.json`, `network.json` and `network-lab.marker`.
    - Units 11510-11514. Multiplayer is off by default.
  - **`UserData/ScorpionBundle/manifest.json`:** every DLL checks all 8 files against it.
- **`mse-dual-pulse-1.1.0/`:** PAC-3 MSE Dual Pulse 1.1.0 (package 8d462b80…7a47), replacing 1.0.0.
  - `Mods/MseDualPulse.dll` 74de937390aeebad.
  - It is a separate DLL, not part of the bundle.

## Status (read from decompiled code; nothing run)
Reviews are in the BA Codex report library on the deck:
- `ba-multiplayer-criteria`
- `scorpion-fa-multiplayer-review`
- `scorpion-fa-bundle-100-review`
- `split-patriot-116-review`
- `scorpion-bundle-101-review`
- `pac3-mse-dual-pulse-review`

What they found:
- **EG18 and Split Patriot:** the owner-only fixes are in.
  - Open: EG18's 0.4 cap must merge into FA `MissileHitChance`.
  - Open (Lateralus): Split Patriot removes ability 59 from Patriots 163/251/448 and adds radar ability 14200.
- **LoiteringMunition:** offline only by default. In normal online play its launchers fire a zero-damage carrier, so keep cards 11511/11513 out of online decks.
  - Still unproved: whether the server accepts its cost-free, non-deck spawns.
- **Dual pulse 1.1.0:** keeps the full vanilla first burn of 3 s. Once the target is within 500 units, it adds one extra burn of 0.45 s (15%), worth up to +180 speed, capped at 800. Reach without the second pulse is the same as vanilla. Turn rate is 90 → 120 °/s. (1.0.0 cut the first burn to 2.4 s, about −11% reach; that is now fixed.)

## Before any of this goes into a build
1. **Source and permission:** focolate's source code, plus their OK to ship it in FA. Only DLLs were delivered; the decompiled code is not committed.
2. **Integration:** port the three into FA's own runtime and tables:
   - payload manifest;
   - FA build checks;
   - no load-time edits of FA rows.
3. **Decisions:** Lateralus and Osama decide the radar, balance and spec placement (FA has no spec 9700).
4. **Tests:** an offline Skirmish test, then a 2-human private Scenario test with both logs compared.

## Document change log
- 2026-11-25 14:15:14 PST (America/Los_Angeles): Staged bundle 1.0.1 and dual pulse 1.0.0 on their own branch (Osama: keep them away from the live build).
- 2026-11-25 16:25:48 PST (America/Los_Angeles): Dual pulse updated to 1.1.0 (full first burn plus a 15% terminal pulse).
