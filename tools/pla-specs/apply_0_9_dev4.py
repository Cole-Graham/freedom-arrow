"""Freedom Arrow 0.9.0-dev.4 batch over exact 0.9.0-dev.3. Built only when Osama or Lateralus say the batch is ready
(Osama 14 Nov 11:05 PST: batch changes, the package is big). Append new sections before rec.update and rerun.
Run with --check while another thread is still building on the shared source folder.
- ZTL-191 main gun (105 mm, shared by ZTL-191 and ZTL-191 Recon) shows the autoloader (AutoLoaded true, as the vanilla T-72/T-80/T-90
  guns); its 4-5 s reload is unchanged (Osama 14 Nov 15:39 PST, thread 1567745029781454889).
- Spec names (same message): PLAGF Ground Force/Armored -> "PLAGF Armored Force", PLARF Rocket Force/Reservist ->
  "PLARF Rocket Conscript Force", PLAN Navy/SOF -> "PLAN Special Forces" (UIName and Name).
- Spec descriptions in the style of the vanilla ones (Osama 15:44 PST). DF-15 125 -> 150. J-5 Heavy strike 2x 1000 kg -> 2x 500 kg.
- PHL-191 Cruise fires a copy of the vanilla Iskander-K 9M728 cruise missile named CJ-10, with the Iskander's cruise loadouts
  (2x default, 4x +50) instead of Fire Dragon 480 / 280A; PHL-191 Ballistic keeps the Fire Dragons.
- Osama 16:02 PST: Mengshi Recon removed; PF-98 Tank Hunters out of PLAGF Armored Force; PLAAF Airborne 8 and Thunder Gods 2 cards;
  ZBL-08 12 HP; ZBD-251 9 seats; VT-5 base 140 without APS, Iron Fist APS option +60 (as on the ZBD-20), Motorized 4 cards. VT-5 and VT-5 Recon KE front 500 (was 600; Osama 16:09 PST).
- Icons: J-31 uses the J-35 icon, J-11D the J-16 icon, J-15D a new icon from its own model.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.4';PREV='0.9.0-dev.3'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks only; write nothing');a=p.parse_args()
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
# ---------- ZTL-191 autoloader (Osama 15:39 PST) ----------
W=t['WeaponsJson'];TU=t['TurretUnitsJson'];TW=t['TurretWeaponsJson']
ok(U[1080]['HUDName']=='ZTL-191' and U[1263]['HUDName']=='ZTL-191 Recon','ZTL-191 cards')
ok(W[2011297]['Name']=='PLA ZTL-191 105 mm high-pressure rifled gun' and W[2011297]['AutoLoaded'] is False,'ZTL-191 gun, not autoloaded')
users=sorted({x['UnitId'] for x in TU.values() for y in TW.values() if y['TurretId']==x['TurretId'] and y['WeaponId']==2011297})
ok(users==[1080,1263],('gun users',users));g.put('WeaponsJson',2011297,{'AutoLoaded':True})
rec['ztl191_autoloader']={'weapon':2011297,'units':users,'reload':[W[2011297]['MagazineReloadTimeMin'],W[2011297]['MagazineReloadTimeMax']]}
# ---------- Spec names (Osama 15:39 PST) ----------
SP=t['SpecializationsJson'];NEW={18:('PLA PLAGF Armored Force','PLAGF Armored Force'),19:('PLA PLARF Rocket Conscript Force','PLARF Rocket Conscript Force'),20:('PLA PLAN Special Forces','PLAN Special Forces')}
OLD={18:'PLAGF Ground Force/Armored',19:'PLARF Rocket Force/Reservist',20:'PLAN Navy/SOF'}
for sid,(n,ui) in NEW.items():
    ok(SP[sid]['UIName']==OLD[sid],('spec',sid,SP[sid]['UIName']));g.put('SpecializationsJson',sid,{'Name':n,'UIName':ui})
ok(len({SP[s]['UIName'] for s in (17,18,19,20,21,22)})==6,'spec names unique')
rec['spec_names']={str(k):[OLD[k],v[1]] for k,v in NEW.items()}
# ---------- Spec descriptions in the vanilla style (Osama 15:44 PST: "write little descriptions of our specs and use the vanilla
# description as a reference"). Vanilla text read from the game's localization bundle (eng, ui_spec_*_description). ----------
DESC={17:'The PLA Air Force fields China\'s most modern fighters, bombers and stealth jets, and its airborne troops ride helicopters to seize ground ahead of the main force.',
18:'The armored force gives you access to China\'s heaviest tanks, backed by self-propelled artillery and mobile air defense. This firepower comes at the cost of having no fixed-wing aircraft.',
19:'Conscript infantry and older tanks hold the line while the Rocket Force\'s ballistic missiles and long-range artillery strike deep into enemy territory. An aging fleet of jets provides the air cover.',
20:'Elite special forces and marines supported by carrier aviation and long-range drones, striking from the sea and the air deep behind enemy lines.',
21:'Fast wheeled vehicles carry a large infantry force, supported by mobile rocket artillery and air defense, to hit hard and keep moving.'}
for sid,d in DESC.items():
    ok(SP[sid]['UIDescription'].endswith('provisional5000-point category budget.'),('old description',sid));g.put('SpecializationsJson',sid,{'UIDescription':d})
rec['spec_descriptions']={str(k):v for k,v in DESC.items()}
# ---------- DF-15 150 (Osama 15:4x PST) ----------
ok(U[1029]['HUDName']=='DF-15' and U[1029]['Cost']==125,('DF-15',U[1029]['Cost']));g.put('Units',1029,{'Cost':150});rec['df15_cost']=[125,150]
# ---------- J-5 Heavy strike: 2x 500 kg instead of 2x 1000 kg (Osama 15:4x PST) ----------
AM=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];T=t['TurretsJson']
ok(U[1089]['HUDName']=='J-5' and O[31040]['UIName']=='Heavy strike (2x 1000 kg bomb)' and O[31040]['Turret1Id']==O[31040]['Turret2Id']==2018685,'J-5 heavy strike 2x 1000 kg')
ok([x['WeaponId'] for x in TW.values() if x['TurretId']==2016615]==[2016616] and W[2016616]['Name']=='PLA air 500 kg bomb x1','500 kg x1 pylon')
tu1000=[x for x in rows('TurretUnitsJson',1089) if x['TurretId']==2018685];wa1000=[x for x in rows('WeaponAmmunitionsJson',1089) if x['WeaponId']==2018684];ok(len(tu1000)==1 and len(wa1000)==1,'J-5 1000 kg rows')
g.add('TurretUnitsJson',tu1000[0],{'TurretId':2016615});g.add('WeaponAmmunitionsJson',wa1000[0],{'WeaponId':2016616,'AmmunitionId':2016618,'Quantity':1})
g.remove('TurretUnitsJson',tu1000[0]['Id']);g.remove('WeaponAmmunitionsJson',wa1000[0]['Id'])
g.put('OptionsJson',31040,{'Turret1Id':2016615,'Turret2Id':2016615,'UIName':'Heavy strike (2x 500 kg bomb)'})
rec['j5_heavy_strike']={'option':31040,'bombs':'2x 500 kg (was 2x 1000 kg)','cost':O[31040]['Cost']}
# ---------- PHL-191 Cruise: Iskander-K cruise missile, named CJ-10 (Osama 15:4x PST: "use Isnaker cruise missiles (but rename Chinese)") ----------
# Same loadouts as the vanilla 9K720 Iskander cruise options: 2x (default, +0) and 4x (+50).
C=1267;ok(U[C]['HUDName']=='PHL-191 Cruise' and sorted(x['TurretId'] for x in rows('TurretUnitsJson',C))==[2018666,2018671],'PHL-191 Cruise mounts')
ok(O[31055]['UIName']=='2x Fire Dragon 480' and O[31056]['UIName']=='2x Fire Dragon 280A','PHL-191 Cruise options')
ok(AM[219]['Name']=='Missile Cruise IskanderK HE Guided' and W[317]['Name']=='Cruise IskanderK x2' and W[318]['Name']=='Cruise IskanderK x4','vanilla Iskander-K rows')
cj=g.add('AmmunitionsJson',AM[219],{'Name':'PLA CJ-10 cruise missile','HUDName':'CJ-10'})
mounts={}
for n,wv,tsrc,oid,cost in ((2,317,2018666,31055,0),(4,318,2018671,31056,50)):
    wid=g.add('WeaponsJson',W[wv],{'Name':f'PLA PHL-191 CJ-10 x{n}'})
    tid=g.add('TurretsJson',T[tsrc],{'Name':f'PLA PHL-191 CJ-10 x{n}'})
    g.add('TurretWeaponsJson',[x for x in TW.values() if x['TurretId']==tsrc][0],{'TurretId':tid,'WeaponId':wid})
    tu=[x for x in rows('TurretUnitsJson',C) if x['TurretId']==tsrc][0];g.put('TurretUnitsJson',tu['Id'],{'TurretId':tid})
    g.put('OptionsJson',oid,{'UIName':f'{n}x CJ-10','Turret0Id':tid,'Cost':cost});mounts[n]=(wid,tid)
old=[x for x in rows('WeaponAmmunitionsJson',C)];ok(sorted(x['WeaponId'] for x in old)==[2018667,2018672],'old PHL-191 Cruise ammo rows')
for x,n in zip(sorted(old,key=lambda x:x['WeaponId']),(2,4)):g.add('WeaponAmmunitionsJson',x,{'WeaponId':mounts[n][0],'AmmunitionId':cj,'Quantity':n});g.remove('WeaponAmmunitionsJson',x['Id'])
ok(sorted((x['WeaponId'],x['Quantity']) for x in rows('WeaponAmmunitionsJson',C))==sorted((mounts[n][0],n) for n in (2,4)),'PHL-191 Cruise carries CJ-10 only')
ok(sorted(U[x['UnitId']]['HUDName'] for x in WA.values() if x['WeaponId'] in (2018667,2018672) and x['UnitId'] in U)==['PHL-191 Ballistic','PHL-191 Ballistic'],'Ballistic keeps its Fire Dragons')
rec['phl191_cruise']={'ammo':cj,'name':'CJ-10 (copy of vanilla 9M728 Iskander-K, ammo 219)','options':{'2x CJ-10':0,'4x CJ-10':50},'mounts':mounts}
# ---------- Icons (Osama 15:5x PST): J-31 uses the J-35 icon, J-11D the J-16 icon, J-15D its own (rendered from m_j15d_cg) ----------
icon_dir=ROOT/'releases/0.6/source/runtime-qa/icons';IC={1251:('J-31','J35'),1242:('J-11D','J16'),974:('J-15D','J15D')}
for uid,(h,k) in IC.items():
    ok(U[uid]['HUDName']==h and U[uid]['DisplayInArmory'],('icon card',uid));ok((icon_dir/f'FA_PLA_VEH_{k}.png').exists() and (icon_dir/f'FA_PLA_VEH_{k}_OUTLINE.png').exists(),('icon files',k))
    g.put('Units',uid,{'ThumbnailFileName':f'FA_PLA_VEH_{k}'})
rec['icons']={str(u):f'FA_PLA_VEH_{k}' for u,(h,k) in IC.items()}
# ---------- Osama 16:02 PST batch ----------
SAJ=t['SpecializationAvailabilitiesJson'];TAJ=t['TransportAvailabilitiesJson'];ABJ=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson'];ARJ=t['ArmorsJson'];UAJ=t['UnitArmorsJson']
def drop_cards(uid,specs=None):
    gone=[]
    for sa in [x for x in SAJ.values() if x['UnitId']==uid and (specs is None or x['SpecializationId'] in specs)]:
        for ta in [x for x in TAJ.values() if x['SpecializationAvailabilityId']==sa['Id']]:g.remove('TransportAvailabilitiesJson',ta['Id'])
        g.remove('SpecializationAvailabilitiesJson',sa['Id']);gone.append(sa['SpecializationId'])
    left=sorted(x['SpecializationId'] for x in SAJ.values() if x['UnitId']==uid)
    if left:assign['assignments'][str(uid)]=left
    else:assign['assignments'].pop(str(uid),None);assign.get('shared_transports',{}).pop(str(uid),None)
    return sorted(gone)
# Mengshi Recon removed (all three cards)
ok(U[1265]['HUDName']=='Mengshi Recon' and not [x for x in TAJ.values() if x['UnitId']==1265],'Mengshi Recon carries nobody')
rec['mengshi_recon_removed']=drop_cards(1265);ok(rec['mengshi_recon_removed']==[17,20,21] and not [x for x in SAJ.values() if x['UnitId']==1265],'Mengshi Recon gone')
# PF-98 Tank Hunters out of PLAGF Armored Force
ok(U[1155]['HUDName']=='PF-98 Tank Hunters','Tank Hunters');rec['tank_hunters_removed_from']=drop_cards(1155,{18});ok(rec['tank_hunters_removed_from']==[18],'Tank Hunters card 18')
# Availability: Airborne 8, Thunder Gods 2 (PLAAF)
for said,uid,h,was,new in ((2011853,1136,'Airborne 空降兵',4,8),(2012042,1143,'Thunder Gods 雷神',4,2)):
    ok(U[uid]['HUDName']==h and SAJ[said]['UnitId']==uid and SAJ[said]['SpecializationId']==17 and SAJ[said]['MaxAvailabilityXp0']==was,(h,'card'));g.put('SpecializationAvailabilitiesJson',said,{'MaxAvailabilityXp0':new})
rec['availability']={'Airborne':[4,8],'Thunder Gods':[4,2]}
# ZBL-08 12 HP; ZBD-251 9 seats
ok(ARJ[2009037]['MaxHealthPoints']==10 and [x['UnitId'] for x in UAJ.values() if x['ArmorId']==2009037]==[903],'ZBL-08 own armour 10 HP');g.put('ArmorsJson',2009037,{'MaxHealthPoints':12})
ok(U[1056]['HUDName']=='ZBD-251' and U[1056]['InfantrySlots']==7,'ZBD-251 7 seats');g.put('Units',1056,{'InfantrySlots':9})
rec['zbl08_hp']=[10,12];rec['zbd251_seats']=[7,9]
# VT-5: base 140 without APS; Iron Fist APS option +60 (as on the ZBD-20); Motorized 4 cards
VT=1261;ok(U[VT]['HUDName']=='VT-5' and U[VT]['Cost']==200,('VT-5',U[VT]['Cost']));ok([x['AbilityId'] for x in UAB.values() if x['UnitId']==VT]==[2018639] and ABJ[2018639]['IsAPS'],'VT-5 has APS built in')
ok(not [x for x in M.values() if x['UnitId']==VT and x['Name']=='PLA VT-5 APS'],'no VT-5 APS slot yet')
na=g.add('AbilitiesJson',ABJ[2018639],{'Name':'PLA VT-5 AbilitiesJson no APS','IsAPS':False,'APSHitboxProportion':0.0,'APSQuantity':0,'APSCooldown':0.0,'APSSupplyCost':0.0,'APSResupplyTime':0.0})
ua=[x for x in UAB.values() if x['UnitId']==VT][0];g.put('UnitAbilitiesJson',ua['Id'],{'AbilityId':na})
for ab in (82,4):g.add('UnitAbilitiesJson',ua,{'AbilityId':ab})
ok(ABJ[82]['IsAPS'] and ABJ[82]['APSQuantity']==ABJ[2018639]['APSQuantity'] and ABJ[82]['APSCooldown']==ABJ[2018639]['APSCooldown'],'Iron Fist APS = the VT-5 APS stats')
vm=g.add('ModificationsJson',M[2019016],{'UnitId':VT,'Name':'PLA VT-5 APS'})
v1=g.add('OptionsJson',O[31065],{'ModificationId':vm,'Ability1Id':na,'Ability2Id':4,'Cost':0,'IsDefault':True})
v2=g.add('OptionsJson',O[31066],{'ModificationId':vm,'Ability1Id':na,'Ability2Id':82,'Cost':60,'IsDefault':False})
ok(v1<=32767 and v2<=32767,'short option ids');g.put('Units',VT,{'Cost':140})
ok(SAJ[2018649]['UnitId']==VT and SAJ[2018649]['SpecializationId']==21 and SAJ[2018649]['MaxAvailabilityXp0']==6,'VT-5 Motorized card 6');g.put('SpecializationAvailabilitiesJson',2018649,{'MaxAvailabilityXp0':4})
rec['vt5']={'cost':[200,140],'aps_option':{'id':v2,'cost':60},'none_option':v1,'base_ability_no_aps':na,'motorized_cards':[6,4]}
# VT-5 and VT-5 Recon: 500 KE front (Osama 16:09 PST, thread 1571014792016171120; was 600)
_AR=t['ArmorsJson'];_UAR=t['UnitArmorsJson'];rec['vt5_ke_front']={}
for _u,_h in ((1261,'VT-5'),(1262,'VT-5 Recon')):
    ok(U[_u]['HUDName']==_h,(_u,_h));_a=[r['ArmorId'] for r in _UAR.values() if r['UnitId']==_u];ok(len(_a)==1 and sum(1 for r in _UAR.values() if r['ArmorId']==_a[0])==1,(_h,'own armour'))
    ok(_AR[_a[0]]['KinArmorFront']==600,(_h,'KE front 600',_AR[_a[0]]['KinArmorFront']));g.put('ArmorsJson',_a[0],{'KinArmorFront':500});rec['vt5_ke_front'][_h]=[600,500]
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
if a.check:print('checks',checks,'(check only, nothing written)');raise SystemExit
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
