"""Freedom Arrow 0.8.0-dev.30 over exact 0.8.0-dev.29 (Osama 13 Nov 02:20 PST, thread 1567745029781454889):
- MD-22: the LS-6 1000kg loadout (option 31027) drops its two PL-15s and becomes "Heavy strike (2x LS-6 1000kg)": pylon 0 gets a
  new LS-6 1000kg x2 mount, pylon 1 the native empty mount (160). Price 105 -> 60 (2 PL-15s cost 45 in this aircraft's pricing;
  2x 1000 kg = the 60-point 4x 500 kg strike load). Loadouts ordered by category then price.
- Godswords 80 -> 100 points (Osama 02:27).
- Spike LR (vanilla 549, FA copy 2000177) and GAM-102LR (2014293): penetration 700 -> 140, the Javelin's value for a
  top-attack missile.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.30'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.29.json').read_text())['complete']['sha256']
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
T,TW,TU,O,A=t['TurretsJson'],t['TurretWeaponsJson'],t['TurretUnitsJson'],t['OptionsJson'],t['AmmunitionsJson']
MD,OPT,OLD,OLD1,EMPTY=976,31027,2018481,2018488,160
assert U[MD]['HUDName']=='MD-22' and O[OPT]['UIName']=='Light strike (LS-6 1000kg)' and O[OPT]['Cost']==105
assert (O[OPT]['Turret0Id'],O[OPT]['Turret1Id'])==(OLD,OLD1) and all(not O[OPT].get(f'Turret{i}Id') for i in range(2,21))
lsrow=[x for x in TW.values() if x['TurretId']==OLD and W[x['WeaponId']]['HUDName']=='LS-6 1000kg'];assert len(lsrow)==1
pl15w=[x['WeaponId'] for x in TW.values() if x['TurretId']==OLD and W[x['WeaponId']]['HUDName']=='PL-15']+[x['WeaponId'] for x in TW.values() if x['TurretId']==OLD1]
assert any(x['UnitId']==MD and x['TurretId']==EMPTY for x in TU.values())
NEW=g.add('TurretsJson',T[OLD],{'Name':'PLA air pylon LS-6 1000kg x2','ModelFileName':T[2018251]['ModelFileName']})
g.add('TurretWeaponsJson',lsrow[0],{'TurretId':NEW,'Order':0})
tu_old=[x for x in TU.values() if x['UnitId']==MD and x['TurretId'] in (OLD,OLD1)]
g.add('TurretUnitsJson',tu_old[0],{'TurretId':NEW})
used=lambda tr:any(o['Id']!=OPT and tr in [o.get(f'Turret{i}Id') for i in range(21)] for o in O.values() if o['ModificationId']==O[OPT]['ModificationId'])
removed=[]
for x in tu_old:
    if not used(x['TurretId']):g.remove('TurretUnitsJson',x['Id']);removed.append(x['TurretId'])
for wid in pl15w:
    still=any(tw['WeaponId']==wid for tw in TW.values() for tu in TU.values() if tu['UnitId']==MD and tu['TurretId']==tw['TurretId'])
    if not still:
        for r in [r for r in WA.values() if r['UnitId']==MD and r['WeaponId']==wid]:g.remove('WeaponAmmunitionsJson',r['Id']);removed.append(('ammo',wid))
g.put('OptionsJson',OPT,{'Turret0Id':NEW,'Turret1Id':EMPTY,'UIName':'Heavy strike (2x LS-6 1000kg)','Cost':60})
ORDER=[31008,31009,31012,31013,31011,31027,31010,31015,31014]
for i,oid in enumerate(ORDER):
    if O[oid]['Order']!=i:g.put('OptionsJson',oid,{'Order':i})
assert U[1181]['HUDName']=='Godswords 东方神剑' and U[1181]['Cost']==80;g.put('Units',1181,{'Cost':100})
for aid in (549,2000177,2014293):
    assert A[aid]['PenetrationAtGroundRange']==700.0 and A[aid]['IsTopArmorArmorAttack'];g.put('AmmunitionsJson',aid,{'PenetrationAtMinRange':140.0,'PenetrationAtGroundRange':140.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
o=O[OPT];ok((o['Turret0Id'],o['Turret1Id'],o['Cost'],o['UIName'])==(NEW,EMPTY,60,'Heavy strike (2x LS-6 1000kg)'),'MD-22 heavy strike')
ok([W[x['WeaponId']]['HUDName'] for x in TW.values() if x['TurretId']==NEW]==['LS-6 1000kg'],'no PL-15 on new mount')
ok(sorted(O[i]['Order'] for i in ORDER)==list(range(9)),'order')
ok(U[1181]['Cost']==100,'Godswords 100')
for aid in (549,2000177,2014293):ok(A[aid]['PenetrationAtGroundRange']==140.0,('pen',aid))
for tu in TU.values():
    if tu['UnitId']==MD:ok(tu['TurretId'] in T,('mount exists',tu['TurretId']))
for wid in {tw['WeaponId'] for tu in TU.values() if tu['UnitId']==MD for tw in TW.values() if tw['TurretId']==tu['TurretId']}:
    ok(any(r['UnitId']==MD and r['WeaponId']==wid for r in WA.values()),('ammo row for mounted weapon',wid))
receipt={'version':V,'base':'0.8.0-dev.29','base_sha256':BASE,'request':'Osama 13 Nov 02:20 PST: MD-22 LS-6 1000kg loadout without PL-15s, repriced, called Heavy strike; GAM-102LR and Spike 140 penetration',
 'md22':{'option':OPT,'new_mount':NEW,'cost':[105,60],'removed':removed},'penetration_140':[549,2000177,2014293],'godswords':[80,100],'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['md22'])
