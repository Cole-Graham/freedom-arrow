# Lateralus selected promotion — main dev.34

Changelog items 3, 5 and 7–12 are published in main-build package dev.34. Items 1, 2, 4 and 6 remain separate batch proposals or test features. The package was not installed or tested in a game during this promotion.

## Included

- 3: F-22 and MiG-29K target dummies have no specialization entries and remain editor test targets. Allocate then remove the two deck rows to preserve later IDs.
- 5: passive AA observer from lat.4, with finite/non-finite JSON handling and corrected aiming-time labels. Zero native targeting/scoring diagnostic detours; no cooldown behavior hook. Existing shot callbacks only enqueue signals for later observation.
- 7: RMG damage4 and100% Ignore Cover.
- 8: standard SMAW-D25% Ignore Cover, shared by Mech. Engineers and CQC.
- 9: Mech. Engineers CQC55, including its +10 option over the45-point parent.
- 10: Mech. Riflemen MMG4 AT4CS-RS total, two rounds per existing carrier.
- 11: HIT ammo shown as84mm Thermobaric, damage6.5,100% Ignore Cover; other stats retained.
- 12: Combat Engineers75.

## Still held in the batch

1: helicopter flare stock15. 2: separate helicopter missile range. 4: plane refund and ammo-price rework. 6: SPAAG range/damage and cooldown experiment, including the lat.5 behavior hook. Do not merge the entire historical batch or its17 old native diagnostic detours.

The original batch source is retained as historical working material; the selected items are no longer pending. Base any future remaining-batch build on this main revision and apply only the held features. This avoids reverting the newer LOSAT/M25 work or restoring the old logger.

## Evidence and delivery

- Main base: dev.33, fc4941d. Preserved LOSAT damage10,KE550,speed1300,10-second firing gap and current M25 teams.
- Main source: codex/0.7-lateralus-promote,30f844805c39330a625732964cd5e5df1988c005.
- Source URL: https://github.com/Cole-Graham/freedom-arrow/commit/30f844805c39330a625732964cd5e5df1988c005
- Download: https://drive.google.com/file/d/1g4RZvoIuBN2nfW7Yo60uW8KXUq-7S0Tr/view
- Package SHA256: d3ede473f750101542d3fc050525279037cd9f21ce39a6f826656330ca2b0b49;121356481bytes.
- 19,455 existing RowPlanner/reference checks,47 passive-observer policy/compiled-IL checks,67 payload hashes and anonymous download verification pass. Runtime and offline projects build with0warnings/0errors.
- Exact effective-data comparison:10 changed infantry fields and2 dummy deck entries removed; other rows unchanged. Held batch contracts/gameplay config unchanged. Scope and logs: work/lateralus-promote-20261110 in BA Codex's workspace.
- Changelog updated in place: https://docs.google.com/spreadsheets/d/1JzyNRaXONXOyURw1i_1-cIs5DkgsSaYn0OGINvjNvPY/edit
- Existing build index updated and read back. Canonical local live alias points to dev.34. No Vengeance installation, runtime test or GitHub main-branch push.

## Limits

This is data/code/package verification, not a new combat result. Lat.4 previously logged172seconds and66AA shot observations in Lateralus's supplied run; its27.5ms peak observer work remains unresolved. The passive logger samples state and cannot give exact native rejection reasons or a complete interception kill count. Broader Bible/cloud report synchronization is pending.

## Document change log

- 2026-11-10 04:28:44 PST (America/Los_Angeles) — Promoted only the selected eight changelog items to main dev.34, recorded retained batch features, and verified source/package/download/index without installation or native testing.
