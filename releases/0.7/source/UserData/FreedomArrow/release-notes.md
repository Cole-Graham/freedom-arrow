# Freedom Arrow 0.7.0-devtest.lat.7 — development candidate

**dev.45: Su-75 Checkmate stealth is2 in UI terms (raw Stealth and CurrentStealth0.5), up from approximately1.5 (raw0.666). Includes the current dev.44 T72 armor-card correction. All other gameplay constants match dev.44. Native card/detection verification pending.**

**T-72B3AM obr. 16 armor values: restore the default flag on its linked base armor and clear it on the retired unlinked armor. The native card requires a linked default armor for comparison. Armor thickness, HP, cost and loadouts are unchanged from dev.42. The build now rejects units with armor links but no default armor. Native display verification pending.**

**dev.42: XM30 base price is 200 points, up from 190. All other gameplay constants match dev.41, including LOSAT damage12 and missile card speed1500. The separate Abrams X silver-texture trial does not change geometry or gameplay. Native price/appearance verification pending.**

**dev.41: LOSAT missile damage is 12, up from 10, and missile card speed is 1500, up from 1300 (raw speed 1500/3.6). All other gameplay constants match dev.40. Native damage and speed verification pending.**

**dev.40: LOSAT road speed50 and missile card speed1300. Missile raw speed is1300/3.6, correcting the previous4680 card reading. Bradley mobility and all other balance data are retained. Includes the dev.39 MAKO AMRAAM carried-model correction. LOSAT shared model-map repair is installed separately without replacing other model settings. Native confirmation pending.**

**dev.39: the F-22 MAKO carried mesh uses the native single AMRAAM model instead of the protruding Kinzhal model. Weapon statistics, quantity, +80 per bay, and all other gameplay data remain as dev.38. Native visual review pending.**

**dev.38: F-22 adds 1x MAKO at +80 in each side bay, using the current ARRW statistics. MiG-31BSM loses every R-37, R-77, R-73 and R-27ET option and missile link; its bomber loads and cannon remain. Retired AA deck choices migrate to free empty slots. Includes Black Widow turn700 and Copperhead75 mm. Native fit and firing remain untested.**

**dev.37: YF-23 Black Widow II turn radius calculates to 700 in the native card UI (previously 565). Its own flight/mobility rows preserve every other aircraft. Speed, pitch, roll, weapons, cost and ECM stay unchanged. Includes dev.36 Copperhead 75 mm penetration. Not yet measured in-game.**

**Copperhead:75 mm HEAT penetration at both range endpoints, reduced from472.5. Base damage remains11. Data change; not yet tested in game.**

**Lateralus selected promotion: changelog items 3, 5 and 7–12.** Target dummies are editor-only; passive AA diagnostics from lat.4 are included with zero targeting/scoring detours. RMG4 damage/100% Ignore Cover; standard SMAW-D25%; Mech. Engineers CQC55; Mech. Riflemen MMG4 AT4CS-RS; HIT ammo shown as84mm Thermobaric with6.5 damage/100% Ignore Cover; Combat Engineers75. Latest LOSAT and M25 changes below are retained.

Items1,2,4,6 remain separate: helicopter flare stock, helicopter-only missile ranges, aircraft refund rework, and SPAAG range/damage/cooldown experiments are not imported. No aircraft-refund or cooldown hook is added. The passive observer records sampled state, not exact rejection reasons or a complete interception count; large-scene performance remains unmeasured.

M-25 CDTE: Stryker Troopers AT and Troopers AA each replace two M203s with one special-weapon XM25 copy (0.75 damage, 75% cover bypass). The original five-round magazine and firing/reload timings are retained. Both riflemen remain, with a shared 120-round grenade pool (24 magazines; about 3 minutes at the nominal sustained firing rate). Troopers AT costs100 →105 and Troopers AA60 →65. Green Berets, Delta Force and other M203 users retain their weapons. Data and package checks do not establish native firing, visual weapon switching or multiplayer behavior.
**LOSAT: 200 points, Stryker only, availability 2, 12 damage, 550 mm KE penetration and missile card speed 1500 from launch.** Twelve missiles, interception disabled and tank-shell critical-effect rules are retained. Hull protection remains unupgraded M2A2 Bradley: KE/HEAT100/80/60/40 front/side/rear/top,12 hull HP.

**Static model only:** companion assets0.1.14 remove the LOSAT turret-bone attachment and automatic alignment. Armory and battle versions each contain one root group; all mesh-segment positions,normals,UVs,indices,materials and textures are byte-identical to the prior export. No moving or separately parented LOSAT parts remain. Native placement still needs review.

**Card art:** the colour portrait is Osama’s supplied screenshot, embedded verbatim. The thumbnail is a white strict side-profile render of that same supplied model, facing right. LOSAT now receives the existing mipmapped cutout handling.

**Projectile setting:** MuzzleVelocity=1300,MaxSpeed=1300,Acceleration=0, so the requested speed applies immediately rather than being hidden behind a slow acceleration ramp. Damage=10,KE penetration=550 at both range endpoints. Existing range, guidance, target masks and critical-effect thresholds remain. These are data/code checks; native flight,damage,interception and crit behavior require a game test.

Firing gap:6 seconds between missiles, as requested by Osama; reduced from10. Empty-launcher reload remains15–20 seconds. Native firing cadence remains untested.

## Superseded development history

The following earlier descriptions record previous development steps. Their LOSAT values, pictures and attachment setup are superseded by the current summary above.

**LOSAT is added as its own US vehicle with a kinetic missile: 600 mm KE penetration, 10.5 damage, 12 rounds, twice the base Kornet speed and interception disabled.** Uses the supplied MGM-166 tracked model in companion assets 0.1.13, with separate armory/battle meshes, a source-rendered portrait and right-facing white silhouette. Existing live dev.24 changes are retained.

LOSAT uses unupgraded M2A2 Bradley protection: KE and HEAT 100/80/60/40 front/sides/rear/top. Vehicle HP 12 follows the Bradley because the native field is an integer; the requested 10.5 is interpreted as missile damage. Approved price 180, Stryker only, availability 2. No BUSK/TUSK, APS, smoke, secondary weapons or passenger seats. Parent Bradley mobility/optics remain. Range retains base Kornet 1600 displayed metres. Launcher fires one missile at a time, with twelve loaded and the Kornet launcher’s firing interval; no ripple burst.

Motion values: muzzle 10, maximum 400, acceleration 232, burn 2 s versus Kornet 5/200/58/4 s. Velocity ×2, acceleration ×4 and burn duration ÷2 scale the speed curve in half-time in the theoretical straight-flight model; native flight and steering remain unmeasured. Ammunition targets KE armor, 600 penetration at minimum and maximum ground range; both interception/targeting flags are false. It keeps Kornet guidance and accuracy.

A dedicated LOSAT classification uses the same crit threshold as tank shells: actual front/side damage at least 9.3 gives yellow mobility plus one eligible random yellow. Qualifying rear anti-tank hits give red mobility. Targets remain tanks and IFVs. This does not give every hit an automatic crit and does not broaden other missile rules. Code/host-test result; native firing,APS bypass,model alignment and crit application require a game run.

**F-22, single-seat Su-57 and Su-75 turn-radius correction:** only these three cards use an isolated horizontal-turn preset calculated to display800 in the native card. At250 m/s, MaxSpeedYaw59°/s gives800.43 before UI rounding, versus the earlier565 displayed radius. Horizontal yaw curves scale together; pitch, roll, speed, prices, weapons and all other units are retained. Su-47 keeps its previous maneuverability, including fuel options. Native card/flight verification is pending.

**Wheel zoom over unit icons:** bypass both native follow-target checks so scrolling reaches the normal zoom path. The earlier fix bypassed only the check inside ScrollForward; Update had a second label/follow check that could still consume the wheel. Both call sites and their branch bytes are validated before writing; old one-site installs can upgrade, readback is checked and failed writes attempt rollback. Native UI gates remain. Compiled policy and pinned-code checks pass; actual camera behavior awaits a game test.

**X-47B bay update:** the former single-AMRAAM choice in each bay is now2× AIM-260 JATM for+60. Both selected bays carry four missiles. Existing2× AIM-120 defaults and other loadouts remain. Includes the UI-only cutout alpha/mipmap correction, preserving every solid shape pixel and all source PNGs. Native appearance and firing need review.

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


Full SPAAG test: based on locked dev.45. Only six AA gun ammo profiles gain Actual Arrow 1.1.20 LowAltRange, HighAltRange and Damage endpoints. No price, missile-speed, cooldown or refund changes. Use Mod Manager for this test; public launcher restores dev.45. Native game behavior untested.

## Tracking comparison lat.7

C-RAM and PIVADS horizontal and vertical tracking doubled. C-RAM720/230degrees per second;PIVADS720/180. All18full SPAAG range/damage fields fromlat.6 retained. No lead, aim, cadence, speed, overkill or other gameplay change. Passive log adds yaw,error,target velocity and cached ballistics,without combat helper calls or new native hooks. Shots stay in one session file across editor restarts. Normal game exit writes test-logs-*.zip under UserData/FreedomArrow/diagnostics; send that one ZIP. Collection tested offline;native logger invocation and gameplay still need this test. Public launcher remains locked todev.45.

Compare the same saved editor setup aslat.6,with the same unit positions,starting orientation,readiness and incoming missiles. Judge first shot timing and whether SEAD is stopped;tracer tails are a visual clue,not an impact measurement.

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
- 2026-11-10 01:02:15 PST (America/Los_Angeles) — Replaced X47 single-AMRAAM bay choices with2× native AIM260 JATM,+60 each; included icon alpha/filtering fix.
- 2026-11-10 01:17:30 PST (America/Los_Angeles) — Corrected the second wheel follow-target check; retained native UI guards and added pair validation/readback/rollback. Runtime wheel behavior pending.
- 2026-11-10 01:47:19 PST (America/Los_Angeles) — Isolated F22/Su57/Su75 at calculated800 UI radius; preserved Su47 and other consumers, pitch/roll/speeds.
- 2026-11-10 03:12:59 PST (America/Los_Angeles) — Added LOSAT dedicated KE missile,tank-shell crit classification,base Bradley protection,source-rendered card art and companion model pack requirement; native tests pending.
- 2026-11-10 03:31:13 PST (America/Los_Angeles) — Corrected LOSAT to approved150 points,Stryker-only specialization and600 mm KE penetration; prepared installation replacing PLA TEST.
- 2026-11-10 03:33:44 PST (America/Los_Angeles) — Applied Osama’s final LOSAT values:180 points,availability2,Stryker only,600 mm KE.

- 2026-11-10 03:45:53 PST (America/Los_Angeles) — Added M-25 CDTE replacement for Stryker Troopers AT/AA and the requested +5-point prices; native behavior untested.
- 2026-11-10 03:46:45 PST (America/Los_Angeles) — Removed LOSAT bone attachment via static assets0.1.14; applied200 points,12 damage,KE700,speed1800; replaced card portrait with supplied screenshot and side-profile silhouette.

- 2026-11-10 03:50:21 PST (America/Los_Angeles) — Increased M-25 ammunition to120 rounds per team; incorporated the current static LOSAT revision without changing it.

- 2026-11-10 04:05:07 PST (America/Los_Angeles) — Set LOSAT to missile speed1300,damage10 and KE penetration500 at both endpoints; retained M25 teams and static models.

- 2026-11-10 04:20:03 PST (America/Los_Angeles) — Selected550 KE and the suggested10-second firing gap for LOSAT; retained10 damage and1300 speed.

- 2026-11-10 04:23:12 PST (America/Los_Angeles) — Promoted Lateralus items3,5,7–12 only; passive lat.4 observer and editor-only dummies; six infantry changes; other batch items held.

- 2026-11-10 11:24:11 PST (America/Los_Angeles) — Corrected LOSAT firing gap to6 seconds; retained dev.34 balance changes,1300 missile speed,10 damage and550 mm KE.

- 2026-11-10 16:10:37 PST (America/Los_Angeles) — Set M712 Copperhead ammunition426 to75 mm penetration at minimum and maximum range; retained base damage11 and all other ammunition settings.
- 2026-11-10 16:20:01 PST (America/Los_Angeles) — Recorded isolated YF-23 turn-radius700 change and offline verification limits.
- 2026-11-10 16:31:54 PST (America/Los_Angeles) — Recorded F22 MAKO side bays and bomber-only MiG31BSM loadouts, preserving preceding changes.
- 2026-11-10 16:45:02 PST (America/Los_Angeles) — Changed only the F22 MAKO carried mesh to AMRAAM; all gameplay statistics retained.
- 2026-11-10 16:53:54 PST (America/Los_Angeles) — Corrected LOSAT displayed missile speed and isolated50 road speed; recorded shared model-map repair.
- 2026-11-10 17:19:42 PST (America/Los_Angeles) — Increased LOSAT missile damage from 10 to 12 and card speed from 1300 to 1500; other gameplay constants retained.
- 2026-11-10 17:29:35 PST (America/Los_Angeles) — Raised XM30 base price from190 to200; retained dev.41 LOSAT values and recorded separate source-resolution silver texture trial.
- 2026-11-10 17:58:14 PST (America/Los_Angeles) — Corrected T-72B3AM default armor flags and added all-unit linked-default validation; native card restoration awaits a game check.
- 2026-11-10 18:10:29 PST (America/Los_Angeles) — Increased Su75 UI stealth to2 on the current dev.44 base, preserving its T72 armor flags and all other gameplay data.

- 2026-11-10 21:32:36 PST (America/Los_Angeles) — Prepared isolated full Actual Arrow SPAAG range/damage test lat.6 on dev.45.

- 2026-11-10 22:13:51 PST (America/Los_Angeles) — Prepared tracking-only lat.7 test with bounded passive diagnostics and single-session log collection.
