# link

Relationship service. Computes the derived `link_info` block on canonical
entities and walks the entity graph. Reads/writes through `db`.

## Run

```
link show <table> <id>                 # compute + print (no write)
link touch <table> <id> [<table> <id>...]   # recompute + persist for pairs
link init                              # recompute + persist for every row
link walk <table> <id> [--depth N] [--down-once] [--fields-on t=f1,f2]
link.bat show units 3                  # Windows
```

`show`/`walk` recompute live from the graph. `touch`/`init` persist via a bulk
`db load` per affected table. Bridge tables have no `link_info` (`show` errors).
`init` over the full game database runs in a few seconds.
