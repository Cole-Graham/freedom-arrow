# check_patch

Diagnose "I patched my game and nothing changed". Compares live `json/` to a
chosen backup and prints signals.

## Run

```
check_patch run [--backup NAME]
check_patch.bat run            # Windows
```

Runs `diff` against the backup, then reports: ammo rows where `current` differs
from `vanilla` (scale applied), options matching author fingerprints
(`test`, `custom_option_empty`, `__zombie__`), and modifications without exactly
one default option. Verdict states whether live differs from the backup.
Without `--backup`, presents an interactive picker.
