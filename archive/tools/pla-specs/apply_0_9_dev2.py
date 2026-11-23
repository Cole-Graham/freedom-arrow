"""Freedom Arrow 0.9.0-dev.2 batch over exact 0.9.0-dev.1 (Osama, thread 1571014792016171120). Built only when Osama or
Lateralus say the batch is ready (Osama 14 Nov 11:05 PST: batch changes, the package is big).
- CS/VN3C MG (1057): removed (Osama 14 Nov 11:3x PST, "remove CS/vn3c"). Its only card was PLAGF Motorized (2); it carried nobody.
- QTS Recon Cell (1224) -> "Marine Recon" in PLAN Navy/SOF only (Osama 14 Nov 11:3x PST, thread 1567745029781454889): its four
  other cards (PLAAF, PLAGF Armored, PLARF, PLAGF Motorized) and their transport links are removed; the PLAN card keeps 8 and its
  transports. Marine card art (FA_CN_INF_MARINES-Portrait) and a new icon FA_PLA_INF_LINE_MARINE_RECON(_OUTLINE): the marine
  emblem with the vanilla scout binoculars (runtime-qa/icons, embedded in the runtime DLL).
- Test Suppressed Scouts (1213) -> "Conscript Recon" in PLARF (Osama, same thread): its Test card (4) moves to PLARF, with the
  PLARF Infantry transports (CSK-181, ZSD-89, ZSD-89A), and the PLARF conscript card art.
- Prices and stats after the China pricing check (Osama 14 Nov 11:55 PST, thread 1571014792016171120): ZTQ-15 130, ZTQ-15 Recon 145,
  ZTQ-15 Light 120; ZTL-191 160, ZTL-191 Recon 180; VT-5 200, VT-5 Recon 220; PGZ-09 120; PGZ-95 130; HQ-17A 150; Mengshi Recon 30;
  Wing Loong 100 with its default loadout (base 75 -> 40); Marine HJ-8H Team 60; HJ-12 Team 90 and the HJ-12 missile 1500 m shown
  (GroundRange 650 -> 750) and penetration 130 (was 140; same missile on AT Troopers and Mountain Leopards); ZBD-86 Recon 35;
  PLZ-89 95 and PLZ-85 80 (Osama 12:16 PST; first 110 for PLZ-89); J-8D and J-7 afterburner (their shared copies of the vanilla MiG-29 mobility rows had it switched off) and Heavy
  strike loadout 60 (was 40); QN-506 armour = ZTZ-85-II armour; PGZ-88 1200 m shown ground range (500 -> 600) and 90 pts. GAM-102LR Team 110 (was 50; Osama 14:21 PST). Mountain Leopards 100 (was 90; Osama 14:24 PST). Whistling Arrows 85 (was 65; Osama 14:24 PST).
- Z-6B UAV (1105): stat clone of the vanilla MDP-01 Termit (Osama 11:58 PST): Termit stealth (raw 0.4), recon category and role,
  armour, mobility, optics, laser ability and its loadout slot (empty default, 3x S-8L, 2x Kornet-M, 2x Igla-S; same weapons and
  ammunition rows). Its own catalogue "UAV guided missile" turret is no longer used. Name, model, card and price (65) unchanged.
- ZTQ-15 Light armour 100 -> 80 KE front and sides; road 70 -> 80 km/h, reverse 35 -> 40.
- ZTZ-59 front KE 250 -> 150. CTL-181 NLOS 90 -> 180.
- ZBD-20 base (no APS, semi-active HJ-16) 175 -> 120.
- ZBL-191 105 -> 80 ; every HJ-16 IIR option (ZBL-191, ZBD-20, ZBD-20 Recon) +40 -> +15; ZBL-08 HJ-8E replaced by an optional HJ-73D Super Malyutka (+10, base 40
  without ATGM); ZBL-08 and ZTL-11 armour front 60 KE / 250 HEAT, sides 30 KE / 100 HEAT (Osama 14 Nov ~14:10 PST).
- Y-8 model yaw 180 -> 270 so it faces forward (models.json, assets package).
- PLAGF Z-20 is a transport for recon cards only: removed from the 7 INF-tab cards (PLARF has no Z-20) (Osama 14 Nov).
- KJ-500 card name 'KJ-500 / KJ-500H' -> 'KJ-500' (Osama 14 Nov).
- PLA vehicle and aircraft unit icons (Osama 14 Nov 11:4x-11:5x, thread 1567745029781454889): FA_PLA_VEH_<name>(_OUTLINE)
  rendered from our own models in the vanilla 416x216 label style (tools/pla-specs/unit-icons; Z-19/Z-9 glass and GJ-11 intake cut
  out), replacing the donor icons on every shown card of QN-506, ZBD-04A (+Recon), ZTQ-15 (+Recon, Light), Z-19 family, Z-9 family,
  Z-21 (+Recon), VT-5 (+Recon), ZTL-191 (+Recon), Jiutian, WZ-7, WZ-8, GJ-11 (gear left out, intake cut), ZBD-86 Recon and ZBD-05
  (same ZBD-86 model), ZBD-251, ZSD-89A (four cards), HJ-10.
- AR-2000 (1084): Termit base (Osama 12:00 PST): Termit armour, mobility, optics, laser ability, recon category and role; stealth
  1.75 shown (raw 0.571, not the Termit's 2.5); fixed weapon 8x "AKD-11", a copy of our HJ-10 (AKD-10) weapon and missile (the Z-21's
  8-round HJ-10 weapon) on a copy of the Termit's pylon mount. No loadout choice. Price 95 (was 65; Osama 12:05 PST).
- PTZ-89 looks like metal (Osama 12:06 PST): its material masks had metal 0 and smoothness 0 everywhere (flat matte). New masks: painted
  steel (metallic 0.55, smoothness 0.35), the darkest 4-10% of each texture (rubber, openings) 0.10 / 0.15; ambient occlusion kept.
  New mild normal maps from the colour textures (none before). Files in work/pla-0.9/ptz89-metal; listed in 0.9.0-dev.2-assets.txt.
- Marine Recon (1224, the former QTS Recon Cell) as SF (Osama 14:04 PST): SF card art (FA_CN_INF_SF_CQC-Portrait, the "rest of SF"
  group) and SF soldiers (night-vision woodland body, as on Whistling Arrows; infantry-bodies.json); 4 cards (was 8). Its icon
  (marine emblem with binoculars) and stealth (2.5, already above the SF recon 2.0) are unchanged.
- All recon SF to 4 cards (Osama 14:04 PST): Whistling Arrows, Mountain Leopards, Beijing Swords (were 3) and Marine Recon.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.2';PREV='0.9.0-dev.1'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
# ---------- CS/VN3C MG removed ----------
ok(U[1057]['HUDName']=='CS/VN3C MG','CS/VN3C MG');r=rows('SpecializationAvailabilitiesJson',1057)
ok([(x['SpecializationId'],x['MaxAvailabilityXp0']) for x in r]==[(21,2)] and not [x for x in TA.values() if x['UnitId']==1057] and assign['assignments'].get('1057')==[21],'one Motorized card, no transport links')
for x in r:g.remove('SpecializationAvailabilitiesJson',x['Id'])
assign['assignments'].pop('1057');ok(not rows('SpecializationAvailabilitiesJson',1057),'no card left')
rec['cs_vn3c_removed']={'unit':1057,'card':[21,2]}
# ---------- QTS Recon Cell -> Marine Recon (PLAN Navy/SOF only) ----------
ok(U[1224]['HUDName']=='QTS Recon Cell 数字侦察','QTS Recon Cell')
qsa={x['SpecializationId']:x for x in rows('SpecializationAvailabilitiesJson',1224)};ok(sorted(qsa)==[17,18,19,20,21],'five decks')
gone=[qsa[k]['Id'] for k in (17,18,19,21)];nta=0
for r in list(TA.values()):
    if r['SpecializationAvailabilityId'] in gone:g.remove('TransportAvailabilitiesJson',r['Id']);nta+=1
for sid in gone:g.remove('SpecializationAvailabilitiesJson',sid)
g.put('Units',1224,{'HUDName':'Marine Recon','PortraitFileName':'FA_CN_INF_MARINES-Portrait','ThumbnailFileName':'FA_PLA_INF_LINE_MARINE_RECON'})
assign['assignments']['1224']=[20]
assign['shared_transports'].pop('1224',None)   # one deck now; it was listed as a five-deck card
ok([x['SpecializationId'] for x in rows('SpecializationAvailabilitiesJson',1224)]==[20] and qsa[20]['MaxAvailabilityXp0']==8 and [r for r in TA.values() if r['SpecializationAvailabilityId']==qsa[20]['Id']],'Marine Recon: PLAN card with transports')
ok((ROOT/'releases/0.6/source/runtime-qa/icons/FA_PLA_INF_LINE_MARINE_RECON.png').exists() and (ROOT/'releases/0.6/source/runtime-qa/icons/FA_PLA_INF_LINE_MARINE_RECON_OUTLINE.png').exists(),'Marine Recon icon files')
rec['marine_recon']={'unit':1224,'removed_cards':gone,'removed_transport_links':nta,'kept':qsa[20]['Id']}
# ---------- Test Suppressed Scouts -> Conscript Recon (PLARF) ----------
ok(U[1213]['HUDName']=='Test Suppressed Scouts 消声侦察','Test Suppressed Scouts')
ssa=rows('SpecializationAvailabilitiesJson',1213);ok([(x['SpecializationId'],x['MaxAvailabilityXp0']) for x in ssa]==[(22,4)] and not [r for r in TA.values() if r['SpecializationAvailabilityId']==ssa[0]['Id']],'one Test card, no transports')
g.put('SpecializationAvailabilitiesJson',ssa[0]['Id'],{'SpecializationId':19})
ref=rows('SpecializationAvailabilitiesJson',1175);ok([x['SpecializationId'] for x in ref]==[19],'PLARF Infantry reference')
added=[g.add('TransportAvailabilitiesJson',r,{'SpecializationAvailabilityId':ssa[0]['Id']}) for r in list(TA.values()) if r['SpecializationAvailabilityId']==ref[0]['Id']]
g.put('Units',1213,{'HUDName':'Conscript Recon','PortraitFileName':'FA_CN_INF_CONSCRIPTS-Portrait'})
assign['assignments']['1213']=[19]
ok(sorted(U[r['UnitId']]['HUDName'] for r in TA.values() if r['SpecializationAvailabilityId']==ssa[0]['Id'])==sorted(U[r['UnitId']]['HUDName'] for r in TA.values() if r['SpecializationAvailabilityId']==ref[0]['Id']),'Conscript Recon has the PLARF transports')
rec['conscript_recon']={'unit':1213,'card':ssa[0]['Id'],'spec':[22,19],'transport_links':len(added)}
# ---------- pricing check follow-up (Osama 11:55 PST) ----------
AR=t['ArmorsJson'];UAR=t['UnitArmorsJson'];AM=t['AmmunitionsJson'];MB=t['MobilityJson'];UP=t['UnitPropulsionsJson'];O=t['OptionsJson'];M=t['ModificationsJson']
def hud(u,h):ok(U[u]['HUDName']==h,(u,h,U[u]['HUDName']))
PR={906:('ZTQ-15',150,130),1240:('ZTQ-15 Recon',165,145),1268:('ZTQ-15 Light',150,120),1080:('ZTL-191',180,160),1263:('ZTL-191 Recon',200,180),
    1261:('VT-5',240,200),1262:('VT-5 Recon',145,220),909:('PGZ-09',175,120),1052:('PGZ-95',175,130),1049:('HQ-17A',200,150),1265:('Mengshi Recon',50,30),
    1193:('Marine HJ-8H Team',70,60),1137:('HJ-12 Team',45,90),1258:('ZBD-86 Recon',15,35),1043:('PLZ-89',80,95),1042:('PLZ-85',90,80),1051:('PGZ-88',80,90),1221:('GAM-102LR Team',50,110),1186:('Mountain Leopards 高原雪豹',90,100),1184:('Whistling Arrows 响箭',65,85),946:('Wing Loong',75,40)}
for u,(h,was,new) in PR.items():hud(u,h);ok(U[u]['Cost']==was,(h,'cost',U[u]['Cost'],was));g.put('Units',u,{'Cost':new})
wl=[o for o in O.values() if O and M.get(o['ModificationId'],{}).get('UnitId')==946 and o['IsDefault']];ok(len(wl)==1 and wl[0]['Cost']==60,'Wing Loong default loadout 60')
rec['prices']={h:[was,new] for u,(h,was,new) in PR.items()};rec['prices']['Wing Loong']=[135,100]
hj=AM[2011865];ok((hj['GroundRange'],hj['PenetrationAtGroundRange'],hj['PenetrationAtMinRange'])==(650,140,140),'HJ-12 missile')
ok(sorted({U[x['UnitId']]['HUDName'] for x in t['WeaponAmmunitionsJson'].values() if x['AmmunitionId']==2011865})==['AT Troopers 反坦克组','HJ-12 Team','Mountain Leopards 高原雪豹'],'HJ-12 users')
g.put('AmmunitionsJson',2011865,{'GroundRange':750.0,'PenetrationAtGroundRange':130.0,'PenetrationAtMinRange':130.0});rec['hj12']={'range_data':[650,750],'shown':[1300,1500],'pen':[140,130]}
pg=AM[2010663];ok(pg['GroundRange']==500 and {x['UnitId'] for x in t['WeaponAmmunitionsJson'].values() if x['AmmunitionId']==2010663}=={1051},'PGZ-88 ammo');g.put('AmmunitionsJson',2010663,{'GroundRange':600.0})
hud(1092,'J-7');hud(975,'J-8D')
for mid in (2018944,2018945):
    ok(not MB[mid]['IsAfterburner'] and {U[r['UnitId']]['HUDName'] for r in UP.values() if r['MobilityId']==mid}=={'J-7','J-8D'},('jet mobility',mid))
    g.put('MobilityJson',mid,{'IsAfterburner':True,'Name':MB[mid]['Name'].replace(' no afterburner','')})
for oid,ui in ((24479,'Heavy strike (4x 1000 kg bomb)'),(31041,'Heavy strike (2x 1000 kg bomb)')):ok(O[oid]['UIName']==ui and O[oid]['Cost']==40,(oid,ui));g.put('OptionsJson',oid,{'Cost':60})
rec['j7_j8d']={'afterburner':True,'heavy_strike':[40,60]}
AF=('MaxHealthPoints','HeatArmorFront','HeatArmorRear','HeatArmorSides','HeatArmorTop','KinArmorFront','KinArmorRear','KinArmorSides','KinArmorTop')
hud(937,'QN-506');hud(1264,'ZTZ-85-II');qa=[r['ArmorId'] for r in UAR.values() if r['UnitId']==937];za=[r['ArmorId'] for r in UAR.values() if r['UnitId']==1264]
ok(len(qa)==1 and sum(1 for r in UAR.values() if r['ArmorId']==qa[0])==1 and len(za)==1,'own QN-506 armour');before={k:AR[qa[0]][k] for k in AF}
g.put('ArmorsJson',qa[0],{k:AR[za[0]][k] for k in AF});ok(all(AR[qa[0]][k]==AR[za[0]][k] for k in AF),'QN-506 = ZTZ-85-II');rec['qn506_armour']={'before':before,'after':{k:AR[qa[0]][k] for k in AF}}
# ---------- Z-6B UAV = MDP-01 Termit stats ----------
ok(U[1105]['HUDName']=='Z-6B UAV' and U[632]['HUDName']=='MDP-01 Termit' and U[1105]['Cost']==U[632]['Cost']==65,'Z-6B / Termit')
ok(not rows('ModificationsJson',1105) and len(rows('ModificationsJson',632))==1,'Termit loadout slot only')
for tab in ('TurretUnitsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson'):
    for r in rows(tab,1105):g.remove(tab,r['Id'])
    for r in rows(tab,632):g.add(tab,r,{'UnitId':1105})
g.put('Units',1105,{k:U[632][k] for k in ('Stealth','CurrentStealth','CategoryType','Role','MaxStress','Weight','Length','Width','Height')})
tm=rows('ModificationsJson',632)[0];nm=g.add('ModificationsJson',tm,{'UnitId':1105,'Name':'Weapons Z-6B (MDP01Termit copy)'})
for o in sorted((o for o in t['OptionsJson'].values() if o['ModificationId']==tm['Id']),key=lambda o:o['Order']):g.add('OptionsJson',o,{'ModificationId':nm,'Name':o['Name'].replace('MDP01','Z-6B')})
for tab in ('TurretUnitsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson'):
    a=sorted(tuple(sorted((k,v) for k,v in r.items() if k not in ('Id','UnitId'))) for r in rows(tab,1105));b=sorted(tuple(sorted((k,v) for k,v in r.items() if k not in ('Id','UnitId'))) for r in rows(tab,632));ok(a==b,(tab,'Termit copy'))
ok(len([o for o in t['OptionsJson'].values() if o['ModificationId']==nm])==4,'4 loadout options')
rec['z6b_termit']={'unit':1105,'from':632,'modification':nm,'stealth_raw':U[1105]['Stealth'],'category':U[1105]['CategoryType']}
# ---------- PLA vehicle/aircraft icons ----------
# ---------- ZBL-191, ZBL-08, ZTL-11 (Osama 14 Nov ~14:10 PST) ----------
T=t['TurretsJson'];TW=t['TurretWeaponsJson'];WAJ=t['WeaponAmmunitionsJson']
hud(979,'ZBL-191');ok(U[979]['Cost']==105,('ZBL-191 cost',U[979]['Cost']));g.put('Units',979,{'Cost':80})   # 25 cheaper
for oid,uid in ((31048,979),(31050,945),(31052,1256)):   # every HJ-16 IIR option +15 (Osama 14 Nov ~14:34 PST; ZBL-191 was first set to +20)
    ok(O[oid]['UIName']=='HJ-16 IIR (fire and forget)' and O[oid]['Cost']==40 and M[O[oid]['ModificationId']]['UnitId']==uid,('HJ-16 IIR option',oid));g.put('OptionsJson',oid,{'Cost':15})
ok(sorted(o['Id'] for o in O.values() if 'HJ-16 IIR' in (o.get('UIName') or ''))==[31048,31050,31052],'all HJ-16 IIR options')
hud(945,'ZBD-20');ok(U[945]['Cost']==175,('ZBD-20 cost',U[945]['Cost']));g.put('Units',945,{'Cost':120})   # base without APS or IIR (Osama 14 Nov ~14:35 PST)
hud(1268,'ZTQ-15 Light');ok([x['ArmorId'] for x in rows('UnitArmorsJson',1268)]==[2018999] and [x['UnitId'] for x in UAR.values() if x['ArmorId']==2018999]==[1268] and AR[2018999]['KinArmorFront']==100 and AR[2018999]['KinArmorSides']==100,'ZTQ-15 Light own armour 100/100 KE')
g.put('ArmorsJson',2018999,{'KinArmorFront':80,'KinArmorSides':80})   # Osama 14 Nov ~14:40 PST ("ZTQ-16 light"): 80 KE front and side
MBJ=t['MobilityJson'];ok([x['MobilityId'] for x in rows('UnitPropulsionsJson',1268)]==[2019001] and [x['UnitId'] for x in UP.values() if x['MobilityId']==2019001]==[1268] and MBJ[2019001]['MaxSpeedRoad']==70 and MBJ[2019001]['MaxSpeedReverse']==35,'ZTQ-15 Light own mobility 70/35')
g.put('MobilityJson',2019001,{'MaxSpeedRoad':80.0,'MaxSpeedReverse':40.0})   # Osama ~14:39 PST: "ZTQ-15 light 80 forward 40 reverse"
hud(1060,'ZTZ-59');ok([x['ArmorId'] for x in rows('UnitArmorsJson',1060)]==[2010811] and [x['UnitId'] for x in UAR.values() if x['ArmorId']==2010811]==[1060] and AR[2010811]['KinArmorFront']==250,'ZTZ-59 own armour, 250 KE front')
g.put('ArmorsJson',2010811,{'KinArmorFront':150})   # Osama ~14:40 PST: "ZTZ-59 150 KE"
hud(1054,'CTL-181 NLOS');ok(U[1054]['Cost']==90,('CTL-181 cost',U[1054]['Cost']));g.put('Units',1054,{'Cost':180})   # Osama ~14:41 PST: "CTL-181 to 180 pts"
# ZBL-08: the HJ-8E leaves the gun turret; the ATGM becomes an option: no ATGM (base 40) or HJ-73D Super Malyutka (+10)
Z=903;hud(Z,'ZBL-08');ok(U[Z]['Cost']==40 and not rows('ModificationsJson',Z),'ZBL-08 40, no options')
hj8=[x for x in TW.values() if x['TurretId']==2009046 and x['WeaponId']==2009059];ok(len(hj8)==1,'HJ-8E on the gun turret');g.remove('TurretWeaponsJson',hj8[0]['Id'])
w8=[x for x in rows('WeaponAmmunitionsJson',Z) if x['AmmunitionId']==2009061];ok(len(w8)==1,'HJ-8E ammo row');g.remove('WeaponAmmunitionsJson',w8[0]['Id'])
ok(AM[2011153]['HUDName']=='HJ-73D ammunition','HJ-73D (ZBD-03) ammo')
MT=g.add('TurretsJson',T[2010902],{'Name':'PLA ZBL-08 HJ-73D Super Malyutka option','IsDefault':False})
g.add('TurretWeaponsJson',[x for x in TW.values() if x['TurretId']==2010902][0],{'TurretId':MT,'WeaponId':2011151})
g.add('WeaponAmmunitionsJson',w8[0],{'UnitId':Z,'WeaponId':2011151,'AmmunitionId':2011153,'Quantity':4})
tu0=[x for x in rows('TurretUnitsJson',Z) if x['TurretId']==2009054][0]
g.add('TurretUnitsJson',tu0,{'TurretId':MT,'Order':2});g.add('TurretUnitsJson',tu0,{'TurretId':160,'Order':2})
arm=[x['ArmorId'] for x in rows('UnitArmorsJson',Z)];ok(arm==[2009037],'ZBL-08 armour row')
mid=g.add('ModificationsJson',M[208],{'UnitId':Z,'Name':'PLA ZBL-08 ATGM','UIName':'Custom_Slot_Weapon_package'})
bo={**{f'Turret{i}Id':0 for i in range(21)},'ModificationId':mid,'ArmorId':arm[0],'MobilityId':0,'MainSensorId':0,'ExtraSensorId':0,'ReplaceUnitName':None}
z1=g.add('OptionsJson',O[544],{**bo,'Name':'PLA ZBL-08 no ATGM','UIName':'No ATGM','OptionPicture':'EMPTY','Order':0,'Cost':0,'IsDefault':True,'Turret2Id':160})
z2=g.add('OptionsJson',O[544],{**bo,'Name':'PLA ZBL-08 HJ-73D','UIName':'HJ-73D Super Malyutka','OptionPicture':'MALYUTKA','Order':1,'Cost':10,'IsDefault':False,'Turret2Id':MT})
ok(z1<=32767 and z2<=32767,'short option ids')
ok(sum(T[x['TurretId']]['IsDefault'] for x in rows('TurretUnitsJson',Z))==2,'gun and MG default, ATGM optional')
# armour: front 60 KE / 250 HEAT, sides 30 KE / 100 HEAT; ZTL-11 the same
for uid,aid in ((903,2009037),(938,2009657)):
    ok([x['ArmorId'] for x in rows('UnitArmorsJson',uid)]==[aid] and [x['UnitId'] for x in UAR.values() if x['ArmorId']==aid]==[uid] and not [o for o in O.values() if o.get('ArmorId')==aid and o['Id'] not in (z1,z2)],('own armour',uid))
    g.put('ArmorsJson',aid,{'KinArmorFront':60,'HeatArmorFront':250,'KinArmorSides':30,'HeatArmorSides':100})
hud(938,'ZTL-11')
rec['zbl_ztl_14nov']={'ztq15_light_road_reverse':[[70,35],[80,40]],'ztz59_ke_front':[250,150],'ctl181_cost':[90,180],'ztq15_light_ke_front_side':[100,80],'zbd20_base':[175,120],'zbl191_cost':[105,80],'hj16_iir_options':{'ids':[31048,31050,31052],'cost':[40,15]},'zbl08':{'removed':'HJ-8E','options':{'no_atgm':z1,'hj73d':z2},'mount':MT,'option_cost':10},
 'armour_front_side':{'KE':[60,30],'HEAT':[250,100],'units':[903,938]}}
# ---------- PLAGF Z-20: transport for recon cards only (Osama 14 Nov ~14:30 PST) ----------
SAJ=t['SpecializationAvailabilitiesJson'];hud(1244,'Z-20')
z20ta=[r for r in TA.values() if r['UnitId']==1244 and SAJ[r['SpecializationAvailabilityId']]['SpecializationId']==18]
inf=[r for r in z20ta if U[SAJ[r['SpecializationAvailabilityId']]['UnitId']]['CategoryType']==1]
ok(len(z20ta)==10 and len(inf)==7,('PLAGF Z-20 links',len(z20ta),len(inf)))
for r in inf:g.remove('TransportAvailabilitiesJson',r['Id'])
for r in inf:
    ok(any(x['SpecializationAvailabilityId']==r['SpecializationAvailabilityId'] for x in TA.values()),('INF card keeps a transport',U[SAJ[r['SpecializationAvailabilityId']]['UnitId']]['HUDName']))
ok(not [r for r in TA.values() if r['UnitId']==1244 and SAJ[r['SpecializationAvailabilityId']]['SpecializationId'] in (18,19) and U[SAJ[r['SpecializationAvailabilityId']]['UnitId']]['CategoryType']!=0],'Z-20 only on recon cards in PLAGF/PLARF')
rec['plagf_z20_recon_only']={'removed_inf_links':[U[SAJ[r['SpecializationAvailabilityId']]['UnitId']]['HUDName'] for r in inf]}
# KJ-500 card renamed (Osama 14 Nov 12:3x PST: "rename to just KJ-500")
ok(U[1096]['HUDName'] in ('KJ-500 / KJ-500H','KJ-500'),('KJ-500',U[1096]['HUDName']));g.put('Units',1096,{'HUDName':'KJ-500'});hud(1096,'KJ-500')
A_ICONS=json.loads((ROOT/'tools/pla-specs/unit-icons/assign.json').read_text())   # icon key -> cards and expected name prefix
ICONS={k:v['cards'] for k,v in A_ICONS.items()};NAMES={k:v['name'] for k,v in A_ICONS.items()}
icon_dir=ROOT/'releases/0.6/source/runtime-qa/icons';iconed={}
for k,ids in ICONS.items():
    ok((icon_dir/f'FA_PLA_VEH_{k}.png').exists() and (icon_dir/f'FA_PLA_VEH_{k}_OUTLINE.png').exists(),('icon files',k))
    for uid in ids:
        ok(U[uid]['HUDName'].startswith(NAMES[k]) and U[uid]['DisplayInArmory'],('icon unit',uid,U[uid]['HUDName']))
        g.put('Units',uid,{'ThumbnailFileName':f'FA_PLA_VEH_{k}'});iconed[uid]=k
rec['vehicle_icons']=iconed
# ---------- AR-2000 = Termit base, 8x AKD-11, stealth 1.75 ----------
TR=t['TurretsJson'];W=t['WeaponsJson'];AM=t['AmmunitionsJson'];TW=t['TurretWeaponsJson'];WA=t['WeaponAmmunitionsJson']
ok(U[1084]['HUDName']=='AR-2000' and U[1084]['Cost']==65 and not rows('ModificationsJson',1084),'AR-2000')
hw=W[2017894];ok(hw['HUDName']=='HJ-10' and hw['Name']=='PLA air AKD-10 x8','HJ-10 x8 weapon');ha=AM[2017053];ok(ha['HUDName']=='HJ-10','HJ-10 missile')
ok(TR[1227]['Name']=='PylonTurret Kornet x2 MDP01','Termit pylon')
nw=g.add('WeaponsJson',hw,{'Name':'PLA AR-2000 AKD-11 x8','HUDName':'AKD-11'});na=g.add('AmmunitionsJson',ha,{'Name':'PLA AR-2000 AKD-11','HUDName':'AKD-11'})
nt=g.add('TurretsJson',TR[1227],{'Name':'PLA AR-2000 AKD-11 x8 pylon','IsDefault':True})
g.add('TurretWeaponsJson',next(r for r in TW.values() if r['TurretId']==1227),{'TurretId':nt,'WeaponId':nw})
for tab in ('TurretUnitsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson'):
    for r in rows(tab,1084):g.remove(tab,r['Id'])
for tab in ('UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson'):
    for r in rows(tab,632):g.add(tab,r,{'UnitId':1084})
g.add('TurretUnitsJson',rows('TurretUnitsJson',632)[0],{'UnitId':1084,'TurretId':nt,'Order':0})
g.add('WeaponAmmunitionsJson',rows('WeaponAmmunitionsJson',632)[0],{'UnitId':1084,'WeaponId':nw,'AmmunitionId':na,'Order':0,'Quantity':8})
g.put('Units',1084,{**{k:U[632][k] for k in ('CategoryType','Role','MaxStress','Weight','Length','Width','Height')},'Stealth':0.571,'CurrentStealth':0.571,'Cost':95})
ok([r['TurretId'] for r in rows('TurretUnitsJson',1084)]==[nt] and [(x['WeaponId'],x['AmmunitionId'],x['Quantity']) for x in rows('WeaponAmmunitionsJson',1084)]==[(nw,na,8)],'AR-2000 8x AKD-11')
ok(all(AM[na][k]==ha[k] for k in ha if k not in ('Id','Name','HUDName')) and all(W[nw][k]==hw[k] for k in hw if k not in ('Id','Name','HUDName')),'AKD-11 = HJ-10 copy')
rec['ar2000']={'unit':1084,'cost':[65,95],'weapon':nw,'ammo':na,'turret':nt,'rounds':8,'stealth':[1.25,1.75],'category':[5,U[632]['CategoryType']]}
# ---------- PTZ-89 metal look (asset files) ----------
PT=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.9/ptz89-metal');assets={}
for pre in ('m_ptz89','m_ptz89_lo'):
    for i in range(4):
        for suf in ('_mask.png','_n.png'):
            n=f'{pre}_tex{i}{suf}';k='UserData/FAModels/'+n;f=PT/n;ok(f.exists(),n)
            ok((k in z.namelist())==(suf=='_mask.png'),(n,'mask replaces, normal is new'));assets[k]=str(f)
ok(len(assets)==16,'16 PTZ-89 files');AL=ROOT/f'tools/pla-specs/{V}-assets.txt'
old=dict(l.split('=',1) for l in AL.read_text().splitlines() if '=' in l) if AL.exists() else {}
old.update(assets);AL.write_text(''.join(f'{k}={v}\n' for k,v in sorted(old.items())));rec['ptz89_metal']={'files':len(assets),'assets_list':str(AL.name)}
# ---------- Marine Recon as SF; recon SF 4 cards (Osama 14:04 PST) ----------
ok(U[1224]['HUDName']=='Marine Recon' and U[1224]['PortraitFileName']=='FA_CN_INF_MARINES-Portrait','Marine Recon from the section above')
g.put('Units',1224,{'PortraitFileName':'FA_CN_INF_SF_CQC-Portrait'})
rsf={}
for uid,h in ((1184,'Whistling Arrows 响箭'),(1186,'Mountain Leopards 高原雪豹'),(1187,'Beijing Swords 蓝剑'),(1224,'Marine Recon')):
    ok(U[uid]['HUDName']==h and U[uid]['CategoryType']==0,(h,'recon'));c=rows('SpecializationAvailabilitiesJson',uid);ok([x['SpecializationId'] for x in c]==[20],(h,'PLAN card'))
    rsf[h]=[c[0]['MaxAvailabilityXp0'],4];g.put('SpecializationAvailabilitiesJson',c[0]['Id'],{'MaxAvailabilityXp0':4})
ok(rsf['Marine Recon'][0]==8 and all(v[0]==3 for k,v in rsf.items() if k!='Marine Recon'),rsf)
IB='UserData/FAModels/infantry-bodies.json';ib=json.loads(z.read(IB));b=[x for x in ib if x['unitId']==1224];ref=[x for x in ib if x['unitId']==1184]
ok(len(b)==1 and len(ref)==1 and b[0]['lods'][0]=='pla2_regular_woodland_pack_0.fas','bodies')
b[0].update(lods=list(ref[0]['lods']),offset=list(ref[0]['offset']),anchorHands=ref[0]['anchorHands'])
out=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.9/marine-recon-sf/infantry-bodies.json');out.write_text(json.dumps(ib,ensure_ascii=False,separators=(',',':')) if b'\n' not in z.read(IB) else json.dumps(ib,ensure_ascii=False,indent=1)+'\n')
AL=ROOT/f'tools/pla-specs/{V}-assets.txt';old=dict(l.split('=',1) for l in AL.read_text().splitlines() if '=' in l) if AL.exists() else {}
old[IB]=str(out);AL.write_text(''.join(f'{k}={v}\n' for k,v in sorted(old.items())))
# ---------- Y-8 model faces forward (Osama 14 Nov ~14:28 PST: "facing to the left 90 degrees ... turn 90 degrees to the right") ----------
MJ='UserData/FAModels/models.json';mj=json.loads(z.read(MJ));Y8='PLA Catalogue Y-8 family — seller package'
ok(mj[Y8].get('yaw')==180 and mj[Y8]['file']=='m_y8b_static.fam','Y-8 yaw 180');mj[Y8]['yaw']=270   # Unity: +yaw turns the model right (clockwise from above)
mo=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.9/models/models.json');mo.parent.mkdir(parents=True,exist_ok=True)
mo.write_text(json.dumps(mj,ensure_ascii=False,separators=(',',':')) if b'\n' not in z.read(MJ) else json.dumps(mj,ensure_ascii=False,indent=1)+'\n')
old=dict(l.split('=',1) for l in AL.read_text().splitlines() if '=' in l);old[MJ]=str(mo);AL.write_text(''.join(f'{k}={v}\n' for k,v in sorted(old.items())))
rec['y8_yaw']=[180,270]
rec['recon_sf']={'cards':rsf,'marine_recon_body':ref[0]['lods'][0],'marine_recon_portrait':'FA_CN_INF_SF_CQC-Portrait'}
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
