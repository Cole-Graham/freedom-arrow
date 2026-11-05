# Freedom Arrow game mode: locked design

**Osama locked this design on 5 November 2026. Change it only when Osama or Lateralus asks.** The values are in `source/UserData/FAConquestPrototype/settings.json`. This file does not hold a second copy of a map's zone values.

## Rules

- Setup, F8: the game pauses for 3 minutes while players place units. The clock, income and combat stop.
- Setup, online: the scenario script pauses the game for `OnlineDeploySeconds` in `settings.json`, then starts the mode, with a large DEPLOYMENT countdown. This is the same node pattern as the workshop [Flat 200] scenarios.
- Round 1: the first 5 minutes of the match clock. Zones can be captured but do not score.
- Round 2: from 5:00 to the end. Each 30 seconds, the side with the higher held zone value scores the difference. Contested zones do not count.
- End: the first side to 300 wins, or the higher score when the 45 minute clock ends.
- Economy: 1500 starting points, flat 200 income per minute, no upkeep, and no practical money cap.

## Display

- Setup: a large DEPLOYMENT countdown, F8 only.
- Rounds: the native phase bar with small text and the orange fill. The three phase boxes are hidden.
- Round change: a smaller announcement for 8 seconds.
- Zones: +N beside each zone on the map.
- Team bars: X/300, with text that shrinks to fit.
- Next tick: a green +N under the bar of the side that is ahead.

## Add a map

1. Get the map, its name with the [FA] prefix, and a value for each zone.
2. Add the zone IDs and values to `MapZoneWeights` in `settings.json`.
3. Add the map to `make_scenario.py`. The build stops if the zone letters and IDs disagree with the settings.
4. A map with no script gets the ConquestMode script, as `build_dead_center` does.
5. F8 lists Skirmish scenarios only. An F8 version needs a Skirmish mission with its own AI script.
6. Set the scenario game version to 1.2.2, so the match loads the Freedom Arrow database. Network maps also need `add_deployment` and the raised money cap.
7. Build, then test one online lobby and, if the map has an F8 version, one F8 match.

## Live status

- Seen in F8 on dev.30: the 3 minute pause ran for 180 seconds, zones scored, and a match ended at 305 to 0 with a native win.
- Not seen: this mode on [FA] Dead Center 0.1, a 300 win online, and scores agreeing between online players.

## Document change log

- 2026-11-05 01:38:44 PST (America/Los_Angeles) — Recorded the locked design and the steps to add a map.
- 2026-11-05 01:57:57 PST (America/Los_Angeles) — Online setup follows vanilla. Added the money cap rule.
- 2026-11-05 02:07:06 PST (America/Los_Angeles) — Online setup uses the scenario pause. Added network map steps.
- 2026-11-05 02:20:07 PST (America/Los_Angeles) — Online setup shows a countdown. Its length is in settings.
