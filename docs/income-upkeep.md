# Proposal: subtle income upkeep

**Status: undecided.** Current locked Freedom Arrow economy is still 1500 start, flat 200/min, no upkeep (`releases/0.3/GAME-MODE.md`). This document is a design proposal, not a change to that lock.

The goal is a small living-force tax that feels like Wargame: Red Dragon’s command-vehicle opportunity cost, not like vanilla Broken Arrow’s wipe-to-rich curve. Target average income in real games is **210/min**. The input is **nominal living battlefield value**, never deck ratio.

## Why vanilla is the wrong shape

Vanilla ranked income starts at 300/min and, with the 1.0 income curve on, falls with absolute upkeep to 0/min at 5000 living points. A player who just lost an army is paid like a full rebuild. A player who kept a large force is starved. That is a strong, explicit comeback kit.

The older linear path (curve off) is worse for Freedom Arrow in a second way: raw upkeep is **percent of the player’s deck total**. A padded deck pays less tax for the same army. This proposal does not use that system.

## What “subtle” means here

Wargame had no income upkeep and no phase income curve. The usual player argument for a comeback mechanic was the **command vehicle**:

- Only CVs could take and hold conquest zones.
- Adjusted to Freedom Arrow’s cost scale, a CV is about **240 points** on average.
- It had to sit on the zone, so you wanted one per zone.
- That 240 did not vanish: it bought a score tick. The other player kept 240 in combat units and tried to punish the parked CV hard enough to close the score gap **and** take the lead.

Freedom Arrow will not require a command vehicle. Zone combat units already tick conquest score. The missing piece is only the modest hole in fighting power that map commitment used to cost.

An income tax cannot copy “240 extra guns right now.” Inside a ±20 band it can only copy the **match-level** feel: the player with more living metal is slightly slower to buy the next wave, and the player who just lost units cannot print a new army from income alone.

A 40/min wipe-versus-blob gap is one 240-point tank every six minutes, and only in that extreme. A 1000-point lost fight is more like 10/min. You cannot income-your-way back from a lost battlegroup. That is the point.

Do not try to make “240 extra on the field cost 240 income in one fight.” That does not fit in a 40-point band. Widening the band is how this becomes vanilla.

## Recommended formula

Keep native upkeep and the vanilla income curve **off** (the same bypass Freedom Arrow already uses). Each tick, set that player’s rate from their own living cost:

```text
U = sum of Cost for that player's living units, including upgrades
income/min = 230 − 40 × clamp(U / 4000, 0, 1)
```

| Living value `U` | Income |
| --- | ---: |
| 0 (wiped) | **230** |
| 1000 | 220 |
| **2000** | **210** |
| 3000 | 200 |
| 4000+ | **190** |

- **230** is the ceiling, not a bonus for winning.
- **210** is the design average: a 2000-point living force, roughly the 1500 opener plus one fight.
- **190** is the floor. A blob still gets paid. Nobody goes to 0.
- **4000** is “a fat army,” not a normal one. Opening dump of 1500 sits both players on **215**. Round 1 does not create a comeback; the band only opens when living value diverges.

Worked gaps on the same line:

| Situation | Living values | Incomes | Gap |
| --- | --- | --- | ---: |
| Both opened 1500 | 1500 vs 1500 | 215 vs 215 | 0 |
| Winning a fight, both still have an army | 2500 vs 1500 | 200 vs 215 | 15/min |
| One side broke | 3000 vs 800 | 200 vs 222 | 22/min |
| Blob vs ghost | 4000 vs 0 | 190 vs 230 | 40/min |

At this calibration, **100 more living points is −1/min**. A tank trade is readable. There is no cliff to hover under.

The 4000 is a guess. After a handful of matches, measure median living `U` and set `U_ref = 2 × median U` so the median game is 210. If the median is 2500, move the floor out to 5000 rather than widening 230–190. **Change the X axis, not the band.** The band is the subtlety.

## Linear, not a curve

Wargame’s tax scaled with how much you committed to the map (one CV per zone). Linear on living cost is the same idea: each extra 240 on the field is one more modest opportunity cost, not a new bracket.

Because the whole range is only 40 points, linear versus a fancy curve barely changes a 2200 vs 2400 game. Shape only matters in blowouts, and linear already caps those at +40/min.

Two non-linear shapes are easy to want and wrong for a first ship:

- **Dead zone, then linear** (230 until ~1500, then down to 190). A recon screen and the opening 1500 should not count. If both players opened 1500 they are already equal, so the dead zone does no relative work. It only enlarges the wiped-versus-1500 gap. That is the vanilla wipe instinct.
- **Slow then steep.** Small leads ignored; only a blob pays. 2500 vs 1500 is already the usual winning position, which is when a Wargame player would have bought CVs. Convex lets the real lead through cheap.

A step of “minus 8/min per 240 on the field” is linear with ugly rounding. Vanilla’s 750 / 1500 / 2500 / 3500 / 5000 piecewise curve is the comeback kit this proposal is leaving behind.

## 1v1 versus team games

**The rate is per player, from that player’s living units only.** There is no team sum and no opponent-gap term. Two players with the same `U` get the same income even if the score is 200–50.

1v1 and team games use the same formula. In 1v1, “per player” and “per team” are the same person, so the distinction does not show up. In 2v2 and larger it does.

### Per-player (recommended)

Each wallet stays personal, which is how Broken Arrow already pays income. `PlayerEconomyService` already walks players one by one. Wargame CVs were also bought from a personal pool.

Consequences in 2v2:

- A player who got wiped rebuilds at **230**, even if their teammate still has a 3000-point army at **200**. The person who lost the units is the one who gets the trickle. That matches the Wargame hole: you lost (or spent) fighting power, you need it back.
- A player who is blobbing pays their own 190–200. They do not drag their teammate’s income down.
- The teammate who is still healthy is not paid extra just because the other lane died.
- A cheap-recon specialist with 800 living sits on ~222 while a tank player with 3000 sits on 200. The spread is still only ~20/min. That is acceptable inside this band.
- Typical 2v2 living value per player is lower than 1v1, so 2v2 incomes will cluster a bit closer to 220 than to 210. Do not scale by player count or deck size on day one. If 2v2 medians come in high, lower that mode’s `U_ref` later.

The “gap” is emergent. The hook does not ask who is ahead. If both members of the losing team still have 2000 on the field, they both get 210, same as a winning 1v1 player with 2000.

### Teamwide living value (rejected)

Sum living cost for the whole side, then either give every teammate `f(U_team)` or `f(U_team / player_count)`.

That looks fair on a whiteboard (“the winning team pays”) and fails the case this tax is for. The wiped player on a winning team is the one who needs 230, and teamwide `U` would hand them the blob’s 190. The surviving blob would also share a tax they already earned with metal the dead teammate no longer has.

Dividing by player count only makes 2v2 medians look like 1v1. It still taxes the wiped player for metal they do not own.

### Teamwide gap versus the enemy (rejected)

Something like `income = 210 + k × (U_enemy_team − U_own_team)` is a score-like money comeback. The losing side is paid for being behind, even if they still have more living metal. Vanilla already does “loser gets money.” Freedom Arrow’s score tick is already the reward for winning the map. Do not add a second team-lead bonus on income.

### Why not a zone tax instead

The faithful CV analog would be a small tax **per zone held**, independent of army size. Do not add that on top of living-value upkeep. Score lead plus army-size tax plus a zone tax is three comebacks. This proposal is one knob: the player with more living metal is slightly slower to buy the next wave.

## What this does to current Freedom Arrow

Current Freedom Arrow is flat **200**, no upkeep. This proposal is a **+10 average raise** plus a ±20 spread. A typical 2000-point force gets 210 instead of 200. A blob still gets 190, which is almost today’s flat rate. A trailer gets at most 230. The 1500 start, the raised reserve cap, and native pause/deployment (income stops while paused) stay as they are.

Players will still dump onto the field. −1/min per 100 living points is not a reason to hold units in reserve. The tax is not meant to change army size. It is meant to slightly change who can replace losses.

## Implementation notes (if this is accepted)

- Do not turn native `UseIncomeCurve` on. Those breakpoints are vanilla’s 300→0 curve.
- Do not use native `CurrentGlobalUpkeepModifier`. That path is deck-ratio linear when the curve is off.
- Keep the existing prefix/postfix window that zeros those knobs, and set `PlayerIncome` to `income/min / 60` from measured living `U`, including the online lobby multiplier divide already in `FlatEconomy`.
- Living `U` is that player’s units currently alive on the battlefield, using unit `Cost` (and `UpkeepMultiplier` if it is ever not 1.0). Dead, refunded, and not-yet-spawned units do not count.
- Same formula for humans and bots if the economy hook already writes both. Do not invent a team aggregator.

## Out of scope until someone asks

- Different `U_ref` for 1v1 and 2v2
- HUD beyond the native income number
- Changing start points, score ticks, or the 45-minute / first-to-300 rules
- Replacing this with a per-zone income tax
