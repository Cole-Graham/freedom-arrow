"""Freedom Arrow 0.9.0-dev.34 data over exact 0.9.0-dev.33 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.34';PREV='0.9.0-dev.33'
# dev.33 was built in out/local-dev33.
BASE=json.loads((REL/f'out/local-dev33/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev33/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- Blood Wolves Chinese name (Osama 16 Nov 2026 18:2x PST, thread 1571014792016171120: "Chinese name for blood wolves should be zhurihe
# wolves from the 195th"). Zhurihe is the PLA training base whose opposing force, the 195th Brigade, plays the US side; this is why the squad speaks
# English (its new voice set). Card name only: the internal Name stays, so lookups by name keep working.
_bw=U[1183];ok(_bw['HUDName']=='Blood Wolves 血狼','Blood Wolves 1183')
g.put('Units',1183,{'HUDName':'Blood Wolves 朱日和之狼','Description':'Zhurihe Wolves (朱日和之狼) of the 195th Brigade, the Zhurihe training base opposing force that fights and talks like US forces. '+_bw['Description']})
ok(U[1183]['HUDName']=='Blood Wolves 朱日和之狼','Blood Wolves renamed');rec['blood_wolves_name']={'unit':1183,'HUDName':['Blood Wolves 血狼','Blood Wolves 朱日和之狼']}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
