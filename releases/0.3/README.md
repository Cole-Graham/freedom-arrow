# Freedom Arrow 0.3.0-dev.3 — isolated development candidate

**Build-only candidate for play offline through local setup and online in private scenario lobbies: flat 200 points per simulation minute with no force-size income penalty, conquest scoring, and the vehicle, infantry and detection data. No online match has been run.**

## Included

- Existing 0.1.1 gameplay and scoring, with the dev.5 detection proposal replacing vanilla optics and stealth.
- Economy: 200/minute, converted to 200/60 internally; both linear upkeep and the income curve are bypassed only inside allowed native economy-update calls. Existing opening cash and native reserve cap are not changed. Per-call global and player income values are restored afterward.
- BMO-T base 12→14HP; ERA 14 retained.
- Kornet-D1 base 14→10HP; armored 10HP retained, front/side HEAT180/140→400/400.
- Sprut cage 14→10HP, HEAT200/140→400/400, road70→60km/h; cross-country 55 retained.
- M1283 AMPV BRAT APS is restored using its original two-charge ability; other vehicles sharing the disabled ability clone remain unchanged.

## Vehicle batch and held work

32 base costs are edited. Armata360, T15 200 and K16 30 remain provisional. BTR82A/BTR80 base and armored are10HP; Uran9 four profiles8HP; B15 alone400/400 HEAT.

T80 separate cards and obr2018 retirement are NOT implemented: temporary totals BV100, BVM2017 190, retained2018 200,2018+230. Object787 remains a T72A option at80 total, not a separate card. BMP2 Reserve35; other turret totals55/60/75 are preserved by offsetting surcharges. T72B1+K5=100; T72B75/T72BA90 before other upgrades. Uran70, Konkurs identity, unfinishedT72B3A and new-card availability remain unresolved.

## Held from this candidate

Troopers/card splits, squad resizing, infantry price/availability edits, obsolete-option retirement and Booker AP/APS clarification. These remain in the ongoing 0.2 changelog:
https://docs.google.com/document/d/1zt3iMn8IcSJSLRl4PBCugvVbTkp1HEA_TM6GPADWwOo/edit

## Build and inspect

From this checkout:

```bash
python3 releases/0.3/build_constants.py --vanilla-dir "/path/to/pinned/vanilla/build"
python3 releases/0.3/build.py --game-dir "/path/to/Broken Arrow" --dotnet "/path/to/dotnet"
python3 releases/0.3/verify.py releases/0.3/out/FreedomArrow-0.3.0-dev.3.bamod
dotnet run --project releases/0.3/economy-tests/Tests.csproj -c Release
```

The vanilla cache must match every 0.1.1 compatibility pin. The generated data is not in Git: `constant-audit.json`, `source/UserData/FreedomArrow/constants/` and `deck-migration.json`.

These commands write only this checkout's output/build files. They do not install or launch the game. The isolated branch starts at 72783a5; it deliberately does not copy another task's uncommitted 0.1 guide edit.

## Limits and future acceptance

From dev.18 the override runs in local setup battles and in private scenario lobbies. Native Skirmish, ranked and other network lobbies are blocked, so they never receive it. Online, the rate is divided by the lobby income multiplier, because native online income is `PlayerIncome` x that multiplier. It fails closed if the offline or online guard, current-session identity, payload or observed Unity thread check fails. A known second economy writer (FreedomArrow.Engine or FlatIncomeMod) disables the override. AI funds and this hook's new guards are unverified.

The pin overrides scenario income bonuses. Test 200 credit over 60 simulation seconds below the reserve cap, with purchases/refunds/losses, AI, pause/speed, restart, forced faults and exit to unguarded play. The control must show positive battlefield value and reduced income; otherwise upkeep has not been exercised. This is not an online-compatible release or a stability/FPS result.

## US/Baltic dev.3 data batch

24 additional base-price edits, Abrams160/190/200/240; literal ACV front/rear400 and12HP; Bradley core BUSK400/700 front and12HP; AMPV BRAT700 front with APS retained; named Stryker ESV/ICV/MGS SRAT700/700,12HP,+25; CV9035 armored500/500 and12HP; TypeX8HP. Five tank-gun sabot rows10, all Javelin10.5 (the active0.1 clones12→10.5).

No card split is complete. M60A1/CEV remain90/80; M8AGS/Thunderbolt70/85; Booker105/50mm100/110. XM91350mm stays2.5; BMOPMT12 stays8.5 pending scope. ACV40 armored-total and Battleship50 default-total are provisional interpretations. Recon remains incomplete. Linebacker/MCV/AMPV HP expansion, BUSK price harmonization and SRAT beyond the three named units await decisions. ICV retains active APS option+40 (two charges); inactive ESV/MGS APS duplicates remain selectable at+25 pending removal; AMPV's real APS option remains+45. No install or live acceptance. Lateralus main cleanup123dd7b is merged; no new optics/stealth/noise proposal is included.

## dev.4 balance corrections

Spike LR (row 2000177) 12→10.5 damage; Spike-SR stays 12. M6 Linebacker BUSK front HEAT 250→400 and BUSK3 400→700; Linebacker HP stays 14/16/17, and that question is open. Named Stryker ESV/ICV/MGS SRAT front and side HEAT 700→600, provisional, replacing the 700 in the dev.3 section above; RV and ATGM are unchanged. M2A3 ESV BUSK3 option 1759 stays +20 and that question is open. No live result.

## dev.5 detection proposal (Lateralus)

Ground optics 900/1300/1650/2300/2800 raw on sensor rows, with Medium Plus at 1450 from dev.6. Stealth: vehicles and recon vehicles 1.0, infantry 2.0, recon infantry 2.5, snipers 3.0 (UI values). Air, helicopter, naval and NPC stealth unchanged. Config (from dev.14, everywhere the tables apply): flash cap 2.2, both spotted penalties 1.5, forest cover 3, building cover 4. MaxAntiVisible stays 1.5. No live result.

Dev.7 (Lateralus): any infantry at 3.0 in vanilla stays at 3.0; drone ground optics rows scale by 2800/1200 to 6400, 5250 and 4650, rounded to 50. No live result.

Dev.8 (Lateralus): Humvee LRAS3, Humvee RWS, BRDM-2M and 1V14 Mashina-S are UI stealth 1.25 (raw 0.8). No live result.

Dev.9 (Lateralus): UI stealth 1.25 (raw 0.8) for Scimitar, M981 FISTV, 1V119 Reostat, M1117 Guardian, IFAV, Sarmat-2, Chaborz M-6, UAZ Kozlik and TGB-1111; the nine recon turret options at UI 1.5 in vanilla also go to UI 1.25. No live result.

Dev.10 (Lateralus): Stryker RV base and M-ATV are UI stealth 1.25. Stryker RV Bushmaster options, and non-PRP BRM-3K, BRM-1K and BRDM-3 options, stay at 1.0. No live result.

Dev.11 (Osama, recon list): 30 base prices, for example Stryker RV 40, T-90M 230, M1A2 SEP v2 TUA 240, M2A3 65, M2A3 ESV 55. M3A3 CFV was listed at 80 and at 75; this build uses 75, and that value is provisional. Stryker RV SRAT II +20. UAZ Kozlik 25 with SPG-9 +5 and Fagot +10. Uparmor never changes HP: every armor choice on a vehicle now has the default HP of that vehicle (41 armor rows, including BTR-90 12 and K16 12). Sprut is held at base 14, cage 10. Scimitar 543 is 45 points and 12 HP; LAV-25 is 40 points and 10 HP. BRM-3K and M-ATV are NOT separate cards: option prices give the requested totals (PRP-5G 35, BRM-3K 50; M-ATV 30, M-ATV Javelin 90). Scimitar 543 goes to UI stealth 1.25; dev.9 set this value only on hidden unit 445. No live result.

Dev.12 (Osama): Typhoon VDV is 25 points, replacing the dev.11 value of 20. No live result.

Dev.14 (Lateralus): the config now applies wherever the tables apply, in any battle mode, not only F8 Local AI. Do not take a modded client online. No live result for the write.

Dev.16 (Osama): LAV-AT 10 HP on both armor choices; M3A3 CFV 80 points; Sprut 14 HP on default and cage, and the cage keeps 400/400 HEAT and 60 km/h road. The uparmor HP rule now has no exceptions, and logistics units stay in it for now. Version 15 is left for Lateralus's local build. No live result.

Dev.17 (Osama: apply everything in the log): seven new cards and all held squad and option work. New cards: M-ATV Javelin 90, PRP-5G 35 (BRM-3K 50), T-80BVM 190 with 2018+ at +40, Object 787 80, M728 CEV 80, M8 Thunderbolt 85, M10 Booker XM913 110 (parent renamed M10 Booker M35). Troopers 70 with availability 8 and six AT-4 carriers; Troopers AT 110 with availability 4. CAAT Dragon 90 and CAAT Javelin 105 are separate cards. One launcher on Weapons Squad, CAAT Dragon, VDV Kornet and Kornet-M, PTO Metis, PTRK Fagot and Faktoriya; Baltic Milan keeps two. Five men and 25 HP on Weapons Squad, CAAT TOW-2A, TOW-2B and Javelin. VDV Kornet 65, Kornet-M 95, CAAT TOW-2A 80, TOW-2B 100. Options 565, 1462, 1775, 1792, 1895, 1898, 1931, 1939, 2117 and 1951 are retired. The loader cannot delete rows, so retired rows move to hidden unit 721. BTRs keep their prices (Osama). Availability other than M-ATV and Troopers is provisional. No added card or retired row has run live. No live result.

Dev.19 (change log audit): Uran-9 default loadout 70 (base 25 + Ataka 20 + Igla 25), BRDM ATGM with Konkurs-M 50, M2A3 ESV BUSK3 +25. Sprut stays 80: price still open.

Dev.20 (Osama): T-72B3A 240 -> 105 for now.

Dev.21 (armory fix): dev.17 to dev.20 fail in the game's unit loader on the hidden FA Retired unit, so the armory and decks are empty. The hidden unit is gone. A null row in a constants file now deletes that row, and retired options, squad members, squad weapons and ammo links are deleted. The generator and row tests enforce the game's squad rules. A deck guard removes deleted and moved options from saved decks when they load.

Dev.22 (Osama, prep branch codex/0.2-dev22-prep, not installed): Stryker RV SRAT II 600/600 HEAT. AAVP SU 400/400 HEAT, +15. ACV armored 400/400 HEAT, rear back to 30. IFAV TOW +20. Kornet-T 100. BMPT base side 200. T-72B side 200, K-5 +15 (85 total). T-72B3 105. T-72B3A: T-72B3AM option removed, obr. 16 +30. CAAT Javelin gets ACV and AAVP transports. Troopers gets Stryker ICV. Both M10 Bookers get the APS option at +50 with the vanilla two-charge APS.

## 0.3

0.3 starts from 0.2.0-dev.21 and holds every change made after the first live 0.2 session. 0.2 stays frozen on `codex/0.2-development`.

Dev.1 data: the dev.22 list prepared for 0.2 (Stryker RV, AAVP and ACV armor, IFAV, Kornet-T, BMPT, T-72B, T-72B3, T-72B3A, CAAT Javelin and Troopers transports, M10 Booker APS). All Stryker SRAT 700 front and side. TUSK +15 and 400 side; TUSK 2 700 side.

Dev.1 scoring: the mode now attaches when the native clock is already running, on one absolute tick schedule. A stall skips ticks instead of ending the mode. A scoring fault no longer stops flat income.

Dev.1 scenario: `make_scenario.py` builds `[FA] Central Village` from the game's own `Central Village_network` mission. The runtime plugin copies it to the game's `Scenarios` folder.

Dev.2: starting points 1500. `game-config.json` sets the game's default before players load, and `[FA] Central Village` defaults its lobby slider to 1500. The scenario reserve cap is also 1500.

Dev.3: infantry cover damage. A postfix on `CalculateHitDamage` multiplies infantry damage by 0.60 in forest and 0.30 in buildings, scaled down by ammunition `IgnoreCover`. Values are in `game-config.json`. Not proven live: whether infantry in buildings report the Buildings terrain, and how this meets any vanilla building protection.

## Document change log

- 2026-11-04 15:12:48 PST (America/Los_Angeles) — Created isolated 0.2 development source/build instructions and explicit included/held scope; no game installation or runtime acceptance claimed.

- 2026-11-04 15:54:11 PST (America/Los_Angeles) — Added the dev.2 price/HP/armor batch and documented held splits, fallback totals and provisional prices. No live result.

- 2026-11-04 16:41:49 PST (America/Los_Angeles) — Added dev.3 scope, corrected held-price wording and documented provisional totals/unfinished recon/card work.

- 2026-11-04 17:30:00 PST (America/Los_Angeles) — Added dev.4 Spike LR, Linebacker and provisional SRAT 600 corrections. No live result.

- 2026-11-04 17:54:19 PST (America/Los_Angeles) — Added dev.5 constants-only detection proposal. No live result.

- 2026-11-04 18:01:47 PST (America/Los_Angeles) — dev.6: Medium Plus ground optics 1450, interpolated from vanilla and rounded to the nearest 50, at Lateralus’s instruction. No live result.

- 2026-11-04 18:07:58 PST (America/Los_Angeles) — dev.7: kept vanilla 3.0 infantry and the Scimitar, and scaled drone ground optics. No live result.

- 2026-11-04 18:11:00 PST (America/Los_Angeles) — dev.8: set four recon vehicles to UI stealth 1.25. No live result.

- 2026-11-04 18:26:32 PST (America/Los_Angeles) — dev.9: applied the UI stealth 1.25 recon list and option overrides. No live result.

- 2026-11-04 18:37:44 PST (America/Los_Angeles) — dev.10: set Stryker RV base and M-ATV to UI stealth 1.25. No live result.

- 2026-11-04 19:05:03 PST (America/Los_Angeles) — dev.11: applied the recon price list and the uparmor HP rule, and corrected the Scimitar stealth unit. No live result.

- 2026-11-04 19:11:24 PST (America/Los_Angeles) — dev.12: set Typhoon VDV to 25. No live result.

- 2026-11-04 19:24:04 PST (America/Los_Angeles) — dev.14: config applies wherever the tables apply. Added TESTING.md and bump_version.py. No live result.

- 2026-11-04 19:37:31 PST (America/Los_Angeles) — dev.16: LAV-AT 10 HP, M3A3 80, Sprut 14 HP on both armor choices. No live result.

- 2026-11-04 19:42:51 PST (America/Los_Angeles) — dev.17: applied all held card splits, squad changes and option retirement from the 0.2 log. No live result.

- 2026-11-04 19:55:51 PST (America/Los_Angeles) — dev.18: opened private scenario lobbies for play with other people. Conquest scoring and flat 200 income now run there. No online result.

- 2026-11-04 20:01:19 PST (America/Los_Angeles) — dev.19: applied the Uran-9, BRDM Konkurs and M2A3 ESV BUSK3 prices found by the change log audit. No live result.

- 2026-11-04 20:04:05 PST (America/Los_Angeles) — dev.20: T-72B3A 105 for now. No live result.

- 2026-11-04 20:12:56 PST (America/Los_Angeles) — dev.21: fixed the empty armory by deleting retired rows instead of using a hidden unit. No live result yet.

- 2026-11-04 20:21:00 PST (America/Los_Angeles) — Generated data removed from Git; the build steps now start with the generator.

- 2026-11-04 20:54:37 PST (America/Los_Angeles) — dev.22: prepared Osama's in-game corrections on a separate branch. No live result.

- 2026-11-04 21:28:04 PST (America/Los_Angeles) — Started 0.3 from the dev.22 prep: scoring attach fix, SRAT, TUSK and [FA] Central Village. No live result.

- 2026-11-04 21:30:57 PST (America/Los_Angeles) — dev.2: starting points 1500. No live result.

- 2026-11-04 21:51:15 PST (America/Los_Angeles) — dev.3: infantry cover damage. No live result.
