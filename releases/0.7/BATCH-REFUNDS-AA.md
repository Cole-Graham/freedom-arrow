# Plane refunds and ground-AA investigation — queued batch

**Refund changes and diagnostic logging are implemented on lateralus-batch-0.7. The SPAAG changes below are a proposal only. No release or installation is made by this task. Native hook invocation and gameplay remain untested.**

## Refund behavior

- Aircraft category6: refund health coefficient 0.5 -> 2/9. Configured price includes selected equipment. Keep the native90% cap and20% floor.
- SupplyCost0 on16 aircraft air-to-air ammunition rows and14 aircraft gun ammunition rows. DecoySupplyCost0 on44 aircraft flare abilities. Fuel already has no native refund term.
- No changes to ammunition quantities, missile accuracy, flare strength/count, ResupplyTime or aircraft return/death settings.
- Shared UAV air-to-air ammo also becomes free. Those drones use the general-unit return formula, so their return delay can shorten indirectly. Helicopters and ground units retain existing values.
- The health hook handles previews and actual sales, saves the exact original coefficient, serializes refund calls and restores the original in a finalizer. It does not rewrite the whole native payout routine. Native invocation still requires a game check.

## Ground-AA diagnostic log — historical branch implementation

**Do not ship these original17native detours:later isolated tests implicated them in refusal to fire. The separate devtest.lat.4 branch uses passive LateUpdate diagnostics and was exercised in Lateralus's supplied run. This branch documentation update does not port that runtime correction.**

`UserData/FreedomArrow/diagnostics/aa-targeting-*.jsonl` records ground-AA candidate admission, search result, evaluated target flags/scores, native overkill result and its filter flags, native damage/hit scores, aim/flight times, target-mask eligibility, range, angles, channel availability, ammo availability, exact target-removal reasons, radar status, disabled/reload/burst/aim/cycle state, shot callbacks and observed hit types including missile interception100.

The logger is observational: no RNG, forced targeting, extra searches or score recalculation. Entity snapshots are read through the existing native ECS reader. Repeated identical per-pair states are suppressed for1second. File limit16MiB/60,000lines, pending queue2048, eight retained sessions. Overflow can drop observations and is recorded at the limit; file writing runs on LateUpdate. Log installation coverage states any failed binding. Performance and live event coverage are unmeasured.

It does **not** claim to report every unseen target: entities filtered before the spatial/FOW candidate callback are not individually traced. No patch on the non-blittable ref UnitComponent interception helper or ref-component EvaluateTargets method. Candidate and post-search flags expose their downstream decisions when retained in the list. Native DEBUG/UNITY_EDITOR reporting calls may be compiled out and are not relied on. Network-remote weapons are controlled by their owning side; collect the owning player's log.

## Why C-RAM/PIVADS can struggle

Read from the batch's generated game data:

- PIVADS unit188 / weapon261 / ammo62: aim1–2s; one simulated shot every0.2s; burst7–10; burst cooldown2–3s; shell speed805world units/s; damage2; dispersion1.6/1.6; gun low/high range650/500world units.
- C-RAM unit250 / weapon345 / ammo262: same aim and cadence/burst; cooldown1.5–2s; low/high range700/500world units. The optional RIM-116 weapon732 is a different interceptor and is not counted as the gun here.
- HUDMultiplier20 scales displayed ammunition; it does not create20 independent hit rolls for each callback.
- HARM ammo298 reaches700world units/s, acceleration300. Other SEAD rows include Kh-31P650, Kh-58UShK700 and Sidearm600. These are maximum speeds; actual incoming speed depends on flight stage.
- Native MakeShellTargetable creates a1HP target. Its fake box is10x5x5world units. Target masks on both guns include SEAD256. Increasing raw damage is therefore not the first lever to try.
- These are DirectShot/trajectory10 physical projectiles. A missile's flat ECM/flare pass chance is not the gun's collision probability. No single universal SPAAG interception percentage follows from an accuracy number.

### Conditional HARM timing ceilings, not measured kill rates

Assume a fresh acquisition, stationary gun, straight self-targeting HARM already at700world units/s, constant altitude band, uniformly distributed aim1–2s, no pre-aim, no rotation/stress/crit/reload/visibility penalty. A shot must be fired before impact. This bounds the kill chance from above; a fired shell can still miss or arrive too late.

- High altitude:500/700=0.714s for either gun ->0% firing opportunity under these assumptions.
- Low altitude/radar off: PIVADS650/700=0.929s; C-RAM700/700=1.000s ->0% opportunity apart from a measure-zero endpoint.
- Low altitude/radar on: native relative projectile override applies the1.25 radar range modifier in the altitude range and again after the projectile multiplier. PIVADS1015.625world units ->1.451s, at most45.09% firing opportunity. C-RAM1093.75 ->1.5625s, at most56.25%.
- If acquisition/search consumes0.2s, those last bounds become25.09% and36.25%, before turret rotation, bullet flight, collision or other gates. MAX_AA_MS_DELAY is200ms; this is a scenario with that delay, not a measured fixed delay.
- General ceiling for the stated uniform-aim model: clamp((range/speed - acquisitionDelay -1)/1,0,1). If shots have success probabilities p_i, one-hit kill probability conditional on those shots is1-product(1-p_i), only when independent. The native physical hit process has not been reduced to measured p_i values.

Radar/altitude can change during a dive; slowing missiles, crossfire, pre-aimed guns and a different defended target change this picture. Do not report the conditional0% as the universal in-game interception rate.

## Current SPAAG proposal — not implemented

Supersedes the earlier SEAD-only range 1000/1250 and 0.35-second aim proposal. See [SPAAG-PROPOSAL.md](SPAAG-PROPOSAL.md) for half of Actual Arrow 1.1.20's low/high range and damage increases across six ground-AA gun ammo profiles. SEAD missile speeds remain unchanged. Lateralus's first-of-two SEAD observation is tracked separately; one lat.4 Patriot sequence shows the first missile selected during a 4.974-second burst cooldown,not an overkill rejection. No SPAAG gameplay edits or new build.

## Cooldown-aware coordination proposal

See [AA-COOLDOWN-PROPOSAL.md](AA-COOLDOWN-PROPOSAL.md). The proposed medium-risk rule excludes a future defensive reservation only when the weapon cannot intercept before impact, while retaining interceptors already in flight. This is a separate optional experiment; the range/damage comparison keeps native overkill unchanged. It does not bypass a launcher's cooldown. A separate SEAD-priority experiment is described, with no firing-rate value selected.

## Evidence and limits

- GameAssembly SHA256 `12e7088369539b029a7bf0064062ce030a53b5189e7067420903f47b4281fddf`.
- RefundUnit RVA0x6DBEC0; GetAmmoShootingDistance0x7D69B0; IsKinematicallyAbleToInterceptTarget0x7D9420; TargetSearchHelper.TryAddTargetToCheckList0x7E53B0; OverkillScoringSystem.IsTargetOverkilled0x7F7F60; ShootingSystem.InternalUpdate0x80D810; MakeShellTargetable0x7DF1E0; fake-projectile Init0x7DEEB0; HealthComponent constructor0x821680.
- Raw disassembly, merged tables,74-field delta, conditional timing model and verification logs: `work/aa-refund-batch-20261109/` in BA Codex's workspace. Copyrighted decrypted tables are not committed.
- Batch base0.7dev.12 (`6c8051c`), not rebased to live dev.15 in this task. Apply/rebase the queued batch onto the current release when Lateralus requests its build.
- Validation:24 pinned source tables;18,920 row/reference checks;15 actual refund-hook fixture tests including concurrency/exception restoration;18 native method boundary signatures checked against the real generated assemblies;36 pipeline tests (1skip);27 runtime-host assertions. Runtime DLL compiles with0warnings/0errors. Native detours were not installed or invoked in a game; no package/install/runtime success is claimed.
- Proposal sheet: https://docs.google.com/spreadsheets/d/1sZi4xzdN6CxWajJ4_TPkaLd2GUd6dkOI_P45NvqAYY8/edit#gid=1261345581
- Batch changelog: https://docs.google.com/spreadsheets/d/1JzyNRaXONXOyURw1i_1-cIs5DkgsSaYn0OGINvjNvPY/edit

## Document change log

- 2026-11-09 23:48:25 PST (America/Los_Angeles) — Queued aircraft refund policy and ground-AA diagnostic logging; recorded conditional SEAD interception ceilings and a separate, unimplemented improvement proposal. No game measurements.

- 2026-11-10 02:45:08 PST (America/Los_Angeles) — Replaced the earlier SPAAG range/aim idea with the current half-ActualArrow proposal;linked exact fields andpaired-SEAD evidence; flagged historical native diagnostics as unsuitable for shipping. Documentation only.

- 2026-11-10 02:52:46 PST (America/Los_Angeles) — Added a linked cooldown-aware SEAD coordination proposal with a medium-risk assessment; no runtime or balance changes.
