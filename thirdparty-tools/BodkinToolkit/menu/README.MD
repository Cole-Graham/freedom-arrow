# menu

The toolkit's top-level entrypoint — an interactive launcher that preserves the
legacy nested-menu structure (arrow-key nav on Windows, typed-number fallback
elsewhere) but drives only the new self-contained v3 tools.

## Run

```
menu.bat                # Windows
run.bat                 # same, from the project root
python menu/menu.py     # any platform
```

Every item dispatches to a tool through its single front (`core.proc.run_tool`)
or to a pipeline front (`core.proc.run_entry`); `menu` imports no tool
internals and reads/writes nothing outside `/v3/`.

## Structure

```
Backup ...            make / restore / list
Game files ...        unpack / decrypt / encrypt / pack   (extractor)
Database ...          import / export / link init / walk / show
Ammunition ...        research / scale
Mutations ...         bond replace  (+ edit_unit/edit_option placeholders)
Diagnostics ...       diff / check_patch / backup diff
Import pipeline       clean -> unpack -> decrypt -> import -> link init
Export pipeline       backup? -> export -> diff -> encrypt -> pack
Quit
```
