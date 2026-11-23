"""Freedom Arrow 0.9.4-dev.2 batch data over exact 0.9.4-dev.1 (build 248). Opened by BA Codex thread 1573418243715113213 (Osama, Blue Dragon K2 HEAT tier + Type 74 (G)).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections before the check-mode exit, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
raise SystemExit("RETIRED 21 Nov 2026: blue_dragon_dev2.apply now runs inside apply_0_9_4_dev1.py (the one cumulative 0.9.4 batch over 0.9.3). Run that instead.")
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent),str(Path(__file__).parent/'lateralus')]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.4-dev.2';PREV='0.9.4-dev.1'
# 0.9.4-dev.1 (build 248, 21 Nov 2026) was built in out/local-094dev1.
BASE=json.loads((REL/f'out/local-094dev1/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-094dev1/FreedomArrow-{PREV}-complete.bamod'
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
O=t['OptionsJson'];SM=t['SquadMembersJson'];WA=t['WeaponAmmunitionsJson'];W=t['WeaponsJson']
# ---------- 1. Spetsnaz Alpha, stand-off loadout: 6 RPG-30 (Osama 20 Nov 2026 13:2x PST, thread 1567745029781454889: "Next patch, we need to give 6 rpg

# ---------- 1. Blue Dragon (Osama 21 Nov 2026 14:5x PST, thread 1573418243715113213): K2 front HEAT 1100 -> 1075 ("make sure their tanks follow our new HEAT
# rules") and a Type 74 (G) card with the normal hand-loaded M68 ("add a Type 74G that's the normal real loader option"). See blue_dragon_dev2.py.
import blue_dragon_dev2;blue_dragon_dev2.apply(t,g,ok,rec)
rec['verified']='data checks only'
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
