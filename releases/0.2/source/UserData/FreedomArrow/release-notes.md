# Freedom Arrow 0.2.0-dev.14 — development candidate

**Built and checked offline; no installed-game acceptance.**

Included: guarded Local AI Skirmish flat200 economy prototype; BMO-T base14 HP; Kornet-D1 base10 HP and armored400/400 HEAT; Sprut cage10 HP,400/400 HEAT and60 km/h road limit; M1283 AMPV APS option and unit inventory both reference original two-charge ability82. Other shared disabled-APS profiles remain disabled.

Infantry/card changes, infantry availability/pricing changes, option retirement and the remaining Booker APS decision are held. No normal-Skirmish or online economy override. The rate is200/minute, converted to200/60 per simulation second; it is conditional on the initialized offline guard and null economy network service. A fault can disable the economy override while scoring continues; any economy_failed or combat-time economy_inactive result invalidates economy acceptance.

No live credit, HUD, AI, armor, movement, APS interception, FPS or stability result is claimed. T12 must inspect Base/BRAT without APS as well as the selected AMPV APS option, and prove upkeep-active control before comparison.

## Historical dev.2 Russian vehicle batch

32 base-price changes plus BTR82A/BTR80 10HP, Uran9 8HP and B15-only400/400 HEAT. T80 and Object787 remain loadouts with temporary requested price totals; splits, availability and obr2018 removal are held. BMP2 Reserve35 preserves the other turret totals55/60/75. Armata360/T15 200/K16 30 provisional. Dev.2 did not change sabot; dev.3 normalizes the five specified tank-gun rows. Uran70, Konkurs target and T72B3A request unresolved.

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

## Document change log

- 2026-11-04 15:25:27 PST (America/Los_Angeles) — Replaced stale0.1 acceptance wording with0.2 included/held scope and unverified runtime limits after final review.

- 2026-11-04 15:54:11 PST (America/Los_Angeles) — Added dev.2 batch and held structural scope.

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
