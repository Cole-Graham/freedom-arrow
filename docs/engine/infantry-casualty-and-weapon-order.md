# Infantry casualty order and weapon order

**Summary.** Two data fields set an "order" for infantry. Neither one picks the target a weapon fires at.

- 💀 **`SquadMembers.DeathPriority` sets which soldier dies first.** The squad loses soldiers when its health drops. The game removes an alive soldier with the **highest** value. When several soldiers have that value, it picks one **at random**. The dead soldier's weapons lose one carrier. When a weapon loses its last carrier, that weapon stops firing. Healing brings back the dead soldier with the **lowest** value first.
- 📋 **`SquadWeapons.Order` sets the order of the weapon list.** The list shows on the Arsenal card and in the unit panel in battle. Each weapon of a squad picks its own target and its own round. `WeaponChannel` and `WeaponPriority` are a fire-priority system for vehicle turrets. Vanilla leaves them at 0 on every infantry weapon, and the game skips the system when the channel is 0.
- 🇺🇸🇷🇺 **Vanilla pattern.** One specialist dies last (value 1): the ATGM, reloadable RPG, MANPADS, sniper or HMG/AGL gunner. Machine gunners and marksmen come next. Grenadiers and riflemen with a disposable AT weapon follow. Plain riflemen die first (highest value). The weapon list starts with the rifle and ends with AT and AA weapons.
- 🇨🇳 **China today.** 90 of 136 China squads (63 of 91 fielded) give every member the same `DeathPriority`, so all casualties are random. In only 1 of 40 fielded squads with a specialist does that specialist die last. The China weapon list order is close to the reverse of vanilla's.
- 📌 **Proposal.** Give China the vanilla pattern for both fields. The changes are 498 `SquadMembers` rows ([`infantry-order/death_priority_proposal.json`](infantry-order/death_priority_proposal.json)) and 452 `SquadWeapons` rows ([`infantry-order/weapon_order_proposal.json`](infantry-order/weapon_order_proposal.json)). These are calculations from data. Nobody has tested them in a game yet.

**Basis.** "Code" means read from the 1.2.2.1 binary `work/game-1.2.2.1/GameAssembly.dll` (sha256 `007c0195…`) with the 1.2.2.1 dump `work/port-1.2.2.1/il2cppdump/`. All addresses are 1.2.2.1 RVAs. "Data" means read from the vanilla tables (`lateralus-infantry-20261110/vanilla`) and the Freedom Arrow constants (`releases/0.6/source/UserData/FreedomArrow/constants`, `codex/development-local` 657d31e1). Its squad tables are the same as in `091-wt`. "Inferred" means not proven line by line. Nothing was measured in a game.

> The binary at `ba-dev/game/GameAssembly.dll` (sha256 `12e70883…`) is the build before 1.2.2.1. It matches the older cache dump, not 1.2.2.1.

---

## Contents

- 💀 1. Casualty order: `DeathPriority`
  - 1.1 How the game uses it
  - 1.2 Vanilla pattern
  - 1.3 China audit
  - 1.4 Proposal
- 📋 2. Weapon order: `SquadWeapons.Order`, `WeaponChannel`, `WeaponPriority`, primary and special weapons
  - 2.1 How the game uses them
  - 2.2 Vanilla pattern
  - 2.3 China audit
  - 2.4 Proposal
- ⚠️ 3. Open points and limits
- Document change log

---

## 1. Casualty order: `DeathPriority`

### 1.1 How the game uses it

**Short answer.** Health alone decides **how many** soldiers die. `DeathPriority` decides **which** soldier dies: the highest value goes first, and equal values are picked at random. The game does not look at where a shot hits. It does not look at the weapon or damage type either.

Details (code unless marked):

1. **The value reaches the soldier.** `SquadMembers.DeathPriority` is at +0x14. `UnitBuilder.InitInfantry` (`0x348420`) reads the members in the order of `Units.SquadMembers`. For each member, it calls `SoldierComponent..ctor(deathPriority, …)` (`0x430090`, call at `0x3489DE`). That function stores the value at `SoldierComponent+0x4` (`0x4300CA`). The soldier array keeps member order.
2. **Health sets the number of soldiers alive.** `InfantryDeathHealSystem.InternalUpdate` (`0x40C860`) calculates `target = ceil(Health / HealthPerSoldier)`. The rounding is `roundsd 0xA`, which rounds up (`0x40CA0F` → `0x67628A0`). The result is clamped between 0 and the squad size. Then the method compares the target with `AliveSoldierCount`. When the target is lower, it calls `KillSquadSolders` (`0x40CEF4`). When it is higher, it calls `HealSquad` (`0x40CF05`).
   - **Result:** every damage source that lowers squad health uses this one path. That includes direct fire, splash, artillery and close combat. Stress and panic do not kill soldiers through this path.
3. **The game chooses who dies.** `KillSquadSolders` (`0x40CFF0`) does these steps once for each soldier lost:
   - It finds the highest `DeathPriority` among alive soldiers (`0x40D428`: `cmp [soldier+4], max`).
   - It puts every alive soldier with that value in a list (`0x40D468`).
   - It picks one entry with `_random.Next(count)` (`0x40D4A9`). `_random` is a `System.Random` made with the **parameterless** constructor (`InfantryDeathHealSystem..ctor` `0x40E000`, call `0x40E0F3` → `Random..ctor()` `0x4280060`). That constructor seeds from the clock.
   - **Result:** a higher value dies first, and equal values die in random order. The member order and the row Id do not break ties.
4. **What changes when a soldier dies.** In `KillSquadSolders`:
   - The soldier's `IsAlive` becomes 0. If he was aiming, he leaves every weapon's aiming queue (`0x40D4E8`–`0x40D63A`).
   - `InfantryUnitComponent.ChangeWeaponCount(soldier, −1)` (`0x424F70`) lowers the "current" count of **both** his weapons, primary and special. The HUD weapon panel shows these counts (`UnitWeaponsInfoUpdateModel.UpdateModel` → `TryGetWeaponCount` `0x425870`).
   - For his primary weapon and then his special weapon, the method lowers `InfantryWeaponComponent.UsingAliveSoldierCount` (`0x40D825`, `0x40D884`). Then it calls `RecalculateSoldierWeaponAmmo` (`0x40DA10`), which changes the weapon's ammo pool. The exact ammo formula is not traced.
   - The method resizes the squad collider and nav obstacle. It moves the soldier with the highest formation index into the free slot (`0x40D930`–`0x40D9B2`).
   - If the squad is in a transport or a building, the method updates the loaded count (`LoadedComponent`) and the close-combat damage (`GetCQCDamageInfo`) (`0x40D896`–`0x40D919`).
5. **A weapon with no carriers left stops.** `SoldierWeaponSystem.CheckAndAimNextSoldier` (`0x4306B0`) returns at once when `UsingAliveSoldierCount == 0` (`0x43078C`). The weapon entity stays. Its HUD count shows 0, and the Arsenal card does not change. Nothing in `KillSquadSolders` removes the weapon (code: no removal call). That the weapon fires again after a heal is inferred.
6. **The primary weapon matters too.** A member who carries a rifle and a launcher is one soldier. When he dies, the squad loses one rifle carrier and one launcher carrier together (step 4).
7. **Healing brings soldiers back.** `HealSquad` (`0x40BE90`) scans the dead soldiers in array order. It keeps the **first** dead soldier with the **lowest** value (`0x40C2C6`) and revives `candidates[0]` (`0x40C321`). There is no random choice here. The method adds the soldier back to both weapon counts and calls `RecalculateSoldierWeaponAmmo` (`0x40C78F`, `0x40C7EA`).
8. **Nothing else reads the value.** Every method that reads `SoldierComponent` was checked for `[+0x4]` reads (`xref.py`). Only `KillSquadSolders` and `HealSquad` read it. Airdrop, loading, unloading and movement code does not.
9. **Multiplayer (inferred).** `InfantryDeathHealSystem` has no filter for remote units. Each PC also seeds its own `Random`. So when several soldiers share the highest value, each PC can kill a different soldier. Remote copies do not run target search, so this probably changes only what each player sees. Fewer ties mean fewer of these differences.

### 1.2 Vanilla pattern (data)

**Short answer.** 183 vanilla squads have two or more members. In 179 of them the lowest value is 1. In 171 squads exactly one member holds it: the squad's signature specialist. Plain riflemen hold the highest values.

Member classes. "Rel. pos." is the position between the squad's lowest and highest value: 0 = dies last, 1 = dies first.

| Member class | n | Rel. pos. | Values seen |
| --- | ---: | ---: | --- |
| Rifle + flashbang | 8 | 0.00 | 1 ×8 |
| MANPADS | 26 | 0.12 | 1 ×19, 2 ×7 |
| Reloadable RPG | 50 | 0.14 | 1 ×38, 2 ×7, 3 ×4, 4 ×1 |
| Sniper / AMR | 27 | 0.16 | 1 ×19, 2 ×7, 0 ×1 |
| ATGM | 50 | 0.23 | 1 ×32, 2 ×7, 3 ×10, 0 ×1 |
| HMG / AGL crew | 31 | 0.26 | 1 ×13, 2 ×17, 3 ×1 |
| Machine gun | 135 | 0.48 | 2 ×98, 3 ×30 |
| Shotgun | 20 | 0.50 | 2 ×10, 3 ×9 |
| Stand-alone GL | 14 | 0.51 | 2 ×9 |
| Marksman | 58 | 0.56 | 2 ×48, 3 ×7 |
| Rifle + disposable AT | 177 | 0.60 | 1 ×36, 2 ×47, 3 ×69, 4 ×25 |
| Rifle + under-barrel GL | 130 | 0.71 | 2 ×45, 3 ×64, 4 ×18 |
| Rifle only | 377 | 0.83 | 2 ×121, 3 ×138, 4 ×88, 5 ×6 |

- **The keeper is the member who dies last.** In squads with a specialist, the keeper is that specialist: reloadable RPG 38, ATGM 32, sniper 18, MANPADS 17, HMG/AGL 13. When a squad has two kinds, the order is ATGM > reloadable RPG > MANPADS > sniper/AMR > HMG/AGL, with no counter-example. When a squad has two of the same weapon, one gets 1 and the other gets 2 or 3. In squads with no specialist, the keeper is a rifleman with a disposable AT weapon (31), a flashbang carrier (7) or a machine gunner (4).
- **Officers and radio operators are not protected.** Officer models sit 1–2 above the squad's lowest value (100 of 129). Radio models sit 1–3 above it.
- **The range grows with squad size.** A 4-man squad tops out at 2–3, a 5–6-man squad at 3, a 7–9-man squad at 3–4, and a 12–14-man squad at 4–5.
- **Examples** (value: soldier):
  - 404 Motostrelki Igla: 1 Igla; 2 PKP; 3 GP-34, riflemen; 4 officer, rifleman.
  - 639 Motopekhota AGS: 1 RPG-7V; 2 PKP, AGS-17, rifleman; 3 officer, rifleman; 4 riflemen.
  - 701 Troopers: 1 officer with AT4; 2 M249, M110, AT4; 3 radio, M203, AT4; 4 M203, AT4.

### 1.3 China audit (data)

**Short answer.** China uses flat values. 90 of 136 squads give every member the same value. That includes 63 of 91 fielded squads: 42 all at 3, 19 all at 2, 2 all at 1. In those squads the ATGM, MANPADS or sniper is as likely to die first as any rifleman.

- There are 136 China infantry units (`CountryId 4`) with 828 `SquadMembers` rows. 91 are fielded: 89 are in China specs 17–22, plus 1155 and 1162, which show in the Arsenal. The other 45 are hidden prototype or "Designer" squads.
- Values in use: 3 ×480, 2 ×261, 1 ×83, 4 ×4. Specialists are mostly at the highest value: ATGM at 3 ×16 of 24, MANPADS at 3 ×8 of 13, HMG/AGL at 3 ×18 of 28.
- 40 fielded squads have a specialist. In only 1 of them does the specialist alone hold the lowest value.
- Compared with the vanilla rule on member pairs, 1206 pairs are equal in the data, 209 go the same direction and 155 go the opposite direction.
- Examples of current values:
  - 1152 HJ-8E Team: all 3.
  - 1145 QW-12 Patrol: all 3.
  - 1166 Conscripts: all 2.
  - 901 PLA Rifle Squad: QBU-191 marksman 1, RPK-74M 2, QBZ-191 + RPG-26 3.

### 1.4 Proposal

**Short answer.** Set each China squad to the vanilla tiers below. Number the tiers that the squad uses as 1, 2, 3, …. This changes 498 of 828 rows in 133 units, including all 91 fielded units.

1. **A (value 1): one keeper.** This is the best member by ATGM > reloadable RPG > MANPADS > sniper/AMR > HMG/AGL > rifle + disposable AT > flashbang > MG > stand-alone GL > marksman > shotgun > rifle + under-barrel GL > rifle. When members are equal, the lowest `SquadMembers` Id wins.
2. **B:** other specialists, machine guns, marksmen, shotguns, stand-alone GLs and flashbang carriers.
3. **C:** riflemen with an under-barrel GL or a disposable AT weapon.
4. **D (highest value):** plain riflemen. They die first.

Equal values still die in random order, as in vanilla.

- **Check against vanilla (calculated):** the rule matches vanilla's direction for 1611 member pairs and goes against it for 215. The keeper class matches in 172 of 183 squads.
- **Examples:**
  - 1152 HJ-8E Team: HJ-8E 3 → 1; riflemen 3 → 2.
  - 1145 QW-12 Patrol: QW-12 → 1; QJS-161 → 2; QLG-10A → 3; rifleman → 4.
  - 1163 Mech. Rifles: one PF-89 rifleman → 1; QJB-201 ×2 → 2; the rest 3.
- **File:** `infantry-order/death_priority_proposal.json` has one entry per unit. Each row lists the `SquadMembers` Id, model, primary and special weapon, class, tier, current value and proposed value. The block `apply_as_squad_members_overrides` (`{"<row Id>": {"DeathPriority": n}}`, 498 entries) can be merged into `squad_members.json`.
- **Uncertain points:**
  - In 82 units, the keeper is one of several equal members, chosen by lowest Id.
  - 6 units have more than one specialist kind, so the keeper comes from the vanilla precedence.
  - FHJ-02 (type 62) counts as a reloadable RPG keeper.
  - The QTS-11 integrated GL counts as an under-barrel GL.
  - The 45 hidden units are optional.
- **To test after a batch build (not done):** use a Skirmish against AI. Fire at 1152 HJ-8E Team with small arms. The three riflemen should die before the HJ-8E gunner. The HUD should keep the HJ-8E count at 1 until the last man dies.

---

## 2. Weapon order: `SquadWeapons.Order`, `WeaponChannel`, `WeaponPriority`, primary and special weapons

### 2.1 How the game uses them

**Short answer.** Each distinct weapon of a squad is its own weapon. It picks its own target and round, and all of them fire at the same time. `SquadWeapons.Order` sorts the displayed list. Its zero channel turns `WeaponChannel`/`WeaponPriority` off for every infantry weapon. `HasPriorityOnChassis` is forced off.

1. **One weapon per turret (code).** `LoadUnits.LoadSquads` (`0x288620`) loads each member's primary and special weapon. For each new weapon Id, `CreateFakeTurret` (`0x2836A0`) makes a 360° turret with that one weapon (`FullRotation` +0x34 = true). `InitCombatSystem` (`0x345DB0`) merges weapons only for unit type 4 (`MergeWeaponsOnGroundTurrets`) and types 8/16 (`CombinePylonsOnAircraft`). Infantry (type 2) is never merged (`0x3461F5`).
2. **Independent targeting (code).** The target search and target upkeep systems run once for each weapon entity. The scoring is in `091-wt/docs/engine/target-and-ammo-selection.md`. None of it reads `Order`, primary/special or `Weapons.Type`. In practice, the weapon's ammo `TargetType` mask decides what it may engage. For example, most vanilla AT rockets use mask 45, which excludes infantry.
3. **`WeaponChannel` / `WeaponPriority` (code + data).**
   - `BattleSystemHelpers.CanUseFiringChannel` (`0x7D4AD0`) returns "allowed" at once when `WeaponChannel` (+0xC0) is 0.
   - Otherwise, one weapon per channel per unit may fire. An idle or reloading holder gives up the channel. A ground-attack order takes it. When neither applies, the lower `WeaponPriority` (+0xC4) wins, and a tie goes to the higher score.
   - Two systems call it: `AimingCheckSystem` (`0x7D13DF`, a refused weapon resets its aim) and the overkill scoring (`0x7F8E49`).
   - `TrySetAsActiveWeapon` (`0x813E10`) uses `WeaponPriority` only between weapons on one turret.
   - `LoadWeapons` (`0x289550`) copies channel and priority from `TurretWeapons` for vehicles only. Infantry keeps the `Weapons` row values, and all 812 vanilla rows are 0/0.
   - Inferred: a non-zero channel would stop a whole weapon, for every soldier, in every squad of every country that uses that weapon Id.
4. **`SquadWeapons.Order` (code).**
   - `LoadSquads` writes it to `Weapons.InfantryWeaponOrder` (+0xC8) (`0x288B4B`). A weapon without a row gets `int.MaxValue` and shows last. A duplicate `WeaponId` row for one unit breaks loading.
   - Two places read it:
     - the Arsenal card (`UnitInfoCard.SetUnitWeaponList` `0x561900`, comparator `0x574780`);
     - the battle weapon list (`InitBattleInfoSet` `0x344F50`, comparator `0x36B770`).
   - Both sort by Order and then weapon Id. Both sort only infantry, and only when some Order is not 0.
   - The battle list feeds the HUD panel, labels, the all-weapons toggle, command checks and network routing. It does not feed target search.
5. **`HasPriorityOnChassis` (code).** `SetupWeaponComponents` sets it to false on full-rotation turrets (`0x35275F`). The flag is meant to turn a vehicle hull toward the weapon's target.
6. **Primary and special weapons (code).**
   - The tag only sets the weapon in the soldier's hand (`CheckAndAimNextSoldier` `0x4306B0` → `UsedWeapon`).
   - A soldier who carries two weapons serves one weapon at a time. The first weapon in that frame's pass claims him (`TryGetNextAliveAndAvailableSoldier` `0x40E670`, `IsAiming` flag).
   - The pass follows member order, not `Order`.

### 2.2 Vanilla pattern (data)

**Short answer.** 160 of 198 vanilla squads leave every Order at 0, so they keep member order. The 38 newer squads list the rifle first and AT/AA last. Order: rifle → under-barrel GL → shotgun → MG → marksman → stand-alone GL → sniper → reloadable RPG → disposable RPG → AGL → ATGM → MANPADS → flashbang.

- Example, 701 Troopers: 1 M4A1, 2 M203, 3 M249E3, 4 M110, 5 AT4.
- This rule gives the same shown order as 37 of the 38 squads. The one miss is the GM-94 in 610 Rosgvardia 2.
- 29 of the 38 squads start at 1.

### 2.3 China audit (data)

**Short answer.** 135 of 136 China squads set an explicit order starting at 0. That order puts the AT weapon second and the machine gun third, with the under-barrel GL last.

- Main conflicts with vanilla:
  - a rocket shown before a rifle: 55 cases;
  - an MG shown before a rifle: 53;
  - an MG before an under-barrel GL: 37.
- No rows are missing, duplicated or unused. All 514 weapons have channel 0, priority 0 and `HasPriorityOnChassis` true, as in vanilla.

### 2.4 Proposal

**Short answer.** Set Order to 1..n in the vanilla sequence (ties: more carriers first, then lower weapon Id). Keep channel and priority at 0.

- This changes 452 of 514 rows. The shown order changes on 88 units, 63 of them fielded.
- A 0-based numbering gives the same shown order with 329 row edits.
- The change affects only what players see. It does not change how the squad fights.
- **File:** `infantry-order/weapon_order_proposal.json` (block `apply_as_squad_weapons_overrides`).

---

## 3. Open points and limits

- **Not measured in a game.** Section 1.1 and section 2.1 come from code. The vanilla patterns and the proposals come from data or calculation.
- **Not traced line by line:**
  - the ammo formula in `RecalculateSoldierWeaponAmmo`;
  - the multiplayer effect of random ties;
  - whether a weapon fires again after a heal;
  - each consumer of the sorted battle weapon list.
- **A real fire priority** (for example, "save the AT rocket for vehicles") cannot come from these fields. It needs ammo-mask changes or a code hook. That is a separate decision.
- **Side finding (data):** 66 of 85 China GL entries can target helicopters (mask 47). Vanilla GLs mostly use mask 39, which cannot. CH-901 and the FHJ-02 smoke round can target only the ground (mask 1). Check these against the design notes before you change them.

---

## Document change log

- 2026-11-22 16:40 PST (America/Los_Angeles) — New doc: infantry casualty order (DeathPriority) and weapon order (SquadWeapons.Order) (Lateralus's request)
