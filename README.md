# PLA TEST Build 57

Every Airborne squad (PLAAF Air Force) now wears the SF goggles down desert body: Airborne, HJ-12 Team, Tank Hunters, QLU-11 Team, Pathfinders, Thunder Gods, Snipers, QW-12 Patrol, Assault Raiders and Recon, plus the five unused Airborne rows. Same preset, body offset and hand anchoring as the existing goggles-down squads; weapon alignment is unchanged.

"Mechanized" is removed from the displayed names of the PLAGF squads: HJ-8E Team, QW-2 Team, QLZ-04 Team, PF-98 Tank Hunters, Combat Engineers 工兵班, QJZ-89 Team, plus three unused rows (AT Riflemen, GPMG Riflemen, Guided-AT Riflemen). "Mech. Rifles 机步班" keeps its name for now. No other value changed.

## Historical Build56

# PLA TEST Build 56

China restored. Builds 47-55 wrote empty pylon slots in the new loadout options as null; the game requires 0 and rejected the whole PLA patch (FREEDOM_ARROW_FAILED: Field type mismatch Turret0Id). All 3,870 slots now 0. Everything else is exactly Build55. check_field_types.py now runs on every build.

## Historical Build55

# PLA TEST Build 55

PL-15 and PL-16 copy the AMRAAM with 500 more range (4500); PL-17 copies the AIM-260 JATM (5500). PL-21 and PL-15C unchanged. Native behaviour unverified.

## Historical Build54

# PLA TEST Build 54

Stealth jets (J-20, J-20S, J-35, J-31, J-50, J-36) gain LD-8A anti-radiation loadouts (AGM-88 HARM performance, internal) and PL-16 loadouts (PL-15 performance; 6 in the bay that holds 4 PL-15). J-16 gains 32x 250 kg bombs + 2x PL-15 + 2x PL-10. Menus may hold up to 10 loadouts. Native behaviour unverified.

## Historical Build53

# PLA TEST Build 53

AKD-10 renamed HJ-10 in every PLA weapon, ammunition, pylon and loadout label (statistics unchanged). Z-20KA/Z-20T menu labels now name the Chinese weapons (HJ-10, FS-70A, 70 mm rockets, TY-90, 30 mm gun pods) instead of the vanilla DAP text. Native appearance unverified.

## Historical Build52

# PLA TEST Build 52

Extra loadouts for aircraft that CMO lists few for (Osama: add extra rather than be cautious): J-20/J-20S, J-35, J-31, J-36, J-50, J-15D, J-16D, GJ-11, Wing Loong, J-5, J-6W, H-6K, J-10A, J-8D, J-7, Z-21, Z-9WA now carry 4-8 loadouts each. Stealth jets internal only; recon helicopters stay rockets only. Native behaviour unverified.

## Historical Build51

# PLA TEST Build 51

ZTZ-99 = T-90M (armour, gun, ammo, 195). ZTZ-99A front kinetic armour 800 (300 pts). Z-20KA and Z-20T get the MH-60M DAP pylon menus with Chinese munitions (AKD-10, FS-70A, 70 mm rockets, TY-90, 30 mm pods). HJ-73/HJ-73D missiles slower (100 vs Fagot 150); HJ-73D Team 30, ZBD-03 40, ZBD-86 20. Recon helicopters carry unguided rockets and guns only. Native behaviour unverified.

## Historical Build50

# PLA TEST Build 50

Airborne Riflemen renamed Airborne. Godswords carry 6 QTS-11 with grenade launchers again (no PF-89). Mountain Leopards in the recon tab. HQ-7 removed (HQ-7B stays); HQ-9A stowed. J-16 and J-16D to PLAAF, J-11D and GJ-11 to PLAGF Motorized, FH-97A to PLAAF air tab, MD-22 to the PLAN SOF air tab, WZ-8 to PLAN SOF recon. PHL-16 loadouts: 10x BRE3 300 mm, 8x BRE6/BRE8 370 mm or 2x Fire Dragon 480. SR-5 copies the M142 HIMARS (Fire Dragon 70, Fire Dragon 70 cluster, Fire Dragon 300, Fire Dragon 480) and moves to PLAN SOF. Shaanxi HMV3 Cargo uses M1075A1 PLS statistics on the HEMTT model. Squad weapons listed rifle, AT, MG. In-game appearance and behaviour remain unverified.

## Historical Build49

# PLA TEST Build 49

Artillery: each PLA tube and rocket system copies the main round, launcher behaviour, ammunition count and price of its vanilla counterpart (PHL-03 = Smerch, PHL-16/191 = Tornado-S round, PHL-11 = Grad, SR-5 = Uragan 220 mm, PLZ-05 = K9, PLZ-07/89 = 2S1, PLZ-45 = M109A6, PLZ-83 = 2S3M1, PLL-05 = Nona-SVK, DF-15/17/21 one Iskander missile each). DF-31 untouched. Infantry: PF-97 = MRO-Z values; HJ-8E 700 and HJ-73D 600 penetration everywhere. 53 PLA squads priced from the three most similar vanilla US/RU squads (pla-build49.json lists them). Native behaviour unverified.

## Historical Build48

# PLA TEST Build 48

Ground-vehicle pass over Build47. ZTZ-99A matches the T-14 Armata (850/1300 front armour, 500/525 APFSDS, 3 gun-launched missiles); ZTZ-100/ZTZ-20 the same class; ZTZ-99 = T-90A, 96B = T-72B3, 96 = T-72B, 59D = T-62M, 59 = T-55 class. Every PLA vehicle ATGM uses 10.5 damage. 31 vehicles repriced against their vanilla counterparts (pla-vehicle-pass.json). Native behaviour unverified.

## Historical Build47

# PLA TEST Build 47

Every armed PLA jet and helicopter gets a loadout menu taken from Command: Modern Operations (DB3K_519): up to 8 distinct loadouts, no fuel tanks or pods, internal bays only for stealth fighters. Chinese weapons copy the closest weapon already in the game (PL-15 = AIM-260, PL-12 = R-77-1, PL-10 = AIM-9, YJ-91 = Kh-31P, LT-2 = KAB-500, CJ-10K = Kh-101; helicopter ATGMs 10.5 damage). Each aircraft takes speed, armour, sensors, stealth and default ECM from one vanilla counterpart of its generation, and a new base price. Native behaviour unverified.

## Historical Build46

# PLA TEST Build 46

Shaanxi HMV3 now has the HEMTT mounts and option sets (cab/armor and weapon slot); the native HEMTT model draws those parts through them, and the HMV3 had none. Two versions in every spec: Shaanxi HMV3 (mixed cargo/infantry, 27 seats, carries infantry) and Shaanxi HMV3 Cargo (pure supply, no seats). Everything else is exactly Build45. In-game appearance remains unverified.

## Historical Build45

# PLA TEST Build 45

Names: Recon (was Target Observers), Forward Observers, Mech. Rifles. Squads: Airborne Riflemen +1 QBU-10; Tank Hunters lose the QJY-201; Mountain Leopards QBU-191 -> QBU-10; Mechanized Combat Engineers 7 men; Thermobaric Team 1 FHJ-02; Godswords carry 6 PF-89 (special slot, replacing the QTS-11 grenade launcher). Removed: Motorized PF-98 Tank Hunters, Mechanized GPMG Riflemen, Mechanized AT Riflemen. Mechanized PF-98 Tank Hunters use a tripod PF-98 with its own weapon card: HEAT to 800 m and DZD98A HE (SPG-9 OG-9V copy, 1000 m, ignores cover, no vehicle targets). GAM-102LR uses the Spike weapon card. FH-97A copies the F-35B flight, armor, stealth, sensors and ECM and carries 4 AMRAAM. ZSD-89 also in PLAN SOF. PLARF Infantry uses the conscripts emblem with a gear. In-game appearance and behaviour remain unverified.

## Historical Build44

# PLA TEST Build 44

J-11 family: J-11BS (former J-11B, 4th gen), new J-11BHG (4.5 gen: Su-35S flight and ECM, J-11B weapons) and new J-11D (SEAD copy of J-16D), all on a lighter J-11 skin (J-16 / J-16D models). Removed Y-20B, J-7E, J-8II, JJ-5, J-2. Renamed J-8D and J-6W. Z-8L is in every spec and carries infantry that fits its 27 seats. Z-20 family: Z-20S Air Force recon (Exceptional Optics), Z-20KA Air Force armed transport, Z-20 for PLAGF, Z-20J unarmed and Z-20T armed for PLAN SOF. Armed Z-20s use DAP-style loadouts: 2x TY-90 + 4x CM-501G, 2x TY-90 + 4x CM-502, or 6x TY-90. CM-502 copies the vanilla LMUR; CM-501G is an anti-infantry LMUR (20 damage, ignores cover, no vehicle or helicopter targets). TY-90 copies the vanilla helicopter AIM-9. In-game appearance and behaviour remain unverified.

## Historical Build43

# PLA TEST Build 43

Four-tier MANPAD ladder, each copying a vanilla missile: FN-6 = Igla-N (FN-6 Team), HN-6 = FIM-92F Stinger (Motorized AA Troopers, Air Defense Scouts), QW-2 = Igla-S (Mechanized and Marine QW-2 Teams), QW-12 = Verba (QW-12 Patrol, Sea Dragons). Tank Hunters carry 6 DZT-98 thermobaric rockets, 600 m, no vehicle or helicopter targets. Removed: Recon HJ-8E Ambush Team, ZTZ-99A2, ZTZ-99G, VT-4, J-10CE. MD-22 to PLAN SF, HQ-9B to Rocket Force. New ZTQ-15 Recon in Armored (Very Good Optics); ZTQ-15 gun autoloaded, 4-5 s reload. HJ-10 name restored. Lynx ATV has the M1301 ISV weapons and M240/M2/Mk19 options. Z-19E cards renamed Z-19 and Z-19 Recon. J-35 uses the former J-31 model; J-31 uses the J-35 model with the low-vis texture (no Chinese writing). In-game appearance and behaviour remain unverified.

## Historical Build42

# PLA TEST Build 42

Air Force has Z-10K and a Z-10 (copy of the Armored Z-10); the Z-10K Recon and Z-10 Recon cards are removed. Assault Raiders carry one QLB-06, a handheld 35 mm launcher copied from the vanilla M32 MGL. PF-98 and PF-98A use a weapon card traced from Osama's PF-98 icon. Spec badges: the Bayi star is removed from Air Force and Armored and the emblem enlarged; Navy shows the enlarged anchor with a small Bayi star on the shank; Rocket keeps its original badge. Everything else is exactly Build41. In-game appearance remains unverified.

## Historical Build41

# PLA TEST Build 41

Osama's 12 Nov roster batch. Removed: AFT-10 duplicate card (the HJ-10 card is now named AFT-10), J-20B seller package, ZTZ-85-III, ZTZ-80, VT-5, ZBL-19 seller card, ZBL-09 and the CSK-181 recon card (CSK-181 stays as the Rocket Force transport). Moved: J-10CE to Motorized; FH-97A, J-16D, Jiutian UAV and Y-8 to PLAN SF; H-6K to Air Force. New PLAN SF copies of Z-19, Z-19 Recon and Z-20. Y-8 is a Harvest Hawk-style gunship (native KC-130J Harvest Hawk weapons, model and flight). Designation names replace Type and seller names (ZTZ-59, ZTZ-59D, ZSD-63, ZSD-89, ZSD-89A, ZBD-86, JJ-5, J-2, Y-8, DF-17/ZF). Spec names: PLAAF Air Force, PLAGF Ground Force/Armored, PLARF Rocket/Reservist, PLAN Navy/SOF, PLAGF Motorized. Mi-8 Cargo moves from the hidden Logistic tab to Helicopters and China has no logistic slots, as in vanilla. Infantry: every Rocket Force rifle is the QBZ-95; Godswords are 6 men with 6 QTS-11; Blood Wolves and Sea Dragons in the infantry tab, Beijing Swords in recon; Falcons get a PF-98; names shortened (no Airborne except Airborne Riflemen, no Reserve, Infantry, Counter-Raid Team, Assault Raiders, Marines) with at most four Chinese characters; Whistling Arrows use their own emblem. QBU-191 is suppressed. Recon helicopters keep guns and unguided rockets only. QJY-201 has a traced weapon card. J-11B shows the J-16 model. The J-50 refuelling probe is stowed. In-game appearance and behaviour remain unverified.

## Historical Build40

# PLA TEST Build 40

Restores China in the armory. Builds 33-39 gave 73 new infantry squads a BaseSquadSize field that the game's unit table does not have; the runtime refuses a new row whose fields differ from the table, so it restored vanilla and the armory showed only RU and US. The field is removed (squad size still comes from the squad member rows), and the regression check now applies the same row rule. Everything else is exactly Build39. In-game load remains to be confirmed.

## Historical Build39

# PLA TEST Build 39

QN-202 is a Javelin-style, infantry-only missile with RPG-7 HE, 12 shots in Whistling Arrows; the CTL-181 launcher fires the same missile. GAM-102LR copies Spike LR as the new Motorized GAM-102LR Team (75 pts). Conscripts and Missile Site Security each get one QBU-88 marksman. The five LG export test squads are removed. New QBU-88 and QN-202 weapon cards traced from Osama's photos. Runtime DLL compiled as 39. Native behaviour unverified.

## Historical Build38

# PLA TEST Build 38

Fixes "PLA TEST (verification failed)" at game start. Builds 34-37 carried the Build 33 runtime DLL, so its compiled version (33) did not match the package build number and the runtime refused the payload. The DLL is rebuilt with 38 compiled in, and the regression and package checks now refuse any DLL whose compiled version is not the build number. Everything else is exactly Build37. In-game load remains to be confirmed.

## Historical Build37

# PLA TEST Build 37

J-10A now has its own texture: the J-10C blue-grey panels are repainted a neutral dark white-grey. Builds 31-36 used a colour tint that turned it salmon/tan. J-10C is unchanged. Everything else is exactly Build36. In-game appearance remains unverified.

## Historical Build36

# PLA TEST Build 36

DF-31A now carries the native Kh-47M2 Kinzhal nuclear warhead (666 damage, 350 m blast, nuclear explosion effect and sound) on its ballistic flight. AR-2000, CR-500 Recon, CR-500B and Z-6B UAV are removed because they had no model. ZBD-251 keeps the Kurganets model. Everything else is exactly Build35. Native launch, blast and warning remain unverified.

## Historical Build35

# PLA TEST Build 35

Build34 plus the infantry sheet edits Osama made after the Build32 import: Reserve QJZ-89 and QLZ-87 Teams 12 men (were 9), Reserve Thermobaric Team 12 (was 6), Marine Riflemen 8 (was 12), Reserve HJ-73D Team one HJ-73D (was 2), and the struck FHJ-02 Incendiary Team removed. Carriers follow the new sizes. Everything else is exactly Build34. Native validation pending.

## Historical Build34

# PLA TEST Build 34

Adds the Shaanxi HMV3 supply truck (native HEMTT model and statistics), shared by Armored, Rocket Force and Motorized. Everything else is exactly Build33. Native appearance and resupply remain unverified.

## Historical Build33

# PLA TEST Build 33

One spec per selectable PLA card, except Mi-8 Cargo across all five. Includes latest HQ-17A, J-15/JH-7, PGZ-09, HQ-7 and ZBD-86 assignments, Build32 infantry sheet reconciliation, and the original DF-31 warning draft. Cross-spec carrier links and nine donor-ID fields are corrected. Native deck building, warning audio and appearance remain unverified.

## Historical Build32

# PLA TEST Build 32

**Applies the current formatted infantry sheet: removals, bilingual names, sizes, classes and fixed kits; combat-engineer thermobaric loadout; reference-derived QLG-10A HUD. Build31 equipment and approved body/art alignment retained. Native validation pending.**

## Historical Build31

# PLA TEST Build 31

Build31 applies Sam's 12 November equipment/spec revision over exact Build30. Infantry bodies, approved HUD art, music and saved alignment are retained. Native visual and combat checks remain pending. See `tools/pla-specs/build31-roster-checks.json`. DF-31 has a separate, original synthesized warning draft through the existing ballistic alert; it respects its mute/volume settings. Launch/audio behavior is not yet proven in-game. Nuclear blast tuning remains pending.

**Branch-specific infantry body presets and all15SF in night variants. Approved Build29 weapon artwork, rifle assignments and conscript ability policy retained. All24 gameplay tables, weapon alignment, geometry and materials are unchanged from29. Native appearance pending.**

## Historical Build29

# PLA TEST Build 29

**Reference-edge weapon HUD cards,plain/optic QBZ191 assignments,separate QBZ192/QCW05,and no sprint/smoke for13PLA conscript squads.SF abilities and existing weapon/ammo statistics,stocks,unit stats and model alignment are preserved.Native validation pending.**

## Historical Build28

# Freedom Arrow — pla

**Complete PLA development pack — Build 28. This stream is separate from main gameplay.**

## Maintained branches

- [Main 0.7 development](https://github.com/Cole-Graham/freedom-arrow/tree/codex/0.7-development) — dev.55 integration.
- [Public gameplay source](https://github.com/Cole-Graham/freedom-arrow/tree/main) — locked dev.45.
- [PLA development](https://github.com/Cole-Graham/freedom-arrow/tree/codex/pla-development) — complete PLA pack.
- [Assets development](https://github.com/Cole-Graham/freedom-arrow/tree/codex/assets-development) — shared models, music and voices.
- [Launcher development](https://github.com/Cole-Graham/freedom-arrow/tree/codex/launcher-development) — launcher and manifest client.

Use one `codex/batch/lateralus/<topic>` branch per coherent unpromoted batch; reuse it across commits and test builds. Build identities use tags. See [branch policy](docs/development/BRANCH-POLICY.md) and [source pins](docs/development/branch-streams.json). Source maintenance does not change the public manifest lock or rebuild existing packages.

# PLA TEST Build 28

**Three targeted emblem corrections, white-outline grey-fill right-facing weapon HUD and Russia → USA → China country controls. Original approved masters and all gameplay/model/music data retained. Native inspection pending.**

## Historical Build27

# PLA TEST Build 27

**Replaces Blood Wolves, Mountain Hunters and Blue Sword with photographed central motifs. All26 custom unit-icon families now use clean white/transparent exports; baked grey-green shading and low-alpha halos are removed. Original approved masters are preserved; other silhouettes/layouts remain. Four service badges retain their approved star/八一 contrast; Motorized badge is whitened consistently. Gameplay, models, offsets, weapon HUD, rigging, music and audio stayBuild26. Native appearance pending.**

## Historical Build26

# PLA TEST Build 26

**Corrects the runtime MelonInfo version that remained23 and caused Build25 to refuse its PLA payload. All Build25 artwork, geometry, contrast, gameplay and shared assets are retained. Compiled identity is now checked against channel/build metadata before packaging. Native verification pending.**

## Historical Build25

# PLA TEST Build 25

**Four branch badges now give the 八一 characters stronger contrast against the star. Only existing fill/stroke colors change. Exact shapes, alpha, sizes and positions are preserved; all approved unit icons and gameplay remain Build24. Native appearance pending.**

## Historical Build24

# PLA TEST Build 24

**Approved infantry unit emblems and five branch spec badges. All Build23 gameplay data, weapon HUD art, models, rigging, audio and FA Music1.5.0 retained. Native appearance pending.**

Thirteen approved unit profiles use the reviewed shapes; the earlier requested Godsword blade-only correction is included. Air Force, Ground Force, Rocket Force and Navy spec icons reuse actual branch-badge central SVG geometry; Motorized reuses its approved unit emblem. No new combat statistics or roster assignments.

## Historical Build23

# PLA TEST Build 23

**Build23 combines the complete Build22 emblem/name refinement with the installed FA Music1.5.0 native Home selector. Every game-table field and all64 addressed icon PNGs match Build22; approved Thunder Gods and Whistling Arrows remain untouched. Audio, models, ammo, stats, rigging, preferences and Build17 grouping are retained. The music selector was tested separately on Build21; the combinedBuild23 pack remains untested in-game.**

## Historical Build19 identity and initial badge pass

# PLA TEST Build 19

**Build19 adds patch-derived monochrome unit icons to all90 designer squads and standardizes14 named-team labels from published sources. Generic squads retain their role names with parent-branch insignia; exact-patch and motif/fallback evidence are recorded separately. The eight custom weapon profiles now face right and use filled pale normal/outline sprites with a dark keyline, matching actual native infantry HUD captures. Build17 grouping, all28 rigging fixtures, portraits, ammo, stats, loadouts and model alignment are retained. Native appearance remains untested.**

## Historical Build18 weapon-art candidate

# PLA TEST Build 18

**Weapon HUD revision: replaces the rejected block sketches with detailed native stand-in art for 341 entries and eight custom Chinese profile families (16 normal/outline sprites) for ten entries. Four custom profiles come from the approved meshes; four bullpup profiles use photo references or marked family approximations. Build17 Arsenal grouping is retained. Unit artwork, ammo, weapon stats, loadouts, models and rigging are unchanged. Native HUD validation is pending.**

## Historical Build17 UI correction

# PLA TEST Build 17

**Arsenal specialization presentation fix: shared PLA units follow a selected specialization heading instead of remaining under their first eligible heading. Native availability, search, category/type filters, normal/photo cards and callbacks stay in use. Build16 weapon-family HUD artwork and all existing gameplay, infantry sizes, models, offsets and music are retained. Native UI verification is pending.**

## Historical Build16 weapon HUD update

# PLA TEST Build 16

**Weapon HUD artwork update: 307 vehicle weapon definitions and 44 designer-infantry weapon definitions use 108 physical-family silhouette assets. Related variants share art. Unit portraits, unit thumbnails, ammunition icons, stocks, loadouts, performance, models and saved rigging are unchanged from Build 15. These are simplified recognition drawings; prototype and unnamed weapon geometry remains provisional. Native HUD validation is pending.**

## Historical Build 15 model update

# PLA TEST Build 15

**Final family-model reuse correction: J-20B uses the installed J-20 mesh, J-8II uses J-8 and Y-20B uses Y-20. VT-1A, VT-4, Type 80, Type 63 APC and Type 89/89A reuse the closest installed PLA tank/APC family meshes. This changes nine visual bindings, with Build14 weapons, ammunition, armor, squads, spec pools, camo and saved offsets unchanged. These are explicit related-family stand-ins, not newly acquired exact meshes. Native validation remains pending.**

## Historical Build14 implementation

# PLA TEST Build 14

**This complete PLA draft imports all 90 named squad-designer rows and gives all 160 equipment cards isolated weapon/ammunition definitions with custom HUD artwork. Equipment remains assigned across the five PLA branches, each of the six named gunships retains a Recon card, and all 28 original infantry rigging fixtures stay in Test. Native Arsenal, deck and combat validation remains pending.**

- Infantry names, sizes, Recon flags, selected rifles, extra weapon counts, fixed munitions and design notes follow the saved live sheet rows 8–97. The 18 earlier combat drafts are hidden and their data retained to avoid duplicate playable designs. The 15 named Test concepts remain in Test alongside the 28 rigging fixtures.
- Use installed PLA bodies and saved arm/hand fit. Airborne, Motorized and conscripts use desert uniforms; Ground Force and Marines/SF use green. Armor uses the corresponding native regular/shock/elite tier with five HP per soldier. Missing handheld meshes keep their documented native analog; no missing model is described as installed.
- Ground and rotorcraft get explicit fixed armament drafts. Aircraft have PLA labels and appropriate native analog kits; transports/surveillance platforms remain unarmed, legacy fighters do not inherit modern missile kits, and ground-attack drones carry guided bombs/missiles. This is a design baseline, not final Chinese performance or a full set of weapon upgrade options.
- HJ-10/AFT-10 use the M6 Linebacker chassis and exact vanilla Hellfire ammunition behavior: 36-degree loft, terminal-guidance seeker, reacquisition, eight ready/eight total missiles and no unrelated Bradley cannon. The installed PLA AFT-10 mesh remains the visible model. Code/data support the guidance description; firing over buildings is not yet proven in a game.
- Weapon and ammunition HUD icons are embedded transparent silhouettes. Stocks preserve the native logical-shot/HUD-multiplier relationship; any rounding is listed in the armament receipt. Type 96 total load is sourced at 42 rounds; ammunition mixes and unsourced capacities remain explicit drafts.
- Utility transports are shared and capacity-checked against the exact squad sizes. The basic truck is available to oversized squads. Gunships and unmanned aircraft carry no infantry. No squad is shrunk to fit a transport.
- Approved mesh/texture files, canopy finish, immediate stand-in hiding, rigging comparisons, weapon/body offsets, music and preferences are retained. Available PLA meshes are reused for related variants; pending assets use the closest native stand-in.
- RU/US selectors and spec controls stay visible with their cards hidden. No naval unit or White Emperor is playable. YJ-18 remains a ground cruise-missile launcher. Public LIVE dev.45 remains locked.

## Evidence and editable drafts

The package includes `pla-vehicle-armament.json`, `pla-infantry-designer.json` and `pla-spec-assignments.json`, with source IDs, stocks, model bindings, camo, troop counts and limits. The Google Sheet remains editable. A table/package check does not prove animations, custom sprites, guidance, reload timing or combat behavior in the native game.

## Historical Build 13 context

# PLA TEST Build 13

**All equipment now belongs to the five main PLA specs. Test contains only the 28 infantry appearance/rigging fixtures. The six named gunships each have a separate recon card. Basic ground and helicopter transports are shared where appropriate. This is an editable draft; native Arsenal, deck creation and combat validation remain pending.**

- Airforce / Airborne gets the air and airborne equipment; Armored gets heavy tracked systems; Rocket Force / Conscripts gets missile/rocket support and legacy/reserve equipment; Marines / SF gets amphibious ground equipment and SF; Motorized gets mobile wheeled systems. Existing deliberate support attachments are retained.
- All six recon gunships inherit their parent's weapons, sensor baseline and provisional cost. Their CategoryType is Recon; they are real separate unit definitions, ready for later optic/loadout/price edits. The previous six planned rows are promoted to these IDs.
- Z-20 utility lift serves all five specs. Z-8L serves Airforce and Marines; Z-9 basic lift serves the light/mobile branches. Basic APCs and IFVs are reused without creating duplicate unit definitions. Every infantry transport link is checked against its actual squad size.
- Gunships are excluded from troop transport choices. The Z-9WA, Z-19 and Z-21 donor troop capacities are cleared; no weapon, armor, sensor or price buffs are added.
- Infantry rigging fixtures remain Test-only, including all approved outfit comparisons and the two extra model-list infantry fixtures. The 18 branch infantry roles remain in their assigned specs.
- Approved geometry, textures, canopies, loading behavior, body/weapon offsets, music and preferences are retained. Russia/USA selector/spec controls remain visible with their unit cards hidden. Public LIVE dev.45 stays locked.
- The equipment design sheet remains the editing surface; human design fields must be preserved during roster synchronization.

- No ships, submarines or UUVs are playable. White Emperor is excluded. YJ-18 is a ground cruise-launcher draft in Rocket Force, using native Iskander-K appearance and two cruise missiles until its final design is supplied.

## Historical Build 12 context

# PLA TEST Build 12

**Named stand-ins cover all 157 Model links entries that identify a model or reuse choice. This adds 102 units, reuses existing cards where appropriate, moves SF into Marines / SF, and restores RU/US selectors and specs for UI testing with their unit cards hidden. It retains the combined Build 11 arm repair and aircraft loading/canopy changes. Native filtering still needs validation after the fix.**

## Current changes

- Airforce / Airborne keeps the airborne line squad. SF Assault, SF Recon and QTS-11 Digital Scouts are Marines / SF only. All outfit comparisons remain in Test.
- Model availability and ownership are separate from card creation. Missing/pending model files use named donor stand-ins, with no claim of final Chinese weapons or statistics. New unassigned designs are parked in Test.
- One actual platform can serve several specs or catalogue source rows. Alternate paint/seller packages do not automatically produce duplicate unit definitions. New role variants can be designed separately.
- SR-5 now uses the approved native HIMARS visual. HQ-17 retains native TOR. Approved body/weapon offsets, infantry geometry, canopy finish and immediate stand-in hiding remain intact.
- Russia and USA country/spec controls remain. Their unit DisplayInArmory flags are off. Keeping the native country groups avoids the single-country duplicate mask seen in Build 11; native behavior remains to be tested.
- PLA equipment designs is the canonical editable equipment sheet. PLA equipment by spec links to it and groups entries by spec and class. It contains 174 current/draft equipment records and six planned recon gunships. Infantry uses the separate squad designer; infantry already in the game is retained. Recon plans do not add speculative game units or weapon statistics.
- The public LIVE dev.45 launcher lock remains unchanged. No multiplayer test was performed.

## Earlier Build 11 context

**First PLA branch draft: five planned specializations, a Test pool, and 18 donor-based infantry roles in one complete pack. The arm fit is replaced to preserve forearm and hand thickness. Data and offline previews can be checked; native Arsenal, deck creation and combat remain unverified.**

## Changes in this pack

Build 11 combines the Build 9 branch/Test/infantry work with Build 10 immediate stand-in hiding. Loading failure still restores the original model.


- China is the only selectable nation in the test pack. Russia and USA cards/specs are hidden, while their donor data remains internally.
- Airforce / SF, Ground Force / Armored, Rocket Force / Conscripts, Naval / Marines and Motorized have separate primary/shared unit pools. Category budgets are provisional at 5,000 points per spec.
- Test contains 52 cards: unused or additional vehicle variants, all 25 infantry appearance variants and the seven-man weapon demonstration squad. This is a developer pool, not a balanced combat spec.
- Eighteen new infantry roles use the existing PLA bodies and QBZ-191, QBU-191, QTS-11 and QLU-11 where applicable. Heavy Chinese weapons use explicitly documented native stand-ins. Costs and behavior are provisional donor baselines.
- All 25 appearance variants receive the replacement arm fit. Forearm cross-sections use rotation plus length fitting; hands use a rigid rotation. Approved body and weapon offsets and woodland helmet clearance remain unchanged.
- Existing aircraft canopy repairs and reflections from pinned Build 8 are preserved. Existing vehicle combat statistics, textures, music and voices remain unchanged by this task.
- New transports are limited to the correct branches and sufficient infantry capacity.

## Testing and later integration

Use the complete numbered PLA pack, not historical PLA.infantry or PLA.48 prototypes. This candidate is not installed. Native country 4, deck creation and in-game animation need testing. No multiplayer test was performed.

Later, merge the source feature into LIVE with fresh IDs and without the PLA-only visibility rules. Four existing PLA unit IDs conflict with current LIVE definitions. Do not copy the PLA archive over LIVE or change the public dev.45 lock.

## Preserved project guide and earlier release notes

The following material is retained as historical context from the Build5 source. The current PLA-only candidate is described above.

## freedom-arrow

**Unreleased 0.6 development — ActualArrow features:** [build instructions and changes](releases/0.6/README.md) on `codex/0.6-development`. 0.5 stays on `codex/0.5-development` (accuracy, [changes](releases/0.5/README.md)); 0.4 stays on `codex/0.4-development`.

**Unreleased 0.4 development:** [build instructions and changes](releases/0.4/README.md) on `codex/0.4-development`. 0.3 stays on `codex/0.3-development`.

**Unreleased 0.3 development:** [build instructions and changes](releases/0.3/README.md). 0.2 stays on `codex/0.2-development`.

**0.2 development:** [build instructions, included changes and held work](releases/0.2/README.md). The dev.38 data candidate is built offline; recon and card splits remain incomplete, and in-game acceptance is pending. Its release build uses `releases/0.2/build.py`, not the generic channel package command. Lateralus's optics/stealth/noise cleanup is preserved.

**Prepared 0.1 candidate:** [download, scope and source](releases/0.1/README.md) · [Linux deployment](docs/releases/0.1-linux.md). This review branch keeps detection, stealth and concealment vanilla; revised live acceptance and multiplayer remain unverified.

Tools and data for a Broken Arrow gameplay mod. Gameplay changes live in JSON constants. A MelonLoader plugin inside the `.bamod` applies those constants when the game loads. Players install and launch the mod with [BAModManager](thirdparty-tools/BAModManager-main/README.md): the Mod Manager for development, and BAModLauncher for release.

The game is a Unity 6 IL2CPP title. The database is one `DataBaseCompiled` object inside `BrokenArrow_Data/data.unity3d`: 24 AES-256-CBC JSON tables. BAModLauncher is what players press. It installs MelonLoader and this modpack, starts the game with Anti-Cheat disabled, and **Play vanilla with no mods** removes MelonLoader's `version.dll`.

Do not play ranked or quick match while MelonLoader is installed.

### Layout

| Path | What it is |
| --- | --- |
| `pipeline/` | Extract, patch, inject, rebase, and pack a `.bamod` |
| `runtime/FreedomArrow/` | MelonLoader plugin that applies constants and formulas |
| `mod/constants/` | Stable gameplay changes to the 24 tables |
| `mod/manifest.json` | Game build the stable constants were last reconciled with |
| `mod/formulas/` | Stable injected formulas, one file per game method |
| `mod/testing/constants/` | Testing gameplay changes |
| `mod/testing/formulas/` | Testing injected formulas |
| `mod/testing/manifest.json` | Game build the testing constants were last reconciled with |
| `mod/modpack.json` | Modpack id, version, and GitHub repos for Stable and Testing |
| `config.template.YAML` | Committed config template |
| `thirdparty-tools/BAModManager-main/` | BAModManager and BAModLauncher source |
| `thirdparty-tools/` | Also vendors Bodkin, MelonLoader, Il2CppDumper, and ILSpy |
| `BrokenArrow_Data/` | Local game data. Gitignored |
| `cache/` | Vanilla snapshots and launcher backups. Gitignored |
| `dist/` | Patched bundles. Gitignored |

### Onboarding

You need Python 3.11 or newer, and a Broken Arrow install that contains `BrokenArrow.exe` and `BrokenArrow_Data/data.unity3d`. A copy of `BrokenArrow_Data` in the repo root is valid when `game_root` is the repo root.

From the repo root:

```text
python -m pip install -r pipeline/requirements.txt
copy config.template.YAML config.YAML
```

On Linux or macOS, `cp config.template.YAML config.YAML`.

Edit `config.YAML` and set `game_root` to the install directory. Quote the path. Forward slashes work on Windows and Linux. Examples are in the template. `config.YAML` is gitignored. Every pipeline command stops if it is missing.

Leave `write_game_bundle` false until you intend to copy a bundle over the game. `discover`, `decrypt`, `survey`, `il2cpp`, `apply`, and `package` never write inside `game_root`. `inject` writes `dist/`, not the game. `hangar` writes inside `game_root`, and only when that flag is true.

Build the plugin before packaging:

```text
dotnet build runtime/FreedomArrow/FreedomArrow.csproj -c Release
dotnet run --project runtime/FreedomArrow.Tests/FreedomArrow.Tests.csproj -c Release
```

The console checks load the real plugin and exercise registration, generated hook calls, and encrypted table preparation. They do not start Unity or prove native hooks or combat behavior. The plugin and console checks target .NET 6, matching the bundled MelonLoader host.

Run commands from the repo root so Python can import `pipeline`:

```text
python -m pipeline decrypt
python -m pipeline apply
python -m pipeline inject
python -m unittest pipeline.tests.test_pipeline pipeline.tests.test_package
```

`decrypt` reads the live database and writes `cache/vanilla/<build-id>/`. When an object has `MainBuildDatabase` and level 2, that object is the live database. Otherwise the one with the most units is used, and every candidate path id and unit count is printed. The first run hashes `data.unity3d` and extracts `globalgamemanagers.assets`. Later runs reuse that snapshot.

`inject` repacks the whole archive into `dist/<channel>/data.unity3d`. On a current game that is several gigabytes and takes a few minutes. It also writes `dist/<channel>/channel.json` with the vanilla build id the bundle was built from.

### How constants are written

This section is the authoring shape. The cost object is an example of that shape. It is not a catalogue of mechanics.

A constant file names the place the game or the plugin actually applies the change. A number is a new literal. A string names something that already exists: a field, a return value, a component, or an enum. Do not add a key the game or the hook does not have.

**Existing table data.** `mod/constants/<table>.json` is one of the 24 database tables. An empty object changes nothing. The example sets one field on one row:

```json
{
  "1": { "Cost": 40 }
}
```

A list of rows with an `Id` field is also accepted. The pipeline rejects an unknown file, a missing `Id`, a type change, and a foreign key that does not point at a row. Rows you do not mention stay as the original ciphertext, so an empty constants directory round-trips to the original object bytes.

**Serialized config edits are not implemented.** `mod/configs/<ClassName>.json` and `mod/testing/configs/<ClassName>.json` are reserved for a future ScriptableObject application path. Packaging rejects JSON files there. If JSON files are already installed under `UserData/FreedomArrow/configs`, plugin startup reports the unsupported input and leaves gameplay hooks uninstalled. Reading fields from `dump.cs` or decoding a config asset does not apply edits to that asset.

**Code at a method.** `mod/formulas/<Class>/<Method>.json` names a game method and the parameters its hook reads. The file has `method`, `change`, and `parameters`. `change` is `after`, `before`, `inside`, or `instead`. Only `after` is accepted today. The other three are rejected until a hook implements them.

This file shape is one `after` hook. No hook is registered until a class is added to `FormulaHost`.

```json
{
  "method": "Game.OtherClass.OtherMethod",
  "change": "after",
  "parameters": {
    "scale": 1
  }
}
```

`parameters` are the values for that hook. A new method is a new file plus a hook. `package` checks the envelope only.

Day-to-day and release are `package`, then BAModManager or BAModLauncher PLAY. The plugin applies whatever constants and formulas are in the package. **Play vanilla** stays the manager's button.

```text
python -m pipeline package --channel stable
python -m pipeline package --channel testing
```

`decrypt`, `apply`, and `rebase` are the offline checks. `apply` merges constants and checks links without touching the game. `inject` and `hangar` are diagnostics. `hangar` still requires `write_game_bundle`: it installs `dist/stable/data.unity3d`, launches the game, and restores the previous file when the process exits.

### BAModManager

Source is in [thirdparty-tools/BAModManager-main](thirdparty-tools/BAModManager-main/README.md). It builds two programs. The Mod Manager is for development. BAModLauncher is what players get. Both already have **PLAY** and **Play vanilla with no mods**. Stable and Testing on the launcher are two GitHub repos, each publishing a `.bamod`.

Build them from that directory with the .NET 8 SDK:

```text
build.bat
build_launcher.bat owner/freedom-arrow owner/freedom-arrow-testing
```

`build.bat` writes the Mod Manager zip. `build_launcher.bat` with two `owner/repo` arguments writes a launcher whose Stable and Testing buttons follow those repos. Fill `repo` and `testingRepo` in [mod/modpack.json](mod/modpack.json) with the same names before you publish.

Pack the mod for either channel:

```text
python -m pipeline package --channel stable
python -m pipeline package --channel testing
```

Each command writes `dist/<channel>/FreedomArrow-<version>.bamod`. The zip contains `mod.json` (`"type": "modpack"`), `Mods/FreedomArrow.dll`, the non-empty constant files under `UserData/FreedomArrow/constants/`, and formula files under `UserData/FreedomArrow/formulas/`. BAModManager installs those paths. The patched `data.unity3d` is not inside the package: it is several gigabytes, and the manager does not replace `BrokenArrow_Data`. When `mod/modpack.json` has repos, packaging also writes `dist/launcher.json`:

```json
{ "modpack": "owner/freedom-arrow", "testing": "owner/freedom-arrow-testing" }
```

Put that file next to `BAModLauncher.exe` if you are using the generic launcher instead of `build_launcher.bat`. Publish each `.bamod` as a GitHub release asset. The tag must match `version` in `mod/modpack.json` (`v0.1.0` for version `0.1.0`). PLAY downloads a newer release when the tag is newer than the installed modpack. Keep `id` unchanged across versions.

Drag the `.bamod` onto BAModManager to confirm it installs before you publish it. PLAY in either program starts the game with Anti-Cheat disabled. **Play vanilla with no mods** removes `version.dll` and starts the normal game.

### After a game update

Steam replacing `data.unity3d` is expected. Keep the previous vanilla snapshot in `cache/` until the new one is reconciled.

```text
python -m pipeline update --channel stable
python -m pipeline update --channel testing
```

`update` decrypts the new bundle, rebases that channel's constants, applies them, and injects. A constant is kept when the game did not change that field. When both sides changed it, the row disappeared, or the field's type changed, rebase writes `cache/rebase-conflicts-<channel>.json` and leaves the manifest on the old build. Read the report, edit the constants, then either run `rebase` again or, after you have decided to keep your values, run:

```text
python -m pipeline rebase --channel stable --accept
```

`--accept` records the new build id and leaves the constants in place.

### Commands

| Command | What it does |
| --- | --- |
| `discover` | Find `DataBaseCompiled` by name and record path id, script, and build id |
| `decrypt` | Write the 24 JSON tables and their original ciphertext |
| `survey` | Catalog cover, forest, stealth, and suppression values into `cache/survey/<build-id>/report.json`. Reads the bundle only |
| `il2cpp` | Dump `GameAssembly.dll` from `game_root` and write cover-config fields and values to `cache/il2cpp/<build-id>/configs.json` |
| `apply --channel` | Merge that channel's constants onto the vanilla snapshot |
| `inject --channel` | Repack `dist/<channel>/data.unity3d` and `channel.json` |
| `package --channel` | Write `dist/<channel>/FreedomArrow-<version>.bamod`, including `Mods/FreedomArrow.dll` |
| `rebase --channel` | Three-way merge of the previous snapshot, the new snapshot, and the constants |
| `update --channel` | Decrypt, rebase, apply, and inject |
| `hangar` | Install the stable bundle, launch, and restore on exit |

`python -m pipeline <command> --help` prints the flags. `--config` selects a file other than `config.YAML`.

### Third-party tools

`thirdparty-tools/BodkinToolkit` is an earlier editor whose write path hardcodes a PathID and drops JSON fields the schema does not name. Do not round-trip the game database through its YAML. The AES field order in `pipeline/tables.py` matches Bodkin's list; the lookup and the authoring format do not.

MelonLoader, Il2CppDumper, and ILSpy are vendored beside BAModManager. The manager downloads MelonLoader when a player presses PLAY. Il2CppDumper and ILSpy are for later UI and behaviour work.

### License

Apache License 2.0. See [LICENSE](LICENSE).

## Document change log

- 2026-11-04 16:54:02 PST (America/Los_Angeles) — Added an unreleased0.2 development/build pointer and explicit recon/card/runtime limits; preserved the0.1 candidate and upstream cleanup.
- 2026-11-04 17:30:00 PST (America/Los_Angeles) — Updated the development pointer to dev.4.
- 2026-11-04 17:54:19 PST (America/Los_Angeles) — Updated the development pointer to dev.5.
- 2026-11-04 18:01:47 PST (America/Los_Angeles) — Updated the development pointer to dev.6.
- 2026-11-04 18:07:58 PST (America/Los_Angeles) — Updated the development pointer to dev.7.
- 2026-11-04 18:11:00 PST (America/Los_Angeles) — Updated the development pointer to dev.8.
- 2026-11-04 18:26:32 PST (America/Los_Angeles) — Updated the development pointer to dev.9.
- 2026-11-04 18:37:44 PST (America/Los_Angeles) — Updated the development pointer to dev.10.
- 2026-11-04 19:05:03 PST (America/Los_Angeles) — Updated the development pointer to dev.11.
- 2026-11-04 19:11:24 PST (America/Los_Angeles) — Updated the development pointer to dev.12.
- 2026-11-04 19:24:04 PST (America/Los_Angeles) — Updated the development pointer to dev.14.
- 2026-11-04 19:37:31 PST (America/Los_Angeles) — Updated the development pointer to dev.16.
- 2026-11-04 19:42:51 PST (America/Los_Angeles) — Updated the development pointer to dev.17.
- 2026-11-05 14:52:23 PST (America/Los_Angeles) — Added the 0.4 development pointer; 0.3 stays on its branch.
- 2026-11-06 14:40 PST (America/Los_Angeles) — Added the 0.5 development pointer (accuracy); 0.4 stays on its branch.
- 2026-11-07 12:43 PST (America/Los_Angeles) — Added the 0.6 development pointer (ActualArrow features); 0.5 stays on its branch.

- 2026-11-10 23:19:11 PST (America/Los_Angeles) — Created the PLA-only five-branch draft instructions,prototype limits and later merge boundary.

- 2026-11-10 23:36:02 PST (America/Los_Angeles) — Preserved earlier guide content and every prior document-log entry under the current Build6 summary.

- 2026-11-11 00:04:13 PST (America/Los_Angeles) — Prepared Build 9 with five branches plus Test, 18 infantry roles and replacement arm fit; preserved Build 8 cockpit work. Native checks remain pending.

- 2026-11-11 00:21:03 PST (America/Los_Angeles) — Combined Build 9 specs and arm repair with Build 10 immediate hiding, retaining failure restoration and canopy assets. Native checks remain pending.

- 2026-11-11 00:59:21 PST (America/Los_Angeles) — Added Build 12 catalogue stand-ins, Marines/SF assignment, RU/US UI controls and linked unit-design sheets. Native filter fix awaiting game validation.

- 2026-11-11 01:12:58 PST (America/Los_Angeles) — Restricted the design tabs to equipment; retained existing infantry in the complete game pack.

- 2026-11-11 01:46:18 PST (America/Los_Angeles) — Assigned equipment to the five specs, added separate recon gunships and shared lift, retained Test-only rigging fixtures.

- 2026-11-11 01:50:37 PST (America/Los_Angeles) — Applied Osama’s no-naval/no-White-Emperor direction and the YJ-18 ground cruise-launcher role.

- 2026-11-11 02:55:11 PST (America/Los_Angeles) — Build 14: imported 90 designer squads, explicit equipment armament and custom weapon/ammo HUD icons, matching infantry camo/armor, capacity-checked transport and vanilla Linebacker guidance for HJ-10. Native validation pending.

- 2026-11-11 03:17:32 PST (America/Los_Angeles) — Build15: corrected nine available PLA family-model bindings; Build14 gameplay tables remain unchanged. Native validation pending.

- 2026-11-11 10:45:47 PST (America/Los_Angeles) — Build16: replaced weapon-class HUD symbols with physical-family weapon silhouettes on equipment and designer infantry. Unit art and gameplay retained. Native visual verification pending.
- 2026-11-11 10:58:01 PST (America/Los_Angeles) — Build17: selected-spec shared-card grouping and normal/photo reset support; retains Build16 weapon HUD art. Native UI verification pending.

- 2026-11-11 11:43:40 PST (America/Los_Angeles) — Replaced rejected weapon sketches, added normal/outline contours, documented native stand-ins and retained the Build17 UI correction.

- 2026-11-11 12:11:09 PST (America/Los_Angeles) — Added researched infantry identity/patch adaptations and corrected custom weapon facing and filled-outline style; preserved all gameplay and approved model bindings.

- 2026-11-11 12:30:17 PST (America/Los_Angeles) — Replaced support/specialty branch badges with weapon/equipment icons and removed SF wreaths while enlarging central emblems; all other game data retained.

- 2026-11-11 12:55:47 PST (America/Los_Angeles) — Build21: refined SF contours and transparent overlap gaps, restored short English labels, and assigned17 mixed rifle/security cards patch art while retaining dedicated weapon-team icons and all gameplay data.

- 2026-11-11 13:02:37 PST (America/Los_Angeles) — Build22 feedback: fierce leopard, coiled sea dragon, visible sword, detailed birds; larger star-free Airborne/Rocket patch motifs; Sky Hunters/Mountain Hunters labels; approved Thunder Gods/Whistling Arrows retained.

- 2026-11-11 13:09:29 PST (America/Los_Angeles) — Build23 merges the verified installed FA Music1.5.0 player with unchanged Build22 art/game data to prevent a full-package switch from reverting the native music selector.

- 2026-11-11 17:15:13 PST (America/Los_Angeles) — Integrated approved unit art and branch spec badges into Build24; retained Build23 gameplay/model/music data.
- 2026-11-11 18:58:42 PST (America/Los_Angeles) — Build25 changes star/八一 color contrast only; source geometry and all other icons retained.
- 2026-11-11 20:22:37 PST (America/Los_Angeles) — Corrected runtime build identity and added compiled-attribute regression check; Build25 artwork retained.
- 2026-11-11 21:12:34 PST (America/Los_Angeles) — Source-photo motif copies and clean-white unit icon export; all original masters preserved.
- 2026-11-11 22:33:26 PST (America/Los_Angeles) — Three unit emblems,16weapon HUD sprites and country-control order corrected.
- 2026-11-11 22:48:48 PST (America/Los_Angeles) — Added approved maintained-stream and isolated-batch navigation; preserved existing history and gameplay.
- 2026-11-11 23:28:12 PST (America/Los_Angeles) — Detailed reference HUD and conscript capability rule.

- 2026-11-11 23:52:08 PST (America/Los_Angeles) — Added approved branch/class infantry appearance presets for Build30.

- 2026-11-12 00:30:48 PST (America/Los_Angeles) — Build31 equipment/spec roster, transport coverage and weapon drafts; preserved Build30 infantry/art.

- 2026-11-12 00:44:41 PST (America/Los_Angeles) — Added a DF-31-specific original warning draft through the existing ballistic alert path and audio controls; native launch/mix and nuclear effect remain pending.

- 2026-11-12 00:52:01 PST (America/Los_Angeles) — Added formatting-aware sheet import and QLG10A reference icon.

- 2026-11-12 01:01:43 PST (America/Los_Angeles) — Build33 combines one-spec deck correction and latest PLAN/Rocket moves with the full Build32 infantry pass; Mi-8 Cargo is the only shared card.

- 2026-11-12 01:36:00 PST (America/Los_Angeles) — Build34 adds the Shaanxi HMV3 supply truck from the HEMTT for Armored, Rocket Force and Motorized; second shared exception after Mi-8 Cargo.

- 2026-11-12 01:32:53 PST (America/Los_Angeles) — Build35 applies the latest infantry sheet sizes, kit and removal over Build34.

- 2026-11-12 01:38:31 PST (America/Los_Angeles) — Build36: DF-31 copies the nuclear Kinzhal warhead; four drone helicopters without models removed. Correction: the Build34 entry above says 01:36:00; the actual Build34 edit was about 01:31 PST.

- 2026-11-12 01:43:45 PST (America/Los_Angeles) — Build37: J-10A repainted on its own texture (neutral dark white-grey); the salmon/tan colorScale tint is removed.

- 2026-11-12 01:57:13 PST (America/Los_Angeles) — Build38: runtime DLL rebuilt with compiled version 38; Builds34-37 shipped the Build33 DLL and failed the start-up identity check. Added a compiled-version check to verify_roster_revision.py and the package script.

- 2026-11-12 02:14:22 PST (America/Los_Angeles) — Build39: QN-202 anti-infantry missile (shared with CTL-181), Motorized GAM-102LR Team, QBU-88 conscript marksmen, LG test squads removed, two new weapon cards.

- 2026-11-12 02:18:23 PST (America/Los_Angeles) — Build40: removed the invalid BaseSquadSize field from 73 new infantry Units rows (Builds33-39 loaded vanilla); verify_roster_revision.py now enforces the runtime new-row field rule.

- 2026-11-12 03:24:21 PST (America/Los_Angeles) — Build41: Osama's 12 Nov roster batch (removals, spec moves, designation names, SF helicopter copies, Y-8 Harvest Hawk, QBZ-95 Rocket Force rifles, Godswords, tabs, recon helicopters without missiles, QBU-191 suppressed, QJY-201 card, J-11B J-16 model, J-50 probe stowed, Mi-8 Cargo to Helicopters).

- 2026-11-12 03:41:02 PST (America/Los_Angeles) — Build42: Air Force Z-10K + Z-10, Z-10 recon cards removed, QLB-06 for Assault Raiders, PF-98 weapon card, spec badges without the Bayi star (small star on Navy).

- 2026-11-12 04:03:00 PST (America/Los_Angeles) — Build43: MANPAD ladder, Tank Hunters DZT-98, removals and moves, ZTQ-15 Recon and autoloader, HJ-10 name, Lynx ATV loadouts, Z-19 names, J-35/J-31 model swap (low-vis J-31).

- 2026-11-12 04:24:27 PST (America/Los_Angeles) — Build44: J-11BS/BHG/D with lighter skins, removals/renames, Z-8L shared, Z-20 family with loadouts, CM-501G/CM-502, TY-90 Sidewinder.

- 2026-11-12 04:44:44 PST (America/Los_Angeles) — Build45: squad edits and renames, removals, tripod PF-98 with DZD98A, GAM-102LR Spike icon, FH-97A as F-35B with 4 AMRAAM, PLAN ZSD-89, PLARF Infantry gear icon, Godswords PF-89.

- 2026-11-12 04:48:24 PST (America/Los_Angeles) — Build46: Shaanxi HMV3 HEMTT mounts/options, mixed and Cargo versions in every spec.

- 2026-11-12 05:13:37 PST (America/Los_Angeles) — Build47: CMO-derived aircraft loadouts, generation chassis and prices for every armed PLA aircraft (see pla-air-loadouts.json).

- 2026-11-12 05:19:39 PST (America/Los_Angeles) — Build48: tank armour/penetration/ammo by generation, ATGM 10.5 standard, vehicle prices.

- 2026-11-12 05:23:55 PST (America/Los_Angeles) — Build49: artillery at vanilla scale, infantry weapon fixes, nearest-vanilla squad prices.

- 2026-11-12 05:34:11 PST (America/Los_Angeles) — Build50: Osama 05:24/05:31 requests (Airborne, Godswords, moves, PHL-16 loadouts, SR-5 HIMARS, HMV3 Cargo PLS, weapon order).

- 2026-11-12 05:37:10 PST (America/Los_Angeles) — Build51: ZTZ-99 = T-90M, ZTZ-99A KE 800, Z-20 DAP menus, slow cheap HJ-73D, recon helicopters rockets only.

- 2026-11-12 05:41:30 PST (America/Los_Angeles) — Build52: extra aircraft loadouts.

- 2026-11-12 11:02:32 PST (America/Los_Angeles) — Build53: AKD-10 renamed HJ-10; Z-20 menu labels in Chinese weapon names.

- 2026-11-12 11:13:05 PST (America/Los_Angeles) — Build54: LD-8A and PL-16 stealth loadouts, J-16 heavy bomb load.

- 2026-11-12 11:16:34 PST (America/Los_Angeles) — Build55: PL-15/PL-16 = AMRAAM +500, PL-17 = JATM.

- 2026-11-12 11:21:16 PST (America/Los_Angeles) — Build56: null pylon slots set to 0; China loads again.

- 2026-11-12 11:35:47 PST (America/Los_Angeles) — Build57: all Airborne squads wear SF goggles down desert; "Mechanized" removed from PLAGF names.
