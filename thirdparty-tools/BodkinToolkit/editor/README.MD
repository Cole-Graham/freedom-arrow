# editor

Guided, interactive unit editor. Makes *connected* changes to the db so the
game stays consistent: when you touch a child entity (armor, mobility, sensor,
ability, turret) that other units share, it offers to clone a private copy
instead of altering everyone's.

## Run

```
editor                       # pick a unit interactively
editor --unit 3              # preselect by id
editor --unit BMP-3 --yes    # preselect by name; auto-confirm clones
editor.bat --unit BMP-3      # Windows
```

Reads/writes go through `db`; weapon replacement delegates to `bond`. All
changes are saved to the db on exit; run `export` + `extractor pack` (or the
export pipeline) to apply them to the game.

## What it edits

| Menu item | Effect |
|---|---|
| Specializations | deck membership (multi-select); add/remove `specialization_availabilities`, cascade-removes orphaned transports |
| Price | `units.cost` |
| Transport availability | carrier units that can transport this unit; resolve carrier by id or partial name |
| Armor | armor HP / kinetic / heat values (shared → clone-or-alter) |
| Mobility / speed | speeds, agility, amphibious; **aircraft vs ground** menus differ; aircraft expose the fly-preset model (shared → clone-or-alter) |
| Optics / sensors | optics ground/low/high (shared → clone-or-alter) |
| Stealth | `units.stealth` |
| Replace weapon | swap weapon X→Y across turrets + squad, with multi-ammo; delegates to `bond` (shared turrets → clone-or-alter) |
| Modifications | create slots; create options (empty template or clone); edit option scalars and turret overrides (with hints on which other options use each turret slot) |
| Abilities | view; edit quantities / cooldowns. ("Limitless" deferred until the unlimited sentinel is confirmed.) |

## UI

Built on `core.ui`: single/multi choice menus and multi-level editable forms
that show each field's current value (and default). Arrow-key menus when a TTY
+ questionary are present; numbered fallback otherwise.
