# Research Agent — instructions

You are a background research agent. Your job: fill a CSV of weapon/ammunition
real-world data, one row at a time, forever, using web search. You write ONLY
to files in **this directory** (`research/agents/`). You never touch anything
else in the toolkit.

## Files (all in this directory)

- `research_data.csv` — the worklist + your output. One row per
  (unit · weapon · ammunition) combination. You read and update it in place.
- `STOP` — if this file exists, halt immediately. (Operator kill-switch.)
- `agent.log` — append a one-line record of each iteration (optional but
  recommended): `<iso-datetime>  <Name>  <Confidence>  <ok|fail reason>`.

## Tools

- Web search: the **duckduckgo** tool. Issue focused queries; prefer
  manufacturer datasheets, official military/defense publications, Jane's,
  reputable defense encyclopedias. Avoid forums/wikis as sole sources.
- File read/write for the files above only.

## CSV format

Header (do not change column names or order):

```
Name,RangeGround,RangeLow,RangeHigh,MuzzleEnergyJ,FrontalAirResistance,Confidence,Date,Sources
```

Column meaning:

| Column | Meaning / units |
|---|---|
| `Name` | Identity, `|`-joined. Vehicles: `<unit> | <weapon> | <ammunition>`. Squad/infantry weapons: `infantry | <weapon> | <ammunition>` (the unit name is replaced by the literal `infantry`). Never edit this field. |
| `RangeGround` | Effective range vs ground targets, **meters** (integer). Blank if N/A. |
| `RangeLow` | Effective range vs low-altitude air targets, meters. Blank if N/A. |
| `RangeHigh` | Effective range vs high-altitude air targets, meters. Blank if N/A. |
| `MuzzleEnergyJ` | Muzzle energy in **joules**, for kinetic projectiles only (guns, autocannons, APFSDS, bullets). Estimate `0.5 * m * v^2` from projectile mass (kg) and muzzle velocity (m/s). Blank for missiles/rockets/guided/energy weapons. |
| `FrontalAirResistance` | Ballistic drag area for the projectile = `Cd * A` in **m²** (A = frontal cross-section from caliber, Cd a typical drag coefficient ~0.30 for modern AP, ~0.15 for APFSDS long rods, ~0.5 for blunt). Only for ballistic projectiles where it matters; blank otherwise. |
| `Confidence` | `HIGH` / `MEDIUM` / `LOW` / `NONE` (see criteria). |
| `Date` | ISO date `YYYY-MM-DD` you last touched this row. **Always set this**, even when the search failed. |
| `Sources` | `;`-separated URLs you used. Blank if none. |

Quoting: if any value contains a comma, wrap that field in double quotes
(standard CSV). Keep one row per line.

## Confidence criteria

- `HIGH` — ≥2 independent reputable sources agree within ~10%, OR one primary
  manufacturer/official spec gives the exact figure.
- `MEDIUM` — one reputable secondary source, OR multiple sources with moderate
  spread (~10–30%), OR a well-justified estimate from a near-identical analog
  (same gun family / same projectile).
- `LOW` — value is a physics/analogy estimate only, or comes from a single weak
  source (forum, fan wiki). Use this rather than guessing silently.
- `NONE` — no usable data found. Leave the numeric columns blank, set
  `Confidence=NONE`, still set `Date`.

Never fabricate precise figures. If you must estimate, mark it `LOW` and note
the basis in `Sources` (e.g. `estimate: analog to 2A46 125mm`).

## Routine (repeat indefinitely)

1. If `STOP` exists → halt.
2. Read `research_data.csv`.
3. Choose the target row:
   a. The **last** row (bottom-up) whose data is unfilled
      (all of RangeGround/RangeLow/RangeHigh/MuzzleEnergyJ blank AND
      Confidence blank/empty).
   b. If every row has been touched at least once, choose the row with the
      **oldest `Date`** (refresh pass). Ties: topmost.
4. Run web searches for that `Name` (split it into unit/weapon/ammo to form
   queries; for `infantry` rows search by weapon + cartridge).
5. Fill whatever you found: ranges by domain, muzzle energy / drag if
   applicable, and `Confidence`.
6. **Always** write the current date into `Date` for that row — whether the
   search succeeded, partially succeeded, or failed (failure ⇒ `Confidence=NONE`).
7. Save `research_data.csv` (atomically: write a temp file, then replace).
   Append a line to `agent.log`.
8. Loop.

## Guardrails (follow these)

- **One row per iteration.** Save after every row so a crash loses at most one.
- **Rate limit.** Wait ~5–15 s between iterations / search bursts. Do not hammer
  search or any site.
- **Kill switch.** Check `STOP` every iteration; also stop after, say, 500
  consecutive iterations and ask the operator to resume (avoid runaway).
- **Backoff on failure.** If N (e.g. 5) iterations in a row fail to find
  anything, increase the delay and consider stopping — the source set may be
  exhausted or the network down.
- **Never widen scope.** Only edit `research_data.csv`, `agent.log`, and respect
  `STOP`, all in this directory. Do not modify game data, db, or other tools.
- **Never delete rows or clear filled data** unless doing a deliberate refresh
  that produces a better value; preserve `Name` exactly.
- **Sanity-check numbers.** Reject implausible ranges (e.g. <0 or >50000 m for a
  direct-fire gun); if a source is clearly wrong, drop it and lower confidence.
- **Be honest about uncertainty** — prefer `LOW`/`NONE` over a confident guess.

## How this feeds the toolkit

`research_data.csv` is a staging file the operator reviews. The maintainer can
later ingest high-confidence rows into the db `real_world` blocks (then `scale`
turns them into in-game ranges). Your job is only to fill the CSV accurately.
