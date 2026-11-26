# Damage over time (burning rounds)

**Short answer:** a round with `DamageOverTimeDuration` above 0 does no damage when it lands. It leaves a fire at the landing point. Every 0.5 s the fire deals a blast of `Damage × 0.5 / DamageOverTimeDuration` to everything inside `HealthAOERadius`. A target that stays in the fire for the whole burn takes the full `Damage`, spread over the burn. Each round makes its own fire, so fires stack.

*Read from GameAssembly 1.2.2.1 (Lateralus 25 Nov 2026, thread 1568104480459722894). Not measured in a game.*

---

## Details

### No impact damage

`ShellHitSystem.InternalUpdate` (RVA `0x7FD3F0`) reads `DamageOverTimeDuration` (`Ammunitions` +0x6C) at `0x7FD7B7`:

```text
if DamageOverTimeDuration > 0 and hit.Type != MissileInterceptionHit (100):
    create a fire entity: DamageOverTimeComponent(initialTime = DamageOverTimeDuration, shooter, buildings hit, hit position)
    jump to 0x7FE26B   (after the unit hit, DamageBuilding and DealAOEDamage calls)
```

So a burning round that strikes a unit, a building or the ground deals none of the usual impact damage (`DealUnitDamage` `0x7FDF09` / `0x7FE11E`, `DamageBuilding` `0x7FDC2E`, `DealAOEDamage` `0x7FE236` are all skipped). A burning missile that is shot down (`HitType` 100) takes the normal path.

### The fire

`DamageOverTimeSystem.InternalUpdate` (RVA `0x7EEA30`) runs for each fire entity:

```text
period = BattleSystemConstants.DAMAGE_OVER_TIME_PERIOD      (0.5, set in the static constructor 0x2A4150)
TimeSinceCheck += dt; TimeRemaining -= dt
if TimeRemaining > 0 and TimeSinceCheck >= period:
    DoTModifier = period / DamageOverTimeDuration
    ShellHitSystem.DealAOEDamage(hit info with DoTModifier, buildings, ...)   (0x7FB4F0)
    TimeSinceCheck -= period
if TimeRemaining <= 0:
    DoTModifier = clamp(TimeSinceCheck / DamageOverTimeDuration, 0, 1)        (the last part tick), then the fire ends
```

`DealAOEDamage` is the normal blast: the health fraction (falloff, or 1 with `NoDamageFalloff`), then armour, as in [Damage falloff](damage-falloff.md), where `DoTModifier` multiplies the base damage. The armour formulas are linear in the base damage, so the ticks add up to one blast of the full `Damage` on a target that stays at the same place.

### Worked example: FHJ-02 incendiary rocket (ammo 2013058)

`Damage` 5, `DamageOverTimeDuration` 10, `HealthAOERadius` 20 (40 m on the card), `NoDamageFalloff` set.

- Impact: 0 damage.
- Fire: 20 ticks of `5 × 0.5 / 10 = 0.25` base damage, at 0.5, 1.0 … 10 s after landing, to every unit inside 20 world units.
- A squad that stays in the fire takes 5 base damage in total. One that leaves after 3 s takes 6 ticks, 1.5.

### DPM visualizer

From 25 Nov 2026 (Lateralus), `dev-tools/dpm_visualizer/calculations.py` and the web copy `dpm-core.js` treat a burning round this way:

- **Hit check (accuracy on):** the fire must reach the target. The share is the mean health fraction over the landing spread (`fire_share` / `DPM.fireShare`), with landing closer than `HealthAOERadius`, falloff unless `NoDamageFalloff`. The size the game subtracts for the target is taken as 0. Other rounds still count only direct hits on the target box.
- **Damage per round:** unchanged, the full `Damage`, because the ticks add up to it.
- **TTK:** plus the mean delay `(DamageOverTimeDuration + 0.5) / 2` s (`burn_delay_s` / `DPM.burnDelay`). A unit's delay is the DPM-weighted mean of its weapons' delays.
- **Pin panel:** shows "burns N s, fire R card m radius: no impact damage, the damage arrives over the burn".

### Not checked

- Whether the fire's stress uses the same `DoTModifier` (stress was not traced).
- How the fire treats infantry inside buildings: the fire entity stores the buildings the impact touched (`BuildingsHash`), and that path was not traced. The visualizer uses the fire share there too.

## Document change log

- 2026-11-25 18:5x PST (America/Los_Angeles) — New: burning rounds deal no impact damage; fire ticks every 0.5 s; FHJ-02 example; DPM visualizer model (Lateralus).
