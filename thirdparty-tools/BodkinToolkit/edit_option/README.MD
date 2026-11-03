# edit_option (placeholder - not implemented)

Planned interactive option editor (create/clone options, edit scalar fields and
turret overrides, park options on a "zombie" modification).

**Status:** not implemented. The interactive-editor design was never finalized,
so this tool has no entry point. Option-level data can be edited directly with
`db patch options --id N --set <field>=<value>` (dot-paths reach into maps,
e.g. `--set turret_overrides.3=12`).
