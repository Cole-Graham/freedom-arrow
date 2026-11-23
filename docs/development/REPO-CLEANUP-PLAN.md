# Repository cleanup after 0.9.5

**Short answer.** Lateralus approved four cleanup steps on 22 November 2026 (thread 1572962048705429598): "implement all 4 recommendations immediately after we ship 0.9.5". Start them right after the 0.9.5 release, before the next dev build. `ba-patch-notes release 0.9.5` prints a reminder.

---

## Why

On 22 November, 11 different models files were all named Assets 0.2.52. The packager took the next version only from the receipts in `releases/0.6/out/0.8`, and the 0.9.5 dev builds kept their receipts in `out/local-*` (stopgap fix: bee78cdc). The names in the repo also no longer match what they hold. For example, `apply_0_9_4_dev1.py` builds 0.9.5 over a 0.9.3 base, all current work is in `releases/0.6`, and the packager is `package_0_8_next.py`.

## The four steps (in this order)

1. **One record of builds.** Keep one receipts folder that the packager, `work/build-install/devpost.py` and the retention timer all read. It replaces `out/0.8` and the receipts in `out/local-*`. Copy the existing receipts once, then retire the old reads in the same change.
2. **Names that match the contents.** Rename `package_0_8_next.py` to `package.py`. Use one batch script per release, named after it (for example `batch_0_9_6.py`), with its base read from the record of builds. Rename `releases/0.6` to `mod/`. Update every script, worktree symlink, doc and memory note that uses the old paths.
3. **Archive old material.** Move `releases/0.1`–`0.8`, the finished `tools/pla-specs/apply_*.py` scripts, the old `*.NOTES` files and the per-build `*-contract.json` files into `archive/`. Git history keeps everything.
4. **Game data in the repo.** Commit the full constants of each release, so a build starts from files in git and not from a chain of earlier packages plus batch scripts.

## Rules

- No force-push. Do the work on `codex/batch/<person>/repo-cleanup` and merge it when the build gates pass.
- Before a step deletes or moves anything outside git (for example the files in `out/`), list it and ask for a yes.

## Document change log

- 2026-11-22 18:4x PST (America/Los_Angeles) — Plan recorded at Lateralus's request, to start immediately after 0.9.5 ships.
