# Freedom Arrow 0.1 deployment preparation

**The 0.1 deployment candidate is built. Detection, stealth, firing signature and terrain concealment remain vanilla. The spotting prototype, probe, experiment engine and custom debug panel are excluded. The revised package has not been installed or launched.**

4 November 2026. This is a prepared package for acceptance testing, not a claim that all requested mechanics or multiplayer are verified.

## ✅ Included and excluded

Ground balance retains scoped HP/armor, AT/HE damage and tandem penetration, APS restrictions/charges, vehicle smoke charges/duration, ATGM infantry sprint restrictions and doubled eligible infantry small-arms/GL/sniper carried ammunition. The original KE/HEAT damage formulas remain. Support, Logistics, Helicopters and Air retain their vanilla unit/loadout assignments and shared profiles.

Units, Sensors, SensorUnits and Weapons match their complete vanilla tables. Every option's StealthOverride, MainSensorId and ExtraSensorId also matches vanilla. No spotting config/formula or ground-runtime DLL is packaged. Concealment and damage protection remain distinct: the requested total forest/building damage reductions are not implemented here and are explicitly excluded, along with IFV passenger overdamage.

Only three mods are included: FreedomArrow.Runtime.dll, FreedomArrow.ConquestBatch.dll and BALocalSkirmish.dll. The disposable QA suppression of AI spawns is removed; the initialized offline guard is preserved. The revised AI-enabled build has not been live tested. No read-only probe, Engine experiments, armory suite, behavior test config, command file, saved fixture weights or ground spotting module is present. The custom Conquest OnGUI editor/debug panel is removed from this source.

## 🏁 Mode and interface

The mode retains continuous net-zone advantage scoring, 03:00 opening and 30-second ticks; contested zones are excluded. It uses the native scoreboard/timer with no custom black information box or bar. Match duration comes from the selected native scenario; ending is by time. The temporary six-minute/six-point QA settings are removed. A final point target and once-at-end destruction conversion remain open, so no destruction contribution is claimed.

Custom scoring remains restricted to the package's guarded offline Local AI Skirmish. Multiplayer and cross-client behavior are unverified. The existing native-scoreboard/real-capture test is historical evidence from the earlier QA package, not a fresh launch of this revised archive.

## 🧪 Offline verification

- Runtime loader planner: **1545 patched rows and 8624 field writes** matched all expected tables; 218 cloned profiles isolate eligible ground changes.
- Full vanilla spotting-table and option-sensor/stealth equality checks passed.
- Runtime host regressions: **41 checks passed**, including row validation, rollback, payload protection and shared-weapon references. Some existing host checks cover the historical schedule helper, which is not shipped.
- Existing scoring/HUD host checks: **74 passed** against the same scoring source. The historical HUD model helper is host-only; it does not execute Unity's native UI or prove this package in game.
- The actual shipped PayloadVerifier accepted all **34** file hashes. Archive inventory, duplicate/path safety, pinned settings/Skirmish hashes, required modpack metadata and omitted QA components passed.
- All three DLL builds completed with **0 warnings and 0 errors**.

No game launch, installation, desktop input, main push or external release publication occurred. Final APS interception, smoke lifetime, sprint, resupply, combined loadouts and equal-cost matchups still need live acceptance.

## 📦 Deployment and rollback

Archive: FreedomArrow-0.1.0.bamod (99,312 bytes).
SHA-256: 68f3b42ae70fba61165710f4cc7bfb84b0cd25eec06033d29fc1860aaa308f30.

Import through the existing BAModManager/BAModLauncher. This archive contains mod files and checksum-pinned configuration, not a game bundle or loader installer. Disable older QA/ActualArrow packages that conflict with these DLL paths/hooks. Use the guarded Local AI Skirmish setup (F8 from the menu) for acceptance. Disable/uninstall via the manager to roll back, then use its Play vanilla control. No GameAssembly.dll or data.unity3d replacement is included.

The prepared package, source, verification JSON, README and checksum are included on the codex/0.1-deployment review branch. Main is unchanged, and no final online release has been published. Linux instructions are at ../../docs/releases/0.1-linux.md.

## 📌 Remaining choices and evidence limits

Sam explicitly deferred detection/stealth/concealment to the next update. The native-first research is retained separately and excluded from this package. Its offline arithmetic passes, but cap/critical ordering, startup transactions and live frame time remain unresolved.

Match duration/target and destruction conversion need team confirmation; the package uses the current native-duration/time-ending defaults instead of the QA fixture. Total cover damage reductions and passenger overdamage are absent. Support/air balance remains outside 0.1. A package being built is not proof of a successful live installation.

Reference repository: https://github.com/Cole-Graham/freedom-arrow/tree/0b7c72b7f4c1b93b863879b0217109e8807701f8

Current changelog: https://docs.google.com/document/d/15fXFcDqof1Zkb_3_JM2hnM8FbLbvTfebGF23OLbzGSg/edit

Spotting audit: https://docs.google.com/document/d/11P1F1XTtBJ4vwvxwvalnUNHV0penyztKdiAMnlyiESA/edit

Task: https://discord.com/channels/1566969627743879208/1567304137534603428
