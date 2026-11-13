# Git branch policy — approved

**Lateralus approved this layout and the exact 83-branch first-pass cleanup scope on 11 November 2026. The App installation update is now effective; protection and ruleset reads succeeded. The approved remote transition is recorded in the linked audit.**

Approval: https://discord.com/channels/1566969627743879208/1570305472982941727/1570322693017047061

## Permanent branches

**Update, 12 November 2026 (Lateralus approved): 0.8 is the main development line.** Osama made the China build 0.8 and live on 12 November (13:27 PST). Its source had been `codex/pla-development`; 0.7 dev.58's gameplay was merged into it by data port (`tools/pla-specs/merge_dev58.py`) and code ports, not by a Git merge.

- `main`: source of the approved public gameplay build; still dev.45 (`73f7c1b`). The live launcher manifest is locked separately (0.8.0-dev.1). Updating `main` needs Sam or Lateralus's approval.
- `codex/0.8-development`: **the one integration branch for main development from 0.8 on**, China included. Created at `be49cdd` (0.8.0-dev.20 plus the retired-scenario cleanup). New dev builds advance this branch; snapshots keep their `gameplay/0.8.0-dev.N` tags.
- `codex/0.7-development`: **frozen** at 0.7.0-dev.58 (`c049c26`, tag `gameplay/0.7.0-dev.58`). History only; do not push to it.
- `codex/pla-development`: **retired alias** of the 0.8 line, kept for its history and existing package receipts; do not push to it. Use `codex/0.8-development`.
- `codex/assets-development`: shared model/music/voice add-on source. A gameplay build that needs newer model files than the published assets version must ship a new assets version (or say "complete package only"); see the 13 November note in the build-install workflow.
- `codex/launcher-development`: launcher and manifest client source; initially `e3b7ada`. The manifest controls player versions independently of this source branch.

A pre-push hook in the deck's shared repository refuses pushes to the frozen and retired names.

These are the maintained branch names. Package source commits remain the immutable identity of existing builds; a documentation commit on a maintained branch does not rebuild a package.

## Short-lived work

Use `codex/batch/lateralus/<topic>` for a coherent Lateralus batch that is not ready for 0.8 development integration. Reuse the same branch across commits and test builds. Independent batches use independent branches. Promote the whole batch only when approved, or selected self-contained commits; keep unfinished work on the batch branch. Active and explicitly held batches are excluded from cleanup regardless of age. Updating the batch from development does not merge the batch into development.

- `codex/feature/0.8/<topic>`, `codex/feature/assets/<topic>` or `codex/feature/launcher/<topic>`: one concrete change or coherent batch, based on the appropriate stream.
- `codex/test/0.7/<experiment>`: isolated tests such as SPAAG speed versus dispersion. Record the exact base commit and the fields being varied. Never merge an entire experiment merely because one part performed well; promote the selected changes.
- `codex/fix/0.7/<topic>`: urgent gameplay fixes. Branch from the affected public source when needed, then carry the fix into the appropriate development stream.
- `codex/docs/<topic>`: documentation-only changes, targeted at the relevant maintained branch.

Do not create a new branch for every dev/build number, texture attempt or logging run. Resume work on the maintained stream or the existing feature branch. A resumed historical task must start from the current relevant stream and must not silently recreate a retired branch.

## Version identity and publishing

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

## Document change log

- 2026-11-11 22:27:20 PST (America/Los_Angeles) — Recorded approved layout, explicit batch isolation and unchanged 83-branch cleanup scope; prepared for publication once GitHub permission preflight succeeds.
- 2026-11-11 22:48:48 PST (America/Los_Angeles) — Activated the approved branch workflow after installation permission acceptance; retained the newer pinned PLA28 source and original cleanup scope.
- 2026-11-12 23:43:01 PST (America/Los_Angeles) — 0.8 designated: `codex/0.8-development` created at `be49cdd`; `codex/0.7-development` frozen at dev.58 (tag `gameplay/0.7.0-dev.58`); `codex/pla-development` retired as an alias (Lateralus approval, 12 Nov).
