"""Freedom Arrow 0.8.0-dev.45 over exact 0.8.0-dev.44 (Osama 13 Nov 13:52 PST, thread 1567745029781454889):
- HJ-10 vehicle launchers (AFT-10 'HJ-10' card 2009619, hidden AFT-10 2010721, ZBD-251 2014655) get their own weapon icon
  FA_PLA_HJ10 (+ _OUTLINE), drawn from Osama's Red Arrow 10B photo (tools/pla-specs/hj10-icon/make_icon.py). They showed the
  US Hellfire (HELLFIRE_X2) or the generic PLA ATGM icon. Air AKD-10 racks keep their Hellfire rack icons.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.45'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.44.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);W=t['WeaponsJson']
ICON='FA_PLA_HJ10';assert (SRC/f'runtime-qa/icons/{ICON}.png').exists() and (SRC/f'runtime-qa/icons/{ICON}_OUTLINE.png').exists()
ids={2009619:'PLA HJ-10 HJ-10',2010721:'PLA AFT-10 HJ-10',2014655:'PLA ZBD-251 HJ-10'};before={}
for wid,name in ids.items():
    assert W[wid]['Name']==name and W[wid]['HUDName']=='HJ-10',W[wid];before[wid]=W[wid]['HUDIcon'];g.put('WeaponsJson',wid,{'HUDIcon':ICON})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for wid in ids:ok(W[wid]['HUDIcon']==ICON,('icon',wid))
ok(all(w['HUDIcon']!=ICON for w in W.values() if w['Id'] not in ids),'only the vehicle launchers')
receipt={'version':V,'base':'0.8.0-dev.44','base_sha256':BASE,'request':'Osama 13 Nov 13:52 PST: Here is the HJ-10, make a weapon icon for the vehicle variant',
 'icon':ICON,'weapons':{str(k):[before[k],ICON] for k in ids},'source':'Discord attachment 1570919354122633287 (proportions only; drawn silhouette)','checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['weapons'])
