# Release data

**Short answer.** Each folder holds the full game-data constants of one released playtest, exactly as they shipped
(`UserData/FreedomArrow/constants/` from that release's gameplay package). Repo cleanup step 4 (Lateralus, 22 November 2026):
a build can start from these files in git instead of a chain of earlier packages plus batch scripts.

---

- `<version>/constants/*.json`: the 24 constants files of that release.
- `<version>/SOURCE.json`: build number, package file name and its sha256, checked against `out/receipts` when copied.
- Add a folder when a playtest is released (copy from its gameplay package and check the sha256 against its receipt).

## Document change log

- 2026-11-23 10:5x PST (America/Los_Angeles) — Created with releases 0.9.1 to 0.9.5 (repo cleanup step 4).
