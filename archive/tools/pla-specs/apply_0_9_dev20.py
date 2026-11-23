"""Freedom Arrow 0.9.0-dev.20 over exact 0.9.0-dev.19 (16 Nov 2026): port to Broken Arrow 1.2.2.1, second package (dev.19 kept the old
FreedomArrow/compatibility.json pin; package_0_8_next.py now carries it). No data changes.
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.20';PREV='0.9.0-dev.19'
# dev.19 was built in out/local-dev19 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev19/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev19/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- Port to Broken Arrow 1.2.2.1 (Steam build 26627577, hotfix of 16 Nov 2026; Osama 02:4x PST "there was a BA update just now",
# 02:49 "prepare a proper port"). Read from the new game files (work/game-1.2.2.1, work/port-1.2.2.1): all 24 DataBaseCompiled tables
# decrypt to the same plaintext (every source_plaintext_sha256 pin still matches), so the data stays as dev.18. Changed: GameAssembly
# sha256 12e70883 -> 007c0195 (FreedomArrow and FAConquestPrototype compatibility.json, CramPrediction gate), the MelonLoader interop
# pins (Il2CppBrokenArrow 390b2b82, Il2CppNetworkCommon f458ce7c), and the two camera-zoom call sites (-0x680, same bytes).
ok(U[1061]['HUDName']=='ZTZ-80' and AB[2009067]['IsAPS'],'dev.19 base (ZTZ-80 name, ZTZ-99A dazzler APS)')
rec['port']={'game':'1.2.2.1','steam_build':26627577,'game_assembly':'007c019575fabcf16748fcdc02052d3bb2571757b8bfd8c69b05508eaf022cc1','tables':'unchanged (24 plaintext pins match)'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
