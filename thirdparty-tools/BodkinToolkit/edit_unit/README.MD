# edit_unit (placeholder - not implemented)

Planned interactive unit editor (pick a unit, view it via `link walk`, swap a
weapon with optional ammo - delegating to `bond` and `link`).

**Status:** not implemented. The interactive-editor design was never finalized,
so this tool has no entry point. For weapon replacement today use:

```
bond/bond.bat replace --unit U --old-weapon Wold --new-weapon Wnew [--ammo A ...]
```

When the editor design is settled, `edit_unit` will orchestrate `bond` and
`link` through their fronts like every other tool.
