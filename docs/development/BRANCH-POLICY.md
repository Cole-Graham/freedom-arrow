# Git branch policy — approved

**Lateralus approved this layout and the exact 83-branch first-pass cleanup scope on 11 November 2026. The App installation update is now effective; protection and ruleset reads succeeded. The approved remote transition is recorded in the linked audit.**

Approval: https://discord.com/channels/1566969627743879208/1570305472982941727/1570322693017047061

## Permanent branches

**Update, 24 November 2026 (Osama): two streams, gameplay and models.** Osama, 19:42 PST: "from now on we should have 2 different branches, gameplay and models. This way we don't have to do massive redownloads for models every time we want to test something." Lateralus asked for the same at 19:18 ("my dev builds require only code changes").

- **Gameplay: `codex/development`.** Unit data, cards, prices, weapons, scenarios, the Freedom Arrow runtime DLLs. A dev build from it ships the gameplay package only (about 200 MB) and keeps the current Models & music version; it never re-stages models. New cards whose model is not in that Models & music version show their stand-in body until the next model build.
- **Models: `codex/models`.** Everything that only changes the Models & music package: FAModels source (`mod/experimental-model-loader`), model and texture pipeline scripts, models.json changes. The model files themselves stay in the deck's model stage (outside git). A new Models & music version is built only when Osama asks for a model build; the launcher then downloads only the changed files.
- **Flow:** card data for a new model goes to `codex/development` (it is gameplay data). When Osama approves a model build for the next patch, `codex/models` is merged into `codex/development` and that build pins the new Models & music version. Model-only fixes never block or slow a gameplay dev build.
- `codex/assets-development` (11 Nov) is superseded by `codex/models` and is no longer advanced.

**Update, 22 November 2026 (Lateralus): one version-free development branch; versions are tags.** Lateralus, 07:2x PST, asked whether every version needs its own branch, then "switch it" to the trunk-and-tags layout.

- `codex/development`: **the one integration branch for main development**, from now on and for every later version. Created at `8e13eb31` (the head of `codex/0.9.1-development`, which by then carried 0.9.2, 0.9.3, 0.9.4 and the 0.9.5 batch). Every dev build advances it.
- **A version is a tag, not a branch:** `gameplay/<version>` for every dev build and release (for example `gameplay/0.9.4`, `gameplay/0.9.5-dev.3`). Do not create a new development branch per version.
- **Release branch only for a fix to an old release while development moves on:** `codex/release/<version>`, created from that release's tag (for example `codex/release/0.9.4` for 0.9.4.1). Merge or cherry-pick the fix back into `codex/development`.
- `codex/0.9.1-development`: **frozen** at `8e13eb31`. History only; the pre-push hook refuses it.
- Batches keep `codex/batch/<person>/<topic>`, based on `codex/development`.

**Update, 19 November 2026 (Lateralus): 0.9.1 is the main development line; playtests get plain numbers.** Lateralus, 06:2x PST: "create a 0.9.1 development branch and move the latest dev build along with any queued changes into a 0.9.1-dev.1 build". Playtests are released as 0.9.1, 0.9.2, 0.9.3; the dev builds toward a playtest are 0.9.1-dev.N (order: 0.9.0-dev.44 < 0.9.1-dev.1 < 0.9.1 < 0.9.2-dev.1, `tools/pla-specs/fa_version.py`).

- `codex/0.9.1-development`: **the one integration branch for main development**, created at `bc085f2d` (0.9.0-dev.44 plus the queued dev.45 batch). Dev builds keep `gameplay/0.9.1-dev.N` tags.
- `codex/0.9-development`: **frozen** at `bc085f2d`. History only; the pre-push hook refuses it.

**Update, 14 November 2026 (Osama): 0.9 is the main development line.** Osama, 11:05 PST: "let's launch this as 0.9. Remember from now on we need to batch our changes because the file is big." `0.9.0-dev.1` is 0.8.0-dev.105's content (Osama's 14 Nov batches plus Lateralus's 0.8 batch) under the 0.9 identity.

- `codex/0.9-development`: **the one integration branch for main development from 0.9 on**, created at `007e2ce` (0.8.0-dev.105). New dev builds advance this branch; snapshots keep their `gameplay/0.9.0-dev.N` tags.
- `codex/0.8-development`: **frozen** at 0.8.0-dev.105 (`007e2ce`, tag `gameplay/0.8.0-dev.105`). History only; do not push to it. The pre-push hook refuses it.
- Batching: changes are collected and built only when Osama or Lateralus say a batch is ready, because each package upload is large (assets 8.6 GB).
- Lateralus batches use `codex/batch/lateralus/<topic>` based on 0.9.

**Update, 12 November 2026 (Lateralus approved): 0.8 is the main development line.** Osama made the China build 0.8 and live on 12 November (13:27 PST). Its source had been `codex/pla-development`; 0.7 dev.58's gameplay was merged into it by data port (`tools/pla-specs/merge_dev58.py`) and code ports, not by a Git merge.

- `main`: source of the approved public gameplay build; still dev.45 (`73f7c1b`). The live launcher manifest is locked separately (0.8.0-dev.1). Updating `main` needs Sam or Lateralus's approval.
- `codex/0.8-development`: **the one integration branch for main development from 0.8 on**, China included. Created at `be49cdd` (0.8.0-dev.20 plus the retired-scenario cleanup). New dev builds advance this branch; snapshots keep their `gameplay/0.8.0-dev.N` tags.
- `codex/0.7-development`: **frozen** at 0.7.0-dev.58 (`c049c26`, tag `gameplay/0.7.0-dev.58`). History only; do not push to it.
- `codex/pla-development`: **retired alias** of the 0.8 line, kept for its history and existing package receipts; do not push to it. Use `codex/0.8-development`.
- `codex/assets-development`: shared model/music/voice add-on source. A gameplay build that needs newer model files than the published assets version must ship a new assets version (or say "complete package only"); see the 13 November note in the build-install workflow.
- `codex/launcher-development`: launcher and manifest client source; initially `e3b7ada`. The manifest controls player versions independently of this source branch.

A pre-push hook in the deck's shared repository refuses pushes to the frozen and retired names (`codex/0.7-development`, `codex/pla-development`, `codex/0.8-development`, `codex/0.9-development`, `codex/0.9.1-development`).

These are the maintained branch names. Package source commits remain the immutable identity of existing builds; a documentation commit on a maintained branch does not rebuild a package.

## Short-lived work

Use `codex/batch/lateralus/<topic>` for a coherent Lateralus batch that is not ready for 0.8 development integration. Reuse the same branch across commits and test builds. Independent batches use independent branches. Promote the whole batch only when approved, or selected self-contained commits; keep unfinished work on the batch branch. Active and explicitly held batches are excluded from cleanup regardless of age. Updating the batch from development does not merge the batch into development.

**Merging batches (Lateralus, 26 Nov 2026: "decide for yourself").**
- **Merge, never rebase, a pushed branch.** A rebase needs a force-push (forbidden) and orphans the test-build tags and package receipts that point at batch commits. Rebase only local commits that are not pushed yet.
- **Direction.** Merge `codex/development` into a batch to keep its test builds current. The batch goes into `codex/development` once, with one merge commit, when its owner, Osama or Lateralus says it is ready (`git revert -m 1` undoes it).
- **One home per fix.** A fix that both branches need is committed on `codex/development` only; the batch gets it at its next update merge. No second copy on the batch branch.
- **Conflicts are handled when they happen.** IDs cannot clash (reserved blocks, below). The usual conflict is two sections added at the end of `batch_0_9_5b.py`: keep both, in commit order, and run the batch check before the merge commit is pushed.

- `codex/feature/0.8/<topic>`, `codex/feature/assets/<topic>` or `codex/feature/launcher/<topic>`: one concrete change or coherent batch, based on the appropriate stream.
- `codex/test/0.7/<experiment>`: isolated tests such as SPAAG speed versus dispersion. Record the exact base commit and the fields being varied. Never merge an entire experiment merely because one part performed well; promote the selected changes.
- `codex/fix/0.7/<topic>`: urgent gameplay fixes. Branch from the affected public source when needed, then carry the fix into the appropriate development stream.
- `codex/docs/<topic>`: documentation-only changes, targeted at the relevant maintained branch.

Do not create a new branch for every dev/build number, texture attempt or logging run. Resume work on the maintained stream or the existing feature branch. A resumed historical task must start from the current relevant stream and must not silently recreate a retired branch.

## Version identity and publishing

**Shared main dev builds from 0.9.8 (Lateralus, 26 November 2026):** "next dev build should be 0.9.8-dev.1 ... If Osama is still doing heavy asset work or anything that requires long build times, it should stay on a separate branch, otherwise we can both work on the main dev builds now".
- The next `codex/development` build is **0.9.8-dev.1** (`tools/pla-specs/batch_0_9_5b.py` `V`).
- Osama's and Lateralus's gameplay changes both go on `codex/development` and its dev builds.
- Heavy asset work, or anything with long build times (model builds, new model sets such as the Light Brigade or ROC), stays on its own `codex/batch/<person>/<topic>` branch until it is ready to merge.

**Old dev builds are pruned at every live release (Lateralus, 26 November 2026):** `bin/ba-publish-manifest` runs `bin/ba-prune-dev-builds --apply`. It drops dev builds of earlier versions and releases older than the previous one from the dev launcher list (files stay on R2), and deletes those dev builds' folders on the deck. Releases, test builds (`l`, `-roc`, notes with "test build"), `out/0.8` and `out/receipts` are never touched. Ledger: `work/build-install/pruned-builds.log`.

**Playtest numbers after 0.9.9 (Lateralus, 26 November 2026):** after 0.9.9 the numbers go on to 0.9.10, 0.9.11, 0.9.12 … or to 0.10.0, 0.10.1, 0.10.2 …. **1.0.0 is kept for the larger "beta" release on the roadmap**; do not use it for an ordinary playtest. Version order is numeric per part (`tools/pla-specs/fa_version.py`), so 0.9.10 sorts after 0.9.9. That helper accepts only a leading `0.` today; it must be extended before 1.0.0.

Use immutable tags for named snapshots: `gameplay/0.7.0-dev.55`, `pla/build-27`, `assets/0.1.15`, and `launcher/<actual-version>`. Test versions can use `tests/0.7.0-devtest.lat.17`. These names are proposed; existing tag names and collisions must be checked before creating any.

For each published package record its stream, full source commit, version, file SHA256, download URL, and test/deployment status. A tag or source merge does not publish an artifact. No GitHub Release is created without a release request. Keep the current manifest/profile pins until Sam or Lateralus changes the lock.

Every committed build is pushed first on its `codex/` stream or feature branch, as the existing rule requires. Independent features should use independent worktrees; before advancing a shared stream, reread its remote head and integrate concurrent changes. Never force-push.

Use PRs to explain changes that cross stream boundaries or update `main`. Routine single-stream development need not open a PR for every build; use the agreed stream directly after the required checks. No BA Claude review is introduced. Updating `main` needs Sam or Lateralus's approval under the existing rule. Default-branch README links should make `main`'s public role and 0.7 development's role explicit.

## Cleanup rules

1. Review exact names and full commit IDs, never age alone. A seven-day-old branch can still contain unique work.
2. Keep the current public source, all maintained streams, active features/tests, open PR heads, and branch references required by a live profile or installation workflow until those references are migrated.
3. For fully incorporated history, confirm the old tip is an ancestor of a maintained tip. Preserve the maintained tip before deleting the redundant branch name. Do not confuse GitHub's “merged into main” filter with “incorporated into the correct stream.”
4. For work copied/cherry-picked or only partly promoted, ancestry can be inconclusive. Keep it for explicit review. After a human retires it, preserve the source with an immutable archive tag before removing the branch. Do not merge held proposals just to make the graph look clean.
5. Save a branch-to-SHA restore ledger and verify recovery. If a branch changed after the approved snapshot, remove it from the batch and reassess. Coordinate with active task workers and preserve local worktrees and uncommitted files.
6. After an approved batch, delete remote branch names in one explicit atomic Git push, through the normal `ba-gh` credential helper and pacing/STOP controls. No force, wildcards or blanket “delete stale” job. Verify the result once. Do not delete the local worktrees in that operation.
7. Source branch removal needs an explicitly agreed list. Hosted artifact retention remains a separate policy: latest two per stream plus locked/current and referenced packages/manifests, without deleting source history or active feature branches.
8. Review cleanup at the end of a work batch; do not add hourly GitHub polling or housekeeping writes. Closed PRs can remain in history. Close an obsolete open PR with a short explanation only after identifying its replacement; never merge it merely to clear the list.

## Approved first transition

Create and verify the four named development pointers above. Prepare a PR bringing `main` forward to public dev.45; the audited update is a fast-forward of 385 commits, changing 871 files. It requires review as a substantial accumulated source update. Do not point `main` at untested dev.55 while calling it public.

Retain the six current branch names in the first cleanup pass, because the source receipts and profiles still refer to them. The exact 83 ancestry-covered branches in branch-cleanup-2026-11-11.json are approved as the first remote-cleanup scope, subject to current-head/dependency checks. This approval must not be requested again. Keep the other 42 for review/archive. Fifty-two of those 83 candidates have a local worktree; a remote branch cleanup must not remove those worktrees or their files.

The expected first-stage remote count would be 52: 131 current + four maintained development pointers − 83 approved redundant branch names. This is a calculated target, not the current repository state. Later retirement of unique experiments and old pointer aliases can reduce it further; that needs its own agreed list.

## Reserved ID blocks

Work that is built on its own branch and merged later gets its own block of row IDs, so that its rows and live rows never use the same number. The blocks are in `mod/id-reservations.json`; that file is the one record of them.

- **The guard is in code.** `pla_graph.Graph` refuses a new live row inside a block, and refuses an owner row outside its own block. The `roc_hook` section of the batch fails the build if any row in a block was not made by its owner.
- **Owner rows** are made only inside `g.scope(owner)` with `g.add(...)`, which takes the next free ID in the owner's block. `g.put(table, max(U)+1, ...)` does not work there.
- **Order:** the owner section runs after every live section and the final checks, then runs those checks again on its own rows. A section added after the hook fails the build. Live IDs therefore do not change when the owner's work is loaded.
- **ROC** (Osama, 25 Nov 2026): branch `codex/batch/shawn/roc`, code in `tools/roc/`. Units 5000-5999, options 28000-28999, specializations 60-69, country 9, every other table 2900000-2999999. On `codex/development` there is no `tools/roc/roc.py`, so the hook adds nothing.

## Document change log

- 2026-11-11 22:27:20 PST (America/Los_Angeles) — Recorded approved layout, explicit batch isolation and unchanged 83-branch cleanup scope; prepared for publication once GitHub permission preflight succeeds.
- 2026-11-11 22:48:48 PST (America/Los_Angeles) — Activated the approved branch workflow after installation permission acceptance; retained the newer pinned PLA28 source and original cleanup scope.
- 2026-11-12 23:43:01 PST (America/Los_Angeles) — 0.8 designated: `codex/0.8-development` created at `be49cdd`; `codex/0.7-development` frozen at dev.58 (tag `gameplay/0.7.0-dev.58`); `codex/pla-development` retired as an alias (Lateralus approval, 12 Nov).
- 2026-11-14 11:10:26 PST (America/Los_Angeles) — 0.9 designated: `codex/0.9-development` created at `007e2ce` (0.8.0-dev.105); `codex/0.8-development` frozen; batch-only builds (Osama, 14 Nov 11:05).
- 2026-11-19 06:4x PST (America/Los_Angeles) — 0.9.1 designated: `codex/0.9.1-development` created at `bc085f2d`; `codex/0.9-development` frozen; playtests 0.9.1, 0.9.2, … and dev builds 0.9.1-dev.N (Lateralus).
- 2026-11-24 19:5x PST (America/Los_Angeles) — Two streams (Osama 19:42): gameplay = `codex/development`, models = `codex/models` (created at `f285615d`); `codex/assets-development` superseded.
- 2026-11-25 00:5x PST (America/Los_Angeles) — Reserved ID blocks (`mod/id-reservations.json`, guard in `pla_graph.Graph` and `roc_hook`); first block for the ROC specialization branch `codex/batch/shawn/roc` (Osama, 25 Nov 00:5x).
- 2026-11-26 10:2x PST (America/Los_Angeles) — Playtest numbering after 0.9.9 (0.9.10… or 0.10.0…); 1.0.0 reserved for the roadmap beta (Lateralus).
- 2026-11-26 15:5x PST (America/Los_Angeles) — Next dev build 0.9.8-dev.1; Osama and Lateralus share main dev builds, heavy asset work on its own branch; old dev builds pruned at every live release (Lateralus).
- 2026-11-26 18:1x PST (America/Los_Angeles) — Merging batches: merge not rebase, direction, one home per fix, conflicts handled when they happen (Lateralus left it to BA Codex).
