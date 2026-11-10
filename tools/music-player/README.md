# FA Music 1.4.2

**China and Black Hawk Down now each select between two complete menu compilations with an independent 50/50 draw. The exact recipe is in [menu-compilations](../menu-compilations/README.md).**

The four mixes contain their song order and120-second gaps, including a final120-second gap before the next selection. When these compiled files exist, they take priority over the previous opener/shuffle system; the player adds no extra menu pause. Packs without the new files keep their previous behavior. USA and Russia are unchanged. Battle gaps remain120 seconds, calm gaps10 seconds, and victory/defeat play once.

The Game music selection retains the published 1.3.11 native-voice gate. Custom packs retain the newer 1.4.0 voice queues and US missing-recording suppression. The accompanying sample installs new menu audio and removes BHD theme09. Other songs and voice recordings are preserved.

The regression occurred because 1.4.0 was based on source without the 1.3.11 menu changes. Live logs showed the GLA opener repeated at 22:51:09 and 22:54:59 on 9 November 2026. Host tests execute the actual OnUpdate, PlayNext, Switch and FolderFor methods with a simulated clock/FMOD channel. They retain the legacy gap tests and add forced random outcomes, exclusion of stray menu files, and no double gap for the new compilations. Audible playback remains untested in a new game run.

Build with `dotnet build -c Release -p:GameDir=/path/to/game`. Run `python ../music-player-tests/run.py` with dotnet on PATH.

## Document change log

- 2026-11-09 18:20:26 PST (America/Los_Angeles) — Added BHD menu sequencing, menu silence and explicit voice routing; runtime playback remains untested.

- 2026-11-09 23:02:14 PST (America/Los_Angeles) — Restored missing menu changes on the 1.4.0 voice-player source; added actual-method timing and sequence regression tests.

- 2026-11-10 15:15:58 PST (America/Los_Angeles) — Added compiled China/BHD menu selection, retained fallback behavior, and linked the exact audio recipe and sample-installer scope.
