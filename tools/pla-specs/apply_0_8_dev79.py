"""Freedom Arrow 0.8.0-dev.79 over exact 0.8.0-dev.78 (Osama 13 Nov 20:19 PST, thread 1567745029781454889: "J-36 should be 100 pts less"):
- J-36 (929) unit cost 315 -> 215. Loadout prices unchanged, so every J-36 card is 100 points cheaper
  (Heavy CAP 315+255 = 570 -> 470).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.79'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.78.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units']
J36=929;assert U[J36]['HUDName']=='J-36' and U[J36]['Cost']==315
g.put('Units',J36,{'Cost':215})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(U[J36]['Cost']==215,'J-36 cost 215')
receipt={'version':V,'base':'0.8.0-dev.78','base_sha256':BASE,'request':'Osama 13 Nov 20:19 PST: J-36 should be 100 pts less','j36_cost':[315,215],'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['j36_cost'])
