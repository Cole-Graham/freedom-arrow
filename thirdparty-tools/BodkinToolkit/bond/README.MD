# bond

Bridge-table mutations with link consistency. v3 day-one scope: `replace`.

## Run

```
bond replace --unit U --old-weapon Wold --new-weapon Wnew
             [--ammo A]... [--yes] [--no-relink]
bond.bat replace --unit 3 --old-weapon 6 --new-weapon 270 --ammo 7   # Windows
```

Finds every turret carrying `Wold` for the unit (and the squad path). If a
turret is shared with other units, it is cloned for this unit only (auto with
`--yes`, else prompts) — turret, child turrets, and `turret_weapons` rows are
cloned and `turret_units` repointed. The weapon is then swapped, old
`weapon_ammunitions` dropped, and `--ammo` rows attached. Finally `link touch`
runs on the affected entities (skip with `--no-relink`). All writes go through
`db`.
