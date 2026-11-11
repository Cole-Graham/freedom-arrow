# FA Music 1.5.0

**The music selector is a native UGUI control at the bottom centre of Home. It uses the game's font and underline, shows a pack flag/emblem and name, and cycles on click. The verified mod version appears above it.**

USA, Russia and China use national flags. Black Hawk Down uses an original stylized 3/75 Ranger scroll, based on the involvement of B Company, 3rd Battalion, 75th Ranger Regiment in Task Force Ranger. It is a UI identifier, not a reproduced official battalion flag. [US Army history](https://www.benning.army.mil/Tenant/75thRanger/3rd-Battalion.html). The Game soundtrack option uses a music symbol.

The control follows Home's native selected state and disappears on Arsenal and other tabs. It retains the existing pack.txt persistence and voice/audio switching. Existing China and Black Hawk Down menu compilations are unchanged; the exact recipe is in [menu-compilations](../menu-compilations/README.md).

The four mixes contain their song order and120-second gaps, including a final120-second gap before the next selection. When these compiled files exist, they take priority over the previous opener/shuffle system; the player adds no extra menu pause. Packs without the new files keep their previous behavior. USA and Russia are unchanged. Battle gaps remain120 seconds, calm gaps10 seconds, and victory/defeat play once.

The Game music selection retains the published 1.3.11 native-voice gate. Custom packs retain the newer 1.4.0 voice queues and US missing-recording suppression. The accompanying sample installs new menu audio and removes BHD theme09. Other songs and voice recordings are preserved.

The regression occurred because 1.4.0 was based on source without the 1.3.11 menu changes. Live logs showed the GLA opener repeated at 22:51:09 and 22:54:59 on 9 November 2026. Host tests execute the actual OnUpdate, PlayNext, Switch and FolderFor methods with a simulated clock/FMOD channel. They retain the legacy gap tests and add forced random outcomes, exclusion of stray menu files, and no double gap for the new compilations. Audible playback remains untested in a new game run.

Build with `dotnet build -c Release -p:GameDir=/path/to/game`. Run `python ../music-player-tests/run.py` with dotnet on PATH.

## Document change log

- 2026-11-09 18:20:26 PST (America/Los_Angeles) — Added BHD menu sequencing, menu silence and explicit voice routing; runtime playback remains untested.

- 2026-11-09 23:02:14 PST (America/Los_Angeles) — Restored missing menu changes on the 1.4.0 voice-player source; added actual-method timing and sequence regression tests.

- 2026-11-10 15:15:58 PST (America/Los_Angeles) — Added compiled China/BHD menu selection, retained fallback behavior, and linked the exact audio recipe and sample-installer scope.

- 2026-11-11 12:59:07 PST (America/Los_Angeles) — Added the native menu selector, flag/emblem artwork and Home-only visibility; retained audio and voice logic. Native checks are recorded in the task report.

- 2026-11-11 13:10:01 PST (America/Los_Angeles) — Imported the verified1.5.0 player source into complete PLA Build23; the packaged DLL is pinned to the independently installed/tested SHA from source4712dba.
