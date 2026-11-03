# db

Storage + schema authority. Field-level CRUD over YAML tables in
`v3/world/yaml/<table>.yml`. Every other tool reaches storage only through `db`.

## Run

```
db <verb> ...        # or:  db.bat <verb> ...   (Windows)
python db/db.py <verb> ...
```

`db` (no args) or `db ?` prints the capability summary.

## Verbs

| Verb | Purpose |
|---|---|
| `get <table> --id N` / `--where f=v ...` `[--fields a,b]` | read row(s) |
| `all <table> [--fields a,b]` | human record-block dump |
| `count <table>` | row count |
| `next-id <table>` | `max(id)+1` |
| `find <table> <field...> <needle> [--sep C] [--exact]` | search |
| `put <table> [--id N] --set k=v ...` | upsert (dot-paths into maps OK) |
| `patch <table> --id N --set k=v ...` | update existing only |
| `delete <table> --id N [--yes]` | remove (destructive) |
| `load <table> [--from FILE]` | **bulk** replace table from a YAML list (stdin/file) |
| `dump <table>` | emit a table as a machine-readable YAML list |
| `schema show \| add-field \| rename-field \| change-type \| deprecate \| bump` | schema evolution |

`load` / `dump` are the bulk in/out primitives (added to keep `import`,
`export`, `link`, `scale`, `research`, `bond` O(N) instead of O(N²) from
per-row `put`/`patch`). They validate against the active schema like `put`.

## Value typing on `--set`

`true`/`false`→bool, `null`→None, bare int/float→numeric, `'123'`→forced
string, dotted key (`current.ground=5000`) writes into a map field.
