# FAModels model loading and detail levels

**Summary.** FAModels replaces a unit's model when the game spawns the unit's view, not when the camera comes close. Vehicles get static `MeshRenderer` parts on the stand-in's bones and a new `LODGroup` with the stand-in's switch heights. China infantry get a new mesh on each native `SkinnedMeshRenderer`. From 0.3.45, a vehicle model that is not built yet is read on a background thread. Its lightest detail level is built first and the other levels follow in later frames. Swaps stop for the frame after 6 ms.

Basis: read from `mod/experimental-model-loader` on `codex/development` (FAModels 0.3.44) and the 0.3.45 change. The 0.3.45 behaviour is theoretical, not yet proven in a game.

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
4. The match-start preload (`Preload.cs`) builds every mapped model in the match's decks during the deployment pause, so a normal spawn reuses a built model ("kept model").

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

## Limits

- Building a level still runs on the main thread: Unity allows Mesh and Texture creation only there. One large level 0 can take more than 6 ms by itself.
- A unit that waits for its file is not drawn until its lightest level is built.
- Why the rejoin preload built only 3 models is not checked yet.

## Document change log

- 2026-11-24 13:50 PST (America/Los_Angeles) — New page: swap timing, detail levels, and the 0.3.45 lightest-level-first loading (End's rejoin freezes).
