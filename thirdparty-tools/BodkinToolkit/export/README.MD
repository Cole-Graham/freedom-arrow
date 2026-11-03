# export

Rebuild game JSON from `db` rows. Inverse of `import`.

## Run

```
export run --out DIR            # write to a directory
export run --in-place           # write back into json/ (light backup first)
export one <table> --out FILE
export.bat run --out json_out   # Windows
```

Canonical tables start from the baseline JSON (default `v3/world/json/`, override
with `--baseline DIR`) so unmodelled game fields survive; db-managed fields are
overlaid. Ammunition `current` is halved back to `GroundRange`/`LowAltRange`/
`HighAltRange`; sparse option overrides are re-densified. `link_info` is never
written. Round trip is byte-exact (verified on the full game database).
