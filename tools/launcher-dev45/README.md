# Dedicated dev.45 launcher

**This is BAModLauncher configured for the exact published 0.7.0-dev.45 playtest. It includes the unchanged gameplay archive, verifies its SHA256, and skips GitHub latest for gameplay.**

## Build and validation

Run `tools/launcher-dev45/build.py ARCHIVE --out OUTPUT` with the published dev.45 `.bamod`. This builds the existing vendored BAModLauncher with AppFlavor=Launcher and PinnedFreedomArrow=true. It does not build gameplay or allocate a gameplay version. The output ZIP includes BAModLauncher.exe, the original dev.45 package, instructions and upstream MIT/font licenses. Do not commit the output archives or game files.

Run `dotnet run --project tools/launcher-dev45-tests -c Release -- ARCHIVE` for the real package planner and installer checks in a temporary game folder. The test settings are isolated from ordinary manager/launcher settings.

## Result and limits

14 checks passed: correct archive; dedicated single channel; fresh install without repository metadata; wrong archive rejection before writes; exact payload hashes; shared asset/preference preservation; repeat launch without reinstall; same-version corruption repair; downgrade from a newer installed version to locked dev.45; disabled package reactivation; damaged bundled package rejection.

The Windows executable was opened in a dedicated Wine prefix on an isolated X display. The window shows Freedom Arrow dev.45, dev.45 included/locked, and PLAY uses locked dev.45. No game or actual Windows installation was started. This is an installer-core and Wine UI test, not proof of a successful Windows gameplay launch.

MelonLoader installation/update and Play vanilla retain BAModLauncher's existing paths. MelonLoader may still need internet. Models/Music/Voices remain the separate existing asset package; this launcher includes gameplay only. Generic manager/launcher behavior is retained when PinnedFreedomArrow is false. The dedicated launcher uses a separate FreedomArrowLauncherDev45 settings/single-instance identity. It locates the installed gameplay package by stable ID freedomarrow.gameplay and accepts only the pinned archive on file import. Installed payload hashes are checked before game launch; preferences outside the package stay intact.

Gameplay archive SHA256: `33323fc1c760acabcc87cc1e237e99251d2d2495a14c858977791b0cf7d2ab5d`.

Source base: `73f7c1b48291a780610b1b4a83d0475dee5b35f1`. Pending MMG and Troopers corrections are not included. The original gameplay package, profile pin and installation remain unchanged.

## Document change log

- 2026-11-10 19:00:16 PST (America/Los_Angeles) — Added dedicated locked-dev.45 launcher source, reproducible bundling and real installer checks; recorded Wine UI evidence and limits.
