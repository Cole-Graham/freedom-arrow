# Research README — Weapon Data

This folder holds the human-edited research that feeds `real_world`
ranges into the modding pipeline. Each `*_RESEARCH.md` file documents a
single weapon class (mortars, MANPADS, etc.) and lists per-ammo
real-world effective engagement ranges in meters.

## How the pipeline consumes this folder

`actions/research_to_yaml.py` parses every `*_RESEARCH.md` in this
directory and writes the parsed values into the matching `yaml/<NN>_<class>.yml`
file as a `real_world` block:

```yaml
real_world:
  ground: 4000      # plain number, meters; one per domain
```

Domains:

- `ground` — engagement vs ground targets (incl. air-to-ground)
- `low_alt` — vs helicopters and aircraft at ~10–100 m
- `high_alt` — vs aircraft at ~1000–3000 m

Missing domains are treated as zero. Sentinels `0` and `-1` are passed
through verbatim by the rest of the pipeline.

## Editing rules

- **One plain number per domain.** No `{lo, hi}` dicts, no string
  ranges like `"1500-2000"`, no units suffix. The structural contract at
  `../yaml/_contract.yml` enforces this and the validator catches
  violations.
- **`real_world` is *input*, not output.** The scaler step
  (`actions/scale_ranges.py`) reads it; never write `current` or
  `min_range` values into research files.

## Related files

- `HAIKU_PROMPT.md` — brief for a sub-LLM populating ranges across
  several weapon classes in one pass.
- `COMPLETION_REPORT.md` — historical artifact recording one such bulk
  population run (May 2026). Folder paths in that report reflect the
  pre-refactor layout.

The full pipeline lives one folder up. See `../README.md` for the menu
and step-by-step flow.
