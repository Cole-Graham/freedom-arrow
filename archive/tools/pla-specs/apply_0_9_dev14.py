"""Freedom Arrow 0.9.0-dev.14 data batch over exact 0.9.0-dev.13 (the playtest build, 15 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.14';PREV='0.9.0-dev.13'
# dev.13 was built in out/local-dev13f (the playtest packages on R2 come from there).
BASE=json.loads((REL/f'out/local-dev13f/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev13f/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
# ---------- EA-18G Growler: 45% ECM and a 4x HARM loadout at +0 (Osama 15 Nov 2026 23:5x PST: "EA-18 Growler has 45% ecm and baseline 2x HARMS").
# ECM: the Growler's ECM ability 2001406 "ECM Plane 20 Not Default FA 0.6" (ECMAccuracyMultiplier 0.6 = 40% ECM) is shared with the Su-34,
# Su-35S, JH-7A and J-11BHG. The Growler gets its own copy at 0.55 (45%); the others keep 40%.
# HARM (Osama 23:42: "the plane should have 2xSEAD missiles baseline and the current +2xSEAD still exists. We should probably just say it's
# 4xSEAD loadout and +0"): the outer-pylon slot's one option "2x AGM-88 HARM" (20116, default, +80) becomes "4x AGM-88 HARM", +0, and the
# base cost 210 -> 290 (the old +80 moves into the base). Same 2 pylons with 2 rounds each, on the Growler's own HARM copy (MagazineSize 2,
# so the second missile on a pylon needs no reload; bombs with MagazineSize 1 dropped only 1 of 2 queued in dev.12) and its own pylon copy.
# The F-16CJ, EA-6B, F-35A/C and F-15EX keep 1 HARM per pylon on the shared weapon 395 / pylon 554. Default Growler 345 -> 345 points.
ok(U[742]['HUDName']=='EA-18G Growler' and U[742]['Cost']==210,'EA-18G 742 at base 210')
_gu=[r for r in UAB.values() if r['UnitId']==742 and r['AbilityId']==2001406]
ok(len(_gu)==1 and AB[2001406]['ECMAccuracyMultiplier']==0.6,'Growler has ECM ability 2001406 at 0.6')
# Its centerline options (20121 Empty, 20122 Laser pod) name the ECM ability too, so they move to the copy as well; the Su-34's own
# ECM options (1135, 1137, 2003) keep 2001406.
_AF=('Ability1Id','Ability2Id','Ability3Id')
_eo={o['Id']:[f for f in _AF if o.get(f)==2001406] for o in O.values() if 2001406 in [o.get(f) for f in _AF]}
ok({i:M[O[i]['ModificationId']]['UnitId'] for i in _eo}=={1135:168,1137:168,2003:168,20121:742,20122:742},f'options naming 2001406 {_eo}')
_ecm=g.add('AbilitiesJson',AB[2001406],{'Name':'ECM Plane EA-18G FA 0.55','ECMAccuracyMultiplier':0.55})
g.put('UnitAbilitiesJson',_gu[0]['Id'],{'AbilityId':_ecm})
for i in (20121,20122):g.put('OptionsJson',i,{f:_ecm for f in _eo[i]})
ok(not [o for o in O.values() if M[o['ModificationId']]['UnitId']==742 and 2001406 in [o.get(f) for f in _AF]],'no Growler option names the 40% ECM')
ok(sorted(r['UnitId'] for r in UAB.values() if r['AbilityId']==2001406)==[168,169,918,1241],'40% ECM stays on Su-34, Su-35S, JH-7A, J-11BHG')
W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];TJ=t['TurretsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson']
_ho=[o for o in O.values() if o.get('ModificationId')==2001259]
ok(len(_ho)==1 and _ho[0]['Id']==20116 and _ho[0]['Cost']==80 and _ho[0]['IsDefault'] and M[2001259]['UnitId']==742 and _ho[0]['Turret3Id']==554 and _ho[0]['Turret4Id']==554,'outer pylons: one option, 2x HARM on pylons 3-4, +80, default')
ok(not [o for o in O.values() if o.get('ReplaceUnitId')==742],'no swap row to the Growler')
_hw=[r for r in TW.values() if r['TurretId']==554];_hq=[r for r in WA.values() if r['UnitId']==742 and r['WeaponId']==395];_htu=[r for r in TU.values() if r['UnitId']==742 and r['TurretId']==554]
ok([r['WeaponId'] for r in _hw]==[395] and len(_hq)==1 and _hq[0]['Quantity']==1 and len(_htu)==1 and W[395]['MagazineSize']==1,'HARM pylon 554 -> weapon 395, Growler 1 round per pylon')
_hwn=g.add('WeaponsJson',W[395],{'Name':'AGM-88 HARM EA-18G x2','MagazineSize':2});_htn=g.add('TurretsJson',TJ[554],{'Name':'PylonTurret HARM x2 EA-18G'})
g.add('TurretWeaponsJson',_hw[0],{'TurretId':_htn,'WeaponId':_hwn});g.put('TurretUnitsJson',_htu[0]['Id'],{'TurretId':_htn})
g.put('WeaponAmmunitionsJson',_hq[0]['Id'],{'WeaponId':_hwn,'Quantity':2})
g.put('OptionsJson',20116,{'Cost':0,'UIName':'4x AGM-88 HARM','Turret3Id':_htn,'Turret4Id':_htn});g.put('Units',742,{'Cost':290})
ok([r['Quantity'] for r in WA.values() if r['UnitId']==742 and r['WeaponId']==_hwn]==[2] and not [r for r in WA.values() if r['UnitId']==742 and r['WeaponId']==395],'Growler: 2 pylons x 2 HARM on its own weapon')
ok(sorted(U[r['UnitId']]['HUDName'] for r in WA.values() if r['WeaponId']==395)==['EA-6B Prowler','F-15EX Eagle II','F-16CJ','F-35A','F-35C'],'other HARM carriers unchanged')
rec['ea18g']={'unit':742,'ecm':{'ability':_ecm,'options':[20121,20122],'copied_from':2001406,'ECMAccuracyMultiplier':[0.6,0.55],'ecm_percent':[40,45]},'harm':{'option':20116,'cost':[80,0],'loadout':['2x AGM-88 HARM','4x AGM-88 HARM'],'weapon':_hwn,'pylon':_htn,'rounds_per_pylon':2},'base_cost':[210,290]}
# ---------- US M-ATV and M-ATV Javelin get smoke (Osama 15 Nov 2026 23:37 PST: "US M-ATV recon both have smoke"). Both (467 vanilla, 714 FA;
# SOF recon cards) had no ability at all. They get 1 smoke with no launcher model, ability 2000195 "Smoke x1 NoModel", as the vanilla
# Tigr / Tigr Kornet (the Russian armoured car counterparts) and M113A3 / M901A3.
_mv=[r for r in UAB.values() if r['UnitId'] in (467,714)]
ok(U[467]['HUDName']=='M-ATV' and U[714]['HUDName']=='M-ATV Javelin' and not _mv,'M-ATV 467 and M-ATV Javelin 714 have no abilities')
_tg=[r for r in UAB.values() if r['AbilityId']==2000195 and U[r['UnitId']]['HUDName']=='Tigr']
ok(len(_tg)==1 and AB[2000195]['IsSmoke'] and AB[2000195]['SmokeAmmunitionQuantity']==1,'Tigr carries smoke ability 2000195 (1 smoke)')
for _u in (467,714):g.add('UnitAbilitiesJson',_tg[0],{'UnitId':_u})
ok(sorted(r['UnitId'] for r in UAB.values() if r['UnitId'] in (467,714) and r['AbilityId']==2000195)==[467,714],'both M-ATVs have 1 smoke')
rec['matv_smoke']={'units':[467,714],'ability':2000195,'smoke':1,'as':'Tigr'}
# ---------- F-21 Super Tomcat with 2x AIM-9 and 6x AIM-174 = 360 (Osama 15 Nov 2026 23:53 PST, armory screenshot at 400: "F-21 tomcat in this
# configuration should be 360 points. I think"). 400 = base 215 + outer 2x AIM-9 25 + inner 2x AIM-174 60 + fuselage 4x AIM-174 100.
# The 40 comes off the Gunslinger loadouts only, so the default (4x AIM-9, 6x AMRAAM, 370) and the SLAM-ER loadout keep their price:
# 2x AIM-174 60 -> 40 (inner 20302 and fuselage 20305), 4x AIM-174 100 -> 80 (20304), i.e. 20 points per Gunslinger.
_f21={o['Id']:(o['UIName'],o['Cost']) for o in O.values() if o.get('ModificationId') in (2002001,2002002,2002003)}
ok(U[981]['HUDName']=='F-21 Super Tomcat' and U[981]['Cost']==215 and _f21=={20300:('2x AIM-9 Sidewinder',25),20301:('4x AIM-9 Sidewinder',50),20302:('2x AIM-174 Gunslinger',60),20303:('6x AIM-120 AMRAAM',80),20304:('4x AIM-174 Gunslinger',100),20305:('2x AIM-174 Gunslinger',60),20306:('2x AGM-84 SLAM-ER',90)},f'F-21 981 loadouts {_f21}')
ok(not [o for o in O.values() if o.get('ReplaceUnitId')==981],'no swap row to the F-21')
for _i,_c in ((20302,40),(20305,40),(20304,80)):g.put('OptionsJson',_i,{'Cost':_c})
ok(U[981]['Cost']+O[20300]['Cost']+O[20302]['Cost']+O[20304]['Cost']==360 and U[981]['Cost']+O[20300]['Cost']+O[20301]['Cost']+O[20303]['Cost']==370,'F-21: 2x AIM-9 + 6x AIM-174 = 360, default 370 unchanged')
rec['f21_gunslinger']={'unit':981,'options':{'20302':[60,40],'20305':[60,40],'20304':[100,80]},'screenshot_config':[400,360],'default_config':370}
# ---------- PLARF old jets: prices up, J-7 10 HP (Osama 16 Nov 2026 00:02 PST: "J-5 base price seems to be 35, let's bump it to 45, J-6 is 40,
# let's bump to 50, J-7 base is 60, change to 90, HP set to 10, J-8 base is 80, let's change it to 130"). Base costs only (loadout prices
# unchanged): J-5 1089 35 -> 45, J-6W 1091 40 -> 50, J-7 1092 60 -> 90, J-8D 975 80 -> 130. J-7 used armour row 238 (20 HP), shared with
# the J-8D and vanilla 309-311 and 744; it gets its own copy at 10 HP, as the J-5/J-6W did in dev.12.
UAR=t['UnitArmorsJson'];AR=t['ArmorsJson']
_jc={1089:('J-5',35,45),1091:('J-6W',40,50),1092:('J-7',60,90),975:('J-8D',80,130)}
ok(all(U[i]['HUDName']==h and U[i]['Cost']==c0 for i,(h,c0,_) in _jc.items()),'J-5 35, J-6W 40, J-7 60, J-8D 80')
ok(not [o for o in O.values() if o.get('ReplaceUnitId') in _jc],'no swap rows to these jets')
for i,(_,_,c1) in _jc.items():g.put('Units',i,{'Cost':c1})
_j7=[r for r in UAR.values() if r['UnitId']==1092]
ok(len(_j7)==1 and _j7[0]['ArmorId']==238 and AR[238]['MaxHealthPoints']==20,'J-7 on armour 238 (20 HP)')
ok(not [o for m in M.values() if m['UnitId']==1092 for o in O.values() if o['ModificationId']==m['Id'] and o.get('ArmorId')],'no J-7 option sets armour')
_a7=g.add('ArmorsJson',AR[238],{'MaxHealthPoints':10});g.put('UnitArmorsJson',_j7[0]['Id'],{'ArmorId':_a7})
ok(AR[238]['MaxHealthPoints']==20 and sorted(r['UnitId'] for r in UAR.values() if r['ArmorId']==238)==[309,310,311,744,975],'J-8D and vanilla jets keep 238 at 20 HP')
rec['plarf_jets']={'costs':{str(i):[c0,c1] for i,(_,c0,c1) in _jc.items()},'j7_armor':{'row':_a7,'copied_from':238,'hp':[20,10]}}
# ---------- ZSD-89A 25 -> 40 points (Osama 16 Nov 2026 00:06 PST: "ZSD-89A to 40 pts"). All four ZSD-89A rows (1065, 1248, 1249, 1250;
# the camo/spec copies), no loadouts or swap rows. The ZSD-89 (1064, 1246, 35) is a different vehicle and stays.
_z89=[i for i,u in U.items() if u.get('HUDName')=='ZSD-89A']
ok(sorted(_z89)==[1065,1248,1249,1250] and all(U[i]['Cost']==25 for i in _z89),'four ZSD-89A at 25')
ok(not [o for o in O.values() if o.get('ReplaceUnitId') in _z89] and not [m for m in M.values() if m['UnitId'] in _z89],'ZSD-89A: no loadouts or swap rows')
for i in _z89:g.put('Units',i,{'Cost':40})
rec['zsd89a_cost']={'units':_z89,'cost':[25,40]}
# ---------- Conscripts 25 -> 35 points (Osama 16 Nov 2026 00:08 PST: "Conscripts should be 35 points"). Unit 1166 only (Conscript Recon 1213
# stays 40); no loadouts or swap rows. 35 had been asked about on 15 Nov 11:58 ("did we make conscripts 35 points?") but never queued.
ok(U[1166]['HUDName'].startswith('Conscripts') and U[1166]['Cost']==25 and not [o for o in O.values() if o.get('ReplaceUnitId')==1166] and not [m for m in M.values() if m['UnitId']==1166],'Conscripts 1166 at 25, no loadouts')
g.put('Units',1166,{'Cost':35});rec['conscripts_cost']={'unit':1166,'cost':[25,35]}
# ---------- ZBD-20 HJ-16 can hit helicopters, 1300 m (Osama 16 Nov 2026 00:08 PST: "ZBD-20 gets 1300 low alt range (HJ-16 get SPIKE icon)").
# The ZBD-20's HJ-16 (semi-active 2018803 / round 2018804, and IIR 2018866 / 2018867; both already show the Spike LR launcher icon) had
# LowAltRange 0 and TargetType 36 (no helicopters). Its own copies get LowAltRange 1300 and TargetType 44, the target set of the ZBD-251's
# HJ-16 (round 2014656: 44, low alt 1000). Card ranges are table x 2 (the unit card shows 2x GroundRange), so Osama's 1300 m is
# LowAltRange 650 (corrected 00:3x; first written as 1300 = 2600 m on the card). Ammo rows are per unit, so only the ZBD-20 (945) and its hidden Recon copy (1256) move to the
# copies; the ZBL-191 (same missile) keeps ground-only HJ-16s.
A=t['AmmunitionsJson']
ok(all(A[i]['LowAltRange']==0 and A[i]['TargetType']==36 for i in (2018804,2018867)) and A[2014656]['TargetType']==44 and A[2014656]['LowAltRange']==1000,'HJ-16 rounds ground-only (36), ZBD-251 HJ-16 44 / 1000')
_hj={}
for i in (2018804,2018867):_hj[i]=g.add('AmmunitionsJson',A[i],{'Name':A[i]['Name']+' ZBD-20 AA','LowAltRange':650.0,'TargetType':44})
_hr=[r for r in WA.values() if r['AmmunitionId'] in _hj and r['UnitId'] in (945,1256)]
ok(len(_hr)==4,f'ZBD-20 and Recon each carry both HJ-16 rounds ({len(_hr)})')
for r in _hr:g.put('WeaponAmmunitionsJson',r['Id'],{'AmmunitionId':_hj[r['AmmunitionId']]})
ok(sorted({U[r['UnitId']]['HUDName'] for r in WA.values() if r['AmmunitionId'] in (2018804,2018867)})==['ZBL-191'],'ZBL-191 keeps the ground-only HJ-16')
rec['zbd20_hj16_air']={'units':[945,1256],'rounds':{str(k):v for k,v in _hj.items()},'LowAltRange':[0,650],'card_m':1300,'TargetType':[36,44]}
# ---------- ZTZ-96B APFSDS 500-525 and 220 points (Osama 16 Nov 2026 00:13 PST: "ZTZ-96B gun penetration 500-525 and up to 220").
# Its 125 mm APFSDS (round 2009103, only on the ZTZ-96B 905): penetration 425 at max range / 450 close -> 500 / 525. HE, HEAT and the GP125
# missile unchanged. "up to 220" read as the price: 170 -> 220 (no loadouts or swap rows).
ok(U[905]['HUDName']=='ZTZ-96B' and U[905]['Cost']==170 and A[2009103]['PenetrationAtGroundRange']==425 and A[2009103]['PenetrationAtMinRange']==450,'ZTZ-96B 170, APFSDS 425/450')
ok({r['UnitId'] for r in WA.values() if r['AmmunitionId']==2009103}=={905} and not [o for o in O.values() if o.get('ReplaceUnitId')==905] and not [m for m in M.values() if m['UnitId']==905],'APFSDS only on 905, no loadouts or swap rows')
g.put('AmmunitionsJson',2009103,{'PenetrationAtGroundRange':500.0,'PenetrationAtMinRange':525.0});g.put('Units',905,{'Cost':220})
rec['ztz96b']={'unit':905,'apfsds':2009103,'penetration':[[425,450],[500,525]],'cost':[170,220]}
# ---------- 105 mm APFSDS 450-500 on ZTQ-15s, ZTL-191s and VT-5s (Osama 16 Nov 2026 00:18 PST: "ZTQ-15s, ZTL-191, VT-5 (all variants) 450mm to
# 500mm penetration"). Read like his "500-525": 450 at max range, 500 close. Rounds: 2009131 (ZTQ-15, ZTQ-15 Recon, ZTQ-15 Light, VT-5 1261,
# VT-5 Recon 1262; was 475/525), 2011301 (ZTL-191, ZTL-191 Recon; 475/525), 2009967 (hidden VT-5 953; 325/520).
_r105={2009131:(475,525),2011301:(475,525),2009967:(325,520)}
ok(all(A[i]['PenetrationAtGroundRange']==g0 and A[i]['PenetrationAtMinRange']==m0 for i,(g0,m0) in _r105.items()),'105 mm APFSDS rounds as in dev.13')
_u105=sorted({U[r['UnitId']]['HUDName'] for r in WA.values() if r['AmmunitionId'] in _r105})
ok(_u105==['VT-5','VT-5 Recon','ZTL-191','ZTL-191 Recon','ZTQ-15','ZTQ-15 Light','ZTQ-15 Recon'],f'105 mm APFSDS users {_u105}')
for i in _r105:g.put('AmmunitionsJson',i,{'PenetrationAtGroundRange':450.0,'PenetrationAtMinRange':500.0})
rec['apfsds_105']={'rounds':{str(k):[list(v),[450,500]] for k,v in _r105.items()},'units':_u105}
# ---------- ZTZ-99A: 850 KE front, APFSDS 500-550 (Osama 00:18: "ZTZ-99A 850 KE front, 500-550 penetration on the main gun's sabot"). Unit 904
# only (own armour 2009063, own round 2009075); the hidden ZTZ-99A2 939 unchanged.
ok(U[904]['HUDName']=='ZTZ-99A' and [r['ArmorId'] for r in UAR.values() if r['UnitId']==904]==[2009063] and sorted(r['UnitId'] for r in UAR.values() if r['ArmorId']==2009063)==[904] and AR[2009063]['KinArmorFront']==800,'ZTZ-99A own armour, KE front 800')
ok({r['UnitId'] for r in WA.values() if r['AmmunitionId']==2009075}=={904} and A[2009075]['PenetrationAtGroundRange']==500 and A[2009075]['PenetrationAtMinRange']==525,'ZTZ-99A APFSDS 500/525, only on 904')
g.put('ArmorsJson',2009063,{'KinArmorFront':850});g.put('AmmunitionsJson',2009075,{'PenetrationAtMinRange':550.0})
rec['ztz99a']={'unit':904,'ke_front':[800,850],'apfsds':[[500,525],[500,550]]}
# ---------- ZBD-20 jammer option +20, 30% ECM (Osama 00:18: "ZBD-20 protective loadout option +20 points for 30% ecm jammer"). Its protection
# slot (None 31065 / GL-5 APS 31066 +40) gains the ZBL-191's jammer option (31080: ANVLQ6 jammer, ECM Hardhat ability 80 = 0.7 = 30%), with the
# ZBD-20's own base ability; one of the three, as on the ZBL-191.
_pz=[o for o in O.values() if o['ModificationId']==O[31065]['ModificationId']]
ok(sorted(o['Id'] for o in _pz)==[31065,31066] and M[O[31065]['ModificationId']]['UnitId']==945 and O[31080]['Cost']==20 and O[31080]['Ability2Id']==80 and AB[80]['ECMAccuracyMultiplier']==0.7,'ZBD-20 protection None/APS; ZBL-191 jammer +20 at 30%')
_jz=g.add('OptionsJson',O[31080],{'ModificationId':O[31065]['ModificationId'],'Ability1Id':O[31065]['Ability1Id'],'IsDefault':False,'Order':1})
# Every option ability needs a (unit, ability) link (audit_mp_equipment; vanilla pattern): a non-default ZBD-20 -> ECM Hardhat 80 row.
ok(not AB[80]['IsDefault'] and not [r for r in UAB.values() if r['UnitId']==945 and r['AbilityId']==80],'ZBD-20 has no ECM Hardhat link yet');g.add('UnitAbilitiesJson',{'UnitId':945,'AbilityId':80})
g.put('OptionsJson',31066,{'Order':2})
ok(sorted((o['UIName'],o['Cost']) for o in O.values() if o['ModificationId']==O[31065]['ModificationId'])==[('Custom_Option_ANVLQ6_jammer',20),('Custom_Option_None',0),('GL-5 APS',40)],'ZBD-20 protection: None / jammer +20 / GL-5 APS +40')
rec['zbd20_jammer']={'option':_jz,'copied_from':31080,'cost':20,'ecm':0.3}
# ---------- Mountain Leopards: 3 HJ-12s again (Osama 00:20: "Mountain lions should have 3 HJ-12's"). dev.12 left one carrier with 2 missiles;
# all three men carry the HJ-12 again (as before dev.12), 1 missile each = 3 HJ-12s. To confirm: 1 or 2 missiles per man.
SM=t['SquadMembersJson'];_ml=sorted((m for m in SM.values() if m['UnitId']==1186),key=lambda m:m['Id'])
ok(U[1186]['HUDName'].startswith('Mountain Leopards') and [m['SpecialWeaponId'] for m in _ml]==[0,2011864,0],'Mountain Leopards: one HJ-12 carrier (dev.12)')
_mq=[r for r in WA.values() if r['UnitId']==1186 and r['WeaponId']==2011864];ok(len(_mq)==1 and _mq[0]['Quantity']==2,'2 missiles')
for m in (_ml[0],_ml[2]):g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':2011864})
g.put('WeaponAmmunitionsJson',_mq[0]['Id'],{'Quantity':1})
rec['mountain_leopards_hj12']={'unit':1186,'launchers':[1,3],'missiles_per_man':[2,1]}
# ---------- Marine Recon: 4 PF-89, 45 points (Osama 00:20: "Marine recon give 4 PF-89 and 45 points"). Unit 1224 (4 men: two QTS-11 with the
# QTS-11 grenade launcher as their special weapon, a QBU-191 and a QBZ-191). A soldier has one special weapon, so the QBU-191 and QBZ-191 men carry
# the PF-89 (weapon 2011887, round 2011888) with 2 each = 4. Cost 35 -> 45.
SWJ=t['SquadWeaponsJson']
_mr=sorted((m for m in SM.values() if m['UnitId']==1224),key=lambda m:m['Id'])
ok(U[1224]['HUDName']=='Marine Recon' and U[1224]['Cost']==35 and [m['SpecialWeaponId'] for m in _mr]==[2019270,2019270,0,0] and not [o for o in O.values() if o.get('ReplaceUnitId')==1224] and not [x for x in M.values() if x['UnitId']==1224],'Marine Recon 35, 2 GL + 2 free special slots')
_pt=next(r for r in WA.values() if r['WeaponId']==2011887 and U[r['UnitId']]['HUDName'].startswith('Marines'));_ps=next(r for r in SWJ.values() if r['WeaponId']==2011887 and r['UnitId']==_pt['UnitId'])
for m in _mr[2:]:g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':2011887})
g.add('WeaponAmmunitionsJson',_pt,{'UnitId':1224,'Quantity':2});g.add('SquadWeaponsJson',_ps,{'UnitId':1224});g.put('Units',1224,{'Cost':45})
ok(sum(1 for m in SM.values() if m['UnitId']==1224 and m['SpecialWeaponId']==2011887)==2 and [r['Quantity'] for r in WA.values() if r['UnitId']==1224 and r['WeaponId']==2011887]==[2],'Marine Recon: 2 men x 2 PF-89')
rec['marine_recon']={'unit':1224,'pf89':{'carriers':2,'per_man':2,'total':4},'cost':[35,45]}
# ---------- ZBD-251 GL-5 APS +60 -> +40 (Osama 16 Nov 2026 00:25 PST: "ZBD-251 should be +40", after the IFV APS price list: every other
# China/Russia/US IFV APS option is +40). Option 31044 on unit 1056.
ok(U[1056]['HUDName']=='ZBD-251' and O[31044]['UIName']=='GL-5 APS' and O[31044]['Cost']==60 and M[O[31044]['ModificationId']]['UnitId']==1056,'ZBD-251 GL-5 APS +60')
g.put('OptionsJson',31044,{'Cost':40});rec['zbd251_aps']={'option':31044,'cost':[60,40]}
# ---------- Airborne: QJY-201 instead of QJS-161 (Osama 16 Nov 2026 00:28 PST: "Give Airborne QJY-201 instead of QJS-161"). Airborne 空降兵
# (1136) is the only Airborne card with the QJS-161: its two gunners (members 2014856, 2014857) take the QJY-201 (weapon 2012411, round
# 2012412, 400 rounds as on every QJY-201 squad). Ammo and squad-weapon rows move with them. Neither gun has an FA model entry.
_qs,_qy=2011922,2012411
_am=[m for m in SM.values() if m['UnitId']==1136 and _qs in (m['PrimaryWeaponId'],m['SpecialWeaponId'])]
_aw=[r for r in WA.values() if r['UnitId']==1136 and r['WeaponId']==_qs];_as=[r for r in SWJ.values() if r['UnitId']==1136 and r['WeaponId']==_qs]
ok(U[1136]['HUDName'].startswith('Airborne') and sorted(m['Id'] for m in _am)==[2014856,2014857] and all(m['PrimaryWeaponId']==_qs for m in _am) and len(_aw)==1 and _aw[0]['Quantity']==400 and len(_as)==1,'Airborne 1136: two QJS-161 gunners, 400 rounds')
ok({(r['AmmunitionId'],r['Quantity']) for r in WA.values() if r['WeaponId']==_qy}=={(2012412,400)},'QJY-201 round 2012412, 400 rounds')
for m in _am:g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':_qy})
g.put('WeaponAmmunitionsJson',_aw[0]['Id'],{'WeaponId':_qy,'AmmunitionId':2012412});g.put('SquadWeaponsJson',_as[0]['Id'],{'WeaponId':_qy})
ok(not [m for m in SM.values() if m['UnitId']==1136 and _qs in (m['PrimaryWeaponId'],m['SpecialWeaponId'])],'no QJS-161 left in Airborne')
rec['airborne_qjy201']={'unit':1136,'gunners':2,'from':_qs,'to':_qy,'dpm_per_gunner':[74,52]}
# ---------- VT-5 base 140 -> 160 (Osama 16 Nov 2026 00:30 PST: "VT-5 base to 160"). The armory VT-5 is 1261; the hidden copies (953 at 55,
# VT-5 Recon 1262 at 220) are not in any deck list and stay. Its loadout prices (None / GL-5 APS +60) are unchanged.
ok(U[1261]['HUDName']=='VT-5' and U[1261]['Cost']==140 and U[1261]['DisplayInArmory'] and not U[953]['DisplayInArmory'] and not U[1262]['DisplayInArmory'] and not [o for o in O.values() if o.get('ReplaceUnitId')==1261],'VT-5 1261 at 140 in the armory, no swap rows')
g.put('Units',1261,{'Cost':160});rec['vt5_cost']={'unit':1261,'cost':[140,160]}
# ---------- VT-5 availability 4 (Osama 00:31: "VT-5 availability to 4"). Its two cards: spec 21 already 4 (row 2018649), spec 20 6 -> 4 (row 2018650).
SAJ=t['SpecializationAvailabilitiesJson']
ok(sorted((r['SpecializationId'],r['MaxAvailabilityXp0']) for r in SAJ.values() if r['UnitId']==1261)==[(20,6),(21,4)] and SAJ[2018650]['SpecializationId']==20,'VT-5 cards: spec 20 at 6, spec 21 at 4')
g.put('SpecializationAvailabilitiesJson',2018650,{'MaxAvailabilityXp0':4});rec['vt5_availability']={'unit':1261,'spec20':[6,4],'spec21':[4,4]}
# ---------- ZTQ-15 Light 120 -> 140 points (Osama 16 Nov 2026 00:3x PST: "ZTQ-15 light to 140 points"). Unit 1268 (PLAAF airborne copy).
ok(U[1268]['HUDName']=='ZTQ-15 Light' and U[1268]['Cost']==120 and not [o for o in O.values() if o.get('ReplaceUnitId')==1268],'ZTQ-15 Light 1268 at 120')
g.put('Units',1268,{'Cost':140});rec['ztq15_light_cost']={'unit':1268,'cost':[120,140]}
# ---------- ZTQ-15 LG3 AGL 1000 m and its 12.7 mm back (Osama 16 Nov 2026 00:34 PST: "For the ZTQ-15's LG3 AGL, make it 1000m range. ONLY The GL
# on the ZTQ, and it gets its 50 cal machine gun back. The commander's turret has a 50 cal and GL"). dev.102 replaced the roof QJC-88 12.7 mm
# with the LG3 on its own mount 2018997 (ZTQ-15 906, Recon 1240, Light 1268 only). Range: the LG3 round 2018996 (only on those three)
# GroundRange 400 -> 500 = 1000 m on the card (card = table x 2). 12.7 mm: the QJC-88 (weapon 2009141, round 2009145, 100 rounds as before
# dev.102). Not on the LG3 mount: it has no model, and a model-less mount on this body (US_M10) carries at most 1 weapon in vanilla; more
# weapons than the model's slots freeze the match at spawn (check_mount_weapons). It goes on mount 1 (model RU_BTR82AT, up to 3 weapons in
# vanilla, now the Type 86 7.62 mm only). Mount 1 (2009136) is shared with the VT-5 and VT-5 Recon, so the three ZTQ-15s get their own copy.
_lgu=sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==2018996})
ok(_lgu==[906,1240,1268] and A[2018996]['GroundRange']==400 and sorted(r['UnitId'] for r in TU.values() if r['TurretId']==2018997)==[906,1240,1268],'LG3 round and mount only on the three ZTQ-15s, range 400')
ok([(r['WeaponId'],r['Order']) for r in TW.values() if r['TurretId']==2018997]==[(2018995,2)] and W[2009141]['HUDName']=='QJC-88 12.7 mm' and A[2009145]['GroundRange']==400,'LG3 alone on its mount; QJC-88 donor rows')
ok([(W[r['WeaponId']]['HUDName'],r['Order']) for r in TW.values() if r['TurretId']==2009136]==[('Type 86 7.62 mm',1)] and TJ[2009136]['ModelFileName']=='RU_BTR82/RU_BTR82AT' and sorted(r['UnitId'] for r in TU.values() if r['TurretId']==2009136)==[906,1240,1261,1262,1268],'mount 1: 7.62 mm only, shared with VT-5s')
_m1=g.add('TurretsJson',TJ[2009136],{'Name':'PLA ZTQ-15 mount 1 12.7 mm'})
for _r in [r for r in TW.values() if r['TurretId']==2009136]:g.add('TurretWeaponsJson',_r,{'TurretId':_m1})
_mgt=next(r for r in TW.values() if r['WeaponId']==2009141)
g.add('TurretWeaponsJson',_mgt,{'TurretId':_m1,'WeaponId':2009141,'Order':2,'WeaponPriority':2})
_mga=next(r for r in WA.values() if r['WeaponId']==2009141 and r['AmmunitionId']==2009145)
for _u in (906,1240,1268):
    _tu=[r for r in TU.values() if r['UnitId']==_u and r['TurretId']==2009136];ok(len(_tu)==1,(_u,'one mount 1 row'));g.put('TurretUnitsJson',_tu[0]['Id'],{'TurretId':_m1})
    ok(not [r for r in WA.values() if r['UnitId']==_u and r['WeaponId']==2009141],(_u,'no 12.7 mm yet'));g.add('WeaponAmmunitionsJson',_mga,{'UnitId':_u,'Quantity':100})
g.put('AmmunitionsJson',2018996,{'GroundRange':500.0})
ok(sorted(W[r['WeaponId']]['HUDName'] for r in TW.values() if r['TurretId']==_m1)==['QJC-88 12.7 mm','Type 86 7.62 mm'] and [W[r['WeaponId']]['HUDName'] for r in TW.values() if r['TurretId']==2018997]==['LG3 40 mm AGL'],'ZTQ-15: LG3 alone on mount 2, QJC-88 on its own mount 1 copy')
rec['ztq15_roof']={'units':[906,1240,1268],'lg3_ground_range':[400,500],'lg3_card_m':[800,1000],'qjc88':{'weapon':2009141,'round':2009145,'rounds':100,'mount':_m1}}
# ---------- Z-19 940: no cargo (Osama 16 Nov 2026 00:35 PST: "Z-19 remove the cargo capacity"). The other Z-19s (1103, Recon 1132/1134, Z-19G
# 1236/1237) already use mobility 2018990 "PLA Heli Z-19 no cargo" (the AS365 row with HeavyLiftWeight 0); Z-19 940 was still on the shared
# vanilla AS365 row 258 (1500 supply), which the AS-365 Dauphin and Z-9WA keep. 940 moves to 2018990. No infantry seats on any Z-19.
UP=t['UnitPropulsionsJson'];MJ=t['MobilityJson']
_zp=[r for r in UP.values() if r['UnitId']==940]
ok(U[940]['HUDName']=='Z-19' and [r['MobilityId'] for r in _zp]==[258] and MJ[258]['HeavyLiftWeight']==1500 and MJ[2018990]['HeavyLiftWeight']==0 and {k for k in MJ[258] if MJ[258][k]!=MJ[2018990].get(k)}=={'Id','Name','HeavyLiftWeight'},'Z-19 940 on AS365 258; 2018990 = 258 without cargo')
ok(not [o for x in M.values() if x['UnitId']==940 for o in O.values() if o['ModificationId']==x['Id'] and o.get('MobilityId')],'no Z-19 940 option sets mobility')
g.put('UnitPropulsionsJson',_zp[0]['Id'],{'MobilityId':2018990})
ok(all(MJ[r['MobilityId']]['HeavyLiftWeight']==0 for r in UP.values() if str(U.get(r['UnitId'],{}).get('HUDName','')).startswith('Z-19')),'every Z-19 without cargo')
rec['z19_cargo']={'unit':940,'mobility':[258,2018990],'supply':[1500,0]}
# ---------- Z-19 escort loadout: 8x TY-90 + 14x FS-90 (Osama 16 Nov 2026 00:4x PST: "Z-19 needs an escort loadout that's 8x TY-90 and 14 FS-90").
# The three armed Z-19s (940, 1103, Z-19G 1236) share one weapon slot layout: Turret0 = rocket pylon (FS-70A x14 2018829 / 90 mm), Turret1 = a
# 2-pylon missile mount (Heavy anti-armor uses the TY-90 x4 mount 2019145, 8 rounds). New: an FS-90 x14 rocket pylon (copy of 2018829 with its
# own weapon: the FS-70A x14 weapon 2018822 with the FS-90 name and bursts of the Z-21 FS-90 weapon 2018820, MagazineSize 14, round 2018819)
# and option "Escort (8x TY-90, 14x FS-90)" = FS-90 x14 + TY-90 x4 mount, 75 points like the Z-21 Air escort (price to confirm).
_zs=(940,1103,1236);_zo={940:24521,1103:24525,1236:24529}
ok(all(O[i]['UIName']=='Heavy anti-armor' and O[i]['Turret0Id']==2017249 and O[i]['Turret1Id']==2019145 and M[O[i]['ModificationId']]['UnitId']==u for u,i in _zo.items()),'Z-19 Heavy anti-armor options on TY-90 x4 mount')
ok(sorted(r['UnitId'] for r in TU.values() if r['TurretId']==2018829)==list(_zs) and [x['WeaponId'] for x in TW.values() if x['TurretId']==2018829]==[2018822],'FS-70A x14 pylon on the three Z-19s')
ok(all([r['Quantity'] for r in WA.values() if r['UnitId']==u and r['WeaponId']==2019141]==[8] for u in _zs),'TY-90 x4 mount: 8 rounds on each Z-19')
_fw=g.add('WeaponsJson',W[2018822],{'Name':'PLA air FS-90 x14','HUDName':'FS-90','MagazineSize':14,'ShotsPerBurstMin':W[2018820]['ShotsPerBurstMin'],'ShotsPerBurstMax':W[2018820]['ShotsPerBurstMax']})
_ft=g.add('TurretsJson',TJ[2018829],{'Name':'PLA air pylon FS-90 x14'})
g.add('TurretWeaponsJson',next(x for x in TW.values() if x['TurretId']==2018829),{'TurretId':_ft,'WeaponId':_fw})
_fwa=next(r for r in WA.values() if r['WeaponId']==2018822)
for u in _zs:
    g.add('TurretUnitsJson',next(r for r in TU.values() if r['UnitId']==u and r['TurretId']==2018829),{'TurretId':_ft})
    g.add('WeaponAmmunitionsJson',_fwa,{'UnitId':u,'WeaponId':_fw,'AmmunitionId':2018819,'Quantity':14})
    g.add('OptionsJson',O[_zo[u]],{'UIName':'Escort (8x TY-90, 14x FS-90)','Name':f'Z-19 {u} escort TY-90 FS-90','Cost':75,'IsDefault':False,'Turret0Id':_ft,'Turret1Id':2019145,'Order':9})
ok(all(len([o for o in O.values() if o['ModificationId']==O[_zo[u]]['ModificationId']])==4 for u in _zs),'each Z-19 slot: 4 loadouts')
rec['z19_escort']={'units':list(_zs),'weapon':_fw,'pylon':_ft,'loadout':'8x TY-90, 14x FS-90','cost':75}
# ---------- New China units and PLARF cards (Osama 16 Nov 2026 01:1x PST: "load it for me, those new chinese tanks go to PLARF and remove the
# ZTZ-96 from there", "HHQ-10 to PLAN, no guns, its just the SEARIM", VN20 "make it slow like 65 foward speed and 30 reverse"; earlier 00:5x-01:0x:
# "VN20 goes to VEH tab in armored and carries 14 troops. Availability 2, 250 points", "it is the T-15 clone but a BMP-3 turret (no atgm in the
# 100mm) and 2x HJ-12, it comes with Jammer", "HHQ-10 ... CRAM with the RIM-116 except it has 18 missiles making it 220 points", "remove PHL-191
# Cruise", WZ1224 "give it a good estimated value"). Models: work/pla-0.9/dev14/<model> (purchased ShuyangXi packs), models.json by unit Name.
# Built-in abilities: one default ability row per unit (LoadAbility keeps only the first default; sp-mp guard), turrets IsDefault on units
# without options (vanilla: 229 of 243). New tracked mobility follows the road rule road = 1.6 x off-road (0.8.0-dev.61).
AM=t['AmmunitionsJson'];MOB=t['MobilityJson'];AR=t['ArmorsJson'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson']
def _rows(tab,**kw):return [r for r in t[tab].values() if all(r.get(k)==v for k,v in kw.items())]
def _base(parent,name,hud,extra):
    ok(not any(u.get('Name')==name for u in U.values()),(name,'name free'))
    d=dict(U[parent]);d.pop('Id');d.update({'Name':name,'HUDName':hud,'CountryId':4,'DisplayInArmory':True,'OriginalName':None,'Description':None},**extra)
    uid=g.put('Units',max(U)+1,d)
    for r in _rows('SensorUnitsJson',UnitId=parent):g.add('SensorUnitsJson',r,{'UnitId':uid})
    return uid
def _armor(src_unit,uid,name,fields):
    s=[r for r in _rows('UnitArmorsJson',UnitId=src_unit) if AR[r['ArmorId']]['IsDefault']];ok(len(s)==1,(src_unit,'one default armour'))
    a=g.add('ArmorsJson',AR[s[0]['ArmorId']],{'Name':name,**fields});g.add('UnitArmorsJson',s[0],{'UnitId':uid,'ArmorId':a});return a
def _mob(src_unit,uid,name,fields):
    s=_rows('UnitPropulsionsJson',UnitId=src_unit);ok(len(s)==1,(src_unit,'one mobility'))
    m=g.add('MobilityJson',MOB[s[0]['MobilityId']],{'Name':name,**fields});g.add('UnitPropulsionsJson',s[0],{'UnitId':uid,'MobilityId':m});return m
def _turret(src_tid,uid,name,weapons):   # weapons: [(weapon id, Order, WeaponPriority)]
    tid=g.add('TurretsJson',TJ[src_tid],{'Name':name,'IsDefault':True});tw0=next(x for x in TW.values() if x['TurretId']==src_tid)
    for w,o,p in weapons:g.add('TurretWeaponsJson',tw0,{'TurretId':tid,'WeaponId':w,'Order':o,'WeaponChannel':0,'WeaponPriority':p})
    g.add('TurretUnitsJson',{'UnitId':uid,'TurretId':tid,'Order':0});return tid
def _ammo(uid,w,am,q):g.add('WeaponAmmunitionsJson',{'UnitId':uid,'WeaponId':w,'AmmunitionId':am,'Quantity':q,'Order':0})
# PHL-191 Cruise off the deck: its one card (PLARF 2018956). The unit row stays (hidden from every spec) like earlier removals.
ok(U[1267]['HUDName']=='PHL-191 Cruise' and [r['Id'] for r in _rows('SpecializationAvailabilitiesJson',UnitId=1267)]==[2018956] and not [r for r in TA.values() if r.get('UnitId')==1267 or r.get('SpecializationAvailabilityId')==2018956],'PHL-191 Cruise: one PLARF card, no transports')
g.remove('SpecializationAvailabilitiesJson',2018956);assign['assignments'].pop('1267',None)
# ZTZ-96 out of PLARF: its only card (2008240, 6 cards).
ok(U[949]['HUDName']=='ZTZ-96' and [r['Id'] for r in _rows('SpecializationAvailabilitiesJson',UnitId=949)]==[2008240] and SA[2008240]['SpecializationId']==19 and not [r for r in TA.values() if r.get('SpecializationAvailabilityId')==2008240],'ZTZ-96: one PLARF card')
g.remove('SpecializationAvailabilitiesJson',2008240);assign['assignments'].pop('949',None)
rec['removed_cards']={'PHL-191 Cruise 1267':2018956,'ZTZ-96 949 (PLARF)':2008240}
# WZ1224 (PLARF, 4 cards, 95): 1978-79 prototype, 120 mm smoothbore (Rh-120 copy, ~1700 m/s; goal: T-72 front at 2 km), 45 t, ~1000 hp, 65 km/h
# design target, welded steel turret with a composite front insert. Sources: en.wikipedia.org/wiki/WZ-122_main_battle_tank,
# forum.warthunder.com/t/wz1224/105028. Estimated, not tested: between ZTZ-96 (80, KE 550, APFSDS 350/325) and ZTZ-96A (105, KE 600,
# 425/400). Built on the ZTZ-96 (949): own armour KE 500/100/100/60, HEAT 650/200/100/60, 14 HP; own mobility 65 road / 41 off-road; own
# 120 mm weapon and APFSDS 450 close / 425 at max range; the 125 mm HEAT/HE rounds and both machine guns as on the ZTZ-96.
ok(not _rows('ModificationsJson',UnitId=949) and len(_rows('TurretUnitsJson',UnitId=949))==2,'ZTZ-96 has no options, 2 mounts')
wz=_base(949,'PLA WZ1224','WZ1224',{'Cost':95,'Weight':45000})
_armor(949,wz,'PLA WZ1224 ArmorsJson',{'KinArmorFront':500,'KinArmorSides':100,'KinArmorRear':100,'KinArmorTop':60,'HeatArmorFront':650,'HeatArmorSides':200,'HeatArmorRear':100,'HeatArmorTop':60,'MaxHealthPoints':14})
_mob(949,wz,'PLA WZ1224 MobilityJson',{'MaxSpeedRoad':65.0,'MaxCrossCountrySpeed':41.0})
for r in _rows('UnitAbilitiesJson',UnitId=949):g.add('UnitAbilitiesJson',r,{'UnitId':wz})
_mg=None
for tu in sorted(_rows('TurretUnitsJson',UnitId=949),key=lambda r:r['Order']):
    tws=[x for x in TW.values() if x['TurretId']==tu['TurretId']]
    gun=[x for x in tws if W[x['WeaponId']]['HUDName']=='125 mm tank gun']
    if not gun:g.add('TurretUnitsJson',tu,{'UnitId':wz});continue
    ok(len(gun)==1,'one 125 mm gun on its mount');gw=gun[0]['WeaponId']
    nw=g.add('WeaponsJson',W[gw],{'Name':'PLA WZ1224 120 mm smoothbore','HUDName':'120 mm smoothbore'})
    nt=g.add('TurretsJson',TJ[tu['TurretId']],{'Name':'PLA WZ1224 mount 0'})
    for x in tws:g.add('TurretWeaponsJson',x,{'TurretId':nt,'WeaponId':nw if x['WeaponId']==gw else x['WeaponId']})
    g.add('TurretUnitsJson',tu,{'UnitId':wz,'TurretId':nt});_mg=(gw,nw)
for r in _rows('WeaponAmmunitionsJson',UnitId=949):
    if r['WeaponId']!=_mg[0]:g.add('WeaponAmmunitionsJson',r,{'UnitId':wz});continue
    x=AM[r['AmmunitionId']];f={}
    if x['HUDName']=='125 mm tank gun APFSDS':
        ok((x['PenetrationAtMinRange'],x['PenetrationAtGroundRange'])==(350.0,325.0),'ZTZ-96 APFSDS 350/325')
        f={'AmmunitionId':g.add('AmmunitionsJson',x,{'Name':'PLA WZ1224 120 mm APFSDS','HUDName':'120 mm APFSDS','PenetrationAtMinRange':450.0,'PenetrationAtGroundRange':425.0})}
    g.add('WeaponAmmunitionsJson',r,{'UnitId':wz,'WeaponId':_mg[1],**f})
g.add('SpecializationAvailabilitiesJson',{'SpecializationId':19,'UnitId':wz,'MaxAvailabilityXp0':4,'MaxAvailabilityXp1':0,'MaxAvailabilityXp2':0,'MaxAvailabilityXp3':0});assign['assignments'][str(wz)]=[19]
_wa=[AM[r['AmmunitionId']]['HUDName'] for r in _rows('WeaponAmmunitionsJson',UnitId=wz)]
ok('120 mm APFSDS' in _wa and '125 mm tank gun APFSDS' not in _wa and len(_wa)==len(_rows('WeaponAmmunitionsJson',UnitId=949)),('WZ1224 ammo',_wa))
rec['wz1224']={'unit':wz,'spec':19,'cards':4,'cost':95,'KE':[500,100,100,60],'HEAT':[650,200,100,60],'hp':14,'speed':[65,41],'apfsds':[450,425],'basis':'estimate from WZ-1224 history; not tested'}
# HHQ-10 (PLAN SF spec 20, 220): the Centurion C-RAM (250) truck with only the SeaRAM launcher (turret 998, RIM-116 round 560), 18 missiles
# in one magazine (own weapon copy, MagazineSize 11 -> 18) and an own round named HHQ-10 (same stats as RIM-116). No gun. 2 cards (not given).
ok(U[250]['HUDName']=='Centurion C-RAM' and [x['WeaponId'] for x in TW.values() if x['TurretId']==998]==[732] and W[732]['MagazineSize']==11,'Centurion SeaRAM turret 998 = RIM-116 x11')
hq=_base(250,'PLA HHQ-10','HHQ-10',{'Cost':220})
_armor(250,hq,'PLA HHQ-10 ArmorsJson',{});_mob(250,hq,'PLA HHQ-10 MobilityJson',{})
for r in _rows('UnitAbilitiesJson',UnitId=250):g.add('UnitAbilitiesJson',r,{'UnitId':hq})
_hw=g.add('WeaponsJson',W[732],{'Name':'PLA HHQ-10 x18','HUDName':'HHQ-10','MagazineSize':18})
_hm=g.add('AmmunitionsJson',AM[560],{'Name':'PLA HHQ-10 missile','HUDName':'HHQ-10'})
_turret(998,hq,'PLA HHQ-10 launcher',[(_hw,0,0)]);_ammo(hq,_hw,_hm,18)
g.add('SpecializationAvailabilitiesJson',{'SpecializationId':20,'UnitId':hq,'MaxAvailabilityXp0':2,'MaxAvailabilityXp1':0,'MaxAvailabilityXp2':0,'MaxAvailabilityXp3':0});assign['assignments'][str(hq)]=[20]
ok([W[x['WeaponId']]['HUDName'] for r in _rows('TurretUnitsJson',UnitId=hq) for x in TW.values() if x['TurretId']==r['TurretId']]==['HHQ-10'],'HHQ-10: launcher only')
rec['hhq10']={'unit':hq,'spec':20,'cards':2,'cost':220,'missiles':18,'from':'Centurion C-RAM 250 SeaRAM turret, no gun'}
# VN20 (PLAGF Armored spec 18, VEH tab, 2 cards, 250, 14 men): T-15 (255) hull, armour and sensors; BMP-3 turret weapons 2A70 100 mm with the
# HE round only (3UOF19, no Arkan ATGM) + 2A72 30 mm AP/HE + PKT, plus 2x HJ-12 (Mountain Leopards' weapon 2011864 / round 2011865, top
# attack); on a copy of the T-15 turret 471 (no PKT, see below). Mobility 65 road / 41 off-road (road rule) / 30 reverse. One built-in ability: a copy of the
# T-15 profile 2000215 (smoke) with 30% jammer (ECM 0.7 like ECM Hardhat 80) and no APS (APSQuantity 0; the T-15's 2-shot Afghanit APS).
ok(AB[2000215]['APSQuantity']==2 and AB[80]['ECMAccuracyMultiplier']==0.7 and [r['AbilityId'] for r in _rows('UnitAbilitiesJson',UnitId=255)]==[2000215],'T-15 one built-in profile with APS 2')
ok([(x['WeaponId'],W[x['WeaponId']]['HUDName']) for x in TW.values() if x['TurretId']==6]==[(6,'2А70 100 mm'),(7,'PKT'),(294,'2А72 30mm')],'BMP-3 base turret weapons')
ok(AM[7]['HUDName']=='100mm 3UOF19' and (AM[3]['HUDName'],AM[177]['HUDName'],AM[9]['HUDName'])==('30x165mm AP','30x165mm HE','7.62x54mm') and AM[2011865]['IsTopArmorArmorAttack'],'VN20 rounds')
vn=_base(255,'PLA VN20','VN20',{'Cost':250,'InfantrySlots':14,'CategoryType':2})
_armor(255,vn,'PLA VN20 ArmorsJson',{});_mob(255,vn,'PLA VN20 MobilityJson',{'MaxSpeedRoad':65.0,'MaxCrossCountrySpeed':41.0,'MaxSpeedReverse':30.0})
_va=g.add('AbilitiesJson',AB[2000215],{'Name':'PLA VN20 smoke + jammer','APSQuantity':0,'ECMAccuracyMultiplier':0.7,'IsDefault':True})
g.add('UnitAbilitiesJson',{'UnitId':vn,'AbilityId':_va})
# The T-15 body allows 3 weapons on its turret (vanilla max; check_slot_weapons), so the PKT is left off: 30 mm, 100 mm, HJ-12.
_turret(471,vn,'PLA VN20 turret',[(294,0,0),(6,1,1),(2011864,2,2)])
for w,am,q in ((294,3,70),(294,177,100),(6,7,40),(2011864,2011865,2)):_ammo(vn,w,am,q)
g.add('SpecializationAvailabilitiesJson',{'SpecializationId':18,'UnitId':vn,'MaxAvailabilityXp0':2,'MaxAvailabilityXp1':0,'MaxAvailabilityXp2':0,'MaxAvailabilityXp3':0});assign['assignments'][str(vn)]=[18]
ok(sorted(AM[r['AmmunitionId']]['HUDName'] for r in _rows('WeaponAmmunitionsJson',UnitId=vn))==sorted(['30x165mm AP','30x165mm HE','100mm 3UOF19','HJ-12 ammunition']),'VN20 ammo: no Arkan')
rec['vn20']={'unit':vn,'spec':18,'cards':2,'cost':250,'troops':14,'speed':{'road':65,'offroad':41,'reverse':30},'ability':{'id':_va,'smoke':True,'ecm':0.3,'aps':0},'weapons':['2A72 30 mm','2A70 100 mm HE only','HJ-12 x2']}
for u in (wz,hq,vn):ok(len([r for r in UAB.values() if r['UnitId']==u and AB[r['AbilityId']]['IsDefault']])<=1,(u,'at most one default ability'))
# ---------- MD-22 Light strike +20 (Osama 16 Nov 2026 01:2x PST: "MD-22 Light strike should be +20"). The MD-22 (976) has two Light strike
# options: 31010 "Light strike (2x LS-6 500kg)" at +75 (since 0.8.0-dev.76 it carries 2x LT-2 laser bombs) and 31011 "Light strike (4x LS-6
# 500kg)" at +60. The +75 one is the outlier; it goes to +20. 31011 stays +60 (to confirm with Osama).
ok(O[31010]['UIName']=='Light strike (2x LS-6 500kg)' and O[31010]['Cost']==75 and M[O[31010]['ModificationId']]['UnitId']==976 and O[31011]['Cost']==60,'MD-22 Light strike options 75 / 60')
g.put('OptionsJson',31010,{'Cost':20});rec['md22_light_strike']={'option':31010,'cost':[75,20]}
# ---------- Y-8: no weapons (Osama 16 Nov 2026 01:2x PST: "Y-8 remove missiles and all armaments"). The Y-8 (1102, PLAN SF) is built on the
# KC-130J Harvest Hawk: two weapon slots (left pylon: Empty / 4x Hellfire +30 / 4x GBU-53 +20; fuselage: Empty / 10x Griffin +50). Both
# slots, their options, its 6 mounts and its 3 rounds rows go. Base cost 100 unchanged.
_y8m=[m['Id'] for m in M.values() if m['UnitId']==1102]
ok(U[1102]['HUDName']=='Y-8' and sorted(_y8m)==[2016020,2016021] and sorted(r['WeaponId'] for r in WA.values() if r['UnitId']==1102)==[12,392,433],'Y-8: 2 weapon slots, Hellfire/Stormbreaker/Griffin')
ok(not [o for o in O.values() if o.get('ReplaceUnitId')==1102],'no Y-8 swap rows')
g.clear_options(1102);g.clear_unit(1102,['TurretUnitsJson','WeaponAmmunitionsJson'])
ok(not [m for m in M.values() if m['UnitId']==1102] and not [r for r in TU.values() if r['UnitId']==1102] and not [r for r in WA.values() if r['UnitId']==1102],'Y-8 unarmed')
rec['y8_unarmed']={'unit':1102,'removed_slots':_y8m,'cost':U[1102]['Cost']}
# ---------- Mixed strike = 4x AKF-98A, no bombs (Osama 16 Nov 2026 01:2x PST: "mixed strike is 4x AKF-98A not 2x and bombs. Fix for J-31
# also"). J-35 (921) 31084, J-31 (1251) 31083 and J-20S (966) 31082 were "Mixed strike (LS-6 500kg + AKF-98A)": slot 1 = 2x LS-6 500 kg,
# slot 2 = the AKF-98A pylon with 2 rounds. Rounds are per pylon (J-10A: 3 per pylon on 2 pylons = 6x AKF-98A), so slot 1 takes the same
# AKF-98A pylon: 2 pylons x 2 = 4x AKF-98A. The J-20S keeps its 2 PL-10 pylons (slots 3, 6). Prices unchanged (105 / 80 / 80).
for _u,_o,_n in ((921,31084,'Mixed strike (4x AKF-98A)'),(1251,31083,'Mixed strike (4x AKF-98A)'),(966,31082,'Mixed strike (4x AKF-98A, 2x PL-10)')):
    _ak=O[_o]['Turret2Id']
    ok(M[O[_o]['ModificationId']]['UnitId']==_u and O[_o]['UIName']=='Mixed strike (LS-6 500kg + AKF-98A)' and [W[x['WeaponId']]['HUDName'] for x in TW.values() if x['TurretId']==_ak]==['AKF-98A'] and [r['Quantity'] for r in WA.values() if r['UnitId']==_u and r['WeaponId']==2016659]==[2],(_u,'mixed strike: AKF-98A pylon in slot 2, 2 rounds'))
    g.put('OptionsJson',_o,{'Turret1Id':_ak,'UIName':_n})
    ok(not any(W[x['WeaponId']]['HUDName'].startswith(('LS-6','LT-2')) for i in range(21) for x in TW.values() if x['TurretId']==O[_o].get(f'Turret{i}Id')),(_u,'no bombs'))
rec['mixed_strike_4x_akf98a']={'J-35':31084,'J-31':31083,'J-20S':31082}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
