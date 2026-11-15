"""Freedom Arrow 0.9.0-dev.7 batch over exact 0.9.0-dev.6 (Osama, 14 Nov 2026 evening, thread 1567745029781454889).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.7';PREV='0.9.0-dev.6'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
UAB=t['UnitAbilitiesJson'];AB=t['AbilitiesJson'];TW=t['TurretWeaponsJson'];SAJ=t['SpecializationAvailabilitiesJson']
# ---------- QN-506 freeze (Osama 20:26 PST: "calling in the QN-506 caused my game to stall"). Game log 20:25:48: "CombatSystem
# initialization for unit=PLA QN-506 failed", IndexOutOfRange in UnitBuilder.SetupWeaponComponents, then a TurretComponent error
# every frame. Its BMPT body's slot 2 holds 1 weapon in vanilla (AG-17); QN-506 put 2 there (QN-502 + QN-201). The QN-201 moves to
# slot 0 (vanilla BMPT carries 3 there: 2A42, PKT, Ataka). check_slot_weapons.py now fails any build with this.
_tw=lambda tid:sorted((w['WeaponId'],w['Id']) for w in TW.values() if w['TurretId']==tid)
ok(U[937]['HUDName']=='QN-506' and [x[0] for x in _tw(2009648)]==[2009647,2009653],'QN-506 slot 2 has QN-502 + QN-201')
ok([x[0] for x in _tw(2009634)]==[2009633],'QN-506 slot 0 has the 30 mm only')
_qn201=dict(_tw(2009648))[2009653];g.put('TurretWeaponsJson',_qn201,{'TurretId':2009634,'Order':1})
ok([x[0] for x in _tw(2009634)]==[2009633,2009653] and [x[0] for x in _tw(2009648)]==[2009647],'QN-506 slots after')
rec['qn506']={'moved':'QN-201 (weapon 2009653) from slot 2 (turret 2009648) to slot 0 (turret 2009634)'}
# ---------- MD-22 (Osama 20:3x PST): "Reduce its points by 65"; "we leave the ECM in there but no flares". Its only ability was 45
# (laser, the vanilla Okhotnik's). New ability: the J-20's ECM 20 + laser (2001399, ECM 0.55) without decoys (flares).
ok(U[976]['HUDName']=='MD-22' and U[976]['Cost']==280,'MD-22 cost 280')
ok(not [o for o in t['OptionsJson'].values() if o.get('ReplaceUnitId')==976],'no MD-22 swap rows')
g.put('Units',976,{'Cost':215})
_md=[a for a in UAB.values() if a['UnitId']==976];ok([a['AbilityId'] for a in _md]==[45],'MD-22 abilities = laser')
_ecm=g.add('AbilitiesJson',AB[2001399],{'Name':'ECM Plane 20 + Laser No Decoy FA 0.55','IsDecoy':False,'DecoyQuantity':0})
g.put('UnitAbilitiesJson',_md[0]['Id'],{'AbilityId':_ecm})
ok(AB[_ecm]['ECMAccuracyMultiplier']==0.55 and AB[_ecm]['IsLaserDesignator'] and not AB[_ecm]['IsDecoy'],'MD-22 ECM + laser, no flares')
# High altitude only (Osama: "the MD-22 can't go low"; "FH-97 remove flares and low altitude"). Both share a mobility row with other
# aircraft (MD-22: MiG-31 row 169; FH-97A: F-35B row 149), so each gets its own copy with IsChangeAltitude False, the vanilla
# S-70 Okhotnik's setting (mobility 309). Speeds and flight model are unchanged.
def high_only(uid,mob,name):
    _p=[p for p in t['UnitPropulsionsJson'].values() if p['UnitId']==uid];ok([p['MobilityId'] for p in _p]==[mob] and t['MobilityJson'][mob]['IsChangeAltitude'],(name,'mobility'))
    ok(not [o for o in t['OptionsJson'].values() if o.get('MobilityId') and M.get(o.get('ModificationId'),{}).get('UnitId')==uid],(name,'no option mobility'))
    _m=g.add('MobilityJson',t['MobilityJson'][mob],{'Name':t['MobilityJson'][mob]['Name']+' '+name+' high only','IsChangeAltitude':False})
    g.put('UnitPropulsionsJson',_p[0]['Id'],{'MobilityId':_m});ok(not t['MobilityJson'][_m]['IsChangeAltitude'],(name,'high only'));return _m
rec['md22']={'cost':[280,215],'ability':[45,_ecm],'ecm':0.55,'laser':True,'flares':False,'mobility':[169,high_only(976,169,'MD-22')]}
# ---------- FH-97A: no flares, no low altitude (Osama 20:4x PST). Same ECM 0.55 + laser as before (2001399), without decoys.
_f=[a for a in UAB.values() if a['UnitId']==1253];ok(U[1253]['HUDName']=='FH-97A' and [a['AbilityId'] for a in _f]==[2001399],'FH-97A ability')
g.put('UnitAbilitiesJson',_f[0]['Id'],{'AbilityId':_ecm})
rec['fh97a']={'ability':[2001399,_ecm],'flares':False,'mobility':[149,high_only(1253,149,'FH-97A')]}
# ---------- J-36 laser (Osama 20:3x PST: "J-36 needs a laser"). Its ability 2001398 (ECM 0.5 + flares) is shared with the F-22, J-50
# and YF-23, so the J-36 gets its own copy with the laser designator of the J-20's ability (2000 m, usable on the move).
_j=[a for a in UAB.values() if a['UnitId']==929];ok(U[929]['HUDName']=='J-36' and [a['AbilityId'] for a in _j]==[2001398],'J-36 ability ECM 0.5')
_jl=g.add('AbilitiesJson',AB[2001398],{'Name':'ECM Plane 20 + Laser Default FA 0.5','IsLaserDesignator':True,'LaserMaxRange':2000.0,'LaserUsableInMove':True})
g.put('UnitAbilitiesJson',_j[0]['Id'],{'AbilityId':_jl})
ok(AB[_jl]['ECMAccuracyMultiplier']==0.5 and AB[_jl]['IsDecoy'] and AB[_jl]['IsLaserDesignator'],'J-36 ECM 0.5 + flares + laser')
rec['j36_laser']={'ability':[2001398,_jl]}
# ---------- AKF-98A mixed strike loadouts (Osama 20:4x PST: "J-10A, J-20S, J-31/35 all need AKF-98A loadouts, basically find a mixed
# bomber loadout that only has 4 munitions/bombs and mix in the AKF-98A. Price accordingly"). Each copies the jet's 4x LS-6 500kg loadout
# (two pylons, 2 bombs each) and puts the J-16's AKF-98A pylon (turret 2016658, 1 weapon) on one of them with 2 missiles: 2 LS-6 500kg +
# 2 AKF-98A. Price: on the J-16, 4 AKF-98A (160) cost 45 more than 4 LS-6 500kg (115), about +11 per missile; 2 missiles = +20.
TUJ=t['TurretUnitsJson'];WAJ=t['WeaponAmmunitionsJson'];O=t['OptionsJson']
_akf_tu=TUJ[2016678];_akf_wa=next(w for w in WAJ.values() if w['UnitId']==916 and w['WeaponId']==2016659)
ok(_akf_tu['TurretId']==2016658 and _akf_wa['AmmunitionId']==2016661 and _akf_wa['Quantity']==1,'J-16 AKF-98A pylon')
rec['akf98a']={}
for _uid,_name,_base,_slot,_bomb in ((1226,'J-10A',24437,4,2016559),(966,'J-20S',24593,2,2017628),(1251,'J-31',24601,2,2017670),(921,'J-35',24597,2,2017670)):
    _o=O[_base];ok(U[_uid]['HUDName']==_name and M[_o['ModificationId']]['UnitId']==_uid and _o[f'Turret{_slot}Id']==_bomb,(_name,'base loadout'))
    _bw=next(x['WeaponId'] for x in t['TurretWeaponsJson'].values() if x['TurretId']==_bomb)
    ok(next(w['Quantity'] for w in WAJ.values() if w['UnitId']==_uid and w['WeaponId']==_bw)==2,(_name,'2 bombs per pylon'))
    ok(not [r for r in TUJ.values() if r['UnitId']==_uid and r['TurretId']==2016658],(_name,'no AKF pylon yet'))
    g.add('TurretUnitsJson',_akf_tu,{'UnitId':_uid});g.add('WeaponAmmunitionsJson',_akf_wa,{'UnitId':_uid,'Quantity':2})
    _ord=max(o.get('Order',0) for o in O.values() if o.get('ModificationId')==_o['ModificationId'])+1
    _n=g.add('OptionsJson',_o,{f'Turret{_slot}Id':2016658,'IsDefault':False,'Order':_ord,'Cost':_o['Cost']+20,'Name':f'PLA loadout {_name} mixed AKF-98A','UIName':'Mixed strike (LS-6 500kg + AKF-98A)'})
    rec['akf98a'][_name]={'option':_n,'from':_base,'cost':[_o['Cost'],_o['Cost']+20],'slot':_slot,'load':'2x LS-6 500kg + 2x AKF-98A'}
# ---------- XM30 (Osama 20:4x PST: "XM-30 to 200 with TOW, 210 with Javelin. remove XM-30 from the VEH tab"). It stays the transport
# of Mech. Riflemen, Mech. Riflemen AA and Mech. Riflemen MMG (Armored Brigade), like the 72 other transport-only vehicles.
ok(U[983]['HUDName']=='XM30' and U[983]['Cost']==230 and O[20239]['Cost']==0 and O[20240]['Cost']==0,'XM30 230, TOW/Javelin +0')
ok(not [o for o in O.values() if o.get('ReplaceUnitId')==983],'no XM30 swap rows')
g.put('Units',983,{'Cost':200});g.put('OptionsJson',20240,{'Cost':10})
_xs=[r for r in SAJ.values() if r['UnitId']==983];ok([r['Id'] for r in _xs]==[2001842],'XM30 one deck card (Armored Brigade)')
g.remove('SpecializationAvailabilitiesJson',2001842)
ok(len([r for r in t['TransportAvailabilitiesJson'].values() if r['UnitId']==983])==3,'XM30 still a transport for 3 cards')
rec['xm30']={'cost':[230,200],'javelin_option':[0,10],'removed_card':2001842,'transport_for':3}
# ---------- ZFB-05 removed from the game (Osama 20:5x PST). It was only a transport: 10 PLAGF Motorized infantry cards, each of which
# keeps 4 other transports (ZBL-08, ZBL-191, ZSL-92, CSK-131). Its unit rows stay (not on any card); saved decks that picked it fall back
# through the mod's deck guard.
_TA=t['TransportAvailabilitiesJson'];_z=[r for r in _TA.values() if r['UnitId']==954]
ok(U[954]['HUDName']=='ZFB-05' and len(_z)==10 and not [r for r in SAJ.values() if r['UnitId']==954],'ZFB-05 = 10 transport links, no card')
for r in _z:
    ok(len([x for x in _TA.values() if x['SpecializationAvailabilityId']==r['SpecializationAvailabilityId'] and x['UnitId']!=954])>=1,('other transport',r['Id']))
    g.remove('TransportAvailabilitiesJson',r['Id'])
ok(not [r for r in _TA.values() if r['UnitId']==954],'ZFB-05 gone')
rec['zfb05_removed']={'transport_links':[r['Id'] for r in _z]}
# ---------- Recon helicopter FireSnakes doubled (Osama 20:4x PST: "Z-19 recon loadout seems to only have half the number of rockets",
# "same with Z-21 recon"). Z-19 Recon / Z-19G Recon: 14 -> 28 on their one pylon; Z-21 Recon: 7 -> 14 per pylon (28 total). Prices unchanged.
WAJ=t['WeaponAmmunitionsJson']
for _id,_uid,_q in ((2018855,1134,14),(2018857,1134,14),(2018859,1237,14),(2018861,1237,14),(2018863,1135,7),(2018865,1135,7)):
    ok(WAJ[_id]['UnitId']==_uid and WAJ[_id]['Quantity']==_q and t['WeaponsJson'][WAJ[_id]['WeaponId']]['HUDName'] in ('FS-70A','FS-90'),('recon FireSnake',_id))
    g.put('WeaponAmmunitionsJson',_id,{'Quantity':_q*2})
rec['recon_firesnake_x2']={'Z-19 Recon':[14,28],'Z-19G Recon':[14,28],'Z-21 Recon per pylon':[7,14]}
# ---------- Z-19 Recon off PLAGF Motorized (Osama 20:42 PST: "remove Z-19G recon from Moto spec"). Card 2014515, unit 1134 (Z-19 Recon,
# drawn with the Z-19G model). The PLAN SF Z-19G Recon card and the Motorized Z-19 gunship stay.
ok(SAJ[2014515]['UnitId']==1134 and t['SpecializationsJson'][SAJ[2014515]['SpecializationId']]['Name']=='PLA PLAGF Motorized','Motorized Z-19 Recon card')
ok(not [r for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==2014515],'no transports on it')
g.remove('SpecializationAvailabilitiesJson',2014515);rec['moto_z19_recon_removed']=2014515;assign['assignments'].pop('1134',None)
# ---------- Protection-slot options not shown (Osama 20:45 PST: "I don't see the ZTL-191 and ZBL-191 ECM loadout options"). The rows
# are in the data since dev.4/dev.5, built from vanilla M1A1 FEP mod 397. The one difference: our "None" option has IsDefault True;
# all 30 vanilla protection slots (Type 6) have no default option. Same flag on the ZBD-20 and VT-5 APS slots. Cleared on all four.
for _o in (31065,31075,31077,31079):
    ok(O[_o]['IsDefault'] and O[_o]['UIName']=='Custom_Option_None' and M[O[_o]['ModificationId']]['Type']==6,('protection None option',_o))
    g.put('OptionsJson',_o,{'IsDefault':False})
rec['protection_slot_default_cleared']=[31065,31075,31077,31079]
# ---------- PF-98 team cards get the vanilla SPG-9 icon (Osama 20:4x PST: "change to SPG icon"): PF-98 Team (1172, was SMAW) and
# PF-98 AT Team (1023, was RPG-29). Tank Hunters and Fire Support keep theirs.
for _u,_was in ((1172,'US_SMAW_TEAM-Label'),(1023,'RU_RPG29-Label')):
    ok(U[_u]['ThumbnailFileName']==_was,('PF-98 icon',_u));g.put('Units',_u,{'ThumbnailFileName':'RU_SPG9-Label'})
rec['pf98_spg_icon']=[1172,1023]
# ---------- Helicopters (Osama 21:20 PST, thread 1567745029781454889) ----------
# ECM tiers are the game's own heli abilities: 2000771 ECM Heli 05 + Laser (0.95), 2000767 ECM Heli 15 + Laser (0.85, AH-64E),
# 2000770 ECM Heli 20 + Laser (0.8). Optics: "Guardian" = AH-64E's sensor 5 (Exceptional, 2800 ground in this build);
# "current base Z-10" = sensor 3 (Very Good, 2300). Osama wrote 3200 and 2500; no sensor row has those values, so the named
# references are used and the numbers are flagged in the report.
import copy
SUJ=t['SensorUnitsJson'];TUJ2=t['TurretUnitsJson'];SAJ2=t['SpecializationAvailabilitiesJson']
def setab(uid,ab):
    r=[a for a in UAB.values() if a['UnitId']==uid];ok(len(r)==1,(uid,'one ability'));g.put('UnitAbilitiesJson',r[0]['Id'],{'AbilityId':ab})
def setsensor(uid,sid):
    r=[a for a in SUJ.values() if a['UnitId']==uid];ok(len(r)==1,(uid,'one sensor'));g.put('SensorUnitsJson',r[0]['Id'],{'SensorId':sid})
for _u in (978,1239):ok(U[_u]['HUDName']=='Z-10' and U[_u]['Cost']==105,('Z-10',_u));g.put('Units',_u,{'Cost':195});setab(_u,2000771)
ok(U[913]['HUDName']=='Z-10K' and U[913]['Cost']==105,'Z-10K');g.put('Units',913,{'Cost':195});setab(913,2000767);setsensor(913,3)
_z19=[940,1103,1132,1134,1236,1237]
for _u in _z19:
    ok(str(U[_u]['HUDName']).startswith('Z-19'),('Z-19',_u));setab(_u,2000770);setsensor(_u,5);g.put('Units',_u,{'Stealth':0.571,'CurrentStealth':0.571})
rec['helicopters']={'Z-10 (978,1239)':{'cost':[105,195],'ecm':0.95,'optics':'sensor 3 (2300, unchanged)'},'Z-10K 913':{'cost':[105,195],'ecm':0.85,'optics':'sensor 5 -> 3 (2800 -> 2300)'},
    'Z-19 all':{'units':_z19,'ecm':0.8,'optics':'sensor 5 (2800)','stealth':'0.571 raw = 1.75'}}
def clone(parent,fields):
    """Copy a unit with its own armour/mobility/ability rows, mounts, ammo, sensors and loadout options."""
    uid=max(U)+1;d=copy.deepcopy(U[parent]);d.pop('Id');d.update(fields);g.put('Units',uid,d);defs={}
    for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
        for r in g.rows(table,parent):g.add(table,r,{'UnitId':uid})
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
        for r in g.rows(table,parent):g.add(table,r,{'UnitId':uid})
    for m_ in g.rows('ModificationsJson',parent):
        nm=g.add('ModificationsJson',m_,{'UnitId':uid})
        for o in [o for o in list(O.values()) if o.get('ModificationId')==m_['Id']]:
            ok(not o.get('ReplaceUnitId'),('no swap rows',o['Id']));g.add('OptionsJson',o,{'ModificationId':nm})
    return uid
# Z-10U: PLAN SF copy of the PLAAF Z-10 (same loadouts), ECM 15 %, Guardian optics, Z-10K icon, navy grey skin.
ok(not any(u.get('Name')=='PLA Z-10U' for u in U.values()),'Z-10U name free')
_zu=clone(1239,{'Name':'PLA Z-10U','HUDName':'Z-10U','ThumbnailFileName':U[913]['ThumbnailFileName']})
setab(_zu,2000767);setsensor(_zu,5)
_c=[r for r in SAJ2.values() if r['UnitId']==1239];ok(len(_c)==1,'Z-10 one card');g.add('SpecializationAvailabilitiesJson',_c[0],{'UnitId':_zu,'SpecializationId':20})
assign['assignments'][str(_zu)]=[20]
ok(len([o for o in O.values() if M.get(o.get('ModificationId'),{}).get('UnitId')==_zu])==6,'Z-10U 6 loadouts')
rec['z10u']={'unit':_zu,'from':1239,'spec':20,'cost':U[_zu]['Cost'],'ecm':0.85,'optics':'sensor 5','icon':U[913]['ThumbnailFileName'],'cards':_c[0]['MaxAvailabilityXp0']}
# Mi-8 Cargo out of China (5 cards, no transport links).
_mi=[r for r in SAJ2.values() if r['UnitId']==1227];ok(U[1227]['HUDName']=='Mi-8 Cargo' and len(_mi)==5,'Mi-8 Cargo 5 cards')
ok(not [r for r in t['TransportAvailabilitiesJson'].values() if r['UnitId']==1227],'Mi-8 no transport links')
for r in _mi:g.remove('SpecializationAvailabilitiesJson',r['Id'])
assign['assignments'].pop('1227',None);rec['mi8_cargo_removed']=[r['Id'] for r in _mi]
# Z-18: PLAN copy of the Z-8L under its own name; the Z-8L's PLAN card moves to it. Grey navy skin (models.json in the dev.7 assets).
ok(U[1106]['HUDName']=='Z-8L' and not g.rows('ModificationsJson',1106),'Z-8L no options')
_z18=clone(1106,{'Name':'PLA Z-18','HUDName':'Z-18'})
ok(SAJ2[2016119]['UnitId']==1106 and SAJ2[2016119]['SpecializationId']==20,'Z-8L PLAN card');g.put('SpecializationAvailabilitiesJson',2016119,{'UnitId':_z18})
assign['assignments']['1106']=[17,18,19,21];assign['assignments'][str(_z18)]=[20]
ok(assign['shared_transports'].get('1106')==[17,18,19,20,21],'Z-8L shared list');assign['shared_transports']['1106']=[17,18,19,21];assign['shared_transports'].pop('1227',None)
rec['z18']={'unit':_z18,'from':1106,'spec':20,'card':2016119}
# ---------- Spec metadata: shared-transport lists brought in line with the cards that dev.4-dev.6 already have (HMV3 1235 and 1247
# in PLAGF Armored/PLARF/Motorized; SX2190 1269 in PLAAF/PLAN). Metadata only; verify_roster_revision compares it with the cards.
for _u,_l in (('1235',[18,19,21]),('1247',[18,19,21]),('1269',[17,20])):
    ok(sorted(assign['assignments'].get(_u,[]))==_l,('assignment',_u));assign.setdefault('shared_transports',{})[_u]=_l
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
