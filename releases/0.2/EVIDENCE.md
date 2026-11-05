#0.2 development evidence

**Not live tested.** The authoritative audit is constant-audit.json; build logs and host-check results are retained in the task directory. Archive verification checks the actual payload, metadata, held tables and requested vehicle data. Source checks do not prove native credits, APS interception, armor behavior, speed or gameplay stability.

The next review must inspect source and actual archive before an isolated future test. No game installation or launch by this task.

## US/Baltic dev.3 data batch

24 additional base-price edits, Abrams160/190/200/240; literal ACV front/rear400 and12HP; Bradley core BUSK400/700 front and12HP; AMPV BRAT700 front with APS retained; named Stryker ESV/ICV/MGS SRAT700/700,12HP,+25; CV9035 armored500/500 and12HP; TypeX8HP. Five tank-gun sabot rows10, all Javelin10.5 (the active0.1 clones12→10.5).

No card split is complete. M60A1/CEV remain90/80; M8AGS/Thunderbolt70/85; Booker105/50mm100/110. XM91350mm stays2.5; BMOPMT12 stays8.5 pending scope. ACV40 armored-total and Battleship50 default-total are provisional interpretations. Recon remains incomplete. Linebacker/MCV/AMPV HP expansion, BUSK price harmonization and SRAT beyond the three named units await decisions. ICV retains active APS option+40 (two charges); inactive ESV/MGS APS duplicates remain selectable at+25 pending removal; AMPV's real APS option remains+45. No install or live acceptance. Lateralus main cleanup123dd7b is merged; no new optics/stealth/noise proposal is included.

## dev.4 balance corrections

Spike LR (row 2000177) 12→10.5 damage; Spike-SR stays 12. M6 Linebacker BUSK front HEAT 250→400 and BUSK3 400→700; Linebacker HP stays 14/16/17, and that question is open. Named Stryker ESV/ICV/MGS SRAT front and side HEAT 700→600, provisional, replacing the 700 in the dev.3 section above; RV and ATGM are unchanged. M2A3 ESV BUSK3 option 1759 stays +20 and that question is open. No live result.

## dev.5 detection proposal (Lateralus)

Ground optics 900/1300/1650/2300/2800 raw on sensor rows, with Medium Plus at 1450 from dev.6. Stealth: vehicles and recon vehicles 1.0, infantry 2.0, recon infantry 2.5, snipers 3.0 (UI values). Air, helicopter, naval and NPC stealth unchanged. Config, written only in a guarded offline battle: flash cap 2.2, both spotted penalties 1.5, forest cover 3, building cover 4. MaxAntiVisible stays 1.5. No live result.

Dev.7 (Lateralus): any infantry at 3.0 in vanilla stays at 3.0; drone ground optics rows scale by 2800/1200 to 6400, 5250 and 4650, rounded to 50. No live result.

Dev.8 (Lateralus): Humvee LRAS3, Humvee RWS, BRDM-2M and 1V14 Mashina-S are UI stealth 1.25 (raw 0.8). No live result.

Dev.9 (Lateralus): UI stealth 1.25 (raw 0.8) for Scimitar, M981 FISTV, 1V119 Reostat, M1117 Guardian, IFAV, Sarmat-2, Chaborz M-6, UAZ Kozlik and TGB-1111; the nine recon turret options at UI 1.5 in vanilla also go to UI 1.25. No live result.

Dev.10 (Lateralus): Stryker RV base and M-ATV are UI stealth 1.25. Stryker RV Bushmaster options, and non-PRP BRM-3K, BRM-1K and BRDM-3 options, stay at 1.0. No live result.

## Document change log

- 2026-11-04 15:12:48 PST (America/Los_Angeles) — Started0.2 development evidence record without inheriting0.1 acceptance claims.

- 2026-11-04 16:41:49 PST (America/Los_Angeles) — Added dev.3 scope, corrected held-price wording and documented provisional totals/unfinished recon/card work.

- 2026-11-04 17:30:00 PST (America/Los_Angeles) — Added dev.4 Spike LR, Linebacker and provisional SRAT 600 corrections. No live result.

- 2026-11-04 17:54:19 PST (America/Los_Angeles) — Added dev.5 constants-only detection proposal. No live result.

- 2026-11-04 18:01:47 PST (America/Los_Angeles) — dev.6: Medium Plus ground optics 1450, interpolated from vanilla and rounded to the nearest 50, at Lateralus’s instruction. No live result.

- 2026-11-04 18:07:58 PST (America/Los_Angeles) — dev.7: kept vanilla 3.0 infantry and the Scimitar, and scaled drone ground optics. No live result.

- 2026-11-04 18:11:00 PST (America/Los_Angeles) — dev.8: set four recon vehicles to UI stealth 1.25. No live result.

- 2026-11-04 18:26:32 PST (America/Los_Angeles) — dev.9: applied the UI stealth 1.25 recon list and option overrides. No live result.

- 2026-11-04 18:37:44 PST (America/Los_Angeles) — dev.10: set Stryker RV base and M-ATV to UI stealth 1.25. No live result.
