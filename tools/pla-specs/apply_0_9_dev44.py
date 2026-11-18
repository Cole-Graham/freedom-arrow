"""Freedom Arrow 0.9.0-dev.44 data over exact 0.9.0-dev.43 (18 Nov 2026). Opened by BA Codex thread 1567745029781454889 (Osama, HHQ-10 = MML AIM-9).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.44';PREV='0.9.0-dev.43'
# dev.43 was built in out/local-dev43.
BASE=json.loads((REL/f'out/local-dev43/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev43/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- HHQ-10 = MML with AIM-9 in stats, 18 missiles (Osama 18 Nov 2026 13:3x PST, thread 1567745029781454889: "HHQ-10 should be like the MML
# with side winders in stats but of course 18 missiles"). Weapon 2019357 / missile 2019358 (HHQ-10 unit 1273 only) take the combat values of the vanilla
# MML AIM-9 launcher 625 / missile 465. Kept: names, icons, sound and effect, TargetType 1944 (HHQ-10 also engages other missiles; the MML 792 does
# not - a targeting role, left for Osama), 18 rounds, unit price 220.
_W=t['WeaponsJson'];_A=t['AmmunitionsJson'];_WA=t['WeaponAmmunitionsJson']
ok(U[1273]['HUDName']=='HHQ-10' and [(r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in _WA.values() if r['UnitId']==1273]==[(2019357,2019358,18)],'HHQ-10 one launcher, 18 missiles')
ok(sorted({r['UnitId'] for r in _WA.values() if r['WeaponId']==2019357 or r['AmmunitionId']==2019358})==[1273],'HHQ-10 rows used by HHQ-10 only')
ok(_W[625]['Name']=='SAM AIM9 x15 MML' and _A[465]['Name']=='Missile AA AIM9 Ground','MML AIM-9 rows')
_wkeep={'Id','Name','HUDName','HUDIcon','MagazineSize'};_akeep={'Id','Name','HUDName','HUDIcon','AudioPreset','FXPreset','ModelFileName','TargetType'}
_wch={k:v for k,v in _W[625].items() if k not in _wkeep and _W[2019357].get(k)!=v};_ach={k:v for k,v in _A[465].items() if k not in _akeep and _A[2019358].get(k)!=v}
_before={'weapon':{k:_W[2019357].get(k) for k in _wch},'missile':{k:_A[2019358].get(k) for k in _ach}}
g.put('WeaponsJson',2019357,_wch);g.put('AmmunitionsJson',2019358,_ach)
ok(all(_W[2019357].get(k)==v for k,v in _W[625].items() if k not in _wkeep) and _W[2019357]['MagazineSize']==18,'HHQ-10 launcher = MML AIM-9, magazine 18')
ok(all(_A[2019358].get(k)==v for k,v in _A[465].items() if k not in _akeep),'HHQ-10 missile = AIM-9')
rec['hhq10_as_mml_aim9']={'weapon':2019357,'missile':2019358,'from':_before,'to':{'weapon':_wch,'missile':_ach},'kept':'names, icons, sound/FX, TargetType 1944, 18 rounds, cost 220'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
