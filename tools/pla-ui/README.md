# China Arsenal UI candidate and Mod Launcher compatibility

**PLA TEST Build 5 is an offline-built UI candidate. It adds a China country and five provisional specialization groups. The native hooks compile, all existing Build 4 model/music/infantry asset bytes are preserved, and the launcher core accepts a fresh local-file installation in a temporary test folder. Your installed game and public download remain dev.45.**

## What changed

- China is country4. Existing Russian and US countries and non-PLA units are unchanged.
- The China Arsenal row is placed before Russia by the native country-group initialization hook. The native filter capacity accepts a third visible country.
- The native deck-country popup receives China through database data; its actual button and callback remain the game's own.
- Specializations17–21: Airforce / SF, Ground Force / Armored, Rocket Force / Conscripts, Naval / Marines and Motorized.
- Existing PLA availability rows are assigned to provisional groups. No new unit, weapon, armor, price, ammunition or transport row is created. All175 fitted comparison-squad members remain.
- Six small code-drawn sprites are embedded in the PLA runtime. The supplied attachment could not be fetched (HTTP403; unsigned alternatives404); the clean flat flag and five generic badges are placeholders, not an edit of the supplied photo or final official branch insignia.

## Verification and limits

**Compiled/data evidence:** native runtime builds with zero warnings/errors;39,394 real RowPlanner/reference checks pass;7,934 complete payload hashes and72 core hashes pass. All7,922 untouched payload members match the pinned Build4 archive, including every model, infantry binding, offset and music file.

**Visible preview:** two browser screenshots were posted in the original task thread. They show an explicitly labelled interactive layout preview, not the native game. Provisional buttons filter candidate names. Native layout, flag rendering, localization, clicks and deck creation remain untested.

**Network limitation read from game code:** NetworkCommon.Enums.Country is a byte enum with Random0, Russia1 and USA2. China4 is absent. A third database country does not establish online or campaign support. This candidate is for menu/UI testing; no multiplayer test was attempted.

**Live preservation:** neither canonical profile alias was promoted. No game files, launcher settings or download post were changed for this candidate. Public dev45 lock remains. The complete PLA candidate retains Build4 assets; it does not claim to incorporate later live-only Abrams X finish overrides. A future install must preserve those separately.

## Launcher findings

The linked-source harness runs the actual vendored LauncherService, ModService, package parser, activation, manifest and install code. Only branding/localization are stubbed. All writes occur in a temporary fake game directory with a private compatibility-test settings ID, followed by cleanup.

- Existing dev45 `.bamod`: a fresh configured launcher's local-file path rejects it. Its `mod.json` has no `repo`, and no existing matching installed package is present. This reproduces an integration defect; it does not mean the launcher could never install45 through its automatic release path.
- Candidate Build5: adds `repo: Cole-Graham/freedom-arrow`. The fresh local-file path accepts it and installs7,935 planned files, then finds the enabled `freedomarrow.gameplay` package. No Manager GUI is used.
- Automatic download is a separate unresolved path. The vendored launcher requests `/repos/{repo}/releases/latest` and selects the first `.bamod`. Git branches and Drive links do not configure that feed. Publishing a release with multiple packs can select the wrong asset, and current Stable/Testing config uses different repositories rather than branches.
- No new GitHub release was created, no auto-update channel was redirected, and no player launcher was advertised as ready. Windows GUI, first-run MelonLoader download, HTTP504 recovery, automatic core/assets downloads and PLAY require separate end-to-end validation.

Lateralus's thread1568104480459722894 is independently preparing the dedicated dev45 launcher. Shared compatibility evidence is also in `work/launcher-dev45-compatibility.json`; this task does not edit that worker's source or the frozen public instructions.

## Reproduce

Use the repository's Python environment with Pillow for `tools/pla-ui/make_icons.py`. Run `tools/pla-ui/prepare.py --base PLA-TEST-Build-4.bamod --vanilla PINNED_B64_DIRECTORY`; this verifies the exact Build4 SHA and preserves its comparison rows. Build `releases/0.6/source/runtime-qa/FreedomArrow.Runtime.csproj` against the generated MelonLoader assemblies. Then run `tools/pla-ui/package.py --base PLA-TEST-Build-4.bamod --out PLA-TEST-Build-5.bamod` and `releases/0.6/verify.py`.

Do not use the historical `build_constants.py` to reconstruct this candidate: it predates the25 comparison cards. The pinned-pack preparation script is the reproduction path. No live install is required.

Run the portable launcher harness with `dotnet run --project tools/launcher-compat/LauncherCompat.csproj -c Release -- PACKAGE.bamod`. It tests local-file installation only; it does not launch the game or request a GitHub release.

## Document change log

- 2026-11-10 18:56:28 PST (America/Los_Angeles) — Created the candidate implementation, verification record, native/network limits, attachment fallback and launcher acceptance findings.
