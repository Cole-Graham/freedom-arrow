"""Freedom Arrow 0.8.0-dev.27 over exact 0.8.0-dev.26 (Osama 13 Nov 02:05 PST, thread 1567745029781454889):
- QLU-11 round (ammunition 2004003): almost no dispersion, as a smart (programmable airburst) grenade launcher.
  DispersionHorizontalRadius 16.667 -> 0.5, DispersionVerticalRadius 3.333 -> 0.25, DispersionMinimal 0. Every round lands
  inside a squad's hit box out to 1000 m. XM25 and the QTS-11 grenade launcher are unchanged.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.27'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.26.json').read_text())['complete']['sha256']
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
QA=2004003;A=t['AmmunitionsJson'];assert A[QA]['Name']=='PLA Test Grenade Launcher QLU11 ammunition' and A[QA]['GroundRange']==500.0
g.put('AmmunitionsJson',QA,{'DispersionHorizontalRadius':0.5,'DispersionVerticalRadius':0.25,'DispersionMinimal':0.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok((A[QA]['DispersionHorizontalRadius'],A[QA]['DispersionVerticalRadius'])==(0.5,0.25),'QLU-11 dispersion')
for tab in t:
    for key,row in before[tab].items():
        if (tab,key)!=('AmmunitionsJson',QA):ok(t[tab].get(key)==row,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.26','base_sha256':BASE,'request':'Osama 13 Nov 02:05 PST: QLU-11 should have very little to no dispersion, it is a smart grenade launcher',
 'qlu11_dispersion':{k:[before['AmmunitionsJson'][QA][k],A[QA][k]] for k in ('DispersionHorizontalRadius','DispersionVerticalRadius','DispersionMinimal')},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['qlu11_dispersion'])
