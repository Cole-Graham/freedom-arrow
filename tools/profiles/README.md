# PLA and live build selection

**PLA means the complete integer-numbered PLA Build1 package. Never infer the requested build from an old filename or select the historical infantry prototype.**

The manifest`profiles.json` pins the exact file, version and archive hash. Keep the current manifest with the installed switch tool. Commands are `python3 switch.py pla` and `python3 switch.py live`; both require the game closed. `--check` validates without installation.

Switches preserve shared model/music files and user voice preferences, replace gameplay as one unit, remove obsolete gameplay markers, update BAModManager selection by stable package ID, and create a console-only restore command. PLA preflight checks QLU11/QTS11 membership and saved offsets. An unknown or corrupted archive stops before any write. Four fixture tests cover PLA→live→PLA retention, preferences, bad archive, bad alignment and read-only validation. These are host checks, not native game evidence.

The complete PLA archive contains all required assets. The live profile uses the existing live package and retains those shared installed assets. Do not disable/uninstall PLA between switches; use the pinned switch command. Profiles retain game saves but do not promise conversion of decks between incompatible rosters. Current profile names and package versions belong in the manifest, not filename globs.

## Document change log

- 2026-11-10 02:46:20 PST (America/Los_Angeles) — Added explicit PLA/live aliases, package guards, retained assets and tested rollback-based switching; native/deck limits stated.
