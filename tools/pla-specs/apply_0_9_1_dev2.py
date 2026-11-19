"""Freedom Arrow 0.9.1-dev.2 data over exact 0.9.1-dev.1 (19 Nov 2026). Opened by BA Codex thread 1572962048705429598 (Lateralus, Infantry 步兵 price).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.1-dev.2';PREV='0.9.1-dev.1'
# 0.9.1-dev.1 was built in out/local-091dev1.
BASE=json.loads((REL/f'out/local-091dev1/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-091dev1/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
# ---------- Infantry 步兵 50 -> 35 (Lateralus 19 Nov 2026 08:1x PST, thread 1572962048705429598: "lower Infantry 步兵 price from 50 -> 35").
# Unit 1175: 7 men, 4 QBZ-95, 2 QBB-95, 1 QBU-88, 6 single-shot PF-89 (its internal Name "PLA Designer 47 Missile-Site Security — HJ-73D" is a
# stale squad-designer label; it carries no HJ-73D). No loadout options and no swap rows (OptionsJson.ReplaceUnitId) point at it.
ok(U[1175]['HUDName']=='Infantry 步兵' and U[1175]['Cost']==50,'Infantry 步兵 1175 at 50')
_mods={i for i,m in t['ModificationsJson'].items() if m['UnitId']==1175}
ok(not [o for o in t['OptionsJson'].values() if o.get('ModificationId') in _mods or o.get('ReplaceUnitId')==1175],'no options or swap rows on 1175')
g.put('Units',1175,{'Cost':35});ok(U[1175]['Cost']==35,'Infantry 步兵 35')
rec['infantry_1175_price']={'unit':1175,'cost':[50,35],'verified':'data checks only'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
