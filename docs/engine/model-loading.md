# FAModels model loading and detail levels

**Summary.** FAModels replaces a unit's model when the game spawns the unit's view, not when the camera comes close. Vehicles get static `MeshRenderer` parts on the stand-in's bones and a new `LODGroup` with the stand-in's switch heights. China infantry get a new mesh on each native `SkinnedMeshRenderer`. From 0.3.45, a vehicle model that is not built yet is read on a background thread and its lightest detail level is built first. From 0.3.47, a heavier level is built only when the camera is close enough to need it and is removed again 30 s after it stops being needed. Swaps stop for the frame after 6 ms.

Basis: read from `mod/experimental-model-loader` on `codex/development` (FAModels 0.3.44) and the 0.3.45 and 0.3.46 changes. The 0.3.45 and 0.3.46 behaviour is theoretical, not yet proven in a game.

---

## Detail levels

- **LOD0 is the most detailed level.** LOD1 and LOD2 are lighter copies. Past the last level the model is not drawn.
- **Vehicles:** level 0 is the entry's `file` (the battle `_lo` file in a match). The entry's `"lods"` list names the lighter levels.
- **Switch heights:** `SetLevels` copies `screenRelativeTransitionHeight` from the stand-in's own `LODGroup`. Without one it uses 0.10 / 0.04 / 0.005 of the screen height.
- **A level that is not built yet** is covered by the next lighter level that is built. With only the lightest level, that level shows at every distance and is culled at the last height.
- **China infantry bodies:** each native body renderer gets the `.fas` level that matches its place in the soldier's `LODGroup` (`GetLODs()`, capped at 2), or its name (`lod0`/`lod1`/`lod2`). The native bones, animation and LOD switching stay.

## When a swap happens

1. A postfix on `UnitBuilder.InitView` queues the unit (`After`). Infantry bodies and weapons are queued from the same postfix and from `InitInfantryView`.
2. `LateHide` hides the stand-in's renderers every frame (`forceRenderingOff`) while the unit waits and for 5 s after the swap.
3. `UpdateRest` builds queued units on the next frame. `Apply` waits up to 0.5 s for a missing turret bone.
4. The match-start preload (`Preload.cs`) builds the mapped models in the match's decks during the deployment pause, so a normal spawn reuses a built model ("kept model"). From 0.3.46 it builds only the lightest level of each battle model (see below).

## 0.3.45: lightest level first, no file work on the main thread

End reported freezes on Linux 6–8 s after a rejoin (24 Nov 2026). His two MelonLoader logs show, in those seconds:
- up to 78 model swaps and 23 body swaps in one frame;
- 20 model files read on the main thread, 1,872 ms in total;
- the preload built only 3 models on that rejoin.

From the spawn queue, `Apply(..., stream: true)` now:
- checks that every level of the model is already built (`KeptFam`). If yes, it builds all levels at once, as before;
- otherwise it starts the background read of each level (`StreamReady` → `Prefetch`). The unit waits hidden until the lightest level is ready, then only that level is built;
- `TickLodUpgrades` adds the other levels later, one per unit per frame, lightest first, each when its file is ready. Each new part goes on the same bone with the same local pose as the first level's part.

Both the queue and the added levels stop for the frame after `ModelBudgetMs` (6 ms). Infantry bodies already stop after 6 ms (`BodyBudgetMs`). Infantry weapons still build at once.

The turret alignment shift is now worked out once per unit type and entry (`alignCache`). Before, every spawn copied the turret mesh's vertex array.

Log lines:
- `FAMODELS <unit>: ... ; lightest of N detail levels first, the others follow`
- `FAMODELS <unit>: all N detail levels in X s after its lightest`
- `FAMODELS hitch ...: previous frame FAModels did A model swap(s), B later detail level(s), C deferred, ...`

## 0.3.46: the preload builds only the lightest level

Osama, 24 Nov 2026: "load the lowest load and let the engine logic handle the rest". Up to 0.3.45 the preload built every level of every battle model in one burst at match start.

- **Burst:** for a battle model with detail levels, only the lightest level is built in the match-start burst (meshes, materials and textures). The heavier levels are read and prepared on a background thread (`Prefetch`).
- **Rest of deployment** (Osama: "Shouldn't we preload during deployment?"): `TickPreloadHeavy` builds the heavier levels during the deployment pause, at most one per frame and only while the frame's 6 ms model budget has room. It runs after the spawn queue and the level upgrades, so units being swapped come first. Lighter levels are built before heavier ones.
- **A unit that spawns before its heavier levels are built** (early spawn, or a rejoin that skips deployment) shows its lightest level at once, and `TickLodUpgrades` adds the rest over later frames.
- **Same unit type again:** once one unit has built a level, the next unit of that type reuses the kept level. Only the parts are made for it.
- **Unchanged:** models without detail levels, infantry bodies and infantry weapons are still built in full by the preload.
- **Log line:** `FAMODELS preload deck of player N: A lightest battle level(s), bodies and infantry weapons queued; B heavier level(s) to build during deployment`, then `FAMODELS preload: N heavier detail level(s) built in X s after the burst`.
- **Order checked in a log** (Osama's PC, 0.9.6, 24 Nov 12:49): the scene-load free (`freed 3 unused model(s) ... (scene Void)`) runs before the decks are set, and the preload burst follows 11 s later. The preload is not freed straight after it is built in that log.

## 0.3.47: heavier levels only when needed, removed when not

End asked (25 Nov 2026) to load a level only when the engine asks for it, and to unload it the same way.

- **Unity has no hook for this.** A `LODGroup` only picks which loaded renderers to draw. The pick happens inside the native engine (`UnityPlayer`), with no callback and no public current-level getter. Harmony cannot patch it.
- **So FAModels works the level out itself,** every 0.25 s per unit, with Unity's formula: screen share = `LODGroup.size` × scale × `QualitySettings.lodBias` / (2 × distance × tan(FOV / 2)). It uses the camera `Camera.main` (or the highest-depth camera) and multiplies the share by 1.25, so a level is ready a little before the switch.
- **Build:** every unit starts on its lightest level. A heavier level is built only when the camera needs it, within the 6 ms frame limit. `QualitySettings.maximumLODLevel` is respected.
- **Unload:** a heavier level that the unit has not needed for 30 s has its parts removed. A level file that no unit has built for 30 s has its meshes destroyed (`FreeUnusedLevels`); the file is read again in the background when a unit needs it. Materials and textures stay, because all levels of a model share them (measured on the 0.9.6 model stage: 270 battle entries with levels, 0 textures used only by LOD1/LOD2).
- **Deployment:** the heavier levels are only read in the background during deployment; they are not built on the GPU. `UserData/FAModels/lod-preload-build.txt` brings back the 0.3.46 behaviour (build them all during deployment, never free them in battle).
- **Texture leak fixed:** the background read of a heavier level read its textures again although they were already on the GPU, and nothing freed those bytes. `texMade` now skips them.
- The memory line every 60 s counts levels built on demand, levels removed, and files freed.

Not proven in a game: the formula's match with HDRP's own LOD bias (HDRP frame settings can scale or replace `QualitySettings.lodBias`), the VRAM saved, and any hitch when a heavier level is built while zooming in.

## 0.3.48: back to 0.3.46 loading (on-demand levels removed)

Lateralus tested 0.3.47 in 0.9.7-dev.21 (25 Nov 2026): "The hitch when zooming in the first time is unacceptable". 0.3.48 removes the on-demand part: heavier levels are built during deployment and after the spawn again, as in 0.3.46, and nothing is removed in battle after 30 s. `lod-preload-build.txt` is gone with it. The texture re-read leak fix (`texMade`) from 0.3.47 stays. Measured basis: Lateralus's play test (first-zoom hitch); the 0.3.46 behaviour shipped in 0.9.7-dev.16 to dev.20.

## 0.3.49: the armory shows only the full model

Lateralus (25 Nov 2026, dev.21): "the mod's new custom units pop in at the highest LOD before switching to the lowest LOD, the vanilla units don't do that". Read from the code: an armory entry kept its battle detail levels (`lods`), so the full armory model became level 0 of a `LODGroup` whose lower levels were the battle copies, and the armory camera's screen share dropped it to the lightest one. From 0.3.49 the armory (not Potato/Low, which use the battle model on purpose) builds only the full model: one level, and `Apply` adds a `LODGroup` only for two or more. Battles are unchanged. Not yet seen in a game.

## Limits

- Building a level still runs on the main thread: Unity allows Mesh and Texture creation only there. One large level 0 can take more than 6 ms by itself.
- A unit that waits for its file is not drawn until its lightest level is built.
- Why the rejoin preload built only 3 models is not checked yet.
- Up close, a unit can show its lightest level for a few frames until its heavier levels are added.

## Document change log

- 2026-11-24 13:50 PST (America/Los_Angeles) — New page: swap timing, detail levels, and the 0.3.45 lightest-level-first loading (End's rejoin freezes).
- 2026-11-24 15:35 PST (America/Los_Angeles) — Added 0.3.46: the match-start preload builds only the lightest level; heavier levels stream after the spawn (Osama).
- 2026-11-24 15:45 PST (America/Los_Angeles) — 0.3.46: heavier levels are built during the deployment pause within the 6 ms budget (Osama).
- 2026-11-25 09:55 PST (America/Los_Angeles) — Added 0.3.47: on-demand heavier levels, unloading, read-only deployment preload switch and the texture re-read leak fix.
- 2026-11-25 15:4x PST (America/Los_Angeles) — 0.3.48: on-demand levels and 30 s unloading removed after the dev.21 first-zoom hitch (Lateralus); texture leak fix kept.
- 2026-11-25 16:5x PST (America/Los_Angeles) — 0.3.49: armory models without battle detail levels (Lateralus: custom units dropped to the lowest LOD in the armory).
