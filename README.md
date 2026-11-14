# Freedom Arrow 0.8.0-dev.101

- J-36 Heavy CAP: 4x PL-17, 4x PL-16 and 4x PL-21.
- Shaanxi HMV3 Cargo: 15000 supply in both armory versions (was 9000, or 4500 armored).
- Helicopter glass copies a similar base-game helicopter: Z-20 family UH-60M, Z-19 AH-1Z, Z-10 AH-64E, Z-9 UH-1Y, Z-11WB OH-58 (FAModels 0.3.24).
- CSK-131: side panels back (solid body), dark glossy windows. CSK-181: dark glossy windows instead of the wavy canopy glass.
- ZTZ-96A and ZTZ-96B show the right models again; ZTZ-96B in green digital camo.
- Z-19: no cargo. PLAN SOF Z-19 is now Z-19G. ZBD-20 Recon removed. DF-15 and YJ-18 models 20% smaller.
- PLAN SOF spec points: aircraft 1250, helicopters 1000. PLARF is now named PLARF Rocket Force/Reservist.
- Infantry: backpacks on all non-conscript PLA soldiers (conscripts and deck crew excepted).
- Type 59D and ZTZ-59D1: textures in the ZTZ-99A style (digital woodland, ZTZ-99A tracks).
- Mengshi Recon: now on the CSK-131 (Mengshi) model in a darker finish, with closed doors and windows.
- ZBD-05: loadouts with the HJ-8E ATGM (+10, default) or without it (35 pts).
- Motorized AT Troopers: 4 PF-89 launchers. CTL-181 NLOS: 2 cards. Blood Wolves: CH-901 1400 m range, 75 points.
- Everything else as 0.8.0-dev.100.

## Historical 0.8.0-dev.100

- ZFB-05 is a transport for Motorized infantry (10 seats, like the base-game BPM-97 it is built on), not its own card.
- Z-19: stealth 1.75.
- J-10C and J-10S: ECM and flares (same as the J-10CE).
- Y-8: faces forward, and the flaps and elevators lie flat again.
- KQ-200: propellers no longer look mid-spin.
- Everything else as 0.8.0-dev.99.

## Historical 0.8.0-dev.99

- Transports (IFVs, APCs, trucks, ATV) no longer have their own vehicle card; buy them with the infantry, as in the base game. ZBD-20 is now a transport like ZBD-04A. Helicopters keep their cards.
- Removed: CSK-131 Mengshi; the PLAN SOF ZSD-89; CSK-131 4x4 as a PLAAF transport; CSK-181 as a PLAN SOF transport.
- Cards: DF-17 1, YJ-18 2, HQ-9C/HQ-9B 2, ZTZ-99A 2, ZTZ-99 4, J-5/J-6W/J-7/J-8D 4, Conscripts/HJ-73D Team/Infantry/Mech. Rifles 8, PLAN SOF SF infantry 2 and SF recon 3.
- Prices: Forward Observers 25, ZTQ-15 150, ZTQ-15 Recon 165, PLZ-70 95, PLZ-85 90, PLZ-07B 130, MD-22 +100.
- Sharp Blades is now Sharp Swords.
- PLZ-85 dispersion 300 m x 240 m; PLZ-89 range 4300 m.
- 20 smoke rounds on PLL-05, PLL-09, PLZ-70 and PLZ-07B; PLZ-07B 12 laser-guided rounds.
- Recon helicopters with loadouts get an Empty loadout (0 pts). FK-2000 model 10% smaller.
- ZTL-191 uses the desert camo too.
- PTL-02 50, VT-5 240. ZSD-89A is no longer a Motorized transport. Line Infantry renamed Moto. Riflemen; Moto. Riflemen, Light Riflemen and Marines 6 cards. Recon tanks (ZTQ-15, VT-5, ZTL-191 Recon) 2 cards.
- Everything else as 0.8.0-dev.98.

## Historical 0.8.0-dev.98

- Type 59D and ZTZ-59D1: the 59D model is back, with dark olive colours instead of the pale ones.
- HQ-9, HQ-9A, HQ-9B: darker paint, less metal shine, real clear glass in the cab windows.
- HQ-7B and HQ-7: clear glass in the windows (they were cut out).
- ZTL-191 Recon: desert camo.
- PHL-03: darker, especially the tyres. Mengshi Recon: darker and more metallic.
- Ambush Team 40 points. YJ-18 moved to PLAN SOF. PHL-191 Cruise moved to PLARF.
- Everything else as 0.8.0-dev.97.

## Historical 0.8.0-dev.97

- FAModels 0.3.23: jets that use the vanilla F-16 canopy no longer turn frosted when the F-16 glass is not loaded yet; the stand-in glass is clear and becomes the F-16 glass once it loads.
- Z-9 (transport): no weapons on the model. Z-9WA and Z-9WA Recon: seller model with the weapons.
- PHL-191 Cruise: loose tube door removed, launcher behind the cab.
- CSK-131: no longer glows white. CSK-181: camo without the scraped-metal shading.
- Everything else as 0.8.0-dev.96.

## Historical 0.8.0-dev.96

- Aircraft glass restored to how it was before the glass passes (F-14, Su-47, Su-57D, YF-23 had been made more frosted).
- Helicopter and ground-vehicle clear glass at the aircraft value (opacity 0.025).
- PHL-191 Cruise: launcher moved back so it no longer clips into the cab.
- Everything else as 0.8.0-dev.95.

## Historical 0.8.0-dev.95

- Spec points: PLAAF Recon 500 / Air 1500; PLAGF Armored Air 0 / Vehicles 2000; PLARF Recon 500 / Support 2000; PLAN SOF Support 500 / Air 1500 / Vehicles 500 / Helicopters 750; PLAGF Motorized Infantry 1250 / Helicopters 500 / Recon 750 / Air 750.
- Everything else as 0.8.0-dev.94.

## Historical 0.8.0-dev.94

- WZ-550: seller model rebuilt in the seller's dark olive (was pale with brown hatches and a loose missile).
- PHL-191 AR3 model fixed (travel position, no smoke plume or flying missile, woodland digital, clear windows) and used by a new PHL-191 Cruise card in Motorized (Ballistic stats and loadouts until the cruise loadout is set).
- Everything else as 0.8.0-dev.93.

## Historical 0.8.0-dev.93

- Armory vs multiplayer audit (tools/pla-specs/audit_mp_equipment.py, now run on every build):
  - ZBD-251: its laser designator never loaded (the game loads only a unit's first default ability). Smoke, resupply and laser are now one ability.
  - ZBD-04A, ZBD-20 and their Recon cards: two duplicate smoke abilities removed (nothing lost).
  - HQ-7B: duplicate radar removed; it keeps the moving radar that already loaded.
  - F-15EX: its ECM loadouts now have the matching ability link (ECM 40%), as vanilla requires.
- Everything else as 0.8.0-dev.92.

## Historical 0.8.0-dev.92

- Clear glass: opacity 0.3 -> 0.1 (it looked frosted white).
- HQ-16: Osama's seller model. VT-5 Recon: seller desert camo. HQ-6A model 75%.
- CSK-131: the 4x4 seller model (card renamed from "CSK-181 4x4"; CSK-131 Mengshi too). CSK-181 stays the 6x6.
- Everything else as 0.8.0-dev.91.

## Historical 0.8.0-dev.91

- ZTZ-59, ZTZ-59D, ZTZ-59D1: stand-in turret models as the vanilla T-62M (the gun mount had the Toros Rapira turret model), so the model can show.
- ZBD-04 (non-A) removed.
- PTZ-89: painted-metal material and model 90%.
- J-7 and J-8D: no afterburner (J-5 and J-6W had none).
- Everything else as 0.8.0-dev.90.

## Historical 0.8.0-dev.90

- HQ-7B: Osama's seller HQ-7 model.
- ZBD-86 removed from PLAAF. ZBD-86 Recon: no ATGM by default (15 points), HJ-73 Malyutka option +10.
- Z-20, Z-20J, Z-20KA, Z-20T: laser designation.
- CSK-181: the 6x6 stays on CSK-181 Transport; new CSK-181 4x4 card wherever the 6x6 is (cards and squad transports). 4x4 paint fixed.
- Mengshi Recon model 75%.
- Everything else as 0.8.0-dev.89.

## Historical 0.8.0-dev.89

- HQ-9C, HQ-9B, HQ-9A: Osama's new seller model (HQ-22 pack).
- Mengshi Recon: much darker paint.
- ZTZ-99: both tracks back (dev.85 position fix had moved both to one side).
- HJ-16 on ZBD-251 uses the vehicle Spike icon, as on ZBD-20 and ZBL-191.
- Everything else as 0.8.0-dev.88.

## Historical 0.8.0-dev.88

- FireSnake: FS-70A and new FS-90 laser-guided rockets (rocket-pod-with-laser icon). Recon gunships (Z-19 Recon, Z-21 Recon) carry FireSnake 70/90 loadouts; higher-end Z-19, Z-10, Z-10K and Z-21 loadouts swap basic rockets for FireSnakes.
- ZBL-191, ZBD-20 and ZBD-20 Recon: semi-active HJ-16 by default, option HJ-16 IIR (fire and forget) +40.
- Abrams X: jammer removed.
- Base ZTZ-59 in PLARF Rocket/Reservist (seller ZTZ-59 model, 40 points).
- Everything else as 0.8.0-dev.87.

## Historical 0.8.0-dev.87

- ZTQ-15 Recon: seller desert digital camo.
- ZTZ-100: front KE 700 (front HEAT 1200 unchanged), side HEAT 700, Abrams X jammer.
- ZSL-92 models 90%. ZTL-191 and ZTL-191 Recon reload 4-5 s.
- Lasers on Z-19, Z-19 Recon, Z-9WA Recon, Z-11WB and Z-20S (Z-10/Z-21 already had them).
- New Mengshi Recon (CSK-131 stats, Very Good optics, 50 points) in PLAAF, PLAN Navy/SOF and PLAGF Motorized.
- Everything else as 0.8.0-dev.86.

## Historical 0.8.0-dev.86

- ZTZ-85-II: T-80BV stat copy (armour, mobility, optics, smoke, 2A46M-1 with AP/HE/HEAT, PKT, Kord, 85 points).
- VT-5 and VT-5 Recon: front HEAT armour 1000 (was 700). ZTL-11 moved to Motorized.
- PLAN Navy/SOF ZBD-86 and ZBD-86 Recon removed; ZBD-05 uses the ZBD-86 model. QN-506 model 80%.
- Everything else as 0.8.0-dev.85.

## Historical 0.8.0-dev.85

- J-20, J-20S: stealth 2 (as J-31/J-35). ZTD-05 removed.
- HJ-10: 1600 m. QN-506: QN-502 is an HJ-10 copy at 1600 m with NLOS fire, Recon category, laser designator, 2000 m optics.
- ZBD-20 and ZBD-20 Recon: 8 HJ-16 (long-range Spike copy, 1600 m, top attack, semi-active) replace the precision missiles.
- Models: J-20S and Z-19 glass, armed Z-20KA/Z-20T, PGZ-95 guns, ZBD-20 gun, ZTZ-99 track, VT-5 MG; PGZ-95 and ZTZ-99A 90%, ZBD-251 85%; desert ZSD-89A fixed.
- Helicopter and ground-vehicle windows use clear glass (the copied F-16 glass looked wavy); jets keep it.
- Everything else as 0.8.0-dev.84.

## Historical 0.8.0-dev.84

- ZBD-20: purchased VN-17 model (woodland digital). ZBD-20 Recon and ZBD-04A Recon: seller desert digital.
- Marine HJ-8H Team (PLAN Navy/SOF): HJ-8H launcher and missile copied from the Kornet-M, Kornet icon, 70 points.
- Names: HQ-12 (was HQ-12 / KS-1), PCL-181 (was PCL-181 / SH-15).
- Everything else as 0.8.0-dev.83.

## Historical 0.8.0-dev.83

- New purchased models, seller paint, static: ZTZ-99, ZTZ-59A (on ZTZ-59D and ZTZ-59D1), PGZ-95, VT-5 and VT-5 Recon, PLZ-07 and PLZ-07B, Z-9, all Z-19 cards, Z-20 (navy grey for PLAN SOF and PLAAF, green for PLAGF), ZBD-86 (also on ZBD-03), the 4x4 CSK-181 on the CSK-181 Transport.
- New unit: ZTZ-85-II in PLARF Rocket/Reservist (ZTZ-85-III stats).
- PLZ-83 model 75%; PHL-191 Ballistic model 90% with vanilla window glass.
- Needs the complete package or the new assets version.
- Everything else as 0.8.0-dev.82.

## Historical 0.8.0-dev.82

- PGL-625: Stryker armour profile (HEAT and KE 60 front, 40 sides, 30 rear, 20 top; 12 HP). Was the ZBL-191 profile (HEAT 700).
- FAModels 0.3.22: when the vanilla glass (F-16 canopy) is not loaded, for example in the scenario editor, a model now uses clear glass instead of being refused. Before, the FK-2000, DF-15/17/21/31A, HQ-12 and the J-5 to J-16 showed their stand-ins in those scenes.
- CSK-181: windows use the vanilla glass.
- ZSL-92: the autocannon version is now the ZSL-92; the 12.7 mm MG version is removed (both carried the same squads).
- Everything else as 0.8.0-dev.81.

## Historical 0.8.0-dev.81

- CSK-181: model fixed. The seller file's tread lugs (all six tyres and the spare) imported one wheel radius too high, so the tyres were smooth, the lugs floated over the fenders and the spare stuck up over the roof. Each lug ring now sits on its tyre. The side and rear windows are clear glass (were plain white-grey).
- ZTZ-100: gun range back to 1400 m (dev.78 had 2000 m). The dev.78 penetration (APFSDS 550/525) stays.
- Everything else as 0.8.0-dev.80.

## Historical 0.8.0-dev.80

- ZTL-11 and AFT-10: Lateralus's purchased models replace the stand-ins (seller woodland digital, static). The HJ-10 uses the new AFT-10 model.
- ZSD-89A: the PLAAF card uses the seller's desert paint; the other three cards stay woodland.
- Needs the complete package or Assets 0.2.7 (new model files).
- Everything else as 0.8.0-dev.79.

## Historical 0.8.0-dev.79

- J-36: 100 points cheaper (unit cost 315 -> 215; loadout prices unchanged, so Heavy CAP is 470 in total).
- Everything else as 0.8.0-dev.78.

## Historical 0.8.0-dev.78

- ZTL-191, VT-5, ZTQ-15 (and Recon cards): 105 mm APFSDS penetration 525 close, 475 at range (was 550/500).
- ZTZ-100: 125 mm APFSDS penetration 550 close, 525 at range (was 525/500); gun range 2000 m (was 1400 m) for APFSDS, HE and HEAT. The GP125 missile stays 1800 m.
- Everything else as 0.8.0-dev.77.

## Historical 0.8.0-dev.77

- ZTQ-15, ZTQ-15 Recon, VT-5, VT-5 Recon: 105 mm gun reload 4 s (was 4-5 s).
- ZSD-63C removed (its card and its 7 transport links).
- ZSD-89 (PLAGF Armored and PLAN cards): 12 HP (was 10).
- Everything else as 0.8.0-dev.76.

## Historical 0.8.0-dev.76

- J-36: card turn radius 985 (was 1095); yaw rates x1.144, speed unchanged.
- J-36 Heavy CAP: one loadout, 4x PL-17 and 4x PL-16 (default). The 8x PL-17 + 4x PL-21 and the PL-16 Heavy CAP loadouts are removed. Prices unchanged.
- J-8D: Light strike +30 (was +50).
- JH-7A removed for now.
- MD-22: Light strike (2x LS-6 500kg) no longer carries PL-15 air-to-air missiles. Its other strike loadouts had none.
- MD-22: J-35 optics (Optics Plane Air Superiority: high altitude 8000, low 2000, no ground spotting; was the drone set 5250/1600/1000).
- Everything else as 0.8.0-dev.75.

## Historical 0.8.0-dev.75

- DF-17/ZF: missile resupply costs 2000 supply (was 1000). Resupply time is unchanged (120 s).
- SR-5: its launchers are named Fire Dragon 70, Fire Dragon 70 CLU, Fire Dragon 300 and Fire Dragon 480 (were HIMARS and ATACMS). Same stats; they are now SR-5 copies, so the M142 HIMARS is unchanged. The Fire Dragon 300 loadout no longer renames the unit to "ATACMS".
- Everything else as 0.8.0-dev.74.

## Historical 0.8.0-dev.74

- Radar now loads on JRVG-1, PGZ-09, HJ-10 and AFT-10 (Radar SHORAD values: low-altitude optics and weapon range x1.25, high-altitude optics x2). The game loads only the first default ability of a unit; these units had smoke first and radar second, so the radar was dropped. Smoke and radar are now one ability.
- Everything else as 0.8.0-dev.73.

## Historical 0.8.0-dev.73

- FK-2000: both 30 mm guns use the PGL-625 gun stats again: 7.8 damage per round (was 3.0), 20 damage per second per gun, 40 for the unit. The SAM is unchanged.
- Everything else as 0.8.0-dev.72.

## Historical 0.8.0-dev.72

- PGZ-88: ZTZ-59D armour profile (front HEAT 600 / KE 400, sides 200 / 100; was 30 all round).
- ZTZ-100: front kinetic armour 750 (was 800).
- ZSD-89A (all four cards): M1283 AMPV base armour, speed and optics, 25 points (was 35), 12 seats, no weapons (the 12.7 mm mount is removed).
- Everything else as 0.8.0-dev.71.

## Historical 0.8.0-dev.71

- PGL-625: gun at 20 damage per second (7.8 per round at the Pantsir gun rate; was 3.0, about 7.7/s), and the ZBL-191 armour profile (HEAT 700 front and sides).
- WZ-8: flies high only; it can no longer switch to low altitude.
- Everything else as 0.8.0-dev.70.

## Historical 0.8.0-dev.70

- WZ-8: 300 points (was 260).
- Everything else as 0.8.0-dev.69.

## Historical 0.8.0-dev.69

- PLZ-05: a 2S35 Koalitsiya-SV stat copy (armour, speed, optics, smoke, 260 points; was 200) with the Koalitsiya menu:
  - HE rounds (default): 155 mm L/54 howitzer, 70x 155 mm ERFB-BB.
  - Extended range (+70): 50x 155 mm ERFB-BB-RA and 20x GP155 laser-guided.
  - A QJC-88 12.7 mm roof gun in both.
- Everything else as 0.8.0-dev.68.

## Historical 0.8.0-dev.68

- PLARF Infantry 步兵: no HJ-73D (the soldier who carried it keeps his QBZ-95). Still 7 men, 50 points.
- Everything else as 0.8.0-dev.67.

## Historical 0.8.0-dev.67

- Sea Dragons and Beijing Swords: amphibious, swimming at 18 like the vanilla PDSS and Green Light Team (were land only).
- Forward Observers: VDV Razvedka unit icon.
- Everything else as 0.8.0-dev.66.

## Historical 0.8.0-dev.66

- Tank speeds: the 152 tracked vehicle road speeds raised in dev.61 (road = 1.6x off-road) are back to their dev.60 values for every nation. A road bonus will return as a game rule that leaves unit speeds alone.
- ZTZ-100: 4 s reload (was 5-6 s).
- ZBD-251: new protection slot like the M2A3 Bradley's: None or APS (+60, 2 charges).

## Historical 0.8.0-dev.65

- ZTL-191, VT-5 and ZTQ-15 (and their Recon copies): 105 mm DU APFSDS penetration 550 close and 500 at full range (ZTQ-15/VT-5 were 500/475, ZTL-191 575/550).
- FH-97A and MD-22: Light SEAD and Heavy SEAD loadouts removed.
- Everything else as 0.8.0-dev.64.

## Historical Freedom Arrow 0.8.0-dev.64

- CH-901 (Blood Wolves NLOS missile) damage 8 -> 15.

## Historical 0.8.0-dev.63

- DF-ZF top speed 1200 (was 2400), acceleration stays 300. Test: can HQ-9s still engage it? Vanilla ballistic missiles fly at 800; HQ-9s ignored 1600.
- DF-17/ZF costs 250 points (was 300).

## Historical 0.8.0-dev.62

- DF-ZF: acceleration 3x the DF-21 (300, was 200). Top speed is 2400 = acceleration x 8 s burn, so the cap never stops the boost.
- Ballistic missiles keep their burnout speed to impact; the game adds no speed on the descent.
- DF-15, DF-17, DF-21, DF-21D and DF-31A keep their own models in matches: the copied F-16 glass now survives scene loads (FAModels 0.3.21).

## Historical 0.8.0-dev.61

- Road speed: every tracked vehicle (all nations) now drives 60% faster on roads than off-road: road speed = off-road speed x 1.6.
  - Examples: M1A2, T-90M, BMP-3, ZTZ-99A 70 -> 88; T-80U, T-14, XM30, ZTZ-100 80 -> 96; Bradley 60 -> 72; Spartan 95 -> 112.
  - 152 mobility rows. Off-road, reverse and water speeds are unchanged.
- Wheeled vehicles are unchanged: their road speed is already about double (1.8-2.3x, most exactly 2x).
- Broken Arrow has no global road multiplier; the only global movement settings are the forest multipliers (vehicles 0.5, infantry 1.0).

## Historical 0.8.0-dev.60

- AFT-09 is now called WZ-550 (the model is the WZ-550 4x4 with HJ-9).
- PGL-625 and FK-2000 guns: 1200 m ground range, the same on both.
- Spec moves: FK-2000 to PLAN Navy/SOF, GJ-11 to PLAAF, PHL-191 Ballistic to PLAGF Motorized, PHL-03 to PLAGF Ground Force/Armored.
- New ZTL-191 Recon (Motorized, +5 points, Very Good Optics), like the ZTQ-15 Recon.
- DZD98A HE damage 7.5 -> 10. HJ-8 uses the Kornet unit icon.
- QBZ-95, QBB-95 and QBU-88 now show their own models on every squad that carries them.
- Models: ZTL-191 gun raised back to its source height; DF-17 small utility doors visible again; stand-in models are hidden every frame until our model is built (FAModels 0.3.20).
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.59

- FK-2000: two 30 mm AA guns, each with the PGL-625 gun stats (the Pantsir 2A38M stats): muzzle velocity 805 -> 1610 and 133 rounds (was 70). The FK-2000 SAM is unchanged.

## Historical 0.8.0-dev.58

- FK-2000: the purchased CGTrader model with the seller's own textures and vanilla glass replaces the old stand-in model (static, launchers in travel position as the seller exported them).
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.57

- PGL-625: a Pantsir S1 stat copy (armour, radar, optics, guns and missiles) with road speed 100, reverse 40, 8 missiles (Pantsir 12) and a missile ground range of 1200 as shown in game. 170 points as before.
- PGZ-09: twin 35 mm guns with the Pantsir 30 mm gun stats and 133 rounds (was 67).
- PHL-16: 350 points (was 250); its 300 mm and 370 mm rockets do 48 damage (was 33) with a 165 m blast as shown in game (was 150 m).
- PHL-191 Ballistic: loadouts named after its real missiles, 2x Fire Dragon 480 and 2x Fire Dragon 280A (stats as before: ATACMS and PrSM).
- PHL-03: choosing a guided loadout no longer renames the unit "9K515 Tornado-S".
- PGZ-88: 80 points (was 175).
- JRVG-1: moved from Motorized to PLAN Navy/SOF; ground range 1400 and high-altitude range 1800 as shown in game (were 1100 and 1000); road speed 100 (was 70), reverse 25.
- HQ-7B: moved from PLAN Navy/SOF to PLAAF.
- HQ-17A: now in both PLAN Navy/SOF and Motorized.
- HQ-6A: moved from Rocket Force to Motorized.

## Historical 0.8.0-dev.56

- PLA infantry cards now use Osama's six supplied images (40 cards changed):
  - SF High Tech: Blood Wolves, Godswords, Whistling Arrows, Mountain Leopards.
  - SF CQC: every other special forces card (Thunder Gods, Sharp Blades, PAP Snow Leopards, Falcons, Beijing Swords, Sea Dragons, Taishan Eagles).
  - SF Jungle: PLAGF Ground Force/Armored infantry.
  - Airborne: PLAAF infantry. Motorized: PLAGF Motorized infantry. Marines: Marines, Marine HJ-8 and Marine QW-2.
- Conscripts and sniper pair cards are unchanged. The three replaced dev.41 images are removed from FreedomArrow.Runtime.dll.

## Historical 0.8.0-dev.55

- J-5, J-7 and J-8D get one cannon and the J-6W two, with GSh-23 stats and their real names (Type 23-1, Type 30-1, Type 23-3).
- Z-8L: King Stallion stats (cost 120, 30 seats, armour, speed, sensors), no weapons. WZ-7: Global Hawk stats.
- Z-10K: Longbow optics (the Z-21 already had them). ZBD-251: its missile is the HJ-10 with the name HJ-16.
- CSK-181 Transport is now just CSK-181. Mountain Leopards cost 90. Z-11WB is also in PLAN Navy/SOF. The PLAAF Z-19 Recon is removed.
- Models: DF-15 black tyres, dark olive missile and vanilla glass; HQ-17 front radar further forward; Z-11WB shinier; QN-506 more metallic; crew hidden on the Lynx ATV, SR-5 and both Shaanxi HMV3 (FAModels 0.3.19 keeps checking for late-spawned crew).
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.54

- DF-31A: 10 minutes to rearm its missile (was about 22) and 30000 supply per missile (was 27500).
- Everything else as 0.8.0-dev.53.

## Historical 0.8.0-dev.53

- DF-15: the seller's 3-colour camo now covers the cab and body at the size shown in the seller's picture; the paint no longer renders as bare metal.
- PHL-03: the doors have the seller's camo again and the paint no longer renders as bare metal.
- CSK-181: the camo body is kept at full detail (only the wheels and small parts are reduced). PCL-181: body reduced, tyres intact, vanilla window glass.
- QN-506: tracks and wheels dark, gun and missile pods olive.
- ZBD-04, ZBD-04A and ZBD-04A Recon: the seller's digital camo, as one static model.
- PGL-625: the seller's digital camo. KQ-200: see-through propeller discs from the seller's texture.
- SR-5: the driver is hidden.
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.52

- DF-17/ZF: now a ballistic missile with the same arc as the DF-21 and Iskander-M (it flew flat with the Kinzhal profile), with twice their acceleration (200) and twice their top speed (1600; they cap at 800).
- Everything else as 0.8.0-dev.51.

## Historical 0.8.0-dev.51

- Vanilla glass (the game's own F-16 canopy glass) on J-5, J-6, J-7, J-8, Z-10, Z-11WB, HQ-12, PCL-09, PHL-16, DF-ZF (DF-17), DF-21, DF-31A and PHL-191. Where the seller painted the windows into the main texture, the see-through parts are cut out using the seller's own opacity map.
- HQ-6A and Z-11WB: more metallic and a little smoother, like the vanilla helicopters and trucks.
- Z-8L glass is not done yet: its seller texture has no map that marks the windows.
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.50

- DF-17/ZF: the missile's motor now lights at launch (it waited 2 s, the air-launched Kinzhal setting, so it fell onto its own launcher and the blast killed it). The steep climb, dive and 1500 top speed stay.
- DF-31A: normal ballistic aim time, 10-12 s (was 120 s). Blast 500 m as shown in game (was 700 m).
- Everything else as 0.8.0-dev.49.

## Historical 0.8.0-dev.49

- Removed (parked until models are found): PHL-11, Shaanxi Troop Truck, VP4, PGZ-04 / PGZ-04A (it is the PGZ-95), WZ-701, ZSD-90, PHL-81. The Lynx ATV keeps VP4's Air Force availability and carries every squad VP4 carried.
- FH-97A: the strike and SEAD packages no longer carry PL-15 air-to-air missiles.
- J-5, J-6W, J-7 and J-8D: no ECM. New Heavy strike for +40: J-5 and J-7 2x 1000 kg bomb, J-6W 2x 500 kg bomb, J-8D 4x 1000 kg bomb (replaces its old Heavy strike).
- Names and icons: Light Riflemen 轻步兵, Weapons Squad 火力班; ABZ-13 uses the TOW-2BB icon; GAM-102LR Team uses the Spike unit icon.
- Models: PLZ-07/PLZ-07B use the PLZ-89 model; Z-10 is 20% smaller; Z-8L faces forward; ZSD-89A is 20% bigger; the Lynx ATV no longer shows the seated US soldiers; ZTQ-15, ZTZ-99 family, ZBL-191 and ZTZ-100 seller camo models are unrigged (one static model) and ZTZ-100 is no longer see-through; HQ-17 front radar forward and lower.
- FAModels 0.3.18 (hide-only entries). Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.48

- PHL-191 Ballistic: a loadout choice like the vanilla HIMARS, 2x ATACMS (default) or 2x PrSM, both at +0, instead of 8x 370 mm rockets. Unit cost 250 -> 225.
- Everything else as 0.8.0-dev.47.

## Historical 0.8.0-dev.47

- Seller woodland digital camo (the artist's own coatings): ZTQ-15 and ZTQ-15 Recon, ZTZ-99, ZTZ-99A, ZTZ-99A2, ZTZ-99G, ZBL-191 and ZTZ-100. ZSD-89A already uses the seller's woodland digital set (dev.43).
- PGZ-09: the twin 35 mm guns are back on the turret.
- HQ-17 / HQ-17A: both radars moved onto the turret roof (search radar forward and lower, tracking radar higher).
- ZTL-191: turret, gun and remote MG lowered onto the hull, matching Shawn's original Blender file.
- ZSL-92: the MG card is now called "ZSL-92" and uses the model without the turret; the other card stays "ZSL-92 Autocannon".
- CSK-181 and PCL-181: the very heavy seller meshes (3.1 million and 14 million vertices) are reduced so they draw properly; PCL-181 tyres are dark as in the seller's picture.
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.46

- ZBD-251 ABZ-13: the same stats as the Bradley ESV BLAAM (TOW-BB): damage 15 (was 13.5), 20 m blast (was 10), 2-round magazine with an 8-12 s reload (was 4 and 5-6 s), but 60 mm penetration (was 35). It keeps its own vertical launch, model and sounds.
- HE and thermobaric ATGMs at 60 mm penetration: TOW-BB and Kornet-M 9M133FM-2, Kornet 9M133F, Khrizantema 9M123F (were 80); Kokon 9M114F, Ataka-M 9M120F, Konkurs-M 9M113F (were 70).
- Air-launched HE missiles (Griffin, LMUR, Hellfire AGM-114M, Kh-BPLA) are unchanged.

## Historical 0.8.0-dev.45

- HJ-10 weapon icon: the AFT-10 (HJ-10 card) and ZBD-251 launchers show a new HJ-10 silhouette instead of the US Hellfire or the generic ATGM icon. Drawn to the proportions of Osama's Red Arrow 10B photo. Helicopter and drone AKD-10 racks keep their rack icons.
- Everything else as 0.8.0-dev.44.

## Historical 0.8.0-dev.44

- HQ-6A: the seller's Camouflage set (the forest camo on the listing preview), from Osama's re-download, in place of the plain Base Green set.
- Model files ship in the complete package only until the next assets release.

Models and music: 0.2.5 plus the dev.35-44 files (complete package).

## Historical 0.8.0-dev.43

- Seller textures that the FBX export had dropped are reconnected, checked against each CGTrader listing preview:
  - DF-15: the seller's 3-colour camo on the cab, body and launcher (was plain green).
  - PCL-181: the seller's digital camo on the body (was plain tan); the seller's flag and badge textures are no longer painted over.
  - ZSD-89A: the seller's main woodland-digital set from the listing preview (was the plain-green set).
- Still missing from the seller downloads (reported, not made up): QN-506 and ZTZ-59D paint (SketchUp/Lumion only), DF-15 and PHL-03 decal placement, PHL-03 tyre texture.
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.42

- Seller-provided textures on all models (Osama: "we want to use what the seller already provided"):
  - Back to the seller's own paint (desert recolours removed): DF-15, DF-17, DF-21/21D, DF-31A, YJ-18, HQ-6A (also no brightening), HQ-12, PGZ-88, PGZ-09, PLZ-70, PLZ-83, PLZ-85, PLZ-89, Type 89 (PLARF) and ZTZ-59D/59D1.
  - Generated digital camo replaced with the seller files: ZTQ-15, ZTQ-15 Recon, VT-5, VT-5 Recon, ZTZ-99, ZTZ-99A, ZTZ-99A2, ZTZ-99G, VT-4, ZBD-04, ZBD-04A and ZTZ-100.
- Kept: QN-506 woodland camo (its seller files have no textures), the ZTZ-96/96A/96B swap, black tyres and dark windows where seller textures were missing, and clear glass.
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.41

- PLA infantry card portraits: 43 PLA infantry cards now use new Chinese portraits instead of Russian ones.
  - Conscripts: every PLARF Rocket/Reservist infantry card.
  - Airborne assault: PLAGF Motorized and PLAGF Armored infantry.
  - Air assault: PLAAF Airborne infantry.
  - Sea Dragons: Marines, Marine HJ-8, Marine QW-2 and Sea Dragons.
  - Sniper pair: both Snipers cards and the Armored Sniper Pair.
- Special forces keep their current portraits until more SF art is made. Test cards are unchanged.
- The portraits are original generated art, embedded in FreedomArrow.Runtime.dll.

## Historical 0.8.0-dev.40

- QN-506: woodland digital camo on the hull and turret. The seller files have no texture maps (the re-download is identical), so the camo is projected onto the model's main paint.
- ZBL-08: now uses Shawn's PBR ZBL-09 model (same 8x8 family, woodland) in place of the old model with camo netting.
- Model files ship in the complete package only until the next assets release.


## Historical 0.8.0-dev.39

- 17 purchased models from Osama's cart now show in the armory and in battle:
  - New models (these units had none): DF-15, DF-17, HQ-6A, HQ-11, PHL-16, PHL-191 Ballistic, PCL-181 / SH-15, AFT-09, CTL-181, CSK-181 and CSK-181 Transport, ZBD-251, Type 59D and ZTZ-59D1.
  - Replaced stand-ins: PHL-03, QN-506, ZSL-92 (both cards), ZSD-89 (Type 89 and PLAN ZSD-89) and ZSD-89A (all four cards).
  - Camo: Rocket Force-only units (DF-15, DF-17, HQ-6A, Type 59D, ZTZ-59D1, Type 89) in desert; the rest keep the seller's woodland or green paint. The QN-506 file is flat sand, recoloured olive.
- PHL-191 card renamed "PHL-191 Ballistic" (the two-pod launcher). "PHL-191 Cruise" (three-box AR3) comes when its model arrives.
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.38

- PLZ-05: the gun sits in the turret again (it was 1.66 m forward) and the roof MG is back on the roof.
- HQ-17 and HQ-17A: both radars raised out of the hull onto the turret; they move at wheeled speed (the vanilla Tor-M2KM: road 90, cross-country 45, reverse 20, turn rate 80).
- ZBD-04, ZBD-04A and ZBD-04A Recon (PLAGF) in woodland digital (were plain green).
- ZTZ-100 in woodland digital.
- ZTZ-96A and ZTZ-96B swap models: the ZTZ-96B now uses Shawn's woodland-digital model, and the ZTZ-96A the old plain-green one.
- Model files ship in the complete package only until the next assets release.

## Historical 0.8.0-dev.37

- Woodland digital camo on the ZTZ-99 and ZTZ-99A (were plain green) and the ZTZ-96B (was plain green).
- The ZTZ-96 uses Shawn's woodland set, the same as the ZTZ-96A (was his desert set).
- The ZTQ-15 Recon is in desert digital; the ZTQ-15 tank stays woodland.
- Gameplay data unchanged from 0.8.0-dev.36. Model files ship in the complete package only until the next assets release.

Models and music: 0.2.5 plus the dev.35-37 files (complete package).

## Historical 0.8.0-dev.36

- ZTQ-15 and ZTQ-15 Recon now both serve PLAGF Armored, in woodland digital. The ZTQ-15 card moved from Motorized.
- New VT-5 and VT-5 Recon for Motorized, in desert digital; the VT-5 card is also in PLAN Navy/SOF. They are ZTQ-15 / ZTQ-15 Recon stat clones except:
  - APS (2 charges, 10 s cooldown, the vanilla light APS).
  - ZTZ-96A front armour: kinetic 600, HEAT 700 (ZTQ-15: 300 / 500).
  - SRAT II side armour: HEAT 700 (ZTQ-15: 250); kinetic sides stay 100.
  - 140 and 145 points (ZTQ-15: 95 and 100).
- The VT-5 uses the ZTQ-15 model until the VT-5 model is bought and converted.
- Model files ship in the complete package only until the next assets release.

Models and music: 0.2.5 plus the dev.35 and dev.36 files (complete package).

## Historical 0.8.0-dev.35

- ZTQ-62-I removed from the game (its PLARF card is gone).
- New ZTZ-59D1: a recon copy of the ZTZ-59D in PLARF. Recon category, Very Good Optics (2300 m ground), 65 points, 6 cards. Same gun, armour and model as the ZTZ-59D.
- ZFB-05 uses the Russian BPM-97 model, portrait, sound and size; its 12.7 mm mount shows the BPM-97 Kord turret.
- ZTQ-15 in PLA digital camo: desert digital for Motorized, woodland digital for the PLAGF ZTQ-15 Recon.
- US voice lines at 70% of their original level by default (FA Music 1.5.2, -3.1 dB). UserData/FAMusic/voice-gain-db.txt still overrides it.
- Model and music files ship in the complete package only until the next assets release.

Models and music: 0.2.5 plus the files above (complete package).

## Historical 0.8.0-dev.34

- US voice lines (FA Music C&C clips) 6 dB quieter, to sit with the game's Russian lines. FA Music 1.5.1 reads the level from UserData/FAMusic/voice-gain-db.txt (one number in dB, default -6; restart the game after changing it).
- Gameplay data unchanged from 0.8.0-dev.33. FAMusic.dll ships in the complete package only until the next assets release.

Models and music: 0.2.5 plus FAMusic 1.5.1.

## Historical 0.8.0-dev.33

- Shawn's models: HQ-17 and HQ-17A, J-20S (high res), PLZ-05, ZTZ-96A (woodland) and ZTZ-96 (desert), ZTL-191, ZBL-09, Z-21, Type 052D, PGL-625 and PGZ-09 (desert).
- Model fix: parts that the source files moved with animation tracks (turrets, guns, launchers) are now baked in place for every purchased model.
- Includes 0.8.0-dev.32. Not yet verified in a game run.

Models and music: 0.2.5.

## Historical 0.8.0-dev.32

- Purchased models fixed: PLL-09, PLZ-45A4, PLZ-83 and PLZ-89 have their guns on the turret again (and the PLL-09/PLZ-89 roof MGs); DF-31A, HQ-12 and J-7 glass is clear instead of mirror chrome; Jiutian faces forward.
- Includes 0.8.0-dev.31. Not yet verified in a game run.

Models and music: 0.2.4.

## Historical 0.8.0-dev.31

- ZSL-92: smoother surface. The fine noise in its surface-detail (normal) maps that looked wrinkly is filtered out; panel shapes, colours, camo and markings are unchanged.
- Gameplay data unchanged from 0.8.0-dev.30. The two normal maps ship in the complete package only (needs the all-in-one file until the next assets release).

Models and music: 0.2.3 plus the two ZSL-92 normal maps.

## Historical 0.8.0-dev.30

- MD-22: the LS-6 1000kg loadout is now "Heavy strike (2x LS-6 1000kg)" with no PL-15s, 105 -> 60 points; loadouts ordered by category then price.
- Godswords 80 -> 100 points.
- Spike LR and GAM-102LR: penetration 700 -> 140, the Javelin's value for a top-attack missile.
- Includes 0.8.0-dev.29 (purchased models). Not yet verified in a game run.

Models and music: 0.2.3.

## Historical 0.8.0-dev.29

- 22 purchased models replace their stand-ins: DF-21, DF-31A, YJ-18, PCL-09, PLL-09, PLZ-45A4, PLZ-70, PLZ-83, PLZ-85, PLZ-89, HQ-12, PGZ-88, PTL-02, J-5, J-6, J-7, KJ-500, KQ-200, Y-8, Jiutian, WZ-7 and Z-8L. Rocket Force ground units in desert digital, Motorized and PLAGF in woodland digital.
- Includes 0.8.0-dev.28. Not yet verified in a game run.

Models and music: 0.2.3.

## Historical 0.8.0-dev.28

- QN-202: hits twice as hard (damage 9 -> 18) at half the rate of fire (reload 5-6 s -> 10-12 s), so the 12 rounds last.
- Includes 0.8.0-dev.27. Not yet verified in a game run.

Models and music: 0.2.2.

## Historical 0.8.0-dev.27

- QLU-11: almost no dispersion (smart airburst grenade launcher). Rounds land on the aim point out to 1000 m.
- Includes 0.8.0-dev.26. Not yet verified in a game run.

Models and music: 0.2.2.

## Historical 0.8.0-dev.26

- QN-202 anti-personnel missile: damage 4 -> 9 (Whistling Arrows). Build 39 had given it the RPG-7 HE warhead's damage.
- Includes 0.8.0-dev.25. Not yet verified in a game run.

Models and music: 0.2.2.

## Historical 0.8.0-dev.25

- CTL-181 NLOS missile: laser guidance off. Lasering for it made the missile go haywire; it now flies its precision path to the point it was fired at, like a cruise missile.
- Includes 0.8.0-dev.24. Not yet verified in a game run.

Models and music: 0.2.2.

## Historical 0.8.0-dev.24

- Godswords 90 -> 80 points.
- QLU-11 fires at the full XM25 rate (dev.21's 10% slowdown removed); still the XM25 round out to 1000 m.
- Includes 0.8.0-dev.23 (darker ZSL-92). Not yet verified in a game run.

Models and music: 0.2.2.

## Historical 0.8.0-dev.23

- ZSL-92: the same textures, a lot darker (tyres too), with a stronger metallic layer. Only the ZSL-92 textures change.
- Includes 0.8.0-dev.22. Not yet verified in a game run.

Models and music: 0.2.2.

## Historical 0.8.0-dev.22

- Conscript rifles QBZ-95, QBB-95 and QBU-88 fire another 30% slower (QBZ-95 one shot every 8.2 s, QBB-95 4.1 s, QBU-88 6.1-8.2 s).
- WZ-8: armour, laser, sensor, stealth (0.5) and size of the RQ-170 Sentinel with the MiG-31 flight model (1260 speed, afterburner). 260 points.
- Includes 0.8.0-dev.21. Not yet verified in a game run.

Models and music: 0.2.1.

## Historical 0.8.0-dev.21

- Prices from the infantry DPS-per-point check: PAP Snow Leopards 60 -> 90, Weapons Squad 35 -> 45, AA Troopers 55 -> 60, Beijing Swords 55 -> 70, Marine HJ-8 Team 70 -> 55, Godswords 50 -> 90, Taishan Eagles 55 -> 65.
- Kits: PAP Snow Leopards carry 4 DZJ-08; Falcons carry a PF-98 instead of the PF-89; Mountain Leopards carry 3 HJ-12.
- Blood Wolves CH-901: 12 rounds, 1800 m, damage 8, penetration 30, can be intercepted. The squad can now lase targets for it (laser designator, 1800, not on the move).
- PLAAF Tank Hunters: DZT-98 thermobaric rounds 6 -> 10.
- QLU-11 fires the XM25 round at the XM25 rate, 10% slower, out to 1000 m, with spread scaled to the longer range. The QTS-11 grenade launcher fires the XM25 round at the XM25 rate (600 m). The QTS-11 rifle and QLZ-04 are unchanged.
- Includes the retired-scenario cleanup (old untagged Airport, Baltiisk and Dam folders are removed at start). Not yet verified in a game run.

Models and music: 0.2.1.

## Historical 0.8.0-dev.20

- Launcher ammo matched to the Russian/US equivalents: PF-98 and PF-98A carried inside squads 10 -> 6 (dedicated PF-98 teams keep 10, like the RAWS and RPG-29 teams); FHJ-02 14 -> 6; HJ-12 Team 2 -> 4 (as the Javelin team); single-gunner AA teams (QW-12 Patrol, AA Troopers) 4 -> 6.
- In a match, infantry can board any deck unit that has seats, whatever the armory transport list says. Z-20T, Shaanxi HMV3, Z-8L, Mi-8 Cargo and Shaanxi Troop Truck now have 0 infantry seats, so they no longer appear as transports in the match either.
- CSK-181 Transport gets an empty default mount; its armory card threw a resupply-time error.
- Includes 0.8.0-dev.19 (ZSL-92 retexture pilot). Not yet verified in a game run.

Models and music: 0.2.0 plus FAModels.dll 0.3.17 and the ZSL-92 textures.

## Historical 0.8.0-dev.19

- ZSL-92 retexture pilot (both ZSL-92 cards): woodland digital camo applied across the hull in 3D, markings kept, dust and edge wear, colour map 2048 px (was 1024), and new surface-detail (normal) and metal/shine (mask) maps. Complete package only; the launcher models package is unchanged.
- Includes 0.8.0-dev.18 (FAModels 0.3.17 infantry fix). Not yet verified in a game run.

Models and music: 0.2.0 plus FAModels.dll 0.3.17 and the ZSL-92 textures.

## Historical 0.8.0-dev.18

- Infantry models fixed: FAModels 0.3.17. In the 0.8.0-dev.15 game log, after two matches every Chinese infantry body in the Arsenal failed (Mesh.vertexCount NullReferenceException) and the game showed the native Russian body. The loader kept body and weapon meshes that the game had unloaded between scenes; it now rebuilds them and keeps built meshes across scene changes. Included in the complete package; the launcher's models package (0.2.0) still has 0.3.16.
- ZBL-191: HJ-16 range 1500 m (the Javelin's), SRAT II armour (12 HP, HEAT 700/700/130/20, kinetic 80/60/30/20). Price stays 105.
- Not yet verified in a game run.

Models and music: 0.2.0 plus FAModels.dll 0.3.17.

## Historical 0.8.0-dev.17

- ZBL-191: 4x HJ-16 in place of the HJ-8E. HJ-16 = the Javelin (10.5 damage, 140 penetration, top attack, fire-and-forget) at 2000 m instead of 1500 m.
- ZBL-191: IronFist APS (as on the ZBD-20) and Stryker SRAT I armour (12 HP, HEAT 250/200/130/20, kinetic 80/60/30/20 front/sides/rear/top; was 60/40/30/30).
- ZBL-191 price 40 -> 105 (theoretical: 30 mm wheeled IFV, 4 long-range top-attack missiles, APS, SRAT I armour; compare M2A3 65, Stryker ATGM 70, ZBD-20 175).
- Includes 0.8.0-dev.16 and earlier. Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.16

- Shaanxi Troop Truck is no longer offered as a squad transport (10 squad links removed); it stays as its own card.
- ZSD-63 removed (Rocket card and its 7 squad transport links). ZSD-63C stays.
- Every squad that had a transport still has at least one.
- Includes 0.8.0-dev.15 (transport cleanup) and dev.14 (HJ-10 no-LOS hook). Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.15

- Shaanxi HMV3, Z-8L and Mi-8 Cargo are no longer offered as squad transports (53 squad links each removed); they stay as their own cards.
- Z-20T is a gunship: no longer a squad transport, gunship role (Helo tab).
- CSK-131 Transport is merged into CSK-131 Mengshi (its 7 squad links duplicated the Mengshi's; the copy leaves the roster).
- CSK-181 Transport is now in Air Force/Airborne, Navy/SOF and Motorized as well as Rocket, offered to 32 more squads.
- Lynx ATV: Type 86 7.62 mm, QJC-88 12.7 mm and QLZ-87 35 mm grenade launcher replace the M240, M2 and Mk19.
- Includes 0.8.0-dev.14 (HJ-10 no-LOS hook). Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.14

- Ground HJ-10: back to the ground Hellfire missile (13 damage, 90 penetration, top attack, 1800 m, fast and straight, interceptable by APS), with a semi-active seeker and no firing on the move. A runtime hook lets it fire at enemies its side has spotted, within its range, without its own line of sight; the seeker hook keeps the missile locked on a moving target without line of sight. Every target the hook allows is logged (`FREEDOM_ARROW_NLOS fire:`).
- CH-901: a CTL-181-style precision munition (laser guided, no seeker, not interceptable). No hook.
- Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.13

- CH-901 cannot be intercepted by APS (Osama: OK as is). The ground HJ-10 NLOS missile stays interceptable (0.8.0-dev.12).
- Includes 0.8.0-dev.8 to dev.12, with the NLOS hook launcher lookup through the warhead. Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.12

- HJ-10 and CH-901 NLOS missiles can be intercepted by APS again (the precision-path copy had turned this off). Not yet measured against an APS in a match.
- NLOS hook: the 0.8.0-dev.11 game log showed it could not find a target on any HJ-10 missile (empty launcher link), so it stood down and the missiles flew the normal precision path (8 of 8 hit). It now also finds the launcher through the warhead, and logs why when no unit target exists (for example when the launcher fires at a ground position).
- Includes 0.8.0-dev.8 to dev.11. Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.11

- CTL-181 NLOS missile: 8 damage (was 10 in 0.8.0-dev.10, 15 before). Name CTL-181 NLOS and 1800 m range kept.
- Includes 0.8.0-dev.10, dev.9 (NLOS hook fix) and dev.8 (aircraft batch). Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.10

- CTL-181 is named CTL-181 NLOS. Its NLOS missile does 10 damage (was 15) and reaches 1800 m (was 2000 m).
- Includes 0.8.0-dev.9 (NLOS hook fix) and 0.8.0-dev.8 (aircraft batch). Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.9

- NLOS hook fix: in the 0.8.0-dev.7 game log a ground HJ-10 NLOS missile launched with an empty seeker, so the hook fell back to vanilla. The hook now takes the target from the seeker, then the seeker's original target, then the launcher's own target, and retries for 30 checks before it gives up. Each launch logs where its target came from.
- Includes all of 0.8.0-dev.8 (aircraft batch). Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.8

- Stray weapons removed from Chinese aircraft. Planes without a gun mount showed a leftover store in the gun slot (J-7 PL-8, J-8D 4x 250 kg, J-20S PL-12); they now have an empty default mount, with no gun added. Every loadout now sets every pylon of its model (the J-16 left 2 open). 77 unused mount rows and 58 unused ammo rows were deleted.
- Loadout pictures show the role weapon (bomb on strike loadouts). The missing R73 picture is fixed. PL-17 and PL-21 have new icons.
- Loadouts are ordered by category, then price: air-to-air, strike (with CAS and anti-armor), SEAD, standoff and anti-ship.
- YJ-15 loadouts are Standoff strike. GB-6 loadouts are Anti-armor. BBC-5 removed (the GB-6 version is kept).
- SEAD removed from Su-30MKK, J-11BS, J-11BHG and J-15. H-6K: KD-63 standoff is 6x KD-63; new Heavy SEAD with 6x YJ-91 (195).
- New LS-6 1000kg guided bomb (GBU-56 values): 2x on J-20S, J-31, J-35, MD-22 and FH-97A; J-36 Heavy strike is 4x.
- FH-97A has the J-31 loadouts and price (250); its fixed AMRAAM is removed.
- ECM: J-16 40%, J-16D 50%, F-15EX 40% (165 points, the J-16 price), Su-35S 30% in every loadout (135 points).
- J-36: top speed 900 km/h in flight (it flew on the F-35's 810 km/h preset).
- Blood Wolves NLOS missile is the CH-901.
- Not yet verified in a game run.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.7

- New NLOS trait. A missile with the trait flies the CTL-181 precision path, so it fires at any enemy your side has spotted without its own line of sight, and a runtime hook keeps its seeker on the target while the target lives, so it follows a moving target with no laser. The trait list is `UserData/FreedomArrow/nlos.json`; any missile added there gets the same behaviour. Every hook action is logged (`FREEDOM_ARROW_NLOS`).
- Ground HJ-10: NLOS trait. Warhead unchanged (13 damage, 90 penetration, top attack, 1800 m). Laser guidance off.
- Blood Wolves: the HJ-12 is replaced by an NLOS missile launcher, 2 missiles: the ZBD-20 precision AT warhead (20 damage, 65 penetration, top attack, 2000 m) with the NLOS trait.
- Not yet verified in a game run. The unit card trait icon is a follow-up.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.6

- CTL-181 NLOS missile: 30 mm penetration (was 20), no dispersion, laser guided, an attack order fires repeatedly (4/48/48 short/normal/long).
- ZBD-20 precision missile: no dispersion, laser guided, repeat fire (2/4/4).

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.5

# Freedom Arrow 0.8.0-dev.5

- ZBD-20 and ZBD-20 Recon: 4 of the CTL-181 precision missiles with a top-attack AT warhead (base 20, penetration 65): 2 hits on low-end tanks (top 80), 3 on high-end (top 100), about 20 to infantry. Calculated with the native HEAT formula, not measured. 175 / 180 points.
- ZBD-20 and ZBD-20 Recon have the vehicle laser designator; the ZBD-20 and CTL-181 missiles follow laser spots.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.4

# Freedom Arrow 0.8.0-dev.4

- CTL-181 NLOS: small precision-strike cruise missile copied from the vanilla Iskander-K (vertical launch, cruise flight) with a Hellfire-size missile and AT-missile impact; 48 missiles, 15 damage, 20 penetration, 50% ignore cover, 2000 m. Replaces the mortar-style round of 0.8.0-dev.1.
- ZBD-20 and ZBD-20 Recon: 100 mm gun / HJ-9 launcher removed (30 mm main gun); 165 / 170 points.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.3

# Freedom Arrow 0.8.0-dev.3

- ZBD-03 / ZLC-2000 renamed ZBD-03.
- ZBD-04A: Bradley BUSK armour with weaker sides (KE 100/60, HEAT 400/150), Bradley M2A2 mobility (60/20), 65 points. ZBD-04: Bradley base armour, keeps 70/25.
- ZBD-20: ZTZ-96B armour (650/750 front, 14 HP) and mobility (80/40); 30 mm on the Bushmaster II profile with 57 mm HE blast/ignore cover and 550 range; Iron Fist APS; 175 points.
- ZTZ-99: T-90M armour with 750 KE front.
- Recon copies: ZBD-04A Recon (PLAGF, Exceptional Optics), ZBD-20 Recon (PLAGF), ZBD-03 Recon (Airborne), ZBD-86 Recon (Rocket Force) and ZBD-86 Recon (PLAN SOF), Very Good Optics.

Models and music unchanged: 0.2.0.

## Historical 0.8.0-dev.2

# Freedom Arrow 0.8.0-dev.2

- CSK-131 Mengshi and CSK-131 Transport: 7 seats (the Tigr model's vanilla seats; were 4), now carrying the Airborne squads of 7 or fewer.
- Shaanxi SX2190 removed (Shaanxi Troop Truck stays).

Models and music unchanged: Freedom Arrow — Models and Music 0.2.0.

## Historical 0.8.0-dev.1

# Freedom Arrow 0.8.0-dev.1

Freedom Arrow 0.8: China (PLA) as the third nation on the full 0.7.0-dev.58 game. Same game content as PLA TEST Build 68; this build changes the identity to Freedom Arrow 0.8.0-dev.1 and ships as two launcher packages: gameplay `FreedomArrow-0.8.0-dev.1.bamod` and models/music `FreedomArrow-Assets-0.2.0.bamod`. Change log: Library → Changelogs → Freedom Arrow Changes 0.8.

## Historical PLA TEST Build 68

# PLA TEST Build 68

JRVG-1 gun copied from the vanilla Arleigh Burke Mark 45 naval gun (sound, autoloader, elevation, muzzle flash, 127 mm shell model and impact effect), tuned down: 8 damage, 20 m blast, 7 m proximity fuse, 2400 m low-altitude range, one shot per second (about 8 damage per second). It keeps the AA gun type, direct fire and air targets.

## Historical Build67

# PLA TEST Build 67

- PHL-191 (no "/ AR3") in Rocket Force; PHL-03 in Motorized as a Smerch copy (HE, Cluster, Guided HE, Guided Cluster).
- PHL-16: only the default launcher is mounted at spawn, so the other loadouts' weapons no longer appear together.
- DF-21: 82 damage and 90 m blast (KAB-1500), 180 points. DF-17/ZF: Kinzhal flight, top speed 1500, not interceptable, 300 points. DF-31A: 120 s aim, 1000 points.
- PCL-181: Koalitsiya weapons and menu, 155 mm HE / HE-RAP / Guided.
- JRVG-1: 76 mm HE 8 damage (about 8/s), 20 m blast, 2400 m low-altitude range, SHORAD radar, Mark 45 naval gun sound; camo net hidden, metal mask maps.

## Historical Build66

# PLA TEST Build 66

- Live models restored: Object 640 Black Eagle (dev.51 model), MGM-166 LOSAT (scale 1.2), F-21 scale 1.1, and the live 0.1.14 copies of the Su-57D, F-14, Su-47, Su-75 and YF-23 models.
- ZTQ-62-I: generated normal and mask maps at the Black Eagle (vanilla-matched) metal/gloss levels.
- J-31, J-35 and MD-22: 6x PL-15C loadouts removed.
- Removed: SH-16, ZTZ-20, PGZ-04, ZTZ-59, PLZ-07 (Armored), Z-10 Armored card (Airborne keeps its Z-10).
- ZTZ-99, 99A, 96, 96A: M1A2 Abrams mobility (70/35, cross-country 55). ZTZ-96B 80/40. ZTZ-100 keeps 80/40.
- PTZ-89 main gun autoloaded, 5 s reload.
- Shaanxi HMV3 Cargo: LVSR mobility with HEMTT model, default resupply 15,000.

## Historical Build65

# PLA TEST Build 65

- Aircraft pylons clear: every PLA loadout sets every pylon its menu uses, with the vanilla Empty turret on unused ones (306 slots filled), so weapons from another loadout no longer stay mounted.
- Loadouts are named by role: Light/Heavy CAP, Light/Heavy SEAD, Anti-ship, Standoff strike, Light/Heavy strike, CAS; helicopters Light/Heavy anti-armor, Multirole, Fire support, Air escort.
- LT-2 and LS-6 are one bomb, shown as LS-6 500kg. J-16 32-bomb load is LS-6 250kg (guided). Duplicate entries removed.
- J-20 air-to-air only; J-20S strike/SEAD. J-20/J-20S: at most 4 PL-15 internal, PL-16 gives 6, no PL-17. YJ-91 removed from all stealth aircraft.
- MD-22: MiG-31BM flight profile, the J-31 loadout menu, J-31 stealth. J-50 hidden. J-36 uses the F-35A fly preset.
- CTL-181 NLOS: indirect laser-guided missile (vanilla PGMM behaviour) at targets others spot; 2000 m, 48 missiles, 15 damage, 20 penetration, 50% ignore cover.
- CSK-181 transport also in Motorized.

## Historical Build64

# PLA TEST Build 64

The PLA pack now sits on the latest main dev build, 0.7.0-dev.58, instead of 0.6.0-dev.101. Everything Russian and US, the runtime (AA cooldown, C-RAM prediction, playable borders, conquest and the rest), the skirmish mod, the game config and the maps (Oil Rush, Airport, Baltiisk, Dam, Highway of Death, Dead Center, Chkalovsk) are exactly dev.58. Every China unit, loadout, squad and specialization is exactly Build 63.

Four China units moved to new IDs because dev.58 uses those numbers: J-31 971 -> 1251, WZ-8 972 -> 1252, FH-97A 973 -> 1253, Type21 woodland fixture 985 -> 1254. Saved decks with those four cards lose them. PLA's own older copies of RU/US units (Su-75, Su-47, F-14, YF-23, XM30, ZIL Karatel) are replaced by dev.58's versions. Merge: tools/pla-specs/merge_dev58.py; 0 field conflicts.

## Historical Build63

# PLA TEST Build 63

Chinese APCs and IFVs carry cargo (resupply points) like their vanilla analogues: ZSD-89A (all four), ZSD-89, ZSD-90, ZSD-63, ZSD-63C and CSK-181 carry 400 (M113A3 class); CSK-131 Transport, ZBD-86, ZBD-03, ZBL-191 and ZBD-251 carry 250 (Tigr, BMP-1, BMD-2, Bumerang and Kurganets class), as do the recon cars with seats (CSK-131 Mengshi, ZFB-05, CS/VN3C MG, WZ-701, VP4). Helicopters, aircraft and trucks have no cargo field in vanilla's tables; their cargo comes from the native model, which they share with the vanilla unit. ZBD-04A, ZBD-20 and ZBD-04 already had 250 on their third default ability; the game keeps only the first, so every default ability now carries it. Prices are unchanged. Everything else is exactly Build62. In-game check pending.

## Historical Build62

PLARF size correction: Conscripts, QJZ-89 Team, QLZ-87 Team and Thermobaric Team are 12 men again; Ambush Team (4) and Sharp Blades (6) are as in Build60; HJ-73D, FN-6, PF-98 Teams, Infantry and Counter-Raid Team stay 7. Conscripts cost 25. ZSD-89A is four separate cards with 12 seats and a QJC-88 12.7 mm HMG: PLARF, PLAGF (both PLAGF specs), PLAAF and PLAN SOF. All use the M113A3 body until the ZSD-89A model is bought. ZBD-86 is also in PLAAF airborne. Everything else is exactly Build61. In-game check pending.

## Historical Build61

Every PLARF infantry card is now 7 men (plain QBZ-95 riflemen trimmed or added; every launcher, MG and DMR kept; HP 35). The 12-man squads now also fit the 10-seat ZSD carriers. QBZ-95, QBB-95 and QBU-88 fire 30% slower: PLARF conscripts are meat shields. The Malyutka Recon Ambush Team is renamed Ambush Team 伏击组, and PLARF Infantry carries one PF-89 beside its HJ-73D. Prices are unchanged. Everything else is exactly Build60. In-game check pending.

## Historical Build60

The PLARF PF-98 Team and the Mechanized PF-98 Tank Hunters swap PF-98 versions: PLARF carries the tripod PF-98 (HEAT to 800 m, DZD98A HE to 1000 m, no vehicle targets for the HE), Mechanized carries the plain PF-98. Rifles, squad size and price stay with each squad. Everything else is exactly Build59. In-game check pending.

## Historical Build59

# PLA TEST Build 59

Blood Wolves become armour hunters: QBZ-192 riflemen, one HJ-12, two PF-89 and a QBU-10 sniper. Falcons become desert raiders: QBZ-192 riflemen, a QJZ-171 12.7 mm HMG, two QLB-06, a QBU-10 sniper and a PF-89. Everything else is exactly Build58. In-game check pending.

## Historical Build58

# PLA TEST Build 58

GAM-102LR Team: the launcher was a TOW-2A clone (M220 model, TOW sound, 1-2 s aim, 5-6 s reload). It now copies the vanilla Spike LR team launcher in full: SPIKE_LR_Tripod model, Javelin-type sound, 2-3 s aim, 8-10 s reload. Missile unchanged (Spike LR copy).

"Motorized" is removed from every PLA unit name (12 rows), and Motorized Light AT Riflemen is now "Light Riflemen".

Russian and US units are visible again: the PLA build had set DisplayInArmory to false on every non-China unit. 470 vanilla RU/US units get their vanilla value back and 46 Freedom Arrow RU/US additions are visible (as in live dev.45). Vanilla-hidden units and other countries stay hidden; China stays the default deck country.

Every Motorized squad now wears SF assault desert (Taishan Eagles keep SF night vision). The GAM-102LR Team was on the regular woodland body.

No other value changed. Includes Build57 (Airborne goggles-down desert bodies, "Mechanized" removed from PLAGF names).

## Historical Build57

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

- 2026-11-12 11:39:54 PST (America/Los_Angeles) — Build58: RU/US units visible; Motorized in SF assault desert; GAM-102LR launcher = Spike LR; "Motorized" removed from names; Light Riflemen.

- 2026-11-12 11:48:01 PST (America/Los_Angeles) — Build59: Blood Wolves armour hunters, Falcons desert raiders (Osama 11:46).

- 2026-11-12 11:54:53 PST (America/Los_Angeles) — Build60: PF-98 swap between the PLARF PF-98 Team and the Mechanized PF-98 Tank Hunters.
- 2026-11-12 12:07:25 PST (America/Los_Angeles) — Build61: PLARF 7-man squads, conscript rifle fire rate -30%, Ambush Team name, PF-89 for PLARF Infantry.
- 2026-11-12 12:15:10 PST (America/Los_Angeles) — Build62: PLARF size correction, Conscripts 25, ZSD-89A x4 (12 seats), ZBD-86 in PLAAF.
- 2026-11-12 12:22:54 PST (America/Los_Angeles) — Build63: vanilla-style cargo on Chinese APCs and IFVs.

- 2026-11-12 12:28:51 PST (America/Los_Angeles) — Build64: PLA pack on main dev 0.7.0-dev.58.

- 2026-11-12 12:56:55 PST (America/Los_Angeles) — Build65: aircraft loadout pass, CTL-181 NLOS, CSK-181 Motorized.

- 2026-11-12 13:11:01 PST (America/Los_Angeles) — Build66: live models, ZTZ mobility, removals, PTZ-89, HMV3 Cargo, ZTQ-62-I maps.

- 2026-11-12 13:22:04 PST (America/Los_Angeles) — Build67: rocket force, artillery and JRVG-1 batch.

- 2026-11-12 13:25:45 PST (America/Los_Angeles) — Build68: JRVG-1 on the Mark 45 naval gun.

- 2026-11-12 13:28:26 PST (America/Los_Angeles) — 0.8.0-dev.1: Build 68 content as Freedom Arrow 0.8, live package split.

- 2026-11-12 13:42:25 PST (America/Los_Angeles) — 0.8.0-dev.2: CSK-131 seats, SX2190 removed.

- 2026-11-12 13:48:37 PST (America/Los_Angeles) — 0.8.0-dev.3: ZBD batch.

- 2026-11-12 13:54:42 PST (America/Los_Angeles) — 0.8.0-dev.4: CTL-181 cruise missile, ZBD-20 without missiles.

- 2026-11-12 14:00:25 PST (America/Los_Angeles) — 0.8.0-dev.5: ZBD-20 precision missiles and laser.

- 2026-11-12 14:03:39 PST (America/Los_Angeles) — 0.8.0-dev.6: CTL-181/ZBD-20 missile tuning.

- 2026-11-12 14:29:14 PST (America/Los_Angeles) — 0.8.0-dev.7: NLOS trait hook, ground HJ-10, Blood Wolves NLOS missile.

- 2026-11-12 14:52:50 PST (America/Los_Angeles) — 0.8.0-dev.8: Chinese aircraft loadout batch, ECM/prices, CH-901.

- 2026-11-12 14:54:37 PST (America/Los_Angeles) — 0.8.0-dev.9: NLOS hook takes the launcher target when the seeker is empty.

- 2026-11-12 14:57:19 PST (America/Los_Angeles) — 0.8.0-dev.10: CTL-181 NLOS name, 10 damage, 1800 m.

- 2026-11-12 14:59:57 PST (America/Los_Angeles) — 0.8.0-dev.11: CTL-181 NLOS 8 damage.

- 2026-11-12 15:11:59 PST (America/Los_Angeles) — 0.8.0-dev.12: NLOS missiles interceptable by APS; hook launcher lookup via warhead.

- 2026-11-12 15:12:49 PST (America/Los_Angeles) — 0.8.0-dev.13: CH-901 not interceptable.

- 2026-11-12 15:20:33 PST (America/Los_Angeles) — 0.8.0-dev.14: HJ-10 semi-active Hellfire with no-LOS fire hook; CH-901 CTL-style.

- 2026-11-12 15:27:33 PST (America/Los_Angeles) — 0.8.0-dev.15: transport cleanup, CSK-181 spread, Chinese Lynx weapons.

- 2026-11-12 15:40:22 PST (America/Los_Angeles) — 0.8.0-dev.16: Shaanxi Troop Truck not a squad transport; ZSD-63 removed.

- 2026-11-12 15:44:49 PST (America/Los_Angeles) — 0.8.0-dev.17: ZBL-191 HJ-16, APS, SRAT I armour, 105 points.

- 2026-11-12 16:22:23 PST (America/Los_Angeles) — 0.8.0-dev.18: FAModels 0.3.17 infantry body fix; HJ-16 1500 m; SRAT II.

- 2026-11-12 16:48:43 PST (America/Los_Angeles) — 0.8.0-dev.19: ZSL-92 retexture pilot.

- 2026-11-12 18:18:33 PST (America/Los_Angeles) — 0.8.0-dev.20: launcher ammo parity, zero seats on non-transports, CSK-181 Transport mount.
