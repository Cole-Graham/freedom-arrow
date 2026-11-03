# extractor

Owns all interaction with the encrypted game bundle (`data.unity3d`). Wraps the
AES + MonoBehaviour crypto (`crypto.py`) behind four verbs. No other tool
touches the bundle.

## Run

```
extractor unpack  [--bundle PATH] [--work DIR]   # bundle    -> world/_workdir (extract assets)
extractor decrypt [--work DIR] [--json DIR]      # _workdir  -> world/json     (decrypt 24 tables)
extractor encrypt [--work DIR] [--json DIR]      # world/json-> _workdir        (re-encrypt blob)
extractor pack    [--bundle PATH] [--work DIR] [--yes]   # _workdir -> bundle (DESTRUCTIVE)
extractor.bat decrypt          # Windows
```

`--work` defaults to `v3/world/_workdir/`, `--json` to `v3/world/json/`.

## Bundle resolution

In order: `--bundle` → `BA_GAME_ROOT` env → `v3/game_root.txt` → the folder the
toolkit sits in (so placing the toolkit inside your Broken Arrow folder "just
works") → `v3/data.unity3d` → well-known Steam install locations.

## Notes

- `decrypt` finds the `DataBaseCompiled` MonoBehaviour (PathID 15803), AES-CBC
  decrypts its 24 fields, and writes one JSON per table.
- `encrypt` re-encrypts the JSON back into `DataBaseCompiled.blob` in the
  workdir; `pack` injects that blob into the bundle and repacks (lz4).
- `pack` overwrites the game bundle — prompts unless `--yes`. Backups are
  `backup`'s job, not extractor's.
