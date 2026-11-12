# Lateralus infantry follow-up — 10 November 2026

All six requested edits are promoted into the main-build candidate at Lateralus’s request, together with editor-only dummies and the passive AA observer. Existing devtest.lat.5 does not contain these infantry edits. Native gameplay remains untested.

## Changes

- RMG (ammo 121, Grenadiers unit 622): damage 10.5 → 4; IgnoreCover 0.5 → 1 (100%). Penetration, splash and every other field stay unchanged.
- Standard SMAW-D HEDP (ammo 128): IgnoreCover 0.5 → 0.25 (25%). Shared by Mech. Engineers 146 and Mech. Engineers CQC 708; damage remains 8.5.
- Mech. Engineers CQC (unit 708): cost 50 → 55. Its replacement option 3348 rises from +5 to +10 over Mech. Engineers at 45, so both direct and configured costs are 55.
- Mech. Riflemen MMG (unit 370): 2 → 4 AT4CS-RS total. Stock row 2906 remains linked to weapon 59 / ammo 2000131. Quantity 1 → 2 per carrier; the two existing carriers are unchanged. This does not add launchers or change the firing cycle.
- Combat Engineers' SMAW-D HIT ammunition (ammo 937): shown ammo name 84mm HE → 84mm Thermobaric; damage 8.5 → 6.5; IgnoreCover 0.5 → 1 (100%). All other fields stay unchanged, including 45 penetration, 8 m health blast radius, ranges, projectile speed, effects and supply costs. The launcher name remains SMAW-D HIT; the requested ammo label changes.
- Combat Engineers (unit 449): cost 65 → 75.

## Verification and limits

Read from pinned game data and the generated batch overlay; theoretical, not yet proven in a game. The full effective-table comparison finds exactly 10 changed fields across ammunition, units, one option and one stock row. The other 20 tables are unchanged. The existing row/reference test suite passes, including configured price, unchanged carriers, stock links and ammo checks. See `work/lateralus-infantry-20261110/row-tests.log` and `effective-delta.json` in BA Codex's workspace.

These source edits update `infantry-rl-contract.json`, `vehicle-contract.json`, their generator and existing row checks. No runtime hook changes. This older batch's historical AA diagnostic detours remain unsuitable for shipping; use the passive observer from the separate test branch when preparing a future package.

## Sources

- Lateralus request: https://discord.com/channels/1566969627743879208/1568104480459722894/1569682984011833436
- Batch remote branch: codex/0.7-lateralus-batch-proposal (local lateralus-batch-0.7).
- Lateralus 0.7 changelog: https://docs.google.com/spreadsheets/d/1JzyNRaXONXOyURw1i_1-cIs5DkgsSaYn0OGINvjNvPY/edit

## Document change log

- 2026-11-10 04:07:24 PST (America/Los_Angeles) — Queued six infantry/ammo changes, traced shared ammo and configured pricing, and verified exactly 10 effective field changes without building a test package.

- 2026-11-10 04:23:12 PST (America/Los_Angeles) — Promoted these six queued source edits into the separate main-build candidate; earlier no-build status is superseded.
