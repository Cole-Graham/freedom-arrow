# Unit standards

Lateralus, 26 November 2026: "When Osama is making new units they should use all the mod's design standards for reloading, etc."

Every rule below is checked on each run of `tools/pla-specs/batch_0_9_5b.py`, including `--check`. A new or changed squad that breaks a rule stops the batch with the reason. To change a rule, change its check in the same commit.

## Infantry launchers

- **Disposable launchers (Weapons.Type 63, magazine 1) hold one round per carrier.** More rounds means more carriers (`SpecialWeaponId`), never `WeaponAmmunitions.Quantity` > 1 (Lateralus 23 Nov). Only vanilla's MRO-Z ×4 and RPO-M ×2 are exempt. Check: `disposable_launchers_1123.check`.
- **Disposable squad rate = 12.16 × carriers^(1/3) per minute** (Lateralus, 0.5 dev.35; `mod/squad-rof-contract.json`). `SquadReload.cs` sets each squad's reload to 60 × carriers ÷ rate from `squad-reload.json`. The batch rebuilds that table from the current squads every time (`unit_standards.squad_reload_table`), so new squads and changed carrier counts are always included.
- **Reusable launchers (Type 62, magazine 1) fire at a fixed squad rate: 10 per minute with 1 carrier, 15 with 2,** counted from the carriers still alive (`SquadReload.cs`, Lateralus 26 Nov). A squad may carry **1 or 2** of one reusable launcher. Check: `unit_standards.check`.
- **Launcher type matters.** The rate rules read Weapons.Type (62 reusable, 63 disposable). A new launcher must have the right type.

## Infantry weapons

- **One name, one set of stats** (Lateralus 26 Nov). An infantry weapon fires the same round, at the same damage, on every squad. Do not make per-squad tier variants (the vanilla T1/T2/T3 pattern). Vehicle-mounted weapons may differ. Check: `unit_standards.check`. `unit_standards.KNOWN` lists the cases already in the game (Ksp 58B; M249 Para T1/T2/T3), with their exact damages. Adding another damage to them also fails.
- **Reuse rows.** Link existing weapon, round and ability rows when the stats are the same. Copy a row only when the stats really differ, and say why in the commit. No `[TEST]` copies (Lateralus 26 Nov).

## Data the game needs

- **Every weapon row on a unit needs an ammo row**, or the game drops all Freedom Arrow data. Check: `weapon_coverage_check`.

## Document change log

- 2026-11-26 17:3x PST (America/Los_Angeles) — Created: launcher and infantry weapon standards, enforced by the batch (`unit_standards.py`); the disposable squad rate table is now rebuilt from the data each build.
