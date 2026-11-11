# Mech. Riflemen MMG — four AT4 carriers

Corrected in queued main and batch source: four soldiers each carry one AT4CS-RS. The earlier two-carriers/two-rounds implementation was wrong. The deployed/public dev.45 package remains locked and unchanged; no new package or installation is performed.

## Exact correction

- Unit370 keeps seven men: four M4A1 riflemen and three M240L gunners.
- Squad member660(officer) and661(radio) gain SpecialWeaponId59(AT4CS-RS). Existing carriers664 and665 remain. All primary weapons and soldier models are unchanged.
- Stock2906 stays linked to weapon59/ammo2000131. Quantity becomes1 per carrier instead of2; four rounds total.
- Existing squad-rate generation now sees four carriers: calculated rate19.303/min and per-carrier reload12.433s, versus15.321/min and7.833s with two. These follow the existing disposable-launcher policy; firing performance is not measured in a game. No shared weapon/ammo combat stats change.
- Exact overlay comparison against dev.45 finds three fields changed: two SpecialWeaponId assignments and one Quantity. Only squad-reload entry370:59 changes; all other constants and squad rates are unchanged.

## Source and checks

Main fix is based on pinned dev.45 commit73f7c1b48291a780610b1b4a83d0475dee5b35f1, branch codex/0.7-mmg-four-at4. Original batch lateralus-batch-0.7 receives the same correction. This does not import the separately held Troopers/M25 fix or any remaining Lateralus features.

19,894 main-source RowPlanner/reference checks and18,925 batch checks pass. The revised guard checks four distinct AT4 carriers, one round each, all four rifles and three MMGs retained, and unchanged squad size. Data generation only: no version allocated, no archive or build-ledger write. Native armory and firing remain untested.

Evidence: work/mmg-four-at4-20261110 (delta.json, generation and row-check logs).

Changelog: https://docs.google.com/spreadsheets/d/1JzyNRaXONXOyURw1i_1-cIs5DkgsSaYn0OGINvjNvPY/edit

## Document change log

- 2026-11-10 18:40:06 PST (America/Los_Angeles) — Corrected the interpretation from two carriers with two rounds to four carriers with one; verified both source branches and preserved the dev.45 deployment lock.
