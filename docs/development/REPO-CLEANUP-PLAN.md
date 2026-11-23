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

## Status (23 November 2026, branch `codex/batch/lateralus/repo-cleanup`, not merged)

- **Step 1 done:** `out/receipts` is the one record of builds. `package.py` reads its base, the newest-build check and the next Assets number only there, and writes its receipt only there. A build's base is the newest build *older* than it, so parallel lines (0.9.5b, the 0.9.6 model rework) each stack correctly. `receipts_import.py` copied the 213 old receipts; rerun it just before the merge.
- **Step 2 done:** `package_0_8_next.py` → `package.py` (the old Build5 PLA packager that had that name is archived); `apply_0_9_4_dev1.py` → `batch_0_9_5b.py`. Lateralus chose option A for the folder names: the 0.1–0.2 pipeline tree that was `mod/` is now `archive/mod-0.1-0.2/` (`pipeline/` reads it there through `config.LEGACY_MOD`), `releases/0.6` is now `mod/` and `releases/0.8` is now `maps/`. Scripts that found the repo root by folder depth were changed with it.
- **Step 3 done:** `archive/` holds releases 0.1–0.5 and 0.7, 175 finished `apply_*.py`, 25 `*.NOTES` and 2 unused contracts. The map sources moved to `maps/` in step 2.
- **Step 4 done:** `mod/release-data/<version>/constants` holds the full constants of 0.9.1–0.9.5, sha256-checked. The next batch can start from them instead of the 0.9.3 package.

## After the merge (every worktree)

- The shared build output stays where it is: `work/pla-hotfix39-worktree/releases/0.6/out` on the deck. A worktree on the new layout links it as `mod/out` (`ln -s <that folder> mod/out`). Never add that link to git.
- Old recipes in `/tmp` use `releases/0.6`, `apply_0_9_4_dev1.py` and `package_0_8_next.py`. Write new ones with `mod/`, `batch_0_9_5b.py` and `package.py`.
- Receipts, check JSONs and asset lists written before the cleanup keep the old paths. They are records, not inputs.

## Document change log

- 2026-11-22 18:4x PST (America/Los_Angeles) — Plan recorded at Lateralus's request, to start immediately after 0.9.5 ships.
- 2026-11-23 10:5x PST (America/Los_Angeles) — Steps 1, 3 and 4 done on the cleanup branch; step 2 partly done, the folder rename waits for a decision on the existing mod/ folder.
- 2026-11-23 11:1x PST (America/Los_Angeles) — Step 2 done with option A (Lateralus): old mod/ archived, releases/0.6 → mod/, releases/0.8 → maps/; post-merge notes added.
