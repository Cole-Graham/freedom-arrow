# diff

Row + id-set (+ optional field) diff between two JSON directories or files.
Read-only; never touches `db`.

## Run

```
diff run --left DIR|FILE --right DIR|FILE [--only NAME...] [--sample N]
         [--tolerant] [--detail]
diff.bat run --left json --right json_out --detail   # Windows
```

Summary table of row counts + Δrows, then per-file id diffs (lost/forged rows),
and with `--detail` the changed fields per id. `--tolerant` repairs a truncated
JSON tail. Exit 0 only when totals match and no diffs.
