# Task: populate real-world ammunition ranges for Broken Arrow mod

You're a research worker for a Broken Arrow modding project. Your job is
to **fill the real-world effective range for ammunition entries that
need one**, by writing markdown research files in `_mod_tools/research/`.

A separate script (`actions/research_to_yaml.py`) parses your research
markdown into the yaml category files. After that, a scaler step
(`actions/scale_ranges.py`) compresses real-world ranges into game
values using a hyperbolic-tangent rational curve. You do not run those
steps; you only write the markdown.

## Where things live

Repo root: `D:\SteamLibrary\steamapps\common\broken_arrow\_mod_tools\`.

```
_mod_tools/
├── research/      <-- you write *_RESEARCH.md files here (one per class)
├── yaml/          <-- category yamls (one per weapon class) — eventually
│                      populated from your research
└── ...
```

The yaml category file you'll indirectly populate looks like this (one
entry; the validator's `yaml/_contract.yml` defines the full shape):

```yaml
- id: 7
  name: Round 100 2A70 T1 HE
  hud_name: 100mm 3UOF19
  weapons:  [...]
  units:    [...]
  vanilla:   { ground: 2000.0, low_alt: 0.0, high_alt: 0.0 }
  real_world: { ground: 4000 }      # <-- your output ends up here
  current:   { ground: 3200.0, low_alt: 0.0, high_alt: 0.0 }
  min_range: { ground: 160.0,  low_alt: 0.0, high_alt: 0.0 }
```

## What to produce per category

One markdown file in `research/`, named like `TANK_GUNS_RESEARCH.md`,
`SAM_SYSTEMS_RESEARCH.md`, etc. Each file lists one weapon system per
section with its real-world range(s). The exact markdown layout is
flexible — the parser in `actions/research_to_yaml.py` looks for ammo
IDs and number tokens — but every existing `*_RESEARCH.md` in the
folder is a good template; mimic the closest one for the class you're
researching.

## Range fields (the three domains)

- `ground` — vs ground targets (covers air-to-ground and ground-to-ground).
- `low_alt` — vs helicopters and aircraft at ~10–100 m altitude.
- `high_alt` — vs aircraft at ~1000–3000 m altitude.

For each ammo, fill **only the domains it actually engages**. Tank guns
get `ground` only; MANPADS get `low_alt` + `high_alt`; ATGMs typically
get `ground`. Missing domains are treated as zero by downstream tooling.

## Value rules (the contract enforces these)

- **One plain integer per domain**, meters. E.g. `4000`.
- **No string ranges** like `"1500-2000"`, no `{lo, hi}` dicts, no
  units suffix. If the spec is uncertain, pick a single representative
  number — the scaler later compresses everything to game ceilings
  (15 km long-range / 10 km medium-range) so 30 km vs 40 km mostly does
  not matter.
- **Decimal separator is `.` (not `,`).** YAML treats `2000,5` as a
  string and the validator will reject it.
- **Sentinels.** `0` and `-1` are already-set markers ("doesn't engage"
  / "blocked"). The pipeline auto-preserves them; don't try to fill
  domains where the existing `current` value is 0 or -1.

## Scaling reference (for picking values)

The scaler compresses real-world ranges via tanh into class ceilings:

- Long-Range class (S-300, Patriot, cruise, ballistic, radar SAMs):
  ceiling **15 km**.
- Medium-Range class (default — ATGMs, MANPADS, SHORADs, etc.):
  ceiling **10 km**.

Plus domain penalties: low_alt × 0.4 for radar/long-range,
high_alt × 0.85 for IR/intermediate, A2A look-down × 0.46.

So an SR-71-like 200 km radar-guided long-range SAM and a 60 km medium
SAM both compress to similar in-game values past the 15 km ceiling.
**Prefer accuracy in the 0–15 km band over precision above it.**

## Where to find ammo metadata

Each yaml category file already contains every entry's `id`, `name`,
`hud_name`, `weapons[]`, and `units[]`. Use those as identity anchors
when researching. The HUDName is what the player sees in game
("M829A4 APFSDS"); the Name is the internal slug
("Round 120 M256 AP M1A2C T3").

If a single ammo type is shared by multiple platforms (e.g. one
12.7×99 round used by several MGs), there's only **one entry to fill**
— the platforms reference the same ammo id.

## Hard rules

1. **Zero stays zero.** Don't add a domain that's currently 0 in the
   yaml's `current` block — the engine treats that as "this weapon
   doesn't engage there."
2. **Negative (-1) stays -1.** Engine "blocked" marker.
3. **No `current`, `vanilla`, or `min_range` edits.** Those are
   pipeline-owned. You only produce `real_world` values.
4. **Single source of truth is the yaml.** After your research markdown
   is written, the parser updates yaml entries; don't hand-edit yaml.
5. **Per-domain values are single integers** (per the structural
   contract). Tighter precision adds nothing past the scaler.

## Output expected when done

A summary message naming:

1. Which category file(s) you wrote.
2. Count of ammo IDs populated; count of IDs you couldn't confidently
   research (so a human can review).
3. Any classification mistakes you noticed (an ammo that's in a
   category file where it doesn't belong — e.g. a tank gun in a SAM
   file). Name the offending id so the classifier can be patched.
