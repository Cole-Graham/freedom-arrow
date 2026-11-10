# Cooldown-aware SEAD defense proposal

**Feasible as a narrow, optional change, with medium implementation risk until native tests pass. Count a weapon's future contribution to overkill only if it can realistically intercept before the incoming SEAD missile's deadline. Keep existing airborne interceptors separate. This is a proposal, not implemented gameplay.**

## Problem and evidence

Lateralus reports that radar AA often fires only at the second missile of an incoming pair. One supplied lat.4 sequence shows Patriot selecting the first missile at 87.56 s with overkilled=false and burstCooldown=true, after firing at 86.80 s. A SEAD hit occurs at 90.95 s; Patriot next fires at 91.78 s. The previous shot recorded a 4.974-second between-burst delay. This supports a readiness problem in that instance, not proof that overkill blocked it or that all radar AA has the same cause.

Native declarations expose BurstCooldownComponent.CooldownTime, MagazineReloadingComponent.MagazineReloadingTime and WeaponCycleComponent.TimeCycling as protected GFloat values. OverkillScoringSystem exposes GetCurrentScoreOnTarget, GetCurrentMissileScoreOnTarget, ShouldExcludeWeapon and WeaponOverkillParametersUpdate. These are investigation points, not verified safe patch points. The current passive logger records component presence, not all remaining timers. A limited disassembly pass is saved in the BA workspace; it does not establish whether every native score path already accounts for readiness. Confirm that before changing behavior.

## Proposed rule

Limit the first functional experiment to ground AA evaluating incoming SEAD projectile targets. Keep the native scoring behavior for aircraft, helicopters, ground units and other targets.

Separate two sources of protection:

- Interceptors already in flight: retain their native contribution. Their launcher entering cooldown must not erase their protection.
- Shots that have not happened: exclude only a weapon that is clearly too late to contribute before the SEAD missile reaches its actual intended target.

Estimate the earliest effective interception time from launch readiness, acquisition/aim/traverse readiness and interceptor flight. Use actual remaining cooldown, reload and cycle timers, not their configured maximum or the mere presence of a component. Do not blindly add timers that can overlap; derive the timeline from native update order. Use target motion and the incoming missile's actual intended target where available, rather than assuming it is attacking the AA launcher being scored.

For a conservative first rule, remove a future reservation only when even its optimistic earliest interception is later than the conservative latest plausible impact deadline, allowing a timing tolerance. A cooldown of 4 seconds against a missile due in 2 seconds should not reserve that missile if no shot can arrive in time. A weapon ready in 0.3 seconds whose shot arrives another 0.4 seconds later should retain its native contribution against a missile due in 2 seconds. These numbers illustrate the proposed rule, not measured timings or chosen balance settings.

Unknown deadlines, uncertain timer semantics, non-finite values or unavailable state retain native behavior and produce an explicit diagnostic reason. Do not substitute zero or use the retained LastHitChance values as a trusted probability: lat.4 recorded Infinity there.

Change the contribution for that evaluation only. Do not delete entities from shared shooter/channel lists, clear targets, reset cooldowns, invoke recursive target searches or overwrite global overkill thresholds. A ready second defender may then engage; the cooling launcher remains unable to fire.

## Risk and rollout

- Shadow calculation only: low gameplay risk, because it makes no decision changes. Bounded reads still require a native run and performance measurement. Log would-exclude, remaining timers, predicted deadlines, existing airborne interceptors and the native result.
- Narrow opt-in readiness filter: medium risk, conditional on identifying one verified decision boundary. Risks include native ABI failures, worker-thread access, stale state and extra defensive ammunition use. The prior 17-hook regression rules out calling this low risk from compilation alone.
- Full replacement of overkill, prediction or targeting: medium/high risk and outside this proposal. Reuse native inputs and keep the first rule conservative.

Confirm whether native code already discounts cooldown before adding another filter. Validate a single boundary independently on the pinned assembly, then use an isolated test build. Do not restore the old 17 diagnostic detours. Default fallback is native behavior if required evidence is missing; disable the optional rule after a controlled failure. No package is built by this documentation task.

## What this fixes and what it does not

This can address coordination: a cooling defender should not discourage another ready defender by reserving a missile it cannot stop. It cannot explain or fix the specific first Patriot sequence through overkill alone, because that target was already not overkilled.

For the firing-delay problem, add a separate medium-risk priority experiment: when AA becomes ready, prefer a feasible incoming SEAD threat with the nearest impact deadline over a new shot at the aircraft, while respecting guidance/channel constraints. This may avoid spending the next ready shot on a lower-urgency target. It cannot undo a cooldown already started before the missile was known.

If a lone Patriot must fire again before its existing delay expires, that requires a separate firing-rate balance decision. Shorter between-burst values are technically a low-risk data edit, but can raise aircraft DPS, ammunition use and interception strength. No shorter value, cooldown bypass or emergency reset is proposed for implementation here. Current SEAD speeds remain unchanged. The half-Actual Arrow range/damage proposal remains a separate experiment.

## Acceptance cases

- One cooling defender plus one ready defender, then both ready, then both cooling.
- A launcher in cooldown with an interceptor already in flight: preserve the airborne contribution.
- One, two and four SEADs; late and timely defenders; targets moving or defending a nearby SAM.
- Unknown/invalid estimates: native decision retained; no fabricated coverage.
- Fully ready versus recent plane shot; check selection, alignment, actual shots and missile-end outcomes.
- Non-SEAD decisions unchanged; no runtime exception, firing regression or unjustified work-time increase.

Use full projectile identities and actual launch/end records. Snapshot counts do not supply interception probabilities. A diagnostic-only run precedes any functional trial.

## Evidence and status

Basis: Lateralus's lat.4 uploaded logs, pinned game declarations and limited native disassembly. Native GameAssembly SHA256: 12e7088369539b029a7bf0064062ce030a53b5189e7067420903f47b4281fddf. Local evidence: work/aa-no-fire-20261110/lat4-run/first-pair-sequence.json and work/aa-cooldown-proposal-20261110/. Readiness filter, deadline model and priority experiment are theoretical and not proven in a game. No overkill behavior has been changed.

## Document change log

- 2026-11-10 02:52:46 PST (America/Los_Angeles) — Added the conservative cooldown-aware reservation rule, medium-risk assessment, priority experiment, evidence limits and acceptance cases. Proposal only; no gameplay code, data, build or installation change.
