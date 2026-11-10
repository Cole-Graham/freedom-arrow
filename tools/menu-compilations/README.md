# China and Black Hawk Down menu compilations

**FA Music 1.4.2 uses two complete menu mixes for China and two for Black Hawk Down. Each mix has a 50% chance on each selection. The mixes contain the requested song order and 120 seconds of silence after every song, including the final song.**

These replace each affected pack's old menu files. USA, Russia, game music, voices, gameplay data, and infantry alignment are outside this update. Black Hawk Down theme09 is removed from all its source playlists. Theme11 remains menu-only in that pack; it was not added to battle music.

## Recipe and evidence

`recipe.json` is the exact order. China playlist2 intentionally repeats theme10. There is no initial silence. The final120-second segment supplies the gap before another mix starts, so the player adds no second pause.

`build.py --archive ASSETS.bamod --out OUTPUT` reads supplied audio, measures the US menu reference with FFmpeg loudnorm, levels each source song to that measured integrated loudness, and encodes four320kbps stereo MP3s at48kHz. It uses a true-peak target of−1dBTP rather than copying the reference's over-full-scale peaks. Minor normalization and encoding differences are measured in the output evidence. Source audio is not stored in Git.

`verify.py OUTPUT` uses NumPy and FFmpeg to decode all four completed mixes. It checks exact decoded sample counts and digital silence within every gap, excluding100ms at either MP3 boundary for filter ringing. The unencoded recipe inserts exactly5,760,000 stereo samples per gap.

The player tests execute the actual selection/update methods with a simulated FMOD channel and clock. They force both random outcomes, reject stray legacy files, retain an active mix on duplicate menu cues, and check that embedded gaps receive no extra player delay. This establishes code behavior; it is not audible native-game verification.

`install.py` is a music-only sample installer for Vengeance. Put it beside `music-sample-1.4.2.zip` and `payload-manifest.json`. It requires the game to be closed, checks the previous player hash, backs up affected files, installs four mixes and the new player, removes BHD09, then verifies the new hashes and every other Mods/UserData file. Run the same script with `--undo` to restore the backup; it refuses to overwrite a later player/music update.

This is a local sample update. It does not change the pinned PLA/live package aliases or publish a new combined asset pack. A future profile install must carry this update forward explicitly. Keep the sample backup until that migration is verified.

## Document change log

- 2026-11-10 15:15:58 PST (America/Los_Angeles) — Added the exact four menu recipes, US loudness reference, embedded gap policy, verification method, and guarded sample-install/undo instructions. Native audible playback remains unverified.
