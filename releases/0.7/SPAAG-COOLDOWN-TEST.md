# Lateralus SPAAG and cooldown test — devtest.lat.5

**This isolated test applies the approved half-Actual Arrow SPAAG range/damage values and a conservative cooldown-aware overkill gate. No SEAD speed, physical cooldown, refund or public-build change. It starts from lat.4 on the same dev.15 base. Native invocation, safety and combat improvement still require a game run.**

## Included changes

- Pantsir ammo60:low875/high1000/damage3.25.
- PIVADS62:775/1000/2.4.
- Radar Shilka213:775/1000/2.65.
- Tunguska231:825/1000/3.25.
- C-RAM262:800/1000/2.4.
- M230LF AA454:750/1000/3.75.

Raw engine ranges. Exactly18 ammunition fields differ from lat.4. All other table fields and SEAD speeds are retained. The ranges also affect aircraft.

## Cooldown implementation and deliberate limits

One scalar-bool postfix on OverkillScoringSystem.IsTargetOverkilled. It can only change true to false for a known ground-AA caller and SEAD target when every other registered future contributor is clearly late and no incoming/airborne protection is recorded. The caller's own future reservation is excluded. Mixed late/timely reservations retain native behavior;this first build does not recompute their combined kill probability.

The callback reads an immutable managed cache only:no ECS/Unity reads, file IO, target search or score-helper calls inside the native hook. The independent LateUpdate collector reads remaining burst, reload and cycle timers using the native protected-value getter. It takes their maximum because they can overlap. A read-only native scalar estimator follows the SEAD projectile's intended target. This first rule uses launch delay alone as an optimistic interception lower estimate;it does not add shell flight/aim time or try to justify more aggressive exclusions.

Deadline estimate:1.25×native time-to-impact+0.25seconds;require remaining launch delay to exceed that by another0.35seconds. This is a conservative heuristic,not a mathematically guaranteed bound on a maneuvering missile. Cache age above75ms,unknown/non-finite timing,unknown contributors,airborne interceptors andexplicit include-blocked calls retain the native result. Contributions may change within a cache interval;the isolated run must assess that limitation.

At most128 weapons, 64 unit discoveries and 8 SEADs per 50 ms collection interval;3 ms cooperative budget. A native read or initial scan can exceed it. Larger weapon sets keep native behavior. Managed collector failure clears the cache and returns to native decisions. Native faults cannot be caught reliably by this fallback.

Native code already contains SEAD priority scoring. The native priority and guidance/channel checks remain;no new nearest-impact target-selector hook is installed. The broader optional priority experiment remains held pending invocation evidence. This gate cannot make a lone cooling Patriot fire before its real cooldown ends. The first lat.4 Patriot example had overkilled=false,so this gate alone is not claimed to fix that instance.

## Diagnostics and test request

The passive AA observer remains,with zero native diagnostic hooks. There is now one separate behavior hook;runtime logs name it explicitly.

Collect Latest.log, aa-targeting, shots and runtime JSONL from the same run. Runtime evidence should include aa_cooldown_installed(shadow=false),aa_cooldown_metrics,aa_cooldown_sample and,when the condition is reached,aa_cooldown_reservation. Metrics report hook invocations,wouldCorrect andcorrections;no correction count is fabricated from installation. Samples show full projectile/weapon identities,deadline,max remaining timer,known/airborne flags andclearly-late status. Per-session logging is bounded.

Repeat one/two/fourSEADs against a ready defender and a defender that just fired at the plane. Then one cooling defender plus one ready defender. Verify firing continues and compare alignment,shots and missile outcomes. A zero correction count can mean native overkill was false,no all-late case occurred,or timing was unavailable;send the samples/metrics to distinguish these.

Apply this complete gameplay pack INSTEAD OF lat.4 or public gameplay. Keep the shared model/music add-on. Do not combine gameplay packs. Lat.4 is the rollback. Nothing is installed by creating this package;main and the public build remain unchanged.

## Verification

The pure policy and compiled-IL checks cover stale/invalid/unknown data, airborne preservation,excluded caller,mixed contributors,overlapping timers and the callback's managed-only boundary. The build verifier checks payload hashes and normal row/reference constraints. These checks do not prove native hook invocation or in-game safety.

## Document change log

- 2026-11-10 03:16:34 PST (America/Los_Angeles) — Implemented the 18 SPAAG field changes and the conservative single-hook cooldown experiment;recorded native priority preservation,remaining limits and the required game evidence. No game run or installation performed.
