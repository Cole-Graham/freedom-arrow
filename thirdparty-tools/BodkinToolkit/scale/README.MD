# scale

Project ammunition `real_world` ranges into `current` + `min_range` via the
v2 soft-cap (rational tanh) formula, preserved verbatim.

## Run

```
scale run [--only ID ...] [--dry-run]
scale.bat run              # Windows
```

Rows without `real_world` are skipped. Class heuristics (long-range / A2A /
unguided / CQB) pick the cap and per-domain multipliers. `min_range` ≈ 5% of
the compressed max. Writes back with one bulk `db load`.
