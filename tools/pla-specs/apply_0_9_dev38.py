"""Freedom Arrow 0.9.0-dev.38 data over exact 0.9.0-dev.37 (18 Nov 2026). Opened by BA Codex thread 1572551547726991400 (Osama, PLZ-07 splash).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.38';PREV='0.9.0-dev.37'
# dev.37 was built in out/local-dev37.
BASE=json.loads((REL/f'out/local-dev37/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev37/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- Not table data, but in this batch (Osama 18 Nov 2026, thread 1571014792016171120): China voices regenerated with a word-for-word
# check, 10 Selection/Move/Attack lines per unit (commit 952fbc88). Packaged from the voice folder; no runtime DLL change for voices.
# ---------- China 122 mm explosion effect -> the 152-155 mm howitzer effect (Osama 18 Nov 2026 02:1x PST, thread 1572551547726991400: "many of the
# units in our Chinese faction have these massive explosive shockwaves ... Let's try option A for now"). Option A as offered: every China 122 mm round
# uses the 152-155 mm howitzer explosion (vanilla Msta-S, Koalitsiya, Paladin), which Osama says looks fine. Effect only: no damage, splash, range or
# spread change. The vanilla 2S1 (174) keeps its own 122 mm effect. This reverses the dev.36 move of the smoke and GP6 rounds to the 122 mm effect.
# Data reading (18 Nov, GameAssembly 1.2.2.1): these rounds were field-for-field the 2S1 HE except names, the game resizes impact effects from data
# only for burning rounds (DamageOverTimeDuration > 0), and the supply dump explosion is vanilla ammo 459, untouched by FA. So the large brown
# shockwave is not shown to come from FA data; this swap is a visual trial. Not yet seen in game.
_P='AMMUNITION_VFX_PRESET_';_old=_P+'SHELL_120mm_HE';_new=_P+'SHELL_152-155mm_HE'
_A=t['AmmunitionsJson'];_WA=t['WeaponAmmunitionsJson']
_cn={2009545:931,2010413:None,2010465:1037,2010479:1038,2010505:None,2010533:None,2010547:None,2018959:1037,2018961:1040,2018963:931,2018965:931}
_users={}
for _r in _WA.values():_users.setdefault(_r['AmmunitionId'],set()).add(_r['UnitId'])
_on=sorted(i for i,r in _A.items() if r.get('FXPreset')==_old and _users.get(i))
ok(_on==sorted([174]+list(_cn)),('rounds on the 122 mm effect',_on))
ok(all(int(U[u].get('CountryId') or 0)==4 for i in _cn for u in _users[i]),'only China units fire these rounds')
ok(_new in {r.get('FXPreset') for i,r in _A.items() if i in native['AmmunitionsJson']},'152-155 mm effect is vanilla')
for _i in _cn:
    g.put('AmmunitionsJson',_i,{'FXPreset':_new});ok(_A[_i]['FXPreset']==_new,(_i,'152-155 mm effect'))
ok(_A[174]['FXPreset']==_old,'vanilla 2S1 keeps the 122 mm effect')
rec['china_122mm_fx_152']={'from':_old,'to':_new,'rounds':{str(i):_A[i]['HUDName'] for i in _cn},'units':sorted({U[u]['HUDName'] for i in _cn for u in _users[i]})}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
