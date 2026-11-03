# research

Parse `v3/world/research/*.md` range tables and patch ammunition `real_world`.
Prepares data for `scale`.

## Run

```
research run [--no-overwrite] [--dry-run]
research.bat run            # Windows
```

Tables need an `Entry ID` and `Effective Range` column (`Altitude` optional).
Ranges use the `<number>m` convention (commas allowed). Files listed in
`group_classifier.AIR_DEFENSE_FILES` map range→`low_alt`, altitude→`high_alt`;
all others map the single range→`ground`. Ids missing from `db` are warned and
skipped. `--no-overwrite` fills only null fields.

## Background research agent

`research/agents/` holds an autonomous research-agent setup:

- `AGENTS.MD` — instructions for a background AI agent (web search via the
  duckduckgo tool, CSV format, confidence criteria, loop routine, guardrails).
- `research_data.csv` — the worklist + output. One row per
  (unit · weapon · ammunition); squad weapons use the `infantry` placeholder.

Generate / refresh the worklist from the current db:

```
research seed
research.bat seed     # Windows
```

`seed` adds any new Names and preserves rows the agent has already filled.
High-confidence rows can later be ingested into db `real_world` for `scale`.
