# import

Translate game JSON (`v3/world/json/`) into `db` rows. Inverse of `export`.

## Run

```
import json [--from DIR] [--yes]
import one <table> [--from FILE]
import.bat json            # Windows
```

PascalCase→snake_case per table; unknown JSON fields dropped. Ammunition
ranges are doubled into `current`/`vanilla` (JSON stores half-range) and
`real_world` is seeded null. Options collapse dense `TurretNId`/`AbilityNId`
and zero scalar overrides into sparse `turret_overrides` / `ability_overrides`.
Each table is pushed with a single `db load` (O(N)).

`--yes` skips the "db already populated" prompt.
