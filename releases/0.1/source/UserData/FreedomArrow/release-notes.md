# Freedom Arrow 0.1 — deployment candidate

Ground balance changes are packaged. Detection, stealth, firing signature and
concealment use vanilla game behavior for this version. Support, Logistics,
Helicopters and Air keep their original unit/loadout assignments.

Included: scoped vehicle HP/armor, ground AT/HE ammunition tuning, selected APS
restrictions and quantities, vehicle smoke quantity/duration, ATGM infantry
sprint restrictions, and doubled eligible infantry small-arms/GL/sniper carried
ammunition. AT/HE/AA launcher quantities, magazines and reload times are unchanged.

The mode uses the native scoreboard/timer and continuous net-zone advantage.
Contested zones are excluded. It retains the scenario-selected match duration,
with time-limit ending; no 6-minute/6-point QA override is packaged. Final target
points and destruction conversion remain deferred. Developer score/weight
fixtures, custom information box, debug panel and read-only probe are omitted.

This candidate includes guarded Local AI Skirmish setup (F8 in the menu) with AI
spawning restored. The revised AI-enabled package has not had a live launch.
Custom scoring remains guarded to offline Local AI Skirmish. Multiplayer
compatibility and cross-client scoring are unverified; this is not an online
release acceptance result.

Not implemented: requested total cover damage reductions and IFV passenger
overdamage. These are excluded rather than claimed working. Full APS/smoke/
sprint/resupply behavior and all effective loadouts still need gameplay QA.
Upkeep and the income curve remain native. Game build: 26273833.

Install and rollback

1. Keep a clean game installation and a backup of your current mod selection.
2. Import the .bamod through BAModManager/BAModLauncher. Enable only this package
   for the controlled acceptance test; older QA/ActualArrow plugins can conflict.
3. Install the matching MelonLoader dependency using the existing manager flow.
   This archive contains mod files, not MelonLoader or a game bundle.
4. Use the package's guarded Local AI Skirmish setup. Check the runtime receipt
   and logs before accepting the balance changes as loaded.
5. To undo, disable/uninstall this package through the manager. Use its existing
   Play vanilla control. The package does not replace GameAssembly.dll or
   data.unity3d. Do not manually overwrite those files from a QA copy.

This file is an accurate scope/readiness note, not proof of live installation.
