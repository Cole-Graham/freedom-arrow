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
| QJZ-89 Team (Armored) | 1157 | PLAGF Armored Force, 4 cards (the PLARF QJZ-89 Team 1170 stays) | `qbz95_qjz89_1123.py` | Osama 23 Nov 18:3x "QJZ-89 PLAGF Armored Force ... hidden" |
| OH-58D Recon Optronic | 733 | Air Naval, 4 cards | `recon_helis_us_1123.py` | Lateralus 23 Nov 18:3x "remove the OH-58D Recon Optronic from the mod (or just disable it/hide it from the menu)" |
| MH-6 Little Bird Recon | 736 | Special Operations Forces, 4 cards | `recon_helis_us_1123.py` | Lateralus 23 Nov 18:3x "remove the MH-6 Little Bird Recon" |
| AH-64D Longbow Recon | 746 | Air Naval, 4 cards | `recon_helis_us_1123.py` | Lateralus 23 Nov 18:3x "remove the AH-64D Longbow Recon" |

## Model build only (`codex/batch/osama/models-096`)

| Card | Unit | Was in | Section | Requested |
|---|---|---|---|---|
| ZTZ-98 | 'PLA ZTZ-98' (1309 in 0.9.6-dev.12) | PLARF Rocket Conscript Force | `roster_1123b.py` | Osama 23 Nov 18:1x |
| Type 19 | see `type19_removed_1123.py` | Blue Dragon | `type19_removed_1123.py` | Osama 23 Nov 18:0x (blue dragons thread) |

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
