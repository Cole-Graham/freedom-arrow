# Freedom Arrow 0.7.0-dev.21 — development candidate

**UI icon edge correction:** the nine custom cutout textures discard faint background alpha, keep every solid pixel, and use trilinear mipmapped sampling. This removes the generated X-47B haze without replacing source PNGs or colour portraits. All gameplay data from dev.20 is retained. Native visual review is pending.

**Aircraft correction batch: F-21 has its own950 km/h flight preset and explicit empty mount positions5/6 so fuselage weapons replace correctly; Su-47 has no R-37 choices in any slot; single-seat Su-57 offers only AA loads.** X-47B now has a white icon with inlet detail and its supplied colour portrait. Six custom aircraft icons are revised without landing gear, with merged white bodies and clearer canopy openings. Osama requested shipment for human visual review; final appearance is not approved or measured. Uses Models and Music0.1.8.

F-21 retains215 base,40% ECM and the seven requested payload choices. A fresh configuration and every pair of repeated swaps now match under the native indexed replacement/append rule; selected option IDs resolve identically after signed16 serialization. This is a source-derived host check, not a multiplayer firing result. Su-47 inner R-37 choices now migrate to the existing2× R-27ET+2× R-77 inner default. Single-seat Su-57 loses ten ground-weapon choices and retains two AA options per bay; Su-57D keeps its separate choices.

**X-47B now has its own right-facing white silhouette icon and a full-colour card portrait from Osama’s supplied second screenshot.** Uses Models and Music0.1.8. All dev.18 gameplay, models and existing pictures are retained; only the X-47B image addresses/resources are added. In-game appearance awaits user inspection.

**F-21 Super Tomcat replaces the F-14 card using the current F/A-18E baseline:215-point airframe,950 speed and40% intrinsic ECM. Seven loadouts match Osama’s list; the explicitly requested2× SLAM-ER is the only ground-attack choice. F-35A moves to Stryker. Eight right-facing cutouts and eight original full-colour portraits are included.** Companion Models and Music0.1.8 adds the F-21 name mapping to the existing F-14 model.

Outer pylons:2× Sidewinder+25 (retained donor price). Inner pylons:4× Sidewinder+50 or2× AIM-174+60. Fuselage:6× AIM-120+80,4× AIM-174+100,2× AIM-174+60 or2× SLAM-ER+90. First choice in each slot is default:370 total. Own multi-round carriers retain native model paths; firing and visible missile placement still need a game check. Saved F-14 choices migrate to legal defaults, with duplicate same-slot selections removed.

Su-47 retains dev.16:Su-57 agility on base/fuel mobility,205 airframe,40% intrinsic ECM, unchanged25 flares and the eight requested loadout removals. Card pictures:Su-75,Su-47,Su-57D,YF-23,F-21,Karatel,XM30,Abrams X. Original screenshots are embedded verbatim; approved aircraft icons are mirrored at render time, and the three new vehicle cutouts face right already. Appearance awaits user inspection.

## Vehicle silhouette correction

Karatel, XM30 and Abrams X use flat white silhouettes matched to Osama’s native-icon reference. No multishade panels or realistic surface shading is intended. The five approved aircraft cutouts and all eight full-colour portraits are unchanged. User inspection at native UI size remains pending.

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

Close the game. In BAModManager > Mods > + Add mods, import the gameplay0.7 candidate and the combined Models and Music0.1.8 pack, confirming replacement. Keep both enabled and ActualArrow disabled. Windows: manager PLAY. Linux: close manager and launch through Steam. A full restart is required. Do not import assets as the main gameplay modpack.


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

## Aircraft pictures and specialization correction

Su-75 Checkmate is available in Russian Motorized Infantry (9); Su-47 Berkut is in Russian Guard (12). Each has one specialization pool. These changes preserve loadouts, ammunition, costs and network-safe option IDs.

Su-75, Su-47, Su-57D, YF-23 and F-14 have custom full-colour portrait addresses. Approved cutout PNGs are included unchanged and mirrored horizontally when their UI texture is created, so all five face right. Colour portraits use Osama's supplied screenshots, embedded verbatim in the gameplay DLL. Names, prices, armour and statistics remain native. Portrait aliases share one texture per image. Visual placement still needs a game check.

The separate model pack contains FAModels0.3.4 and the clear-canopy sidecars. Gameplay does not contain the paid model files.

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
- 2026-11-09 23:07:21 PST (America/Los_Angeles) — Added five aircraft portraits; cutout drafts excluded pending cleanup, Su-75 Motorized and Su-47 Russian Guard assignments; runtime appearance pending.
- 2026-11-09 23:19:12 PST (America/Los_Angeles) — Refreshed the leading release summary and install instructions for current portraits, pools and asset pack0.1.6; dev.14 was an unpublished validation build.
- 2026-11-09 23:54:31 PST (America/Los_Angeles) — Added Su-47 agility, intrinsic40% ECM,+40 airframe price, eight loadout removals and saved-option fallbacks.
- 2026-11-09 23:57:20 PST (America/Los_Angeles) — Included the five approved cutout icons with right-facing rendering; original image pixels retained.
- 2026-11-10 00:20:29 PST (America/Los_Angeles) — F-21 requested baseline/loadouts, F-35A Stryker and three vehicle icons/portraits; retained Su-47 and five approved aircraft icons.
- 2026-11-10 00:26:46 PST (America/Los_Angeles) — Replaced three shaded vehicle thumbnails with white silhouettes following Osama’s native-icon example; dev.17 remained uninstalled.
- 2026-11-10 00:36:34 PST (America/Los_Angeles) — Added X-47B silhouette thumbnail and original colour portrait; gameplay stats unchanged.
- 2026-11-10 00:50:12 PST (America/Los_Angeles) — Corrected F21 flight speed/mount continuity, all Su47 R37 removals, Su57 AA-only choices and six gear-up icon revisions; human visual review pending.
- 2026-11-10 00:59:18 PST (America/Los_Angeles) — Added UI-only alpha preparation and mipmapped icon filtering; source pictures and gameplay retained.
