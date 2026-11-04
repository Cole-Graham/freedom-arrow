# Freedom Arrow 0.1.1 installed validation

**0.1.1 is installed and its selected data/armor values and leader-only Local AI Skirmish scoring are verified. Full combat/loadout acceptance is incomplete. Detection, stealth, firing signature and concealment remain vanilla.**

4 November 2026. Game Steam build 26273833; MelonLoader 0.7.3; Proton Experimental.

## Current evidence

- Startup repaired with the native version.dll override and Windows .NET 6.0.36 runtime. Direct Proton launch of the installed game reached the armory. Steam launch text and anti-cheat-disabled selection were saved; a complete normal Steam launch remains unverified because Steam reported stale running state.
- Fresh generated wrappers differed in exactly the 16-byte MVID. Only that GUID is excluded from generated-wrapper hashes. Native GameAssembly.dll and every other wrapper byte remain pinned. 14 actual-wrapper checks and 10 standalone metadata regression checks passed.
- All 34 installed payload hashes matched; runtime receipt matched all 8,624 expected writes across seven tables, with zero mismatches. The receipt is application evidence, not an independent readback of every ECS property.
- A 30-minute guarded Local AI Skirmish with ordinary AI captures completed at native Victory 48–22. All 55 ticks followed leader-only net-zone scoring; no tick awarded both sides. Five ticks included contested zones, excluded from holdings. All 1,800 native scoreboard readbacks matched. No synthetic ownership, AI suppression or custom black HUD.
- That full match used the same conquest DLL as the final archive, before the final two-field T-90M armor correction; the correction was checked separately in the armory.
- Broad selected-loadout armory checks cover 22 models: tanks, IFVs/transports, light vehicles, infantry and unchanged support/air controls. See the linked report and evidence/armory-observations.json for exact configurations. No exhaustive all-loadout or combat-mechanics claim is made.
- T-90M base and Arena side HEAT: 200 mm; Additional ERA / obr.17 and ERA+Arena: 400 mm. HP remains 14. Razvedchik uses the shared base profile (data checked, not separately selected).
- Confirmed unresolved: Kornet-D1 has 14 HP base and 10 HP with +15-point armor; MT-LBVM retains 14 HP under the Support exclusion despite an earlier 10 HP request. Turret-specific Stryker/K16/B10 APS restrictions remain absent. Team decisions are pending.
- Controlled interception, smoke duration, actual sprint, resupply, all combined loadouts and equal-cost matchup tests remain incomplete. No frame-time benchmark or multiplayer verification.

Artifact: FreedomArrow-0.1.1.bamod.
SHA-256: edb0b97b8fac1c1693333a899ca7b749a210bb2f3491a2f85d60b6cabf23f3bb.
Main is unchanged. The earlier 0.1.0 artifact is historical.

Full report: https://docs.google.com/document/d/1Dw7jVHtnjB1ST4b3Fe7cKfDX20PiUfIcLX_l7OCyEYM/edit
Linux deployment: ../../docs/releases/0.1-linux.md

---

## Historical record — original 0.1.0 preparation

The following records the original preparation stage before installation and the later 0.1.1 repairs. Its “not launched” statements apply to that stage only.

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
