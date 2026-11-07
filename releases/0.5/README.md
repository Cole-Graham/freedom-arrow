# Freedom Arrow 0.5.0-dev.8 — isolated development candidate

**Build-only candidate for play offline through local setup and online in private scenario lobbies: flat 200 points per simulation minute with no force-size income penalty, conquest scoring, and the vehicle, infantry and detection data. No online match has been run.**

## New in 0.5 — accuracy

Started from 0.4.0-dev.49 (4a9084b), 6 November 2026. 0.5's defining feature is accuracy.

- dev.1: unguided tank-gun and rocket-launcher rounds scatter twice as far (dispersion ×2 on 115 rounds); guided missiles unchanged. The runtime logs shots, real hits, hit rate and time between shots per round every 60 s (FREEDOM_ARROW_FIRE_STATS). First test value; not run in a game yet.
- dev.2 (Osama, 6 November 2026): launcher rounds (weapon types 62 and 63, 45 rows) use dispersion 2.14/2.14 with `DispersionMinimal` 0.88 in place of ×2. The game keeps 88% of the max-range spread at point blank (read from `WeaponForceFire`), so a launcher hits a tank front about 80% point blank, 72% at half range and 65% at max range: crew error. Tank-gun rounds keep dev.1's ×2. Calculated, not yet run in a game.
- dev.3 (Osama, 6 November 2026): Sprut-SD, T-80BV and T-72A keep their smoke (exceptions to the dev.5 rule of smoke only on tanks at 100 points and up; `dev5-contract.json` keep_units). Smoke comes with the BMP-2G and BMP-2M turret packages (Smoke x1) and the T-72B1 package, option 1449 (Smoke x2). See `smoke-contract.json`. Not yet run in a game.
- dev.4 (Osama, 6 November 2026): Sprut-SDM is its own card (unit 722, 75 points, availability 6, option 261 moved). Sprut-SD 60 (was 80). Both 12 HP (was 14), both with smoke, SLAT kit +10 (was +15). See `sprut-contract.json`; prices in `vehicle-contract.json`. Not yet run in a game.
- dev.5 (Osama, 6 November 2026): Sprut-SD 55, Sprut-SDM 70. Not yet run in a game.
- dev.6 (Osama, 6 November 2026): UAZ Kozlik SPG-9 package +0 (was +5). Not yet run in a game.
- dev.7 (Osama, 6 November 2026): ground ATGMs hit 75%: missile accuracy 0.75 (was 1.0) on the 46 anti-tank missile rounds fired by infantry and ground vehicles, gun-launched missiles included. Helicopter, plane and drone missiles unchanged. See `accuracy-contract.json` atgm_fields. Calculated from game code; not yet run in a game.
- dev.8 (Osama, 6 November 2026): APS. New M1A1 FEP TUSK + Trophy option +80 and T-72B3AM obr. 16 + Arena option +120 (tank APS = kit +70). IFV and non-tank APS = kit +40: M2A3, M2A3 ESV, M3A3, Bumerang, Kurganets and Vilkas +40; Bumerang armored APS +50; Stryker ICV +65, M-SHORAD +55, MC and SPH +50; M1283 AMPV and M1287 MCV +55. See `aps-contract.json` and `vehicle-contract.json`. Not yet run in a game.

## New in 0.4

Built from 0.3.0-dev.38 (8870d15). Calculated and checked offline; no 0.4 game run yet.

- MBT prices from equal-point fights, 80 point floor, refit in dev.2 for the +50 sabot with M1A1 HC at 160 (Osama, 5 November 2026). Kit prices so the same armor costs the same. See `vehicle-contract.json`.
- Sabot: 26 tank-gun KE rows of 100mm and larger. Point-blank penetration is the long-range value + 50 (dev.1: + 0), falling in a straight line to the long-range value at max range. See `sabot-pin-contract.json`.
- Crits, for tanks and IFVs (`source/conquest/CombatHooks.cs`): a rear hit by a direct anti-tank weapon is red mobility. A front or side hit by a tank-gun sabot or HEAT round doing 9.3 or more is yellow mobility plus one random yellow. From dev.12 a front or side ATGM hit doing 8.9 or more gives the same yellow crit; top-attack missiles (Javelin, TOW-2B, BILL 2) do not.
- Yellow mobility is 40% speed (was 75%). Turning stays 50%. Global setting in `game-config.json`.
- Front arc 60 degrees each side of the hull (vanilla 45). `FrontArcDegrees` in the conquest settings.
- Scenarios (dev.3, from Lateralus's 0.3 commit 223a6fe): `[FA] [1v1] Dead Center 0.1` and `[FA] [2v2] Dead Center 0.1` for lobbies, with `Skirmish` versions of each for F8. Each map's layout is in `scenarios/<map>/layout.bascr`; `scenarios/make_scenario.py` builds them. Old `[FA] Central Village` and `[FA] Dead Center 0.1` copies are removed on install when the GUID matches.
- dev.12 (Osama, 5 November 2026): ground ATGMs do 10.5 damage; base Kornet 650 penetration (was 1000; 700 from dev.13), Kornet-M 950 (was 1200). Air missiles keep their values. Mid-tank front HEAT spread from 600 to 950; tanks at 195 points and up are unchanged. See `dev12-contract.json`. Calculated, not yet run in a game.
- dev.13 (Osama, 5 November 2026): ATGM penetration ladder: Fagot 450; Metis, Fagot-M, Arkan, Shillelagh 500; Konkurs, Spike-SR 550; Konkurs-M, Invar, Invar-M, Arkan-M, Dragon 3, Kokon, Metis-M, MAPATS 600; Invar-M1, Sprinter, TOW-2A, Metis-M1, Ataka-M, Milan ER 650; base Kornet and Khrizantema 700; Kornet-M 950; top-attack missiles unchanged; ATGM card prices unchanged. BMP-3 chassis (BMP-3, BMP-3F, BMP-3K, BRM-3K, Kornet-T) 12 HP. BMP-3 65, BMD-4M 55. 400 HEAT IFV kits +10 (BMP-3 Kaktus, M2A2 and M2A2 ESV BUSK). APS +30 over its armor kit: M2A3, M2A3 ESV and M3A3 Iron Fist +30; Stryker ICV SRAT + Trophy +55, Stryker MC and SPH +40, M1287 MCV +45. One AT launcher on Assaultmen SMAW, RPG-29 Vampyr and Rangers RAWS; their ammo rows are unchanged. See `dev13-contract.json`. Calculated, not yet run in a game.
- dev.14 (Osama, 5 November 2026): ammo with one launcher: VDV Kornet 6, PTRK Fagot 6, RPG-29 Vampyr 10, Rangers RAWS 10, RAWS M4 12, Assaultmen SMAW 6 NE + 6 HEAA, VDV DSh 3 RPG-7 8, Baltic Milan 6; Javelin 4 on Weapons Squad, CAAT Javelin and the Baltic Javelin team, Spike LR upgrade 4. One AT launcher on RAWS M4, VDV DSh 3 and Baltic Milan. RPG-29 Vampyr 45 points, 5 men, 25 HP. Rangers RAWS 40, M4 loadout +15. Rangers Javelin is its own card (90, availability 4) and leaves the Rangers Stinger card. Baltic Milan is its own card at 55; the Baltic Javelin team (65) is a new card with the Spike LR upgrade (+20), availability 4. Infantry launcher reload 6-7 s, disposable 7 s (44 weapons; vehicle launchers unchanged). See `dev14-contract.json`. Not yet run in a game.
- dev.15 (Osama and Lateralus, 5 November 2026): Lateralus's scale on Osama's dev.14 prices: Rangers RAWS 35, RAWS M4 45 (+10), RPG-29 Vampyr 35, Baltic Milan 45. BMP-2 Obr. 86 45, BMP-2G 50, BMP-2M 65 (each ATGM loadout −10), Reserve 35. Vampyr uses the plain 5-man armor row (armor 6). Not yet run in a game.
- dev.16 (Osama, 5 November 2026): Stryker ICV Dragoon (Bushmaster II) +10 (was +20); ACV RT20 (Bushmaster II) +10 (was +20).
- dev.17 (Osama, 5 November 2026): Stryker RV Bushmaster II +15 (was +25), with Javelin +45 (was +55).
- dev.18 (Osama, 5 November 2026): availability 6 for cheap fire-support tanks: M60A1, M551A1 Sheridan, M8 AGS, M8 Thunderbolt, M728 CEV, T-72A, Object 787, T-80BV (T-62M and T-72B already 6).
- dev.21 (Osama, 6 November 2026): Chernye Berety RPG and Chernye Berety RShG are separate cards, availability 2 each. BARS Igla is its own card at 60 points, availability 4; BARS keeps RPG and Fire support.
- dev.22 (Osama, 6 November 2026): base Konkurs 500 penetration (was 550). PTRK Konkurs 30 and PTRK Konkurs-M 50 are separate Coastal Troops cards (Konkurs-M availability 4). BMP-3 45, BMP-3F 45.
- dev.23 (Osama, 6 November 2026): BMP-2 Reserve 30 (base 30; Obr. 86 +15 = 45, BMP-2G +20 = 50, BMP-2M +35 = 65 unchanged). BMP-2 keeps its smoke.
- dev.24 (Osama, 6 November 2026): BMP-1AM turret +10 (was +15).
- dev.25 (Osama, 6 November 2026): BMP-2 keeps its dev.15 loadout prices on the 30 base, so every loadout is 5 cheaper: Reserve 30, Obr. 86 40 (+10), BMP-2G 45 (+15), BMP-2M 60 (+30).
- dev.26 (Osama, 6 November 2026): BMD-4M 45 (was 55).
- dev.27 (Osama, 6 November 2026): BMD-2 Konkurs-M +10 (was +5), BMD-2M +20 (was +10).
- dev.28 (Osama, 6 November 2026): Kornet-D1 90 with both weapon loadouts at +0 (1x Kornet-M + optics, 2x4 Kornet; the 2x4 was +20).
- dev.29 (Osama, 6 November 2026): BMP-2 loses smoke (base 30, the IFV smoke rule).
- dev.30 (Osama, 6 November 2026): Javelin aim 4-5 s (was 2-3) on infantry, Rangers LWCLU and vehicle Javelins. CAAT Javelin 110, Weapons Squad 95, Rangers Javelin 110, Baltic Javelin 90 (Spike LR 110), Troopers AT 100 with a fourth AT-4, Cavalry Scouts 90.
- dev.31 (Osama, 6 November 2026): mortars +50% range (all indirect rounds of 26 mortar weapons; Hawkeye MWS counts as a mortar; MICLIC, UR-77 and the 2S1's 122 mm howitzer excluded). Every mortar loadout has smoke: added on Hawkeye HE/Cluster/HE-RAP, 2S4 Tulpan (new 240 mm smoke round), Drok HE loadout, LAV-M 120, MT-LB Vasilek and Dilemma, Nona-SVK double, Vena/Magnolia double, Floks double. 2S41 Drok 65 (was 40). See `dev31-contract.json`.
- dev.32 (Osama, 6 November 2026): Tigr (transport) 30 (was 35), RWS Kord +0 (was +5), RWS AP-23 +5 (was +10); PKP/AGS +0 unchanged.
- dev.33 (Osama, 6 November 2026): ACV Armored (400 HEAT) +10 (was +5); every IFV 400 HEAT kit is now +10.
- dev.34 (Osama, 6 November 2026): M8 Thunderbolt ERA kit 700 HEAT front and sides (was 300/250); Applique kit 400 front and sides (was 100/40); rear unchanged. M8 AGS unchanged.
- dev.35 (Osama, 6 November 2026): TOW-2B = Javelin, 140 penetration and 10.5 damage (was 250), on every TOW-2B launcher (CAAT TOW-2B Saber, TOW-2B team, Humvee TOW-2, LAV-AT, M2A3 Bradley, M3A3 CFV, Stryker ATGM). M8 Thunderbolt kit rear armor back to 40 (front and sides stay 700/400). Stryker MC 90.
- The state log records crit level changes for every unit, the crits the mod applies, and each side hit the wider arc turns into a front hit.
- Infantry prices (dev.11, Lateralus): every buyable infantry, weapons-team and recon-infantry loadout is its 0.4.0-dev.10 price × 0.8333, rounded to the nearest 5, so the 120 ceiling becomes 100. Stage 2 overrides: HMG & GMG 40, Morskaya pekhota 65. Base card cost is the scaled base, the loadout surcharge is the total minus the base, and a variant card's own cost is its loadout total. 17 hidden infantry rows that no specialization offers keep their price. See `vehicle-contract.json` and the [price sheet](https://docs.google.com/spreadsheets/d/1TeAzbAlL6Q0G6OzlTXMCvqqDjYah4rFCZ8Umr0hhZTQ/edit). No live result.

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
python3 releases/0.5/build_constants.py --vanilla-dir "/path/to/pinned/vanilla/build"
python3 releases/0.5/build.py --game-dir "/path/to/Broken Arrow" --dotnet "/path/to/dotnet"
python3 releases/0.5/verify.py releases/0.5/out/FreedomArrow-0.5.0-dev.8.bamod
dotnet run --project releases/0.5/economy-tests/Tests.csproj -c Release
```

`build_constants.py` picks the dev version: it changes only when the current one is in `builds.json` and its inputs have changed since. See TESTING.md.

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

Ground optics 900/1300/1650/2300/2800 raw on sensor rows, with Medium Plus at 1450 from dev.6. Stealth: vehicles and recon vehicles 1.0, infantry 2.0, recon infantry 2.5, snipers 3.0 (UI values). Air, helicopter, naval and NPC stealth unchanged. Config (from dev.14, everywhere the tables apply): flash cap 2.2, both spotted penalties 1.5 (2.0 again from 0.4.0-dev.9), forest cover 3, building cover 4 (3.5 from 0.4.0-dev.10). MaxAntiVisible stays 1.5. No live result.

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

Dev.4 (Osama): woods 30% and buildings 50% as a start. Forest: a `CalculateHitDamage` postfix multiplies infantry damage by 0.70, scaled by `IgnoreCover`. Buildings: the mod writes `DamageModifierFloor` 0.50 and `DamageModifierPerSoldier` 0, with no hook. This replaces the dev.3 values, which stacked in buildings.

Dev.5 (Osama): all Javelin rows penetration 750 -> 140. By the HEAT formula, 14 HP tanks with top 100 take 6.95 per hit and keep about 0.10 HP after 2 hits. T-14 and T-15 at top 120 also become 3 hits. A scan of 353 playable unit and armor combinations found no other hit count change. No live result.

Dev.6 (Osama): HEAT top armor 100 on every armor choice of the Abrams, T-72, T-80, T-90 and T-14 cards, so Javelin 140 leaves about 0.10 HP after 2 hits on all of them. T-15 and M1150 are not changed. Kinetic top armor is not changed. No live result.

Dev.7 (Osama): APSCooldown 6 -> 30 seconds on all 14 APS abilities. BMPT HEAT top 100. No live result.

Dev.8 (Osama): T-72 family HEAT top 80 (T-72A, T-72B, T-72B3, T-72B3A, Object 787), so Javelin 140 does 7.92 per hit and kills 14 HP in 2 hits.

Dev.9 (Osama): HEAT top 80 on T-15 and BMPT, which joins the T-72 chassis group. TOS-1 (40) and BMO-T (60) stay thinner.

Dev.10 (Osama): HEAT top 80 on BMO-T, which joins the T-72 chassis group. TOS-1 stays at 40.

Dev.11: stable IDs for the M10 Booker XM913 APS option and the added transports. Later armor changes cannot move them. No stat change.

Dev.12 (Osama): lower artillery penetration, so tanks survive shelling. Infantry lose little.
Unguided HE up to damage 12: 30. Damage 15: 25. Damage 17 and above: 20. Unguided cluster: 50.
Laser-guided rows are halfway from today's value to the unguided value: 155mm 75 to 52.5, 203mm 100 to 62.5, 227mm 100 to 60, 300mm 125 to 72.5, 240mm 120 to 70, 120mm 60 to 45, guided cluster 200 to 125, M109A6 guided HEAT 600 to 315.
TOS, CATFAE and Grad incendiary stay at 15. Adds a FREEDOM_ARROW_HIT log line for real artillery hits.

Dev.13 (Osama): all cluster rounds, guided and unguided, return to original penetration (200, Grad 150). Cluster is the dedicated anti-armor round.

Dev.14 (Osama): [FA] Central Village is the first developed map. Zone values per tick: A, B, G, H, I, J are 4; C, D are 3; E, F are 2. The side with the higher held value scores the difference. Zone IDs 53 to 62 are checked against the scenario at build. A joiner without a scenario name is matched by exact zone IDs.

Dev.15 (Osama): each zone shows its value on the map, as +1, +2, +3 or +4, on all maps. The mod draws the labels on each player's own screen. A label fault turns off the labels, not the scoring.

Dev.16: first build with the dev.15 labels. Commit cde1722 (dev.15) did not compile and has no package.

Dev.17 (Osama): RPG-28 penetration 1050 -> 950 on ammo 2000137, the row every unit uses.

Dev.18 (Osama): RPG-28 penetration 950 -> 900 on ammo 2000137.

Dev.19: the runtime copies `[FA] Central Village` to `Mods/Scenarios`, because online lobbies leave out the local `Scenarios` folder. It removes the old local copy.

Dev.20 (Osama): adds `[FA] Central Village Skirmish` for F8 Local AI, which lists Skirmish scenarios only. It is built from the game's `Central_Village_Skirmish` mission with the same zone values on zone IDs 31, 32, 33, 35, 36, 37, 50, 159, 178 and 179.

Dev.21 (Osama): every Central Village zone stays on the map at any lobby size. The native small map hid A, B, C and D, and H on Skirmish, and Auto picks small under 8 players. Zone labels move to the zone centre, clear of the icons.

Dev.22 (Osama, live test): both FA scenarios declare game version 1.2.2, because the game picks a database from the scenario's version. The 1.2.0.2 value inherited from the native mission is the likely cause of `Not found unit in DB by ID:714`, no call-in and no income. A `FREEDOM_ARROW_DB_SOURCE` line logs the database. Zone labels are smaller and sit right of the zone icon.

Dev.23 (Osama): Round 1 is the first 5 minutes with no scoring; zones can still be captured. A banner counts it down and announces Round 2. First tick at 5:00. F8 Skirmish now defaults to 45 minutes and sets every player to 1500 starting points, the same as the multiplayer scenario. Dev.22 was run live online: database patched, 10 zones, weighted ticks, no unit error.

Dev.24 (Osama): first to 300 conquest points wins, or the leader when time runs out. The native team bars return and show points out of 300, without the three goal stars.

Dev.29 (Lateralus): `[FA] Dead Center 0.1` runs the FA game mode, built from `maps/` by `make_scenario.py`. Zone IDs 38, 39, 40 (A, B, C) are worth 2 and 41, 42 (D, E) are worth 3. The map had no script: the build adds `setConquestMode`, the money cap, the income curve switch and the money, income and timer sliders from the native mission. Fastest win is 17:00. The installer removes an old local copy only when its GUID matches. No F8 version. No live result.

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

- 2026-11-04 22:10:01 PST (America/Los_Angeles) — dev.4: woods 30%, buildings 50%. No live result.

- 2026-11-04 22:29:10 PST (America/Los_Angeles) — dev.5: Javelin penetration 140. No live result.

- 2026-11-04 22:32:30 PST (America/Los_Angeles) — dev.6: tank top HEAT 100. No live result.

- 2026-11-04 22:33:53 PST (America/Los_Angeles) — dev.7: APS cooldown 30 seconds, BMPT top 100. No live result.

- 2026-11-04 22:34:56 PST (America/Los_Angeles) — dev.8: T-72 family top 80. No live result.

- 2026-11-04 22:37:29 PST (America/Los_Angeles) — dev.9: T-15 and BMPT top 80. No live result.
- 2026-11-04 22:48:56 PST (America/Los_Angeles) — dev.10: BMO-T top 80. No live result.
- 2026-11-04 22:50:15 PST (America/Los_Angeles) — dev.11: stable saved-deck IDs. No stat change. No live result.
- 2026-11-04 23:30:42 PST (America/Los_Angeles) — dev.12: artillery penetration and hit log. No live result.
- 2026-11-04 23:33:42 PST (America/Los_Angeles) — dev.13: cluster penetration restored. No live result.
- 2026-11-04 23:38:33 PST (America/Los_Angeles) — dev.14: Central Village zone values. No live result.
- 2026-11-04 23:43:37 PST (America/Los_Angeles) — dev.15: zone value labels. No live result.
- 2026-11-04 23:44:21 PST (America/Los_Angeles) — dev.16: fixed the dev.15 compile error. No live result.
- 2026-11-04 23:52:25 PST (America/Los_Angeles) — dev.17: RPG-28 penetration 950. No live result.
- 2026-11-04 23:59:39 PST (America/Los_Angeles) — dev.18: RPG-28 penetration 900. No live result.
- 2026-11-05 00:06:46 PST (America/Los_Angeles) — dev.19: scenario install folder. Listing not yet confirmed live.
- 2026-11-05 00:11:24 PST (America/Los_Angeles) — dev.20: Skirmish version of Central Village for F8. No live result.
- 2026-11-05 00:13:57 PST (America/Los_Angeles) — dev.21: all zones stay visible; label position. dev.19 labels and 6-zone match seen live; dev.21 has no live result.
- 2026-11-05 00:18:10 PST (America/Los_Angeles) — dev.22: scenario game version, database log, label size and position. Not yet run live.
- 2026-11-05 00:34:56 PST (America/Los_Angeles) — dev.23: Round 1 banner, 5 minute opening, F8 time and points. Not yet run live.
- 2026-11-05 00:37:56 PST (America/Los_Angeles) — dev.24: score limit 300 and team bars. Not yet run live.
- 2026-11-05 00:54:48 PST (America/Los_Angeles) — dev.25: 3 minute setup, native round bar, damage hook off. Not yet run live.
- 2026-11-05 00:56:41 PST (America/Los_Angeles) — dev.26: T-80BV top HEAT 80. Not yet run live.
- 2026-11-05 01:04:48 PST (America/Los_Angeles) — dev.27: F8 setup phase pauses the game. Scoring starts at 5:00 again. Not yet run live.
- 2026-11-05 01:08:31 PST (America/Los_Angeles) — dev.28: round text fits, phase boxes hidden, green next-tick number. Not yet run live.
- 2026-11-05 01:10:43 PST (America/Los_Angeles) — dev.29: [FA] Dead Center 0.1 runs the FA game mode. A B C are 2, D E are 3. Not yet run live.
- 2026-11-05 01:11:10 PST (America/Los_Angeles) — dev.30: team score text shrinks to fit its box. Not yet run live.
- 2026-11-05 01:34:32 PST (America/Los_Angeles) — dev.31: woods reduction on with one hook; read-only F8 game state log. Not yet run live.
- 2026-11-05 01:40:45 PST (America/Los_Angeles) — dev.32: PT-76 10 HP on both armor choices. Not yet run live.
- 2026-11-05 01:48:48 PST (America/Los_Angeles) — dev.33: quitting a match no longer stops the mode for later matches. Not yet run live.
- 2026-11-05 01:57:57 PST (America/Los_Angeles) — dev.34: online money cap raised so income pays from 1500. Not yet run live.
- 2026-11-05 02:07:06 PST (America/Los_Angeles) — dev.35: 60 second scripted deployment on online FA maps. Not yet run live.
- 2026-11-05 02:20:07 PST (America/Los_Angeles) — dev.36: online clock and round bar show true time after deployment; online DEPLOYMENT countdown. Not yet run live.
- 2026-11-05 02:28:32 PST (America/Los_Angeles) — dev.37: game state log runs in private online matches. Not yet run live.
- 2026-11-05 02:46:42 PST (America/Los_Angeles) — dev.38: building floor 0.13; state log tracks magazine changes. Not yet run live.
- 2026-11-05 14:52:17 PST (America/Los_Angeles) — 0.4.0-dev.2: started 0.4 from 0.3 dev.38 with MBT and kit prices, pinned sabot, crit rules, 40% yellow mobility and the 60 degree front arc. Not yet run live.
- 2026-11-05 15:23:56 PST (America/Los_Angeles) — 0.4.0-dev.2: sabot +50 at point blank; MBT prices refit with M1A1 HC at 160; T-72B3 obr. 16 +25, T-90A +35. Not yet run live.
- 2026-11-05 15:54:00 PST (America/Los_Angeles) — 0.4.0-dev.8: ported Lateralus's 0.3 scenario build (223a6fe). Scenarios are [FA] [1v1] Dead Center 0.1, [FA] [1v1] Dead Center Skirmish 0.1, [FA] [2v2] Dead Center 0.1 and [FA] [2v2] Dead Center Skirmish 0.1, built by scenarios/make_scenario.py. 0.4 gameplay unchanged. Not yet run live.
- 2026-11-05 15:56:26 PST (America/Los_Angeles) — 0.4.0-dev.8: online deployment 3 minutes; state log records vehicle movement and front-arc real hits. Not yet run live.
- 2026-11-05 16:48:47 PST (America/Los_Angeles) — 0.4.0-dev.8: no smoke on tanks under 100 or IFVs at 30 and below; BMP-3 family 10 HP; PT-76 8 HP; Bumerang uparmor HEAT 400; BTR-80 turrets +5/+10; VDV Kornet M +20; PTRK Kornet 65; PTRK Fagot 40; CAAT Javelin 90; Weapons Squad 80. Not yet run live.
- 2026-11-05 16:51:31 PST (America/Los_Angeles) — 0.4.0-dev.8: BMD-4MK Demidov 10 HP, the same as the BMP-3 family; BMD-4M already 10. Not yet run live.
- 2026-11-05 16:52:54 PST (America/Los_Angeles) — 0.4.0-dev.8: VDV Kornet-M and PTRK Kornet-M cards 85, the same as the base Kornet cards with the Kornet M loadout. Not yet run live.
- 2026-11-05 17:10:52 PST (America/Los_Angeles) — build.py copies the built scenarios to {game_root}/Mods/Scenarios from config.YAML, and warns when the installed package is a different version (Lateralus). Package contents unchanged.
- 2026-11-05 17:23:36 PST (America/Los_Angeles) — Scenario build gives the same .bascr bytes on Windows and Linux (fixed zip header), checks the native Central Village missions against native-pins.json, and copies extra files such as .png into every built map folder. Linux output is unchanged; the lobby compares the .bascr hash.
- 2026-11-05 18:24:37 PST (America/Los_Angeles) — 0.4.0-dev.8: APS cooldown 30 → 10 seconds on all 14 APS abilities; Rangers, Rangers RAWS and Rangers Snipers AT Carl Gustaf M3 HEAT penetration 450 → 650 (own copy of the round) (Osama). Not yet run live.
- 2026-11-05 19:16:00 PST (America/Los_Angeles) — 0.4.0-dev.9: SpottedPenalty and SpottedPenaltyBuildings 1.5 → 2.0 (vanilla), globally; ATGM flash unchanged (Lateralus). Not yet run live.
- 2026-11-05 19:34:00 PST (America/Los_Angeles) — 0.4.0-dev.10: building cover 4.0 → 3.5, so Very Good optics see infantry firing an ATGM from a building at about 1,314 m (calculated) (Lateralus). Not yet run live.
- 2026-11-05 19:46:48 PST (America/Los_Angeles) — Automatic dev version: `dev_version.py` and `builds.json`; 0.4.0-dev.10 recorded. bump_version.py no longer rewrites old version numbers in the change history.
- 2026-11-05 20:55:00 PST (America/Los_Angeles) — dev.11: infantry prices × 0.8333 to the nearest 5 plus two Stage 2 overrides, at Lateralus’s instruction. No live result.
- 2026-11-05 20:47:08 PST (America/Los_Angeles) — 0.4.0-dev.12: ground ATGM damage 10.5, base Kornet 650 and Kornet-M 950, ATGM crits at 8.9 except top attack, mid-tank front HEAT spread 600–950 (Osama). Not yet run live.
- 2026-11-05 21:17:13 PST (America/Los_Angeles) — 0.4.0-dev.13: ATGM ladder 450–700 (Kornet 700, Kornet-M 950), BMP-3 chassis 12 HP, BMP-3 65 and BMD-4M 55, IFV kits +10, APS +30, one AT launcher per squad (Osama). Not yet run live.
- 2026-11-05 21:35:54 PST (America/Los_Angeles) — 0.4.0-dev.14: launcher ammo, one AT launcher per squad, Vampyr 5 men 45, RAWS 40 and M4 +15, Rangers Javelin and Baltic Javelin cards, Milan 55, launcher reload 6–7 s (Osama). Not yet run live.
- 2026-11-05 21:45:12 PST (America/Los_Angeles) — 0.4.0-dev.15: infantry prices on Lateralus's scale, BMP-2 45/50/65 with Reserve 35, Vampyr armor 6. Not yet run live.
- 2026-11-05 22:04:09 PST (America/Los_Angeles) — 0.4.0-dev.16: Stryker ICV Dragoon and ACV RT20 Bushmaster II +10 (Osama). Not yet run live.
- 2026-11-05 22:07:23 PST (America/Los_Angeles) — 0.4.0-dev.17: Stryker RV Bushmaster II +15, with Javelin +45 (Osama). Not yet run live.
- 2026-11-05 22:13:06 PST (America/Los_Angeles) — 0.4.0-dev.18: availability 6 for cheap fire-support tanks (Osama). Not yet run live.
- 2026-11-05 23:58:00 PST (America/Los_Angeles) — 0.4.0-dev.19: spotting cap and optics names (Lateralus). An observer never sees a ground target beyond the vanilla ground optics of its sensor tier (for example Very Good 2,000 m, Exceptional 2,400 m, MQ-9 4,500 m, RQ-4 5,500 m); ranges under the cap are unchanged. Unit cards show optics as coloured tier names (Bad, Medium-, Medium, Medium+, Good, Very Good, Exceptional, Superior, Strategic) for ground, low and high altitude. Hooks: FogOfWarUnit.CreateFilterTaskForTarget prefix and UnitInfoCard.SetUnitStatistic postfix. Not yet run live.
- 2026-11-06 00:05:00 PST (America/Los_Angeles) — 0.4.0-dev.20: ground optics names Exceptional I-IV (2800, 4650, 5250, 6400); high-altitude 1000 is Bad+; Arleigh Burke, AC-130 and carrier ground optics 1200 → 1300 (Medium), with the Medium cap of 1,200 m (Lateralus). Not yet run live.
- 2026-11-06 00:12:20 PST (America/Los_Angeles) — 0.4.0-dev.21: Chernye Berety RPG and RShG separate cards at availability 2; BARS Igla card at 60 (Osama). Not yet run live.
- 2026-11-06 00:27:25 PST (America/Los_Angeles) — 0.4.0-dev.22: Konkurs 500, PTRK Konkurs 30 and Konkurs-M 50 cards, BMP-3 and BMP-3F 45 (Osama). Not yet run live.
- 2026-11-06 00:33:08 PST (America/Los_Angeles) — 0.4.0-dev.23: BMP-2 Reserve 30, ATGM loadouts unchanged, smoke kept (Osama). Not yet run live.
- 2026-11-06 00:34:21 PST (America/Los_Angeles) — 0.4.0-dev.24: BMP-1AM +10 (Osama). Not yet run live.
- 2026-11-06 00:35:13 PST (America/Los_Angeles) — 0.4.0-dev.25: BMP-2 loadouts +10/+15/+30 on base 30 (Osama). Not yet run live.
- 2026-11-06 00:35:43 PST (America/Los_Angeles) — 0.4.0-dev.26: BMD-4M 45 (Osama). Not yet run live.
- 2026-11-06 00:37:10 PST (America/Los_Angeles) — 0.4.0-dev.27: BMD-2 Konkurs-M +10, BMD-2M +20 (Osama). Not yet run live.
- 2026-11-06 00:39:11 PST (America/Los_Angeles) — 0.4.0-dev.28: Kornet-D1 90, both weapon loadouts +0 (Osama). Not yet run live.
- 2026-11-06 00:40:46 PST (America/Los_Angeles) — 0.4.0-dev.29: BMP-2 smoke removed (Osama). Not yet run live.
- 2026-11-06 01:15:40 PST (America/Los_Angeles) — 0.4.0-dev.30: Javelin aim 4-5 s, Javelin team prices, Troopers AT 100 with four AT-4 (Osama). Not yet run live.
- 2026-11-06 01:24:37 PST (America/Los_Angeles) — 0.4.0-dev.31: mortar range +50%, smoke on every mortar loadout, Drok 65 (Osama). Not yet run live.
- 2026-11-06 01:35:30 PST (America/Los_Angeles) — 0.4.0-dev.32: Tigr 30, Kord +0, AP-23 +5 (Osama). Not yet run live.
- 2026-11-06 01:38:34 PST (America/Los_Angeles) — 0.4.0-dev.33: ACV Armored +10 (Osama). Not yet run live.
- 2026-11-06 01:57:20 PST (America/Los_Angeles) — 0.4.0-dev.34: M8 Thunderbolt ERA 700, Applique 400 HEAT all around (Osama). Next patch, not deployed.
- 2026-11-06 01:59:58 PST (America/Los_Angeles) — 0.4.0-dev.35: TOW-2B 140 penetration and 10.5 damage like the Javelin, Thunderbolt rear armor unchanged, Stryker MC 90 (Osama). Not deployed.
