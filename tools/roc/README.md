# ROC specialization

**This branch holds the ROC specialization, kept apart from the live build. Live builds from `codex/development` never contain it. ROC rows use their own reserved IDs, so the two can merge later without number clashes.**

Requested by Osama, 25 November 2026: <https://discord.com/channels/1566969627743879208/1575071006240931931>. Unit details come from Shawn1989 in that thread.

## 📌 Rules

- **Branch:** `codex/batch/shawn/roc`, based on `codex/development`. Merge `codex/development` into it to stay current. Never rebase it or force-push it.
- **Files:** ROC data lives in `tools/roc/` only. Live files stay untouched, so merges from development do not conflict.
- **IDs:** the ROC blocks are in `mod/id-reservations.json`: units 5000-5999, options 28000-28999, specializations 60-69, country 9, every other table 2900000-2999999. The build enforces them (`pla_graph.Graph`, `tools/pla-specs/roc_hook.py`).
- **New rows:** make them in `roc.py` with `g.add(table, row_to_copy, fields)`. It takes the next free ROC ID.
- **Names:** unit `Name` starts with `ROC `; model keys `m_roc_*`; icons `FA_ROC_*`.

## 🔁 Load and unload

- **Load:** a ROC test build is a normal gameplay build made from this branch. The batch runs `roc.py` last, after every live section, so live IDs stay the same.
- **Unload:** install the normal dev build from `codex/development`. It is gameplay-only, so only the gameplay file (about 211 MB) downloads again.
- **Merge into live:** only when Osama approves. The ROC rows keep their IDs.

## Test build 0.9.7-roc4 (build 366), 26 November 2026

**On the dev launcher as a test build: gameplay `0.9.7-roc4` + Models & music `0.2.104-roc4`. Osama approved it and asked for it to be built on his PC (Vengeance) to spare the deck.**

- Gameplay: <https://freedomarrow.app/gameplay/FreedomArrow-0.9.7-roc4.bamod> (sha256 582473dd…, 234 MB). Models & music: file list <https://freedomarrow.app/assets/index/FreedomArrow-Assets-0.2.104-roc4.files.json> (13,716 files, 443 new on R2).
- Contents: 0.9.7 + development (f2f93318) + ROC spec 60 (48 cards, ROC squads and weapons), 21 ROC vehicle and aircraft models, 7 infantry bodies, the T91 rifle, ROC FAModels (reads infantry-bodies-*.json, accepts 5000-5999).
- Checks: 6,449 batch checks; queued changes, multiplayer equipment, battle triangles, slots, fields, swap prices, mounts, squad HP, infantry armour and model carry all pass.
- ROC-branch packager changes: a -rocN build names its models 0.2.104-rocN (never a live number); the version check tolerates the suffix; -rocN sorts just after its base; the DLL version check reads a 10-character version (re.S). The ROC receipt stays out of the shared out/receipts.
- **Build number clash:** the Light Brigade thread also used 366 (0.9.7l-dev.4) while this built; the ROC receipt is kept out of the shared receipts, so they did not see it. Versions are distinct and nothing reads the number for loading; the next ROC build takes a fresh number.
- Built on Vengeance under /home/sam/tars (scratch, kept for the next ROC build): zip and pycryptodome in a scratch venv; inputs copied with rsync at idle priority while Broken Arrow was running.

## Test build 0.9.8-dev.2-roc5 (build 394), 27 November 2026
**On the dev launcher as a test build: gameplay `0.9.8-dev.2-roc5` + Models & music `0.2.109-roc5`. Osama: "Build the Roc dev". The deck was idle, so it was packaged on the deck.**
- Gameplay: <https://freedomarrow.app/gameplay/FreedomArrow-0.9.8-dev.2-roc5.bamod> (sha256 691dcf85…, 252 MB). Models & music: file list <https://freedomarrow.app/assets/index/FreedomArrow-Assets-0.2.109-roc5.files.json> (14,260 files, 388 new on R2).
- Contents: 0.9.8-dev.2 + ROC (cb27b99d): ROC spec 60, 25 ROC model entries (27 Nov weathering/camo, CM-32 v3, EC225 livery v2, CM-33 removed), 7 PBR infantry bodies (atlas v2), T91 and Kestrel rules, paint schemes, ROC FAModels.
- Checks: 7,090 batch checks; queued changes, multiplayer equipment, battle triangles (max 59,682), slots, fields, swap prices, mounts, squad HP and infantry armour pass. The model carry check reports 2 mappings (PLA ZTZ-99A, PLA Catalogue ZTZ-99) that changed in 0.9.8-dev.5, after this build's dev.2 base; the check script was updated for dev.5. Not a ROC change.
- The ROC receipt is kept in out/local-098d2roc5r394, not out/receipts (live packagers would fail to parse a -roc5 Models version).
## Document change log

- 2026-11-25 01:0x PST (America/Los_Angeles) — Branch created: empty `roc.py`, reserved ID blocks, load/unload notes.
- 2026-11-26 04:31 PST (America/Los_Angeles) — Test build 0.9.7-roc4 (build 366) built on Vengeance and published to the dev launcher.
- 2026-11-27 11:03 PST (America/Los_Angeles) — Test build 0.9.8-dev.2-roc5 (build 394) built and published to the dev launcher.
