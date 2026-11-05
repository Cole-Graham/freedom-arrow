# Freedom Arrow 0.2.0-dev.8 — isolated development candidate

**Build-only candidate: flat 200 points per simulation minute with no force-size income penalty in guarded offline Local AI Skirmish, plus the Russian and US/Baltic vehicle data batches. It has not been installed, launched or accepted in game.**

## Included

- Existing 0.1.1 gameplay and scoring, with the dev.5 detection proposal replacing vanilla optics and stealth.
- Economy: 200/minute, converted to 200/60 internally; both linear upkeep and the income curve are bypassed only inside guarded native economy-update calls. Existing opening cash and native reserve cap are not changed. Per-call global and player income values are restored afterward.
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
python3 releases/0.2/build.py --game-dir "/path/to/Broken Arrow" --dotnet "/path/to/dotnet"
python3 releases/0.2/verify.py releases/0.2/out/FreedomArrow-0.2.0-dev.8.bamod
dotnet run --project releases/0.2/economy-tests/Tests.csproj -c Release
```

To regenerate the included data, first supply the vanilla cache matching every 0.1.1 compatibility pin:

```bash
python3 releases/0.2/build_constants.py --vanilla-dir "/path/to/pinned/vanilla/build"
```

These commands write only this checkout's output/build files. They do not install or launch the game. The isolated branch starts at 72783a5; it deliberately does not copy another task's uncommitted 0.1 guide edit.

## Limits and future acceptance

Normal Skirmish, unguarded/scenario/network lobbies and multiplayer do not receive this economy override. It fails closed if the offline guard, current-session identity, payload, observed Unity thread or null network-service check fails. A known second economy writer (FreedomArrow.Engine or FlatIncomeMod) disables the override. AI funds and this hook's new guards are unverified.

The pin overrides scenario income bonuses. Test 200 credit over 60 simulation seconds below the reserve cap, with purchases/refunds/losses, AI, pause/speed, restart, forced faults and exit to unguarded play. The control must show positive battlefield value and reduced income; otherwise upkeep has not been exercised. This is not an online-compatible release or a stability/FPS result.

## US/Baltic dev.3 data batch

24 additional base-price edits, Abrams160/190/200/240; literal ACV front/rear400 and12HP; Bradley core BUSK400/700 front and12HP; AMPV BRAT700 front with APS retained; named Stryker ESV/ICV/MGS SRAT700/700,12HP,+25; CV9035 armored500/500 and12HP; TypeX8HP. Five tank-gun sabot rows10, all Javelin10.5 (the active0.1 clones12→10.5).

No card split is complete. M60A1/CEV remain90/80; M8AGS/Thunderbolt70/85; Booker105/50mm100/110. XM91350mm stays2.5; BMOPMT12 stays8.5 pending scope. ACV40 armored-total and Battleship50 default-total are provisional interpretations. Recon remains incomplete. Linebacker/MCV/AMPV HP expansion, BUSK price harmonization and SRAT beyond the three named units await decisions. ICV retains active APS option+40 (two charges); inactive ESV/MGS APS duplicates remain selectable at+25 pending removal; AMPV's real APS option remains+45. No install or live acceptance. Lateralus main cleanup123dd7b is merged; no new optics/stealth/noise proposal is included.

## dev.4 balance corrections

Spike LR (row 2000177) 12→10.5 damage; Spike-SR stays 12. M6 Linebacker BUSK front HEAT 250→400 and BUSK3 400→700; Linebacker HP stays 14/16/17, and that question is open. Named Stryker ESV/ICV/MGS SRAT front and side HEAT 700→600, provisional, replacing the 700 in the dev.3 section above; RV and ATGM are unchanged. M2A3 ESV BUSK3 option 1759 stays +20 and that question is open. No live result.

## dev.5 detection proposal (Lateralus)

Ground optics 900/1300/1650/2300/2800 raw on sensor rows, with Medium Plus at 1450 from dev.6. Stealth: vehicles and recon vehicles 1.0, infantry 2.0, recon infantry 2.5, snipers 3.0 (UI values). Air, helicopter, naval and NPC stealth unchanged. Config, written only in a guarded offline battle: flash cap 2.2, both spotted penalties 1.5, forest cover 3, building cover 4. MaxAntiVisible stays 1.5. No live result.

Dev.7 (Lateralus): any infantry at 3.0 in vanilla stays at 3.0; the Scimitar keeps vanilla raw stealth 1.25; drone ground optics rows scale by 2800/1200 to 6400, 5250 and 4650, rounded to 50. No live result.

Dev.8 (Lateralus): Humvee LRAS3, Humvee RWS, BRDM-2M and 1V14 Mashina-S are UI stealth 1.25 (raw 0.8). No live result.

## Document change log

- 2026-11-04 15:12:48 PST (America/Los_Angeles) — Created isolated 0.2 development source/build instructions and explicit included/held scope; no game installation or runtime acceptance claimed.

- 2026-11-04 15:54:11 PST (America/Los_Angeles) — Added the dev.2 price/HP/armor batch and documented held splits, fallback totals and provisional prices. No live result.

- 2026-11-04 16:41:49 PST (America/Los_Angeles) — Added dev.3 scope, corrected held-price wording and documented provisional totals/unfinished recon/card work.

- 2026-11-04 17:30:00 PST (America/Los_Angeles) — Added dev.4 Spike LR, Linebacker and provisional SRAT 600 corrections. No live result.

- 2026-11-04 17:54:19 PST (America/Los_Angeles) — Added dev.5 constants-only detection proposal. No live result.

- 2026-11-04 18:01:47 PST (America/Los_Angeles) — dev.6: Medium Plus ground optics 1450, interpolated from vanilla and rounded to the nearest 50, at Lateralus’s instruction. No live result.

- 2026-11-04 18:07:58 PST (America/Los_Angeles) — dev.7: kept vanilla 3.0 infantry and the Scimitar, and scaled drone ground optics. No live result.

- 2026-11-04 18:11:00 PST (America/Los_Angeles) — dev.8: set four recon vehicles to UI stealth 1.25. No live result.
