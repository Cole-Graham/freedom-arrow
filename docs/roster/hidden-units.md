# Hidden and removed units

**The one running list of cards taken out of play** (Osama 23 Nov 2026 18:1x: "we need to keep a running list of units we're hiding and moving off the main build").
A hidden card is not in any spec, is not offered as a transport, and does not show in the Armory (`DisplayInArmory` false). Its unit, weapon and
ammunition rows stay, so nothing that points to them breaks and it can come back by restoring its spec rows. Saved decks lose the card.

Add every new hidden or removed card here in the same commit as the data change.

## Main development (`codex/development`) and the model build

| Card | Unit | Was in | Section | Requested |
|---|---|---|---|---|
| YJ-18 (ship launcher) | 1129 | PLAAF Air Force, 2 cards | `yj18_removed_1123.py` | Osama 23 Nov 17:4x "remove the YJ-18 unit from the game" |
| VN20 | 1274 | PLAGF Armored Force, 2 cards | `roster_1123b.py` | Osama 23 Nov 18:0x "Hide VN-20 and VN-17" |
| VN-17 (ZBD-20) | 945 | transport only, 8 transport links | `roster_1123b.py` | same |
| VT-5 | 1261 | PLAGF Motorized 4, PLAN Special Forces 4 | `roster_1123b.py` | Osama 23 Nov 18:0x "hide VT-5" |
| VT-5 Recon | 1262 | PLAGF Motorized, 2 cards | `roster_1123b.py` | same (hidden with the VT-5) |
| ZTZ-59 | 1060 | PLARF Rocket Conscript Force, 6 cards | `roster_1123b.py` | Osama 23 Nov 18:1x "also hide ZTZ-98 and ZTZ-59" |
| PCL-181 | 1034 | PLAGF Motorized, 3 cards | `roster_1123b.py` | Osama 23 Nov 18:1x "PCL-181 hide from armory" |
| HQ-6A | 1045 | PLAGF Motorized, 4 cards | `roster_1123b.py` | Osama 23 Nov 18:1x "HQ-6A hide from armory" |
| ZSL-92 | 1079 | transport only, 10 transport links | `roster_1123b.py` | Osama 23 Nov 18:1x "ZSL-92 removed too" |
| PLZ-70 | 1040 | PLAAF Air Force, 3 cards | `roster_1123b.py` | Osama 23 Nov 18:2x "PLZ-70 removed" |
| Z-10 | 1239 | PLAAF Air Force, 2 cards | `roster_1123b.py` | Osama 23 Nov 18:3x "Z-10 removed (hidden)" |
| Z-19G | 1236 | PLAN Special Forces, 2 cards | `roster_1123b.py` | Osama 23 Nov 18:3x "Z-19G (and the recon) removed/hidden" |
| Z-19G Recon | 1237 | PLAN Special Forces, 2 cards | `roster_1123b.py` | same |
| F-35B (JASDF) | 1291 | Blue Dragon (Arsenal-only preview), 2 cards | `roster_1123b.py` | Osama 23 Nov 18:4x "F-35 JASDF, let's hide this for now" |
| K1A1 | 1279 | Blue Dragon (Arsenal-only preview) | `preview_specs_1124.py` | Osama 24 Nov 21:2x "Hide the K-1's too" |
| K1 | 1280 | Blue Dragon (Arsenal-only preview) | `preview_specs_1124.py` | same |
| K9 Thunder | 1310 | Blue Dragon (Arsenal-only preview) | `preview_specs_1124.py` | Osama 24 Nov 23:5x "K-9 really does look like a War Thunder rip ... For now we hide it from the game (don't pack it in our live build and download that model ever)"; its model files are refused by `tools/pla-specs/banned-models.txt` |
| QJZ-89 Team (Armored) | 1157 | PLAGF Armored Force, 4 cards (the PLARF QJZ-89 Team 1170 stays) | `qbz95_qjz89_1123.py` | Osama 23 Nov 18:3x "QJZ-89 PLAGF Armored Force ... hidden" |
| OH-58D Recon Optronic | 733 | Air Naval, 4 cards | `recon_helis_us_1123.py` | Lateralus 23 Nov 18:3x "remove the OH-58D Recon Optronic from the mod (or just disable it/hide it from the menu)" |
| MH-6 Little Bird Recon | 736 | Special Operations Forces, 4 cards | `recon_helis_us_1123.py` | Lateralus 23 Nov 18:3x "remove the MH-6 Little Bird Recon" |
| AH-64D Longbow Recon | 746 | Air Naval, 4 cards | `recon_helis_us_1123.py` | Lateralus 23 Nov 18:3x "remove the AH-64D Longbow Recon" |
| Ka-226T Razvedchik | 728 | Defense Forces, 4 cards | `recon_helis_ru_1123.py` | Lateralus 23 Nov 18:5x "Ka-226T, hide it from the mod" |
| Ka-52K Razvedchik | 748 | Coastal Troops, 4 cards | `recon_helis_ru_1123.py` | Lateralus 23 Nov 18:5x "Ka-52K Razvedchik, hide it from the mod" |
| FK-3000 | 1447 | PLAGF Medium CAB, 4 cards (now test spec 26, 4 cards) | `fk3000_hidden_1125.py` | Osama 25 Nov 11:4x "FK-3000 we need to hide in our test mode for now, it's completely fucked as a model" |

## Model build only (`codex/batch/osama/models-096`)

| Card | Unit | Was in | Section | Requested |
|---|---|---|---|---|
| ZTZ-98 | 'PLA ZTZ-98' (1309 in 0.9.6-dev.12) | PLARF Rocket Conscript Force | `roster_1123b.py` | Osama 23 Nov 18:1x |
| Type 19 | see `type19_removed_1123.py` | Blue Dragon | `type19_removed_1123.py` | Osama 23 Nov 18:0x (blue dragons thread) ; 19:5x "I want the type 19 gone entirely": not in the test spec, models removed from the model stage |

## Test specs (specs 26 China, 27 USA, 28 Russia; off by default)

Osama 23 Nov 18:5x: "a hidden toggle for a China test spec", and the old Test spec 22 stays hidden. 19:3x: "you can put all the hidden units here".
Each nation has one "Test: Hidden Units" spec that holds **every card in the lists above** for that nation, with its old card count (YJ-18 too).
VN-17 and ZSL-92 were transports only and get 2 cards each. The test specs have **no transports**: the Armory shows a spec's transports as cards,
so the QJZ-89 Team's ZBD-04A, ZSD-89A and Type 100 CSV had shown up in it. These units have `DisplayInArmory` true again, but the test specs
have `ShowInHangar` false, so the normal Armory and deck creation still do not show them.

Since 24 Nov 23:4x (Osama: "if I don't have developer option on I shouldn't see this") the test-spec units also have `DisplayInArmory`
false: with true, the Armory showed a "Test: Hidden Units" heading with their cards. Test mode sets it back to true for them.

To switch them on for one PC, create `UserData/FreedomArrow/test-spec.json` with `{"show": true}` and restart the game (`runtime-qa/TestSpec.cs`).
Delete the file or set `false` to switch them off. Section: `test_specs_1123.py`. A section that hides a card records its old rows in
`rec['hidden_rows']`, and the card then goes into its nation's test spec automatically.

## Preview specs: look around, no stat card (Blue Dragon, Eurocorp)

Osama 24 Nov 21:2x: "for the BD and Eurocorp preview factions. I want people to go in and see the spec and look around. But I don't want people to
click on it and see the stats." Specs 23 Blue Dragon (Testing Preview), 24 France (Preview) and 25 Germany (Preview) and the Eurocorp flag stay in
the Armory, but clicking one of their units shows no stat card (`runtime-qa/PreviewCards.cs` makes the Armory info card invisible for units of
those specs). With `test-spec.json` `{"show": true}` the stat cards show. Deck creation still hides spec 23, and France and Germany keep
battlegroup size 0. (The first version, 21:0x, hid the specs completely; it was undone at 21:2x.)

## Moved (not hidden)

- ZTQ-15 (906): PLAGF Armored Force -> PLAGF Motorized, 6 cards (Osama 23 Nov 18:0x). `roster_1123b.py`.
- PLL-05 (926): PLARF Rocket Conscript Force -> PLAAF Air Force (airborne), 3 cards (Osama 23 Nov 18:2x "PLL-05 moved to airborne"). `roster_1123b.py`.

## Document change log

- 2026-11-23 18:20 PST (America/Los_Angeles): First version: YJ-18, VN20, VN-17, VT-5 (+Recon), ZTZ-59, PCL-181, HQ-6A, ZSL-92, ZTZ-98 and Type 19; ZTQ-15 move.
- 2026-11-23 18:24 PST (America/Los_Angeles): PLZ-70 added.
- 2026-11-23 18:27 PST (America/Los_Angeles): PLL-05 move added.
- 2026-11-23 18:35 PST (America/Los_Angeles): QJZ-89 Team (Armored) added.
- 2026-11-23 18:40 PST (America/Los_Angeles): Z-10, Z-19G and Z-19G Recon added; the Z-10K/Z-10U name swap was undone (no list change).
- 2026-11-23 18:42 PST (America/Los_Angeles): F-35B (JASDF) added.
- 2026-11-23 18:5x PST (America/Los_Angeles): OH-58D Recon Optronic, MH-6 Little Bird Recon and AH-64D Longbow Recon added (Lateralus).
- 2026-11-23 18:56 PST (America/Los_Angeles): China test spec 26 (toggle) added with the 13 hidden China cards.
- 2026-11-23 19:0x PST (America/Los_Angeles): Ka-226T Razvedchik and Ka-52K Razvedchik added (Lateralus).
- 2026-11-23 19:45 PST (America/Los_Angeles): Test specs for every nation (27 USA, 28 Russia) with all hidden cards incl. YJ-18; no transports in test specs.
- 2026-11-23 19:58 PST (America/Los_Angeles): Type 19 gone entirely on the model build (no test-spec card, no models in the stage).
- 2026-11-24 21:13 PST (America/Los_Angeles): Blue Dragon (23), France (24), Germany (25) and the Eurocorp country only in test mode.
- 2026-11-24 21:3x PST (America/Los_Angeles): Previews visible again with no stat card (PreviewCards.cs); K1 and K1A1 hidden (US test spec 27).
- 2026-11-24 23:5x PST (America/Los_Angeles): Test-spec units hidden from the Armory unless test mode; Blue Dragon (Preview) and the riflemen renamed.
- 2026-11-24 23:5x PST (America/Los_Angeles): K9 Thunder hidden (US test spec 27); m_k9_* banned from every package.
- 2026-11-25 11:4x PST (America/Los_Angeles): FK-3000 moved from the Medium CAB to the China test spec 26 (model broken).
