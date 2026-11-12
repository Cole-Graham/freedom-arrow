"""Build55 over exact Build54 (Osama 12 Nov 11:17 PST): "PL-15 is AIM-120 but 500 more range. PL-17 is JATM."

- PL-15 and PL-16 (clone): copy the game's AMRAAM row (89) with low/high-altitude range 4000 -> 4500.
- PL-17: copies the game's AIM-260 JATM row (531).
- PL-21: unchanged (awaiting Osama). PL-15C unchanged (AMRAAM).
Names, icons and models of the PLA rows are kept.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-54.json').read_text())['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];U=t['Units']
KEEP=('Id','Name','HUDName','HUDIcon','ModelFileName')
AMRAAM,JATM=89,531;assert A[AMRAAM]['HUDName']=='AMRAAM' and A[JATM]['HUDName']=='AIM-260'
done={}
for aid,am in list(A.items()):
    h=am.get('HUDName') or ''
    users={r['UnitId'] for r in WA.values() if r['AmmunitionId']==aid}
    if aid in native['AmmunitionsJson'] or not users or any(U[u].get('CountryId')!=4 for u in users):continue
    if h.startswith(('PL-15','PL-16')) and not h.startswith('PL-15C'):
        g.put('AmmunitionsJson',aid,{**{k:copy.deepcopy(v) for k,v in A[AMRAAM].items() if k not in KEEP},'LowAltRange':4500.0,'HighAltRange':4500.0});done[aid]=h+' = AMRAAM +500 (4500)'
    elif h.startswith('PL-17'):
        g.put('AmmunitionsJson',aid,{k:copy.deepcopy(v) for k,v in A[JATM].items() if k not in KEEP});done[aid]=h+' = AIM-260 JATM'
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for aid,txt in done.items():
    ref=AMRAAM if 'AMRAAM' in txt else JATM
    for k,v in A[ref].items():
        if k in KEEP:continue
        ok(A[aid][k]==(4500.0 if ref==AMRAAM and k in('LowAltRange','HighAltRange') else v),('field',aid,k))
for tab in t:
    for key,row in before[tab].items():
        if tab!='AmmunitionsJson' or key not in done:ok(t[tab].get(key)==row,('other row changed',tab,key))
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
receipt={'build':55,'base_build':54,'base_sha256':BASE,'ammunition':{str(k):v for k,v in done.items()},'checks':checks}
save('UserData/FreedomArrow/pla-build55.json',receipt);(ROOT/'tools/pla-specs/build55-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');print(json.dumps(receipt,indent=1,ensure_ascii=False))
