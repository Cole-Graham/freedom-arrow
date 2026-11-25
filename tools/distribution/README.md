# Automatic distribution and retention

**The launcher reads a stable public manifest, downloads and verifies gameplay plus models/music/voices, and keeps matching archives cached. The current manifest remains locked to dev.45. Hosted artifacts keep the latest two versions per stream plus locked/current versions and their dependencies.**

## Build and verify

`python tools/distribution/build_launcher.py --out OUTPUT` builds the Windows launcher ZIP without game packages. Source is BAModLauncher, with a separate Freedom Arrow mode. Its version manifest endpoint is compiled in HostedDistribution.cs; Windows AppData stores its cache. The bundled gameplay/asset specs are a display/bootstrap fallback only; PLAY must obtain a validated live or last verified cached manifest before installation. Generic BAModManager mode does not run this path.

`dotnet run --project tools/manifest-tests -c Release -- tools/distribution/live-manifest.json` executes manifest, lock, downloader, cache, retry, resume, cancellation and corruption checks. Add --network for an empty-cache real public download test; --network-reuse verifies an existing dedicated test cache. The network test uses its own settings identity. `dotnet run --project tools/launcher-dev45-tests -c Release -- GAMEPLAY_ARCHIVE ASSET_ARCHIVE` checks the actual installer. Native Windows/game behavior is separate from these checks.

The stable manifest lives in Drive file1NvdXaFJrqkuOeZAceTo9s8iSyedAfRqE. It has schema1, live current/locked versions, and explicit package IDs, versions, filenames, public HTTPS URLs, sizes and SHA256 values. The lock selects the playable release even if current points to a newer candidate. Missing, unsupported, ambiguous or invalid data blocks installation. An invalid online manifest does not silently fall back; a network failure may use the last fully verified cached manifest. The new manifest is committed to cache only after both packages verify. Interrupted downloads resume when the server supports Range; otherwise they restart. Cache files become final only after size/hash validation.

## Publishing

On the deck, canonical state and manifest are work/build-install/state.json and live-manifest.json. bin/ba-publish-manifest VERSION GAMEPLAY_FILE DRIVE_URL verifies archive identity and public Drive metadata/hash, updates the stable manifest file in place, and reads it back anonymously. Pass --assets ASSET_FILE when the published asset version changes. The current playtest lock blocks other gameplay versions. The build-install updater invokes this publisher before changing public posts, then starts the guarded retention service.

Installed helpers are copies of publish_manifest.py and retention.py under the BA root bin directory. build_install_update.py records the deployed updater integration. The repository live-manifest.json is the dev.45 test fixture, not a second live endpoint.

## Per-file Assets updates (launcher 1.1.5)

**From launcher 1.1.5 a new Assets version downloads only the files that changed. Dev builds and launchers up to 1.1.4 still use the full Assets package.** (Lateralus, 17 November 2026.)

`python tools/distribution/publish_assets_index.py ASSETS.bamod` hashes every installed file of the package (Mods/, Plugins/, UserData/, UserLibs/). It uploads each content that R2 does not have yet, gzipped, to `https://freedomarrow.app/assets/files/<sha256>.gz`, and writes the file list to `https://freedomarrow.app/assets/index/<package>.files.json`. It never replaces or deletes an R2 object. bin/ba-publish-manifest then adds `assets.index` (URL, size, SHA-256 of the list) to the manifest when a list exists for that exact package.

The launcher downloads the list (checked against the manifest) instead of the full package. For each file it keeps what is already on disk with the right size and SHA-256, and downloads the rest, 8 at a time. Identical content at several paths is downloaded once. Each file is checked before it replaces the old one. A file that the previous list installed and the new list dropped is removed only if it is unchanged. The player's voice and music preferences are kept, as in the full-package install. Hashes are remembered by size and write time, so a launch with nothing changed reads each file once only after it changes.

`dotnet run --project tools/assets-index-tests -c Release -- tools/distribution/live-manifest.json` runs 21 offline checks; add `--network` for a real download of 25 files from the live 0.2.44 list.

Measured on our packages: 0.2.40→0.2.41 changed 66 files (56 MB), 0.2.41→0.2.42 210 files (98 MB), 0.2.42→0.2.43 26 files (35 MB), 0.2.43→0.2.44 4 files (under 1 MB). The full package is 6.48 GB. Assets 0.2.44 has 10,995 files with 4,011 distinct contents.

## Retention

bin/ba-retention --drive --github previews the policy; --apply performs cleanup. Only recognized BA archive names inside the two grounded BA package folders are eligible. Unknown files, reports, images, unrelated files and other folders are untouched. Current public download IDs, profile archives and manifest package references are protected on every mutation. Drive uses Trash with a JSON restore ledger at work/release-retention/actions.jsonl. Newest-two uses semantic version order within gameplay, assets, PLA, Lateralus-test and launcher streams; historical PLA prototypes sort below current integer TEST builds. Unlinked duplicate copies can be retired.

GitHub release inventory uses gh release list (which includes the historical prereleases); the REST list returned only two stable releases during this task and was not sufficient. Deletion goes only through bin/ba-gh release delete with --cleanup-tag and the explicit human request link. No new releases are created. STOP, write pacing and six-release-writes/day guards remain in force. A run removes at most six and defers the rest. Source history and active feature branches are retained; branch cleanup requires an agreed scope.

ba-hosted-retention.timer runs daily at20:00 America/Los_Angeles with a short randomized delay and catches up after downtime. The service invokes the same helper, so deferred GitHub cleanup continues within its existing caps. The timer/service definitions are included here. The build-post updater also starts it after publication.

## Dev launcher (internal)

Lateralus, 24 November 2026: "develop a dedicated launcher for internal/dev use only, where I can select various test builds and dev builds, and make sure it uses incremental asset updates as well".

**In short:** `FreedomArrowDev.exe` is the Freedom Arrow launcher with a **DEV / TEST BUILD** picker. It reads its own signed list, `https://freedomarrow.app/manifest/dev.signed.json`, and installs the picked build. Models and music always update file by file, also when an older build is picked. The player launcher and its list are not changed.

**Details**

- Build: `python3 tools/distribution/build_launcher.py --dev --out DIR --dotnet DOTNET` (MSBuild property `DevChannel=true`, constant `FA_DEVCHANNEL`). Output: `FreedomArrowDev.exe`, version line 1.x of its own.
- Own settings folder `%AppData%/FreedomArrowDevLauncher` (download cache, accepted list, picked build in `downloads/dev-build.txt`), so it never touches the player launcher's cache or its accepted live list. Both can be installed side by side.
- The dev list has channel `dev` and is signed with the same key. The player launcher refuses it (channel `live` only) and the dev launcher refuses the live list. Up to 60 builds. Every build must have a Models + Music/Voices file list; a list entry without one is refused, so the dev launcher never downloads a full Assets package.
- Picker: "Newest build" (follows the list's newest build) or one exact build. A picked build that leaves the list falls back to the newest.
- The list is read again every 2 minutes, when the window comes back to the front (at most every 30 s), with the ↻ button and before PLAY, so new builds appear without a restart (1.0.1, Lateralus 24 Nov).
- Models + Music/Voices: the picked build's exact files. The player launcher keeps a newer installed Assets version; the dev launcher replaces it with the picked one and downloads only the files that differ.
- List tool (BA deck): `bin/ba-dev-manifest add BUILD.json` checks the gameplay file on R2 (download, size, SHA-256, mod.json version) and the Assets file list, then signs and uploads the list and reads it back. `list`, `drop VERSION` and `launcher EXE` (self-update entry) are the other commands. `work/build-install/devpost.py` runs `add` for every dev build it posts. A build whose Assets version has no file list needs `publish_assets_index.py ASSETS.bamod` first.
- Tests: `tools/dev-launcher-tests` (compiled with `FA_DEVCHANNEL`): 14 offline checks (list rules, picker choice, switch to a newer and back to an older Assets version file by file) and `--live` (the real signed dev list, every file list in it, and the download size of each switch).

## Evidence limits

Manifest/downloader checks:20 offline fixtures plus3 real public network/cache checks passed. Installer checks:24 passed, including fresh asset hashes, existing skin/preference preservation, missing model binding merge and newer asset preservation. Retention planning:6 tests passed. The Windows executable opened in isolated Wine; no game was started. Native Windows game launch remains unverified. No gameplay build or PC installation was changed.

## Document change log

- 2026-11-10 19:38:30 PST (America/Los_Angeles) — Added stable manifest distribution, verified cache/download behavior, publisher integration, latest-two-plus-locked retention and daily guarded cleanup.
- 2026-11-17 13:12 PST (America/Los_Angeles) — Added per-file Assets updates (publish_assets_index.py, manifest assets.index, launcher 1.1.5, tests).
- 2026-11-24 18:1x PST (America/Los_Angeles) — Added the internal dev launcher FreedomArrowDev.exe and its signed dev build list (Lateralus).
- 2026-11-24 18:3x PST (America/Los_Angeles) — Dev launcher 1.0.1: build list refreshes without a restart (↻ button, 2-minute and window-activation re-reads).
