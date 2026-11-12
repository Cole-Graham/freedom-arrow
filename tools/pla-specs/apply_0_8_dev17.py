"""Freedom Arrow 0.8.0-dev.17 over exact 0.8.0-dev.16 (Osama 12 Nov PST): "ZBL-191 basically has HJ-16's which are like the
long range javelins. They also have APS. Their Armor is like the SRAT I armor so please update their price".
- ZBL-191 (979) missile: HJ-16 = the FA Javelin row (2000174: 10.5 damage, 140 penetration, top attack, fire-and-forget)
  with range 1000 (2000 m; the Javelin is 750 = 1500 m). Its own HJ-8E launcher/ammo rows (used by no other unit) are edited.
- APS: IronFist APS ability 82, as on the ZBD-20.
- Armour: FA Stryker SRAT I values (armor 2000017): 12 HP, HEAT 250/200/130/20, KE 80/60/30/20 (front/sides/rear/top).
- Price 40 -> 105: 30 mm wheeled IFV (~45) + 4 long-range top-attack missiles (~30) + APS (~20) + SRAT I armour (~10);
  for comparison Stryker ICV 30 + SRAT ERA 25 + APS 65 option, M2A3 65, Stryker ATGM 70, ZBD-20 175. Theoretical.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.17'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.16.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native)
U,W,A,WA,UA,AR,UAR=(t[k] for k in ('Units','WeaponsJson','AmmunitionsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','ArmorsJson','UnitArmorsJson'))
ZBL,LW,LA,JAV,SRAT,APS=979,2010337,2010339,2000174,2000017,82
assert U[ZBL]['HUDName']=='ZBL-191' and W[LW]['HUDName']=='HJ-8E' and A[JAV]['HUDName']=='Javelin' and AR[SRAT]['Name']=='Armor Stryker SRAT'
assert {x['UnitId'] for x in WA.values() if x['WeaponId']==LW or x['AmmunitionId']==LA}=={ZBL}
KEEP=('Id','Name','HUDIcon')
g.put('AmmunitionsJson',LA,{**{k:copy.deepcopy(v) for k,v in A[JAV].items() if k not in KEEP},'HUDName':'HJ-16','GroundRange':1000.0})
g.put('WeaponsJson',LW,{'HUDName':'HJ-16','HUDIcon':W[76]['HUDIcon']})
if not any(r['UnitId']==ZBL and r['AbilityId']==APS for r in UA.values()):g.add('UnitAbilitiesJson',next(r for r in UA.values() if r['UnitId']==945 and r['AbilityId']==APS),{'UnitId':ZBL})
arm=[r['ArmorId'] for r in UAR.values() if r['UnitId']==ZBL];assert len(arm)==1 and arm[0]>2000000 and sum(r['ArmorId']==arm[0] for r in UAR.values())==1
ARMOR=('MaxHealthPoints','HeatArmorFront','HeatArmorSides','HeatArmorRear','HeatArmorTop','KinArmorFront','KinArmorSides','KinArmorRear','KinArmorTop')
g.put('ArmorsJson',arm[0],{k:AR[SRAT][k] for k in ARMOR})
g.put('Units',ZBL,{'Cost':105})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
h=A[LA];ok((h['HUDName'],h['Damage'],h['PenetrationAtGroundRange'],h['GroundRange'],h['IsTopArmorArmorAttack'],h['Seeker'])==('HJ-16',10.5,140.0,1000.0,True,A[JAV]['Seeker']),'HJ-16')
ok(any(r['UnitId']==ZBL and r['AbilityId']==APS for r in UA.values()),'APS')
ok([AR[arm[0]][k] for k in ARMOR]==[AR[SRAT][k] for k in ARMOR],'SRAT I armour')
changed={('AmmunitionsJson',LA),('WeaponsJson',LW),('ArmorsJson',arm[0]),('Units',ZBL)}
for tab in t:
    for key,row in before[tab].items():
        if (tab,key) not in changed:ok(t[tab].get(key)==row,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.16','base_sha256':BASE,'request':'Osama 12 Nov PST: ZBL-191 HJ-16, APS, SRAT I armour, price',
 'hj16':{k:h[k] for k in ('Damage','PenetrationAtGroundRange','GroundRange','IsTopArmorArmorAttack','Seeker','TrajectoryType')},'displayed_range_m':2000,
 'armor':{k:AR[arm[0]][k] for k in ARMOR},'aps_ability':APS,'cost':{'before':before['Units'][ZBL]['Cost'],'after':U[ZBL]['Cost']},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1))
