"""Freedom Arrow 0.9.0-dev.26 data over exact 0.9.0-dev.25 (16 Nov 2026). Opened by BA Codex thread 1571554273639006392 (Lateralus).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.26';PREV='0.9.0-dev.25'
# dev.25 was built in out/local-dev25.
BASE=json.loads((REL/f'out/local-dev25/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev25/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
sys.path.insert(0,str(Path(__file__).parent/'lateralus'))
# ---------- Stryker M-SHORAD laser on the unit card (Lateralus 16 Nov 2026, "queue up a fix to add the laser icon to unit card when the APKSW
# loadout is selected on the stryker shorad"): the game merges only the first chosen option's Ability1, and every armour option also fills
# Ability1, so the dev.25 laser was dropped. The laser moves to Ability2 of option 1937. See lateralus/mshorad_laser_slot.py.
import mshorad_laser_slot as MLS
rec['mshorad_laser_slot']=MLS.apply(t,g,ok)
avail={r.get('UnitId') for r in t['SpecializationAvailabilitiesJson'].values()}
coll=MLS.slot_collisions(U,M,O,AB,avail);ok(not coll,f'no unit has two modifications filling one ability slot with a real ability: {coll}')
# Maps (Lateralus 16 Nov 2026): Klaipeda, Kadaga and Jelgava 1v1 zones A B C 2, D E 4 (scenarios/common.py END_VALUES and
# FAConquestPrototype/settings.json); Central Village 1v1 and Chernyakhovsky removed from make_scenario.py and settings, and the installed
# copies retired by GUID in runtime-qa/Runtime.cs. No table changes; the packager rebuilds the scenarios and drops the removed ones.
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
