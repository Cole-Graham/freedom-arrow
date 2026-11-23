"""Freedom Arrow 0.8.0-dev.75 over exact 0.8.0-dev.74 (Osama 13 Nov 19:45 PST, thread 1567745029781454889: "DF-17 2000 supply"):
- DF-17/ZF (1028) missile ammunition 2010351: SupplyCost 1000 -> 2000. Resupply time (120 s) unchanged.
- SR-5 (934), Osama 19:46 PST "change the weapon name (right now its HIMARS and ATACM)": its four launchers were the vanilla
  HIMARS weapons 10/254/37/569 on HIMARS turrets 9/81/82/779, shared with the M142 HIMARS (11). SR-5 now has its own copies
  (same stats) named after its munitions: Fire Dragon 70, Fire Dragon 70 CLU, Fire Dragon 300, Fire Dragon 480.
  The Fire Dragon 300 loadout no longer renames the unit to "ATACMS" (ReplaceUnitName cleared). Vanilla rows unchanged.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.75'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.74.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,A,WA,W,T,TW,TU,O,M=(t[k] for k in ('Units','AmmunitionsJson','WeaponAmmunitionsJson','WeaponsJson','TurretsJson','TurretWeaponsJson','TurretUnitsJson','OptionsJson','ModificationsJson'))
DF17,AM=1028,2010351
assert U[DF17]['HUDName']=='DF-17/ZF' and sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==AM})==[DF17]
assert sorted({r['AmmunitionId'] for r in WA.values() if r['UnitId']==DF17})==[AM]
before=A[AM]['SupplyCost'];g.put('AmmunitionsJson',AM,{'SupplyCost':2000.0})
SR5=934;assert U[SR5]['HUDName']=='SR-5'
sr5opts=[o for o in O.values() if M.get(o['ModificationId'],{}).get('UnitId')==SR5]
renamed={}
for wid,tid,name in ((10,9,'Fire Dragon 70'),(254,81,'Fire Dragon 70 CLU'),(37,82,'Fire Dragon 300'),(569,779,'Fire Dragon 480')):
    tw=[r for r in TW.values() if r['TurretId']==tid];assert [r['WeaponId'] for r in tw]==[wid] and T[tid]['ParentTurretId'] is None
    nw=g.add('WeaponsJson',W[wid],{'Name':'PLA SR-5 '+name,'HUDName':name})
    nt=g.add('TurretsJson',T[tid],{'Name':T[tid]['Name'].replace('HIMARS','PLA SR-5')})
    g.add('TurretWeaponsJson',tw[0],{'WeaponId':nw,'TurretId':nt})
    tu=[r for r in TU.values() if r['UnitId']==SR5 and r['TurretId']==tid];assert len(tu)==1;g.put('TurretUnitsJson',tu[0]['Id'],{'TurretId':nt})
    for o in sr5opts:
        for i in range(21):
            if o[f'Turret{i}Id']==tid:g.put('OptionsJson',o['Id'],{f'Turret{i}Id':nt})
    wa=[r for r in WA.values() if r['UnitId']==SR5 and r['WeaponId']==wid];assert len(wa)==1;g.put('WeaponAmmunitionsJson',wa[0]['Id'],{'WeaponId':nw})
    renamed[name]={'weapon':[wid,nw],'turret':[tid,nt]}
for o in sr5opts:
    if o.get('ReplaceUnitName'):g.put('OptionsJson',o['Id'],{'ReplaceUnitName':None})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(A[AM]['SupplyCost']==2000.0 and A[AM]['ResupplyTime']==120.0,'DF-17 supply 2000, resupply time unchanged')
ok(sorted(W[r['WeaponId']]['HUDName'] for r in WA.values() if r['UnitId']==SR5 and 'Fire Dragon' in A[r['AmmunitionId']]['HUDName'])==sorted(renamed),'SR-5 launcher names')
ok(not any('HIMARS' in (W[r['WeaponId']]['HUDName'] or '') or 'ATACMS' in (W[r['WeaponId']]['HUDName'] or '') for r in WA.values() if r['UnitId']==SR5),'no HIMARS/ATACMS weapon names on SR-5')
ok(all(all(W[v['weapon'][1]][k]==W[v['weapon'][0]][k] for k in W[v['weapon'][0]] if k not in ('Id','Name','HUDName')) for v in renamed.values()),'SR-5 launcher stats = HIMARS')
ok({r['TurretId'] for r in TU.values() if r['UnitId']==11}>={9,81,82,779} and [W[x]['HUDName'] for x in (10,254,37,569)]==['HIMARS','HIMARS','ATACMS','HIMARS'],'vanilla HIMARS untouched')
ok(not any(o.get('ReplaceUnitName') for o in sr5opts) and not ({o[f'Turret{i}Id'] for o in sr5opts for i in range(21)}&{9,81,82,779}),'SR-5 options use own turrets, keep name')
receipt={'version':V,'base':'0.8.0-dev.74','base_sha256':BASE,'request':'Osama 13 Nov 19:45 PST: DF-17 2000 supply; 19:46 SR-5 change the weapon name (right now its HIMARS and ATACM)','df17':{'ammunition':AM,'supply_cost':[before,2000.0]},'sr5':renamed,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['df17'],json.dumps(renamed))
