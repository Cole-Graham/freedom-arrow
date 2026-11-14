"""Freedom Arrow 0.8.0-dev.68 over exact 0.8.0-dev.67 (Osama 13 Nov 18:3x PST, thread 1567745029781454889):
PLARF Infantry 步兵 (1175) without the HJ-73D: the member carrying it keeps his QBZ-95 and has no special weapon; the HJ-73D
squad-weapon row and its ammo row (6 missiles) go. Squad weapon order renumbered. Price unchanged (50).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.68'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.67.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,SQM,SQW,W,WA=(t[k] for k in ('Units','SquadMembersJson','SquadWeaponsJson','WeaponsJson','WeaponAmmunitionsJson'))
INF,HJ=1175,2012643
assert U[INF]['HUDName']=='Infantry 步兵' and W[HJ]['HUDName']=='HJ-73D'
mem=[r for r in SQM.values() if r['UnitId']==INF and r['SpecialWeaponId']==HJ];assert len(mem)==1
g.put('SquadMembersJson',mem[0]['Id'],{'SpecialWeaponId':0})
sqw=[r for r in SQW.values() if r['UnitId']==INF and r['WeaponId']==HJ];wa=[r for r in WA.values() if r['UnitId']==INF and r['WeaponId']==HJ];assert len(sqw)==len(wa)==1
g.remove('SquadWeaponsJson',sqw[0]['Id']);g.remove('WeaponAmmunitionsJson',wa[0]['Id'])
for i,r in enumerate(sorted([r for r in SQW.values() if r['UnitId']==INF],key=lambda r:(r['Order'],r['Id']))):
    if r['Order']!=i:g.put('SquadWeaponsJson',r['Id'],{'Order':i})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(not any(r['UnitId']==INF and HJ in (r['PrimaryWeaponId'],r['SpecialWeaponId']) for r in SQM.values()),'no member carries HJ-73D')
ok(not any(r['UnitId']==INF and r['WeaponId']==HJ for r in list(SQW.values())+list(WA.values())),'no HJ-73D rows')
ok(sum(r['UnitId']==INF for r in SQM.values())==7,'still 7 men')
ws={r['WeaponId'] for r in SQW.values() if r['UnitId']==INF};ok(all(any(x['UnitId']==INF and x['WeaponId']==w for x in WA.values()) for w in ws),'every squad weapon has ammo')
ok(sorted(r['Order'] for r in SQW.values() if r['UnitId']==INF)==list(range(len(ws))),'order')
ok(any(r['UnitId']==1168 and r['WeaponId']==HJ for r in WA.values()),'HJ-73D Team keeps its HJ-73D')
receipt={'version':V,'base':'0.8.0-dev.67','base_sha256':BASE,'request':'Osama 13 Nov 18:3x PST: Infantry PLARF remove HJ-73D','member':mem[0]['Id'],'removed_rows':{'squad_weapon':sqw[0]['Id'],'ammo':wa[0]['Id']},'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
