"""Freedom Arrow 0.9.0-dev.37 data over exact 0.9.0-dev.36 (17 Nov 2026). Opened by BA Codex thread 1572407822849810463 (Osama, China cosmetic work).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.37';PREV='0.9.0-dev.36'
# dev.36 was built in out/local-dev36.
BASE=json.loads((REL/f'out/local-dev36/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev36/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- "all of our spec names need their Chinese names displayed. It should be after the English" (Osama 17 Nov 2026 16:4x PST, thread
# 1572407822849810463). UIName only; internal Name, slots and points unchanged. 22 (Test) is not a player spec and is left alone.
# Chinese = the PLA's own service names: 空军 Air Force, 陆军装甲兵 Army armored troops, 火箭军 Rocket Force, 海军特种部队 Navy special forces,
# 陆军摩托化部队 Army motorized force. Untested in game: the spec name font must draw CJK (unit names with Chinese already do in the armory).
_S=t['SpecializationsJson']
_cn={17:('PLAAF Air Force','空军'),18:('PLAGF Armored Force','陆军装甲兵'),19:('PLARF Rocket Conscript Force','火箭军'),20:('PLAN Special Forces','海军特种部队'),21:('PLAGF Motorized','陆军摩托化部队')}
for _k,(_en,_zh) in _cn.items():
    ok(_S[_k].get('CountryId')==4 and _S[_k]['UIName']==_en,f'spec {_k} UIName {_en}')
    g.put('SpecializationsJson',_k,{'UIName':f'{_en} {_zh}'});ok(_S[_k]['UIName']==f'{_en} {_zh}',f'spec {_k} Chinese name')
rec['spec_chinese_names']={str(k):f'{e} {z}' for k,(e,z) in _cn.items()}
# ---------- Not table data, but in this batch (Osama 17 Nov 2026 17:0x PST, thread 1572407822849810463):
# - SF night card portraits (v2, red light): runtime-qa/icons/FA_CN_INF_SF_CQC-Portrait.png and FA_CN_INF_SF_HIGH_TECH-Portrait.png. Embedded in
#   FreedomArrow.Runtime.dll (CardIcons.cs): REBUILD THE RUNTIME DLL for dev.37.
# - 110 Blood Wolves / Godswords US-callout clips, staged by tools/china-voice/stage.py into ChinaVoice/Infantry/English and Units/*_EN.
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
