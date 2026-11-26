# Infantry soldiers with two weapons (rifle + shotgun, rifle + launcher)

**Summary.** There is no rule that makes a soldier "switch to the shotgun" at close range. The rifle and the shotgun are two separate weapons. Each picks its own target and fires as fast as its own carrier count allows. A soldier who carries both can only aim one of them at a time, but that rule almost never holds back a shot.

- 🔫 **Each weapon is its own gun.** A squad gets one weapon entity per weapon Id. It counts every member who carries that weapon, primary or special. Its burst cooldown and its reload run N times faster with N alive carriers. So 12 Mk18 carriers fire like 12 Mk18s.
- 🎯 **Range does the "switching".** The shotgun's round (12ga SLUG, `GroundRange` 100) can only target inside 100 m. Beyond 100 m only the rifle fires. Inside 100 m both fire at the same time.
- 🧍 **The shared soldier.** Before each shot the weapon puts one free carrier in its aiming queue. The shot needs a soldier in that queue. A soldier who is aiming for one weapon is skipped by the other. He is freed when the shot goes off, about 0.5 s later.
- 📊 **Effect (calculated).** Marine Raiders CQC inside 100 m: the shared-soldier rule changed nothing in a 10-minute simulation. The Mk18 ×12 and M1014 ×4 gave the same shots with and without it. In all vanilla squads, the busiest dual-weapon soldier aims about 41% of the time (Rosgvardia AK-105 + KS-23), so a soldier is never needed by both weapons for long (this estimate assumes one soldier per burst).
- 🏠 **Close-quarters combat** (`GetCQCDamageInfo`) adds every CQC-flagged weapon with ammo at its rate × carrier count. Rifle and shotgun both count in full there, with no shared-soldier rule.
- 😰 **Shocked and panicked (calculated).** Stress lengthens time between bursts and reload (infantry: shocked ×1.33 / ×1.25, panicked ×2 / ×1.5) and widens dispersion. It does not change the 0.5 s a soldier spends aiming before each shot: `CheckAndAimNextSoldier` reads `AimingAnimationDuration` straight from `InfantryConfig`, with no stress factor. So stressed weapons fire less often and the shared soldiers are free more of the time. In the simulation the Raiders CQC lose the same share as squads with no shared men (Mk18 176.5 → 133.7 → 90.3 shots/min, M1014 105.1 → 80.8 → 56.1), with no wait for a free man at any level. Stress hurts dual-weapon squads by the same percentage, not more.
- 🧮 **DPM visualizer.** It already treats each weapon separately, with its carrier count and its own range. For unit 70 it counts Mk18 ×12, M1014 ×4, M72A10 ×8 and M32 ×2, which matches the game. No change is needed.

**Basis.** "Code" means read from the 1.2.2.1 binary `work/game-1.2.2.1/GameAssembly.dll` with the 1.2.2.1 dump `work/port-1.2.2.1/il2cppdump/`. Addresses are 1.2.2.1 RVAs. "Data" means the vanilla tables (`lateralus-infantry-20261110/vanilla`) and the Freedom Arrow 0.9.7 package. "Calculated" means the simulation [`infantry-dual-weapons/sim.py`](infantry-dual-weapons/sim.py). Nothing here was measured in a game.

---

## Details

### Marine Raiders CQC (data)

- Unit 70 (option `Custom_Option_Closequarters`), 14 men, 26 weapons:
  - 4 men: Mk18 CQBR + M1014 (members 113, 114, 118, 119);
  - 8 men: Mk18 CQBR + M72A10 LAW;
  - 2 men: M32 MGL only.
- Ranges (`GroundRange`): Mk18 5.56 mm 200, M1014 12ga SLUG 100, M72A10 66mm HE 200 (min 10), M32 40 mm 200 (min 6).
- Single-gun rates (card formula): Mk18 15 shots/min, M1014 26.7, M72A10 3.3, M32 22.2.
- Freedom Arrow 0.9.7 keeps the squad as vanilla. Only the 12ga SLUG round (359) changed: damage 4.8 → 7.0, penetration at range 8.

### How the game fires a dual-weapon squad (code)

1. **One weapon per weapon Id.** `LoadUnits.LoadSquads` gives each weapon its own 360° fake turret. `InfantryWeaponComponent` (`UsedBySoldiers` +0x8, `AimedSoldiersQueue` +0x18, `LastAimedSoldierIndex` +0x24, `UsingAliveSoldierCount` +0x28) lists the members who carry it. Targeting runs once per weapon (see [infantry-casualty-and-weapon-order.md](infantry-casualty-and-weapon-order.md) 2.1).
2. **Rate × carriers.** `BurstCooldownSystem.InternalUpdate` (`0x7EBF60`, `0x7EC05B`–`0x7EC063`) and `MagazineReloadingSystem.InternalUpdate` (`0x7F4680`, `0x7F4BC3`–`0x7F4BCB`) multiply the time step by `UsingAliveSoldierCount`.
3. **A soldier is queued shortly before the shot.** `SoldierWeaponSystem.CheckAndAimNextSoldier` (`0x4306B0`):
   - It needs a target or a ground target. Hold fire, reloading or no target empties the queue.
   - It runs when the time to the next shot is at most `InfantryConfig.AimingAnimationDuration` (+0x70; 0.5 s in the asset extract of 11 Nov 2026).
   - `InfantryHelper.TryGetNextAliveAndAvailableSoldier` (`0x40E670`) takes the next carrier after the last one used, round-robin, that is alive (`SoldierComponent` +0x0) and not aiming (+0x61).
   - `AddSoldierIndexToAimingQueue` (`0x40E120`) sets aiming (+0x61 = 1). The soldier's `UsedWeapon` (+0x48) becomes 1 for a primary weapon or 2 for a special weapon (`0x4308D8`).
4. **The shot needs that soldier.** `ShootingSystem.CheckInfantryConditions` (`0x80D060`) returns false with no carriers alive. With an empty queue it returns true only when the squad is in a building or vehicle (`Has<LoadedComponent>`).
5. **The soldier is freed by the shot.** `WeaponShootingEffectsSystem.SpawnShotVfx` (`0x6C97E0`) calls `TryGetSoldierEffectSpawnPoint` (`0x40E760`). That dequeues the soldier, clears aiming (`0x40E8B3`) and uses his muzzle for the effect.
6. **Close-quarters combat.** `BattleSystemHelpers.GetCQCDamageInfo` (`0x7D6C20`) loops over the squad's weapons. It takes those with the `Weapons.CQC` flag (+0x4B) and ammo. Each one adds a value from its round (+0x64, probably damage) × `RateOfFireSecond(weapon, UsingAliveSoldierCount, …)`. Mk18 and M1014 both have `CQC` true.

### Simulation (calculated)

`sim.py` applies rules 2–5 to unit 70 inside 100 m, with both weapons always on a target, for 600 s:

```
shared men (engine):    Mk18 176.5/min, M1014 105.1/min, 0 s waiting for a free man
no sharing (DPM today): Mk18 176.5/min, M1014 105.1/min
```

The calculated rates are 12 × 15 = 180 and 4 × 26.7 = 106.7. The small gap is the 0.01 s time step.

## ⚠️ Limits

- The time-to-next-shot helper (`0x41B520`) was read only in outline. The simulation assumes one queued soldier per upcoming shot and leaves out the aim time.
- `AimingAnimationDuration` 0.5 comes from an asset extract of 11 Nov 2026, not from a 1.2.2.1 read.
- The rule could matter for a weapon whose time between shots per carrier is under 0.5 s and that shares men with another weapon. No vanilla squad comes close (highest calculated busy share 41%).
- Not tested in a game.

## Document change log

- 2026-11-26 10:1x PST (America/Los_Angeles) — New doc (Lateralus: Marine Raiders CQC has more guns than men; is there a shotgun switch, and does the DPM visualizer account for it).
- 2026-11-26 09:4x PST (America/Los_Angeles) — Added shocked/panicked effect on shared soldiers (Lateralus: is stress worse for squads that share soldiers?).
