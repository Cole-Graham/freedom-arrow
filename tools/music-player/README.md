# Music player 1.3.11

Black Hawk Down plays its menu opener once, then shuffles its ten battle tracks without a repeat until the cycle is exhausted. Menu and battle tracks have 120 seconds of silence between them. China retains track 011 as its opener and theme 01 afterwards; its second-song selection remains pending.

Game music uses native voices. Every custom pack enables the existing US custom voice replacements. Selecting Game music stops an active replacement clip and resets custom order suppression. Units or commands without replacement recordings retain the native fallback; this update does not create missing recordings.

Compiled against the current game interop assemblies with zero warnings and errors. Host checks cover ordering, cycle exhaustion, gaps, reset behavior and voice routing for all four packs. These checks do not prove audible runtime playback.

Distributed in one combined Models and Music 0.1.4 pack. Gameplay stays at the separately held 0.7.0-dev.3. Original audio, model and texture bytes are retained.

## Document change log

- 2026-11-09 18:20:26 PST (America/Los_Angeles) — Added BHD menu sequencing, menu silence and explicit voice routing; runtime playback remains untested.
