"""Freedom Arrow 0.8.0-dev.59 over exact 0.8.0-dev.58 (Osama 13 Nov 16:20 PST, thread 1569806740139282476):
"It's [the FK-2000's] guns should be the same as Pgz 625 except dual guns".
- FK-2000 (935) gun 2009599 and its ammo 2009603 take the PGL-625 gun stats (weapon 2009365 / ammo 2009369, the Pantsir
  2A38M stats from dev.57): the only stat that differed was muzzle velocity 805 -> 1610; rounds 70 -> 133 as on the PGL-625.
- Dual guns: the FK-2000 mount carries the gun twice (two weapon slots), named "30 mm AA gun". The FK-2000 SAM is unchanged.
FK-2000's own icon, sound, tracer model and names stay.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.59';PREV='0.8.0-dev.58'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser();p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];TW=t['TurretWeaponsJson'];WA=t['WeaponAmmunitionsJson']
FK,PG=935,920;assert U[FK]['HUDName']=='FK-2000' and U[PG]['HUDName']=='PGL-625'
FW,FA,PW,PA=2009599,2009603,2009365,2009369
VIS={'Id','Name','HUDName','HUDIcon','AudioPreset','ModelFileName','FXPreset'}
before={'weapon':{k:W[FW].get(k) for k in W[PW] if k not in VIS and W[FW].get(k)!=W[PW].get(k)},'ammo':{k:A[FA].get(k) for k in A[PA] if k not in VIS and A[FA].get(k)!=A[PA].get(k)}}
g.put('WeaponsJson',FW,{**{k:copy.deepcopy(v) for k,v in W[PW].items() if k not in VIS},'HUDName':'30 mm AA gun'})
g.put('AmmunitionsJson',FA,{**{k:copy.deepcopy(v) for k,v in A[PA].items() if k not in VIS},'HUDName':'30 mm AA gun ammunition'})
fwa=next(x for x in WA.values() if x['UnitId']==FK and x['WeaponId']==FW);pwa=next(x for x in WA.values() if x['UnitId']==PG and x['WeaponId']==PW)
g.put('WeaponAmmunitionsJson',fwa['Id'],{'Quantity':pwa['Quantity']})
tws=sorted([r for r in TW.values() if r['TurretId']==2009600],key=lambda r:r['Order']);assert [r['WeaponId'] for r in tws]==[FW,2009605],tws
g.add('TurretWeaponsJson',tws[0],{'Order':1});g.put('TurretWeaponsJson',tws[1]['Id'],{'Order':2})
checks=0
for k in W[PW]:
    if k not in VIS:assert W[FW].get(k)==W[PW].get(k),k;checks+=1
for k in A[PA]:
    if k not in VIS:assert A[FA].get(k)==A[PA].get(k),k;checks+=1
guns=[r for r in TW.values() if r['TurretId']==2009600 and r['WeaponId']==FW];assert len(guns)==2;checks+=1
rec={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 16:20 PST: FK-2000 guns same as PGL-625 except dual','changed_from':before,'rounds':pwa['Quantity'],'guns':2,'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');print('checks',checks,json.dumps(before))
