"""Freedom Arrow 0.8.0-dev.24 over exact 0.8.0-dev.23 (ZSL-92 dark textures, ded9bbda). Request: Osama 13 Nov 01:37 PST, thread 1567745029781454889):
- Godswords 90 -> 80 points.
- QLU-11: XM25 rate of fire (dev.21's 10% slowdown removed); still the XM25 round out to 1000 m (500 world) with spread scaled.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.24'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.23.json').read_text())['complete']['sha256']
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
GW,QLU,XM=1181,2004002,365
assert U[GW]['HUDName']=='Godswords 东方神剑' and U[GW]['Cost']==90;g.put('Units',GW,{'Cost':80})
assert W[QLU]['HUDName']=='QLU-11' and W[XM]['HUDName']=='XM25 Punisher'
F=('TimeBetweenBurstsMin','TimeBetweenBurstsMax','MagazineReloadTimeMin','MagazineReloadTimeMax')
g.put('WeaponsJson',QLU,{k:W[XM][k] for k in F})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(U[GW]['Cost']==80,'Godswords 80')
ok(all(W[QLU][k]==W[XM][k] for k in F),'QLU-11 XM25 rate')
ok(t['AmmunitionsJson'][2004003]['GroundRange']==500.0,'QLU-11 1000 m kept')
for tab in t:
    for key,row in before[tab].items():
        if (tab,key) not in {('Units',GW),('WeaponsJson',QLU)}:ok(t[tab].get(key)==row,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.23','base_sha256':BASE,'request':'Osama 13 Nov 01:37 PST: Godswords 80 pts; QLU-11 = XM25 at 1000 m, same rate of fire',
 'godswords':[90,80],'qlu11_rate':{k:[before['WeaponsJson'][QLU][k],W[QLU][k]] for k in F},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:receipt[k] for k in ('godswords','qlu11_rate')}),'checks',checks)
