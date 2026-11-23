"""Freedom Arrow 0.8.0-dev.57 over exact 0.8.0-dev.56 (Osama 13 Nov 15:4x PST, thread 1567745029781454889):
- PGZ-09 (909): its twin 35 mm guns take the Pantsir S1 2A38M gun stats (weapon 19, ammo 60, 133 rounds). Names kept.
- PGZ-88 (1051): 175 -> 80 points.
- PHL-16 (1035): 250 -> 350 points; its rockets (BRE3 300 mm 2017442 and BRE6/BRE8 370 mm 2010439) 33 -> 48 damage and a
  165 m blast as shown in game (82.5 in data; the game shows 2x), stress radius scaled the same. Fire Dragon 480 unchanged.
- PHL-191 Ballistic (1036): real munition names. 2x Fire Dragon 480 (the ATACMS-stat loadout, using the PHL-16 Fire Dragon 480
  ammo 2017443, an ATACMS copy) and 2x Fire Dragon 280A (new ammo row copied from PrSM 427). Vanilla ATACMS/PrSM rows untouched.
- PHL-03 (908): the guided loadouts no longer rename the unit to "9K515 Tornado-S" (ReplaceUnitName cleared).
- PGL-625 (920): Pantsir S1 stat clone: armour, radar ability, optics and mobility of the Pantsir, but road 100 and reverse 40;
  gun = Pantsir 2A38M stats (133 rounds), FB-10 = Pantsir 57E6E stats with 8 missiles (Pantsir 12) and a ground range of
  1200 as shown in game (600 in data; the game shows 2x).
  Its own model, names, icons and sounds stay. Cost unchanged (170 = Pantsir).
- JRVG-1 (952): Motorized (21) -> PLAN Navy/SOF (20). Ranges as shown in game: ground 1400 (700 data, both 76 mm rounds;
  was 550 data = 1100 shown), high altitude 1800 (900 data; was 500). Road 70 -> 100, reverse 25 (already 25).
- HQ-7B (925): PLAN Navy/SOF (20) -> PLAAF (17).
- HQ-17A (1049): in PLAN Navy/SOF (20) and now also Motorized (21), same card (multi-spec list).
- HQ-6A (1045): Rocket Force (19) -> Motorized (21).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.57'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.56.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,W,A,WA,O,AR,MOB,AB,S,SA=(t[k] for k in ('Units','WeaponsJson','AmmunitionsJson','WeaponAmmunitionsJson','OptionsJson','ArmorsJson','MobilityJson','AbilitiesJson','SensorsJson','SpecializationAvailabilitiesJson'))
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN))
KEEP={'Id','Name','HUDName','HUDIcon','ModelFileName','AudioPreset','FXPreset'}
def copy_stats(tab,dst,src,extra=None):
    g.put(tab,dst,{**{k:copy.deepcopy(v) for k,v in t[tab][src].items() if k not in KEEP},**(extra or {})})
def wa(uid,wid):r=[r for r in WA.values() if r['UnitId']==uid and r['WeaponId']==wid];assert len(r)==1;return r[0]
def only(tab,field,i,uid):assert sorted({r['UnitId'] for r in t[tab].values() if r.get(field)==i})==[uid],(tab,i)
PANTSIR,PGUN,PGUNA,PMSL,PMSLA=12,19,60,20,20
assert U[PANTSIR]['HUDName']=='Pantsir S1' and W[PGUN]['HUDName']=='2x 2А38М' and A[PGUNA]['HUDName']=='30x165mm' and W[PMSL]['HUDName']=='2x6 57E6E'
log={}
# ---- PGZ-09 guns
PGZ09,G9W,G9A=909,2009181,2009185
assert U[PGZ09]['HUDName']=='PGZ-09';only('WeaponAmmunitionsJson','WeaponId',G9W,PGZ09);only('WeaponAmmunitionsJson','AmmunitionId',G9A,PGZ09)
copy_stats('WeaponsJson',G9W,PGUN);copy_stats('AmmunitionsJson',G9A,PGUNA);g.put('WeaponAmmunitionsJson',wa(PGZ09,G9W)['Id'],{'Quantity':wa(PANTSIR,PGUN)['Quantity']})
# ---- PGZ-88 and PHL-16 cost
assert U[1051]['HUDName']=='PGZ-88' and U[1035]['HUDName']=='PHL-16'
log['costs']={'PGZ-88':[U[1051]['Cost'],80],'PHL-16':[U[1035]['Cost'],350]}
g.put('Units',1051,{'Cost':80,'OriginalCost':80});g.put('Units',1035,{'Cost':350,'OriginalCost':350})
# ---- PHL-16 rockets
for aid in (2017442,2010439):
    only('WeaponAmmunitionsJson','AmmunitionId',aid,1035);x=A[aid];f=82.5/x['HealthAOERadius']
    log[f'phl16_{aid}']=[x['Damage'],x['HealthAOERadius'],x['StressAOERadius']]
    g.put('AmmunitionsJson',aid,{'Damage':48.0,'HealthAOERadius':82.5,'StressAOERadius':round(x['StressAOERadius']*f,1)})
# ---- PHL-191 names
PHL191=1036;FD480=2017443;assert A[FD480]['HUDName']=='Fire Dragon 480'
rows={W[r['WeaponId']]['HUDName']:r for r in WA.values() if r['UnitId']==PHL191};assert set(rows)=={'ATACMS','PrSM'}
g.put('WeaponAmmunitionsJson',rows['ATACMS']['Id'],{'AmmunitionId':FD480});g.put('WeaponsJson',rows['ATACMS']['WeaponId'],{'HUDName':'Fire Dragon 480','Name':'PLA PHL-191 Fire Dragon 480 x2'})
fd280=g.add('AmmunitionsJson',A[427],{'Name':'PLA Fire Dragon 280A','HUDName':'Fire Dragon 280A'})
g.put('WeaponAmmunitionsJson',rows['PrSM']['Id'],{'AmmunitionId':fd280});g.put('WeaponsJson',rows['PrSM']['WeaponId'],{'HUDName':'Fire Dragon 280A','Name':'PLA PHL-191 Fire Dragon 280A x2'})
for o in O.values():
    if o.get('UIName')=='2x ATACMS':g.put('OptionsJson',o['Id'],{'UIName':'2x Fire Dragon 480','Name':'Loadout PHL-191 Fire Dragon 480 x2'})
    if o.get('UIName')=='2x PrSM':g.put('OptionsJson',o['Id'],{'UIName':'2x Fire Dragon 280A','Name':'Loadout PHL-191 Fire Dragon 280A x2'})
# ---- PHL-03 keeps its name
phl03=[o for o in O.values() if o['ModificationId']==2018334];assert len(phl03)==4
for o in phl03:
    if o.get('ReplaceUnitName'):g.put('OptionsJson',o['Id'],{'ReplaceUnitName':None})
# ---- PGL-625 Pantsir clone
PGL,GW,GA,MW,MA=920,2009365,2009369,2009371,2009373
assert U[PGL]['HUDName']=='PGL-625'
for tab,field,i in (('UnitArmorsJson','ArmorId',2009357),('UnitPropulsionsJson','MobilityId',2009359),('UnitAbilitiesJson','AbilityId',2009361),('SensorUnitsJson','SensorId',2009363),('WeaponAmmunitionsJson','WeaponId',GW),('WeaponAmmunitionsJson','WeaponId',MW),('WeaponAmmunitionsJson','AmmunitionId',GA),('WeaponAmmunitionsJson','AmmunitionId',MA)):only(tab,field,i,PGL)
copy_stats('ArmorsJson',2009357,12);copy_stats('MobilityJson',2009359,177,{'MaxSpeedRoad':100.0,'MaxSpeedReverse':40.0});copy_stats('AbilitiesJson',2009361,60);copy_stats('SensorsJson',2009363,2001447)
copy_stats('WeaponsJson',GW,PGUN);copy_stats('AmmunitionsJson',GA,PGUNA);copy_stats('WeaponsJson',MW,PMSL);copy_stats('AmmunitionsJson',MA,PMSLA,{'GroundRange':600.0})
g.put('WeaponAmmunitionsJson',wa(PGL,GW)['Id'],{'Quantity':wa(PANTSIR,PGUN)['Quantity']});g.put('WeaponAmmunitionsJson',wa(PGL,MW)['Id'],{'Quantity':8})
# ---- JRVG-1 to PLAN SOF
JRVG=952;assert U[JRVG]['HUDName']=='JRVG-1';sa=[r for r in SA.values() if r['UnitId']==JRVG];assert [r['SpecializationId'] for r in sa]==[21]
g.put('SpecializationAvailabilitiesJson',sa[0]['Id'],{'SpecializationId':20});assign['assignments'][str(JRVG)]=[20]
for aid in (2009951,2009953):only('WeaponAmmunitionsJson','AmmunitionId',aid,JRVG);g.put('AmmunitionsJson',aid,{'GroundRange':700.0})
g.put('AmmunitionsJson',2009953,{'HighAltRange':900.0})
only('UnitPropulsionsJson','MobilityId',2009941,JRVG);g.put('MobilityJson',2009941,{'MaxSpeedRoad':100.0,'MaxSpeedReverse':25.0})
HQ7B=925;assert U[HQ7B]['HUDName']=='HQ-7B';sa7=[r for r in SA.values() if r['UnitId']==HQ7B];assert [r['SpecializationId'] for r in sa7]==[20]
g.put('SpecializationAvailabilitiesJson',sa7[0]['Id'],{'SpecializationId':17});assign['assignments'][str(HQ7B)]=[17]
HQ17A,HQ6A=1049,1045;assert U[HQ17A]['HUDName']=='HQ-17A' and U[HQ6A]['HUDName']=='HQ-6A'
s17=[r for r in SA.values() if r['UnitId']==HQ17A];assert [r['SpecializationId'] for r in s17]==[20]
g.add('SpecializationAvailabilitiesJson',s17[0],{'SpecializationId':21});assign['assignments'][str(HQ17A)]=[20,21]
assign['shared_transports'][str(HQ17A)]=[20,21];assign['one_spec_rule']['exceptions'][str(HQ17A)]=[20,21]
assign['one_spec_rule']['basis']+='; HQ-17A in PLAN Navy/SOF and Motorized (Osama 13 Nov 15:5x)'
s6=[r for r in SA.values() if r['UnitId']==HQ6A];assert [r['SpecializationId'] for r in s6]==[19]
g.put('SpecializationAvailabilitiesJson',s6[0]['Id'],{'SpecializationId':21});assign['assignments'][str(HQ6A)]=[21]
assign['pool_counts']={str(s):sum(r['SpecializationId']==s for r in SA.values()) for s in range(17,23)}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
same=lambda tab,a_,b_,skip=():all(t[tab][a_].get(k)==v for k,v in t[tab][b_].items() if k not in KEEP|set(skip))
ok(same('WeaponsJson',G9W,PGUN) and same('AmmunitionsJson',G9A,PGUNA) and wa(PGZ09,G9W)['Quantity']==133,'PGZ-09 Pantsir guns')
ok(U[1051]['Cost']==80 and U[1035]['Cost']==350,'costs')
for aid in (2017442,2010439):ok((A[aid]['Damage'],A[aid]['HealthAOERadius'])==(48.0,82.5),('PHL-16 rocket',aid))
ok(A[FD480]['Damage']==20.0,'Fire Dragon 480 stats unchanged')
ok({A[r['AmmunitionId']]['HUDName'] for r in WA.values() if r['UnitId']==PHL191}=={'Fire Dragon 480','Fire Dragon 280A'},'PHL-191 ammo names')
ok(A[34]['HUDName']=='ATACMS' and A[427]['HUDName']=='400mm HE PrSM','vanilla rows untouched')
ok(same('AmmunitionsJson',fd280,427,('Name','HUDName')),'Fire Dragon 280A = PrSM stats')
ok(not any(o.get('ReplaceUnitName') for o in O.values() if o['ModificationId']==2018334),'PHL-03 keeps name')
ok(same('ArmorsJson',2009357,12) and same('AbilitiesJson',2009361,60) and same('SensorsJson',2009363,2001447),'PGL-625 armour/radar/optics')
ok(same('MobilityJson',2009359,177,('MaxSpeedRoad','MaxSpeedReverse')) and (MOB[2009359]['MaxSpeedRoad'],MOB[2009359]['MaxSpeedReverse'])==(100.0,40.0),'PGL-625 mobility')
ok(same('WeaponsJson',GW,PGUN) and same('AmmunitionsJson',GA,PGUNA) and same('WeaponsJson',MW,PMSL) and same('AmmunitionsJson',MA,PMSLA,('GroundRange',)),'PGL-625 Pantsir weapons')
ok(A[MA]['GroundRange']==600.0 and wa(PGL,MW)['Quantity']==8 and wa(PGL,GW)['Quantity']==133,'PGL-625 8 missiles, 1200 ground')
ok([r['SpecializationId'] for r in SA.values() if r['UnitId']==JRVG]==[20],'JRVG-1 PLAN SOF')
ok(A[2009951]['GroundRange']==A[2009953]['GroundRange']==700.0 and A[2009953]['HighAltRange']==900.0 and (MOB[2009941]['MaxSpeedRoad'],MOB[2009941]['MaxSpeedReverse'])==(100.0,25.0),'JRVG-1 ranges and speed')
ok([r['SpecializationId'] for r in SA.values() if r['UnitId']==HQ7B]==[17],'HQ-7B PLAAF')
ok(sorted(r['SpecializationId'] for r in SA.values() if r['UnitId']==HQ17A)==[20,21],'HQ-17A SOF + Motorized')
ok([r['SpecializationId'] for r in SA.values() if r['UnitId']==HQ6A]==[21],'HQ-6A Motorized')
receipt={'version':V,'base':'0.8.0-dev.56','base_sha256':BASE,'request':'Osama 13 Nov 15:4x PST: PGZ-09 guns like Pantsir; PGZ-88 80; PHL-16 48 damage, 165 m radius, 350; PHL-191 munition names; PHL-03 loadout must not change its name; PGL-625 Pantsir clone (reverse 40, forward 100, 8 missiles, ground range 1200); JRVG-1 to PLAN SOF; JRVG 1400 ground, 1800 high altitude, 100 forward, 25 reverse; HQ-7B to PLAAF; HQ-17A in both SOF and Motorized; HQ-6 to Motorized',
 'log':log,'fire_dragon_280a_ammo':fd280,'names_source':'PHL-16/PCL-191 carries two 750 mm missiles: Fire Dragon 480 and Fire Dragon 280A (Wikipedia PHL-16; Janes)','checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign)
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(log))
