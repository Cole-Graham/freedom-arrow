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

## Model build only (`codex/batch/osama/models-096`)

| Card | Unit | Was in | Section | Requested |
|---|---|---|---|---|
| ZTZ-98 | 'PLA ZTZ-98' (1309 in 0.9.6-dev.12) | PLARF Rocket Conscript Force | `roster_1123b.py` | Osama 23 Nov 18:1x |
| Type 19 | see `type19_removed_1123.py` | Blue Dragon | `type19_removed_1123.py` | Osama 23 Nov 18:0x (blue dragons thread) |

## Moved (not hidden)

- ZTQ-15 (906): PLAGF Armored Force -> PLAGF Motorized, 6 cards (Osama 23 Nov 18:0x). `roster_1123b.py`.

## Document change log

- 2026-11-23 18:20 PST (America/Los_Angeles): First version: YJ-18, VN20, VN-17, VT-5 (+Recon), ZTZ-59, PCL-181, HQ-6A, ZSL-92, ZTZ-98 and Type 19; ZTQ-15 move.
- 2026-11-23 18:24 PST (America/Los_Angeles): PLZ-70 added.
