# FA Music 1.4.1

**Restores the GLA menu pause and shuffle, and China’s theme-11 opener, while keeping the 1.4.0 voice queue fixes.** This player works with the shared live asset pack and PLA gameplay data.

GLA (Black Hawk Down): menu theme 11 first, then themes 01–10 in shuffled cycles without repeats within each cycle. Wait 120 seconds after a track ends. China: `Menu/First` opener first on menu entry, then the ordinary menu songs. China, USA and Russia keep their existing gap policies. Battle gaps remain 120 seconds, calm gaps 10 seconds, victory/defeat play once.

The Game music selection retains the published 1.3.11 native-voice gate. Custom packs retain the newer 1.4.0 voice queues and US missing-recording suppression. No audio files are changed by this source update.

The regression occurred because 1.4.0 was based on source without the 1.3.11 menu changes. Live logs showed the GLA opener repeated at 22:51:09 and 22:54:59 on 9 November 2026. Host tests execute the actual OnUpdate, PlayNext, Switch and FolderFor methods with a simulated clock/FMOD channel. They verify gap boundaries, all ten GLA tracks, China opener/reentry, unchanged USA timing, battle/calm gaps and victory once. Audible playback remains untested in a new game run.

Build with `dotnet build -c Release -p:GameDir=/path/to/game`. Run `python ../music-player-tests/run.py` with dotnet on PATH.

## Document change log

- 2026-11-09 18:20:26 PST (America/Los_Angeles) — Added BHD menu sequencing, menu silence and explicit voice routing; runtime playback remains untested.

- 2026-11-09 23:02:14 PST (America/Los_Angeles) — Restored missing menu changes on the 1.4.0 voice-player source; added actual-method timing and sequence regression tests.
