"""Freedom Arrow 0.9.0-dev.36 data over exact 0.9.0-dev.35 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.36';PREV='0.9.0-dev.35'
# dev.35 was built in out/local-dev35.
BASE=json.loads((REL/f'out/local-dev35/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev35/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- "a lot of models have this weird giant 2d splash, see it on the JRVG in skirmish" / "the weird giant bomb splash" (Osama 16 Nov 2026 22:2x-22:4x PST,
# thread 1571014792016171120). The JRVG-1 76 mm proximity round (ammo, JRVG-1 only) uses AMMUNITION_VFX_PRESET_SHELL_127mm_HE, an effect only ships use in
# vanilla (naval gun, sea impact). No other land unit uses a ship-only effect. It gets the 57 mm HE effect its other round uses. Not yet seen in game.
_A=t['AmmunitionsJson']
_jr=[x for x in t['WeaponAmmunitionsJson'].values() if x['UnitId']==952];_px=[x['AmmunitionId'] for x in _jr if _A[x['AmmunitionId']].get('HUDName')=='76 mm HE (proximity)']
ok(len(_px)==1 and _A[_px[0]]['FXPreset']=='AMMUNITION_VFX_PRESET_SHELL_127mm_HE' and {x['UnitId'] for x in t['WeaponAmmunitionsJson'].values() if x['AmmunitionId']==_px[0]}=={952},'JRVG-1 proximity round on the naval 127 mm effect, JRVG only')
g.put('AmmunitionsJson',_px[0],{'FXPreset':'AMMUNITION_VFX_PRESET_ROUND_57mm_HE'});ok(_A[_px[0]]['FXPreset']=='AMMUNITION_VFX_PRESET_ROUND_57mm_HE','JRVG-1 proximity round 57 mm HE effect')
rec['jrvg_proximity_fx']={'ammo':_px[0],'fx':['AMMUNITION_VFX_PRESET_SHELL_127mm_HE','AMMUNITION_VFX_PRESET_ROUND_57mm_HE']}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
