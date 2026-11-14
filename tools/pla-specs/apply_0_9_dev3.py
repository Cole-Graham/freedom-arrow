"""Freedom Arrow 0.9.0-dev.3 batch over exact 0.9.0-dev.2. Built only when Osama or Lateralus say the batch is ready
(Osama 14 Nov 11:05 PST: batch changes, the package is big). Append new sections before rec.update and rerun.
- Loadout swap prices (12the12, #bug-report 14 Nov 2026; Osama 14:58 PST, thread 1571296493074124892: "verify that all units in the
  current build do not have this issue and fix them"). A loadout that swaps the card to another unit row must leave that row at
  base + option, as in vanilla; the battlegroup overview shows the row's own price, the deck editor shows base + option.
  Of 73 swaps in dev.2, two differed:
  - Spetsnaz Alpha stand-off (row 354): 95 -> 90 (85 + 5; Lateralus 0.6 dev.15 set the total to 90 and left the row at 95).
  - Troopers AA +RPG (row 706): 60 -> 65 (65 + 0; dev.31 set the card to 65 and left the row at the price-scale 60).
  tools/pla-specs/audit_swap_prices.py now runs in package_0_8_next.py, so a build with a split price fails.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
from audit_swap_prices import mismatches
V='0.9.0-dev.3';PREV='0.9.0-dev.2'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
# ---------- Loadout swap prices (12the12 bug report; Osama 14:58 PST) ----------
found=mismatches(U,O,M)
ok(sorted((b,o,r,rc) for b,_,_,o,_,r,rc in found)==[(131,1511,354,95),(413,3334,706,60)],found)
ok(U[131]['Cost']==85 and O[1511]['Cost']==5 and U[413]['Cost']==65 and O[3334]['Cost']==0,'base and option prices as in dev.2')
g.put('Units',354,{'Cost':90});g.put('Units',706,{'Cost':65})
ok(not mismatches(U,O,M),'no swap price mismatch left')
rec['swap_prices']={'Spetsnaz Alpha stand-off (354)':[95,90],'Troopers AA +RPG (706)':[60,65]}
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
