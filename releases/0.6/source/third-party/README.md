# Third-party mods shipped with Freedom Arrow 0.6

Unchanged DLLs from ActualArrow 1.1.20, except FlatIncomeMod, which is the build in ActualArrow 1.1.21 (0.6 dev.9). Osama reports (7 November 2026) that the authors agreed to their use in Freedom Arrow, a mod for him and his friends. ActualArrow has no licence file; the permission is as Osama reported it.

- HudQuick 1.4.2 — Aurka. End-of-match stats, score tab at match end, economy bar, HUD menu.
- TeamVoice 0.9.13 — Aurka. Push-to-talk team voice chat, per-player volume, in-game mod settings page.
- FlatIncomeMod 0.9.16 — Speer. Passengers die with their transport, camera zoom-out (+1000 m), aircraft and ballistic-missile warnings, map notes, air-defence target switches, HUD editor (F10), compact scoreboard. This version has no income code. The 1.1.21 build (sha256 9b71a1eb…) kills passengers through the game's health setter instead of writing the raw health field, and no longer reshapes the guided-MLRS arc.

- ArrowQueue 0.10.31 — ActualArrow (0.6 dev.10). The Mod game tab: who is online, mod lobbies, Find a game, groups, and the Search settings page. Freedom Arrow points it at our own matchmaking hub on Sam's deck (`https://cyberdeck.tailf7ad82.ts.net/hubs/game`) while Freedom Arrow runs, and puts the old address back when the game closes, so ActualArrow keeps its own server (`ThirdPartyGuard.cs`). The hub source is in `work/aa-matchmaking-20261107/server` on the deck.

Freedom Arrow switches off one FlatIncomeMod feature: its forest cover (30% less damage to infantry in woods). Freedom Arrow already applies the same rule (`CoverDamage.cs`), and both together would cut it twice. See `ThirdPartyGuard.cs` in `source/runtime-qa`.
