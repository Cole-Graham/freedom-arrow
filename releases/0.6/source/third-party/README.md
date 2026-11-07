# Third-party mods shipped with Freedom Arrow 0.6

Unchanged DLLs from ActualArrow 1.1.20. Osama reports (7 November 2026) that the authors agreed to their use in Freedom Arrow, a mod for him and his friends. ActualArrow has no licence file; the permission is as Osama reported it.

- HudQuick 1.4.2 — Aurka. End-of-match stats, score tab at match end, economy bar, HUD menu.
- TeamVoice 0.9.13 — Aurka. Push-to-talk team voice chat, per-player volume, in-game mod settings page.
- FlatIncomeMod 0.9.16 — Speer. Passengers die with their transport, camera zoom-out (+1000 m), aircraft and ballistic-missile warnings, map notes, air-defence target switches, HUD editor (F10), compact scoreboard. This version has no income code.

Freedom Arrow switches off one FlatIncomeMod feature: its forest cover (30% less damage to infantry in woods). Freedom Arrow already applies the same rule (`CoverDamage.cs`), and both together would cut it twice. See `ThirdPartyGuard.cs` in `source/runtime-qa`.
