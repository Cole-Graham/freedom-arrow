# actions

Orchestration pipelines. No domain logic — they only sequence v3 tools and
halt on the first failure (propagating its exit code).

## Run

```
python -m v3.actions.import_pipeline run [--yes]
python -m v3.actions.export_pipeline run [--no-backup] [--yes]
# or the standalone entry scripts / Windows proxies:
actions/import_pipeline/import_pipeline.bat
actions/export_pipeline/export_pipeline.bat
```

**import_pipeline**: clean `_workdir/` → detect/wipe stale `json/` → `extractor
unpack` → `extractor decrypt` → `import json` → `link init`.

**export_pipeline**: optional heavy backup → `export run --in-place` →
`backup diff` (warns if nothing changed) → confirm → `extractor encrypt` →
`extractor pack`.
