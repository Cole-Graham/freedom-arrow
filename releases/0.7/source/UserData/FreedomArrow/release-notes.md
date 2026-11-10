# Freedom Arrow 0.7.0-devtest.lat.3 — development candidate

**Lateralus Dev-Test 3 — passive AA diagnostics, same dev.15 gameplay base.**

Select this gameplay package instead of lat.2 or public Freedom Arrow. Keep the existing model/music add-on. No PLA gameplay patch is required.

All 17 AA native diagnostic detours are removed from the observer. It samples its own ECS queries after updates, with bounded work, queue/file limits and performance metrics. Shot callbacks only enqueue an entity; ECS reads occur later. Selected-target overkill flags/scores, ammunition, aim/reload/radar/readiness and nearby sampled air/projectile observations go to UserData/FreedomArrow/diagnostics/aa-targeting-*.jsonl.

These are observations, not exact native rejection reasons. Nearby entities do not prove visibility or target eligibility; brief states may be missed. Native sampling and performance remain untested. The safe fallback lat.2 already demonstrated AA firing with native hooks disabled. If this observer fails, it stops logging and records aa_log_failed.

Gameplay and refund tables are unchanged from lat.2: helicopter flare count15 at10 points each; editor-only target dummies; aircraft free A2A/gun/flares refund costs, health coefficient2/9, cap90%. Helicopter-specific missile ranges and SPAAG range/aim tuning remain proposals.


**Adds full-colour detailed-card portraits from Osama's five supplied aircraft pictures. Su-75 moves to Russian Motorized; Su-47 moves to Russian Guard. Su-47, F-14 and YF-23 remain live from dev.13. Use combined Models and Music0.1.6 for the models, clear canopy preset, approved B-21 and current music/voices.** No PLA test data is included. Cutout icon drafts remain outside this build pending edge cleanup.

The five portrait resources are embedded verbatim; the game still draws the name, price and statistics. Only seven table fields differ from dev.13: five portrait filenames and two specialization links. Weapons, loadouts, prices, ammunition and network-safe option IDs are unchanged. Package, row-planner and installer checks are offline; final portrait framing and canopy clarity still need a game check.

## Defense correction from0.7 dev.1

The native loader selects only the first default ability row. Abrams X previously loaded APS alone; its smoke and ECM rows were separate defaults. XM30 smoke/APS already shared one row, but its ECM was separate. Both units now use one combined default profile. Latest instruction: Abrams X smoke1/APS2/ECM30%; XM30 smoke1/APS2/no ECM. IDs are preserved. Old separate profiles remain linked but non-default. Source/native-control-flow finding; not yet an in-game result.

## Changes from dev.115

- XM30:220 →190 points; same name, weapons, armor, defenses and availability.
- XM30 voice preset: T-15 → M2A3 Bradley. Abrams X retains the existing Abrams preset for the requested Crusader voice lines.
- Companion assets0.1.3: XM30 scale0.70 →0.77; China011 first in the menu, then remaining menu tracks; Mother Of All Weapons added to China battle music. New installs default to USA; existing playlist choice retained.
- Package display name corrected from the stale0.4 label to0.7.

## Carried forward

All other dev.115 data/settings are intended to remain unchanged, including40 mm damaging-artillery penetration floor, TOS damage11 with normal impact, JATM11 km and existing live added units. Su-75 availability remains2. Lateralus's queued branch is separate and is not silently included.

## Known issue and evidence limits

**This candidate corrects the identified first-default ability-selection bug: Abrams X and XM30 now each have one combined default defense profile; Abrams X has30% ECM and XM30 has none. In-game behavior still needs confirmation.** All claimed checks are offline package/data/compile or installer checks until a game result is explicitly recorded. Music playback, XM30 appearance and voice playback need runtime checks. Separate3-second TOS fire remains unimplemented.

## Install

Close the game. In BAModManager > Mods > + Add mods, import the gameplay0.7 candidate and the combined Models and Music0.1.6 pack, confirming replacement. Keep both enabled and ActualArrow disabled. Windows: manager PLAY. Linux: close manager and launch through Steam. A full restart is required. Do not import assets as the main gameplay modpack.


## Network option-ID correction candidate

The native network sends selected option IDs as signed 16-bit values. The old custom IDs exceeded32767 and were truncated, which can remove selected weapons from spawned units despite working in the editor. This candidate maps241 custom options into20000–20240 and migrates saved full-width or already narrowed selections. XM30’s two weapon choices now use20239 and20240. Weapon stats, ammunition, prices, defenses and all other gameplay tables remain unchanged from dev.3. Both players need the same corrected gameplay build.

Host checks cover all option IDs, both XM30 weapon choices and exact table comparison. Live network firing and the separately reported crash remain unverified. Current public gameplay/PC hold stays dev.3 until the candidate is deployed.

## Supply-unloading crash correction candidate

**The two dev.3 dumps show supply UID73/HasValue bytes used as pointer0x100000049 while entering the patched SpawnService.SpawnSupply callback. The candidate removes both supply-creation hooks. It sets existing active caches to the same raw0.4 stealth in LateUpdate instead.** This avoids marshaling the by-reference SupplySpawnData through a generated native-to-managed detour.

The new path checks entity lifetime and the fog component, retries caches whose fog component is not ready yet, and stops after a managed error. A newly created cache can retain vanilla stealth until the next LateUpdate. No supply quantities, costs or combat stats change. This candidate includes dev.4's network option-ID correction. Host regression checks exercise the real SupplyStealth source with native-memory fixtures; they do not prove the IL2CPP runtime behavior. Supply unloading, cache stealth, resupply and removal still need an offline Local AI Skirmish test. No install or public build-index update was performed.

## Diagnostics for the next supply test

**Each run now keeps a separate, flushed diagnostic log with its version and process ID. This records supply invocation and verified changes, rather than only saying that the feature installed.**

Logs are in the game folder under `UserData/FreedomArrow/diagnostics/runtime-<UTC>-<PID>.jsonl`. Startup includes the actual CLR version and SHA-256 hashes of up to128 mod DLLs. Supply records include binding, the first scan, before/after AntiVisible readback, counters and full managed-error stacks. A heartbeat every10 seconds reports whether data applied and whether supply scanning has run. Scene changes, normal quit and unhandled managed errors also get records. Eight sessions are retained, each capped below4 MB; a `log_limit` marker identifies an intentional stop. A diagnostic IO failure disables only this evidence logger.

After a failed test, preserve the diagnostics folder, the matching existing `UserData/FAConquestPrototype` event/state/shot files, MelonLoader logs and any native crash dump. Native access violations can bypass managed handlers: these logs do not replace a `.dmp` and no automatic dump-capture configuration is changed. Invocation, readback and managed-error cases are host-tested; native crash capture and live performance remain untested. Publication and installation are held at Osama's request while this logging candidate is prepared.

## Abrams X autoloader correction

Abrams X now has an exclusive main-gun row with AutoLoaded=true and a5–6 second base reload. It is linked to the intrinsic default turret; gun damage, penetration, aim time, ammunition and other Abrams variants remain unchanged. Network-safe options and saved-deck migration remain included. Solo/editor and network loadout paths are checked offline; live firing intervals, crew/stress effects and a human network retest remain unverified. Candidate only; public gameplay hold remains unchanged.
## Queued next gameplay change

Su-75 Checkmate base price280 →260 points, per Osama. Availability remains2 and loadout prices remain unchanged. Not installed; live hold remains dev.3.

## dev.9 combined build

dev.9 combines the dev.8 supply-crash correction and diagnostics with the Abrams X 5–6 second autoloader and the Su-75 Checkmate base price 260. Osama lifted the hold on 9 November 2026; this build is published to #build-install and installed on his PC. Live gameplay, supply unloading and firing intervals remain untested.

## Changes in dev.13 (Osama, 9 November 2026)

- New cards moved from the PLA test lane, with stand-in stats copied from a parent: Su-47 Berkut (Russia, Su-35S stats and decks), F-14 Tomcat (US, F-15C stats and decks), YF-23 Black Widow II (US, F-22 stats and decks; each bay carries only 2x AIM-120 or 2x AIM-260).
- They are built after every other card, so all existing option IDs and saved decks are unchanged. Their 36 options use new network IDs 20241-20276.
- Their 3D models are private (paid CGTrader models) and load only where FAModels has them; other players see the parent's model.

## Changes in dev.12 (Osama, 9 November 2026: make sure it does not happen again)

- ZIL Karatel: it had two default abilities (1 smoke and Supply Light, 250 supplies). The game loads only the first default ability row (the same bug that dropped Abrams X defenses), so one of them was lost. They are now one combined profile with 1 smoke and 250 supplies.
- New build guards. The build now fails instead of shipping if: a unit has more than one default ability row; an option grants an ability without its unit link; a selectable turret's parent turret is not on the unit (the Abrams X battle-load crash class); or a selectable weapon has no ammunition row for the unit (the armory hides such units). Vanilla's own exceptions are allowed. Row-tests repeat the ability checks.
- Equipment audit: no new doubled default turrets (the UH-1Y Recon's two default door guns match the vanilla UH-1Y), and no new default weapons without ammunition. Four non-selectable leftover cupola links (M8 AGS, M8 Thunderbolt, M10 Booker XM913, M1299) are dead data like vanilla's three; no option can pick them.

## Changes in dev.11 (Osama, 9 November 2026: single-player vs multiplayer check)

- Four option abilities had no matching unit ability link, which vanilla always has: BMP-2 with the BMP-2G and BMP-2M turret packages (1 smoke), T-72B with the T-72B1 package (2 smoke), and BMD-2 with its smoke option. Their links are added, so these options are built the same way as vanilla options. A build check and a row-test now catch any option ability without its link.
- Checked and unchanged: all 2,262 option IDs fit the network's 16-bit range (highest 20,240); the duplicate option orders all copy their vanilla parent's layout.

## Changes in dev.10 (Osama, 9 November 2026)

- XM30 2x TOW-2B option: missile is now TOW-2B top attack (ammo 52, 12 damage, top-armor attack), not the TOW bunker buster (ammo 458, HE, 15 damage). dev.9 used the wrong donor ammunition row. Quantity stays 2.
- M1A1 FEP: Trophy is a Protection system option again, as in vanilla: None, AN/VLQ6 jammer +20, Trophy +70, each with 1 smoke. The armor slot is Default and TUSK. Since 0.5 dev.8 Trophy was a "TUSK + Trophy" armor option, which stacked APS with the protection slot. The option keeps its row id (20015), so saved decks stay valid.
- Abrams TUSK1 +10 → +20 on every Abrams (M1A1 HC, M1A1 FEP, M1A2, M1A2 SEP, SEP v2, SEP v3).
- Abrams TUSK2 +20 → +30 on the M1A2 and M1A2 SEP, +35 on the SEP v2 and SEP v3.
- Abrams Trophy combos follow the kit + 70: TUSK1 + Trophy +80 → +90, TUSK2 + Trophy +90 → +105 (SEP v2, SEP v3).
- Russian side-only armor kits match TUSK1: T-90M ERA +10 → +20, T-90M ERA + APS +80 → +90, T-80BVM obr. 2018+ +10 → +20.

All changes are data only. Built and checked offline; not yet tested in a match.

## Document change log

- 2026-11-09 17:31:05 PST (America/Los_Angeles) — Prepared the authorized0.7 candidate; latest instruction supersedes the previous dev.115 play-session hold. Hold again after this update.
- 2026-11-09 17:45:14 PST (America/Los_Angeles) — Corrected native first-default defense selection; runtime confirmation pending.
- 2026-11-09 17:48:20 PST (America/Los_Angeles) — Latest correction: XM30 one smoke and no ECM; Abrams X retains one smoke, two APS and30% ECM.

- 2026-11-09 18:39:15 PST (America/Los_Angeles) — Prepared network-safe option IDs and saved-selection migration; no live firing or crash fix claim.

- 2026-11-09 19:03:40 PST (America/Los_Angeles) — Added supply-spawn crash candidate: remove by-reference native callback hooks, update active caches in LateUpdate, retain requested stealth and state pending runtime checks.

- 2026-11-09 19:20:18 PST (America/Los_Angeles) — Added bounded per-process diagnostics, build/DLL identity, supply invocation and readback evidence, full managed errors, retention/size limits and collection instructions; deployment held.

- 2026-11-09 19:13:43 PST (America/Los_Angeles) — Added Abrams X exclusive autoloader5–6-second specification, intrinsic linkage and validation gates.
- 2026-11-09 18:11:26 PST (America/Los_Angeles) — Queued Su-75 base price260 for the next gameplay update.

- 2026-11-09 19:30:18 PST (America/Los_Angeles) — Combined dev.8 crash fix and diagnostics with Abrams X autoloader and Su-75 price 260 as dev.9; hold lifted for publication.

- 2026-11-09 19:42:04 PST (America/Los_Angeles) — Queued XM30 TOW-2B top-attack ammunition correction for the next build.
- 2026-11-09 20:46:26 PST (America/Los_Angeles) — Queued M1A1 FEP Trophy back to the Protection system slot for the next build.
- 2026-11-09 21:01:01 PST (America/Los_Angeles) — Queued Abrams TUSK1 +20 and TUSK1 + Trophy +90 for the next build.
- 2026-11-09 21:19:23 PST (America/Los_Angeles) — Queued Abrams TUSK2 +30 (M1A2, SEP) and +35 (SEP v2, v3); TUSK2 + Trophy +105.
- 2026-11-09 21:34:24 PST (America/Los_Angeles) — Queued T-90M ERA +20, ERA + APS +90 and T-80BVM obr. 2018+ +20.
- 2026-11-09 21:36:33 PST (America/Los_Angeles) — Built 0.7.0-dev.10 from the queued changes.
- 2026-11-09 21:44:59 PST (America/Los_Angeles) — Built 0.7.0-dev.11: option ability links (single-player vs multiplayer check).
- 2026-11-09 21:50:52 PST (America/Los_Angeles) — Built 0.7.0-dev.12: Karatel single default profile; ability and equipment build guards.
- 2026-11-09 22:21:46 PST (America/Los_Angeles) — Built 0.7.0-dev.13: Su-47 Berkut, F-14 Tomcat and YF-23 Black Widow II.
- 2026-11-09 23:19:12 PST (America/Los_Angeles) — Refreshed the leading release summary and install instructions for current portraits, pools and asset pack0.1.6; dev.14 was an unpublished validation build.
