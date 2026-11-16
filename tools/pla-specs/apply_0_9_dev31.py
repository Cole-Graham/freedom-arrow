"""Freedom Arrow 0.9.0-dev.31 data over exact 0.9.0-dev.30 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama: LY-1 APS 10 s).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.31';PREV='0.9.0-dev.30'
# dev.30 was built in out/local-dev30.
BASE=json.loads((REL/f'out/local-dev30/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev30/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- LY-1 laser APS cooldown 3 s -> 10 s (Osama 16 Nov 2026 14:0x PST, thread 1571014792016171120: "the LY-1 needs a 10 second aps cd").
# The LY-1's one built-in ability is its own copy of the LSDW APS ('PLA LY-1 laser defense', dev.27), so only the LY-1 changes.
_ly=[a_['Id'] for a_ in AB.values() if a_.get('Name')=='PLA LY-1 laser defense'];ok(len(_ly)==1 and AB[_ly[0]]['APSCooldown']==3.0 and AB[_ly[0]]['IsAPS'],'LY-1 laser APS, 3 s');_ly=_ly[0]
ok(sorted({U[r['UnitId']]['HUDName'] for r in UAB.values() if r['AbilityId']==_ly})==['LY-1'],'LY-1 APS used by the LY-1 only')
g.put('AbilitiesJson',_ly,{'APSCooldown':10.0})
ok(AB[_ly]['APSCooldown']==10.0,'LY-1 laser APS 10 s')
rec['ly1_aps_cooldown']={'ability':_ly,'cooldown_s':10.0}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

