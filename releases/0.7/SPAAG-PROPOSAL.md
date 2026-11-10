# SPAAG range and damage proposal

**Proposal only. Apply half of Actual Arrow 1.1.20's range and damage increases to the matching ground SPAAG ammunition profiles. Keep SEAD missile speeds unchanged. This documentation commit changes no gameplay data, runtime code or build.**

## Exact values

Rule: proposed = current batch + (Actual Arrow 1.1.20 - vanilla) / 2. We halve the increase, not the final value. Current batch values below match pinned vanilla.

Ranges are raw engine units, not displayed metres. Each line shows current → proposed.

- Pantsir, ammo 60: low 750 → 875; high 500 → 1000; damage 3 → 3.25.
- PIVADS, ammo 62: low 650 → 775; high 500 → 1000; damage 2 → 2.4.
- Radar Shilka, ammo 213: low 650 → 775; high 500 → 1000; damage 2.3 → 2.65.
- Tunguska, ammo 231: low 750 → 825; high 500 → 1000; damage 3 → 3.25.
- C-RAM gun, ammo 262: low 700 → 800; high 500 → 1000; damage 2 → 2.4.
- M230LF AA, ammo 454: low 600 → 750; high 500 → 1000; damage 3 → 3.75.

Apply the profiles to their linked ground SPAAG variants. The C-RAM's optional RIM-116 is separate. Do not copy the naval CIWS reduction or invent a delta for an unmatched/new profile; audit those before implementation. These low/high range fields also affect aircraft, so this is not a SEAD-only override.

Keep all SEAD speed fields unchanged, including HARM 298 and Kh-58 315 at their current MaxSpeed of 700. Keep prices, gun cadence, tracking speeds, aim time, dispersion and overkill logic unchanged. The earlier proposal for absolute SEAD ranges of 1000/1250 and a 0.35-second aim cap is superseded/held; do not stack it with this proposal.

## First-of-two SEAD investigation

Lateralus reports that radar ground AA seems to ignore the first of two SEAD missiles and shoot only at the second, including units capable of tracking multiple targets. This is a reported pattern requiring controlled reproduction, not an established universal bug or proven overkill failure.

The supplied devtest.lat.4 logs give one concrete sequence, in game seconds:

- 86.80: Patriot fires. The nearby deferred snapshot names the Su-57. The shot log records 4.974 seconds between bursts.
- 87.15: first SEAD launch callback. Proxy identity `00000A7000010000` is observed around this time.
- 87.55666: Patriot selects that first proxy. It is aligned, not overkilled, has one round left, and has an active burst-cooldown component.
- 88.79: second SEAD launch callback. Proxy `00000A7100010000` appears at 88.981.
- 90.617: Patriot's selected proxy changes to the second one.
- 90.95: a SEAD damage event hits Patriot.
- 91.78: Patriot fires again, 4.98 seconds after its previous shot. This matches the recorded 4.974-second delay.
- 92.21: another SEAD damage event hits Patriot.

The first missile was selected while Patriot was cooling down. At that selection, overkilled=false. This is evidence against describing this particular case as simply ignoring the first missile or rejecting it for overkill.

The damage callbacks do not contain the incoming projectile identity. Association of the 90.95 hit with the first launch is supported by timing, but not independently identified by the hit record. The next deferred shot snapshot already names the plane, so do not claim the 91.78 shot targeted the second missile.

Patriot weapon 238 has MultiTargetTracking=2, SimultaneousTracking=1 and a 4–5-second between-burst delay. Tracking capacity does not remove the firing delay. This sequence does not establish why every radar AA unit behaves as reported. Component presence and sampled retained timers are not exact remaining-cooldown measurements.

## Proposed investigation

1. Test one, two and four SEAD missiles against each AA weapon when fully ready. Compare with a run where the AA just fired at the aircraft. Hold launch spacing, geometry, radar state and health fixed.
2. Correlate full projectile identities, including generation, with launch order, selected targets, overkill flags, assigned shooters, incoming missiles, channels, alignment and shots. Entity slots are reused.
3. Separate acquisition failure, cooldown, alignment failure and target switching. Complete missile-end/interception logging before deriving kill rates. The SelfDestroy/MissileInterceptionHit route used by HudQuick needs separate boundary and runtime validation.
4. Compare this range/damage proposal with unchanged lat.4 data only after implementation is requested. No overkill bypass, tracking change or new native hook is part of this proposal.

## Evidence and branch status

- Actual Arrow 1.1.20 comparisons and hashes: `work/actualarrow-spaag-20261110/comparison.json` and `sources.json` in the BA workspace.
- Lateralus's lat.4 evidence: `work/aa-no-fire-20261110/lat4-run/`. AA SHA256: `96e327b2ffd7548044979bf216e89c5632f9f2a311caab45273e34267c5cffb9`. Shots SHA256: `ea6c7cdcccac6460cb44ada553be87ebe3c5eea8d7866d8cac234cfd476f3a0c`.
- The supplied run recorded 172 seconds of AA states and 37 Patriot, 16 PIVADS, 12 C-RAM and one SLAMRAAM shot callbacks. PIVADS was outside alignment in 32/45 selected snapshots; C-RAM in 21/28. These are correlated snapshots, not kill probabilities. BA Codex did not perform this game run.
- This original batch branch still contains the old native AA diagnostic implementation. Do not ship its 17 diagnostic detours: later tests implicated that group in refusal to fire. The separate `codex/0.7-lateralus-devtest1` branch uses the passive lat.4 observer. This documentation commit does not port runtime code.
- [0.7 changelog proposal tab](https://docs.google.com/spreadsheets/d/1JzyNRaXONXOyURw1i_1-cIs5DkgsSaYn0OGINvjNvPY/edit#gid=2035272602). Status: proposal only. Broader Bible and cloud report synchronization remains pending.

## Document change log

- 2026-11-10 02:45:08 PST (America/Los_Angeles) — Recorded Lateralus's half-ActualArrow range/damage proposal,unchanged SEAD speeds,and paired-missile report;analyzed one selected-but-cooling-down Patriot sequence;no gameplay/build/install changes.
