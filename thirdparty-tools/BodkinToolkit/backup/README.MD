# backup

Snapshot/restore JSON state (light) and the game bundle (heavy).

## Run

```
backup make light|heavy|both [--name PREFIX] [--bundle PATH] [--yes]
backup list [--kind light|heavy]
backup restore [--kind ...] [--name PATTERN] [--yes]
backup diff <name-or-pattern>          # invokes the diff tool vs live json/
backup.bat make light --name preedit   # Windows
```

Light → `backups/light/<name>_<ts>/` (copies `json/*.json`). Heavy →
`backups/heavy/<name>_<ts>/` (filesystem copy of the bundle; no crypto).
Restore and overwrite are destructive — prompt unless `--yes`.
