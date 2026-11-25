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

## Document change log

- 2026-11-25 01:0x PST (America/Los_Angeles) — Branch created: empty `roc.py`, reserved ID blocks, load/unload notes.
