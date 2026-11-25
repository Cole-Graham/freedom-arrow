# Artillery MRSI (batch, not in a build)

**Short answer:** an MRSI gun fires 3 rounds per fire mission, and every player's PC slows and lofts each shell of the salvo so all 3 land at the same moment. It is built to stay the same on every PC: the deck says which gun is MRSI, and one hook runs on the shooter's PC and on every other PC for the same shot. Branch `codex/batch/osama/mrsi` only (Osama, 24 Nov 2026: "Dont put it into the build yet"). Not yet tested in a game.

---

**Details**

- **Data** (`tools/pla-specs/mrsi_1124.py`): the PzH 2000 (unit 540) and the M109A6 (247) get one more ammunition option, **MRSI (3 rounds)**. It is a copy of the HE loadout whose gun is a copy of the HE gun with Short / Normal / Long ground attack burst 3. It has the same rounds and quantities, the same cupola MG and the same cost as HE. `UserData/FreedomArrow/mrsi.json` lists the MRSI gun ids and the interval the runtime plans for: `MagazineReloadTimeMax + 1 s`, at least 6 s (PzH 2000 6 s, M109A6 11 s).
- **Hook** (`mod/source/runtime-qa/Mrsi.cs`): one postfix on `ShootingSystem.WeaponForceFire` (1.2.2.1 RVA `0x80E4C0`). The shooter's PC calls it from `ShootingSystem.InternalUpdate`. Every other PC calls it from `NetworkShootService.Remote` (`0x601609`), after `RemoteSetRandomIndex` and the gun rotation from the `WeaponShot` message. So each PC builds the same shell and runs the same change on it. The hook runs once per shot and returns unless the round is a trajectory shell from a listed gun.
- **Flight time** is `(2000 × DistanceDelta − CurrentDistance) / HorizontalSpeed` (`TrajectoryShellComponent.GetTimeToTrajectoryEnd`, `0x82BBC0`). `TrajectoryShellSystem.InternalUpdate` only adds `HorizontalSpeed × dt` to `CurrentDistance` each frame. `GetShotParameters` (`0x82C4A0`) sets `HorizontalSpeed = v·cos(a)` and `HorizontalSpeedProportion = tan(a)`, with `tan(a) = PointHeights[1] / DistanceDelta`.
- **The change per shell:**
  - The first shell sets the salvo landing time: its own flight + 2 × interval + 1 s (game time).
  - Each shell gets `HorizontalSpeed = remaining distance / time to landing`, with the same `v`, so its launch angle gets steeper.
  - The heights above the muzzle-to-impact line are raised by one factor so the arc matches. `InterpolateArtilleryTrajectory` makes a new 2001-float array for every shot, so it is scaled in place and no pointer is written.
  - The impact point stays the same.
- **Salvo grouping:** per gun entity. A new salvo starts after 3 shells, or when the gun has not fired for longer than interval + 3 s. A shell that would already land late keeps its normal flight.
- **Not changed:** laser-guided rounds (M712 Copperhead), every non-MRSI gun, and the HE / HE-RAP / Cluster loadouts.
- **Log:** `FREEDOM_ARROW_MRSI shell k/3 gun G local|remote t …: flight A -> B s, lands t T, speed …, arc ×S` (first 60 shells). Compare the two players' logs after an online test.

**⚠️ Not proven yet**

- Nothing has been run in a game: Skirmish (arc, timing, card) and a 2-player online match (same `lands t` spacing on both PCs, same hits).
- Which PC decides artillery damage was not checked. Every PC flies the same shell, as in vanilla.
- The MRSI option price is the HE price until Osama sets it.

## Document change log

- 2026-11-24 22:45 PST (America/Los_Angeles) — First version: MRSI data section, one `WeaponForceFire` postfix, the flight-time formula from 1.2.2.1.
