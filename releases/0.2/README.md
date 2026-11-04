# Freedom Arrow 0.2.0-dev.2 — isolated development candidate

**Build-only candidate: flat 200 points per simulation minute with no force-size income penalty in guarded offline Local AI Skirmish, plus the Russian vehicle price/HP/armor batch. It has not been installed, launched or accepted in game.**

## Included

- Existing 0.1.1 gameplay and scoring, with vanilla optics/stealth retained.
- Economy: 200/minute, converted to 200/60 internally; both linear upkeep and the income curve are bypassed only inside guarded native economy-update calls. Existing opening cash and native reserve cap are not changed. Per-call global and player income values are restored afterward.
- BMO-T base 12→14HP; ERA 14 retained.
- Kornet-D1 base 14→10HP; armored 10HP retained, front/side HEAT180/140→400/400.
- Sprut cage 14→10HP, HEAT200/140→400/400, road70→60km/h; cross-country 55 retained.
- M1283 AMPV BRAT APS is restored using its original two-charge ability; other vehicles sharing the disabled ability clone remain unchanged.

## Vehicle batch and held work

32 base costs are edited. Armata360, T15 200 and K16 30 remain provisional. BTR82A/BTR80 base and armored are10HP; Uran9 four profiles8HP; B15 alone400/400 HEAT.

T80 separate cards and obr2018 retirement are NOT implemented: temporary totals BV100, BVM2017 190, retained2018 200,2018+230. Object787 remains a T72A option at80 total, not a separate card. BMP2 Reserve35; other turret totals55/60/75 are preserved by offsetting surcharges. T72B1+K5=100; T72B75/T72BA90 before other upgrades. Uran70, Konkurs identity, unfinishedT72B3A and new-card availability remain unresolved.

## Held from this candidate

Troopers/card splits, squad resizing, price/availability edits, obsolete-option retirement and Booker AP/APS clarification. These remain in the ongoing 0.2 changelog:
https://docs.google.com/document/d/1zt3iMn8IcSJSLRl4PBCugvVbTkp1HEA_TM6GPADWwOo/edit

## Build and inspect

From this checkout:

```bash
python3 releases/0.2/build.py --game-dir "/path/to/Broken Arrow" --dotnet "/path/to/dotnet"
python3 releases/0.2/verify.py releases/0.2/out/FreedomArrow-0.2.0-dev.2.bamod
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

## Document change log

- 2026-11-04 15:12:48 PST (America/Los_Angeles) — Created isolated 0.2 development source/build instructions and explicit included/held scope; no game installation or runtime acceptance claimed.

- 2026-11-04 15:54:11 PST (America/Los_Angeles) — Added the dev.2 price/HP/armor batch and documented held splits, fallback totals and provisional prices. No live result.
