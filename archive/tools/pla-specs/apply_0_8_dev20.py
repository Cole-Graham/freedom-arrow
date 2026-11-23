"""Freedom Arrow 0.8.0-dev.20 over exact 0.8.0-dev.19 (Osama 12 Nov 17:48 PST voice message: infantry launcher ammo must match the
Russian/US equivalents; the armory must match what units use in a match; Skirmish test on Vengeance).
- Launcher ammo (compared with RU/US infantry, work/skirmish-audit-20261112):
  PF-98/PF-98A carried inside squads 10 -> 6 (RPG-7V, RAWS, MAAWS squads carry 3-6; dedicated PF-98 teams keep 10 like the
  RAWS and RPG-29 teams); FHJ-02 14 -> 6 (RPO-M/MRO-Z 4, Bur 6); HJ-12 Team 2 -> 4 (Javelin team 4); single-gunner AA teams
  QW-12 Patrol and AA Troopers 4 -> 6 (Stinger/Igla/Verba/Piorun teams 5-6).
- Transports: the in-match transport picker offers every deck unit with infantry seats, whatever the armory transport list
  says (Skirmish 12 Nov 18:11). Z-20T, Shaanxi HMV3, Z-8L, Mi-8 Cargo and Shaanxi Troop Truck, which Osama took off the
  transport lists (dev.15/16), get 0 infantry seats.
- CSK-181 Transport: an empty default mount (the dev.8 'PLA empty default mount'), since its Tigr body with no turret made the
  armory's resupply-time calculation throw (RefundSystem.GetAmmoResupplyTime NullReferenceException, 1 of 6 card errors).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.20'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.19.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U,W,WA,TU,T=t['Units'],t['WeaponsJson'],t['WeaponAmmunitionsJson'],t['TurretUnitsJson'],t['TurretsJson']
AMMO={2014870:('Airborne 空降兵','PF-98',10,6),2014918:('Pathfinders 先遣队','PF-98A',10,6),2015396:('Sea Dragons 蛟龙','PF-98',10,6),2015458:('Line Infantry 摩步班','PF-98',10,6),
 2014935:('Thunder Gods 雷神','FHJ-02',14,6),2015879:('Thermobaric Team','FHJ-02',14,6),2014881:('HJ-12 Team','HJ-12',2,4),2014959:('QW-12 Patrol 防空巡逻','QW-12',4,6),2015481:('AA Troopers 防空班','HN-6',4,6)}
for rid,(unit,weapon,old,new) in AMMO.items():
    r=WA[rid];assert U[r['UnitId']]['HUDName']==unit and W[r['WeaponId']]['HUDName']==weapon and r['Quantity']==old,(rid,unit)
    g.put('WeaponAmmunitionsJson',rid,{'Quantity':new})
SEATS={1245:'Z-20T',1235:'Shaanxi HMV3',1106:'Z-8L',1227:'Mi-8 Cargo',1231:'Shaanxi Troop Truck'}
for uid,n in SEATS.items():assert U[uid]['HUDName']==n and U[uid]['InfantrySlots']>0;g.put('Units',uid,{'InfantrySlots':0})
CSK=1230;EMPTYDEF=next(k for k,v in T.items() if v.get('Name')=='PLA empty default mount')
assert U[CSK]['HUDName']=='CSK-181 Transport' and not any(r['UnitId']==CSK for r in TU.values())
g.add('TurretUnitsJson',next(iter(TU.values())),{'UnitId':CSK,'TurretId':EMPTYDEF,'Order':0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for rid,(_,_,_,new) in AMMO.items():ok(WA[rid]['Quantity']==new,('ammo',rid))
for uid in SEATS:ok(U[uid]['InfantrySlots']==0,('seats',uid))
ok(any(r['UnitId']==CSK and r['TurretId']==EMPTYDEF for r in TU.values()),'CSK-181 default mount')
changed={('WeaponAmmunitionsJson',r) for r in AMMO}|{('Units',u) for u in SEATS}
for tab in t:
    for key,row in before[tab].items():
        if (tab,key) not in changed:ok(t[tab].get(key)==row,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.19','base_sha256':BASE,'request':'Osama 12 Nov 17:48 PST voice message (ammo parity, armory = in-match, Skirmish test)',
 'ammo':{AMMO[r][0]+' '+AMMO[r][1]:[AMMO[r][2],AMMO[r][3]] for r in AMMO},'zero_seats':list(SEATS.values()),'csk181_transport_default_mount':EMPTYDEF,'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))
