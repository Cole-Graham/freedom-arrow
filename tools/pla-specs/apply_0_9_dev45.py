"""Freedom Arrow 0.9.0-dev.45 data over exact 0.9.0-dev.44 (19 Nov 2026). Opened by BA Codex thread 1572962048705429598 (Lateralus, JRVG-1 overpressure).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.45';PREV='0.9.0-dev.44'
# dev.44 was built in out/local-dev44.
BASE=json.loads((REL/f'out/local-dev44/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev44/FreedomArrow-{PREV}-complete.bamod'
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
_A=t['AmmunitionsJson'];_WA=t['WeaponAmmunitionsJson']
# ---------- JRVG-1 HE: no overpressure (Lateralus 19 Nov 2026 05:1x PST, thread 1572962048705429598: "JRVG-1 seems to be attacking the top armor of tanks
# via the overpressure mechanic by firing HE at it" ... "yes"). Ammo 2009953 '76 mm HE (proximity)' (JRVG-1 952 only) got OverpressureRadius 4.5 in Build 68
# (apply_build68.py copied the Mark 45 127 mm HE, ammo 446, an indirect ground-only shell). The round kept direct fire and TargetType 63 (Vehicle bit).
# ShellHitSystem.InternalUpdate sets IsTargetOverpressured on the directly struck unit when OverpressureRadius > 0, with no distance test (1.2.2.1 RVA
# 0x7fe0f0), so every direct HE hit used roof armour: 8 x 60^2/(60^2+100^2) = 2.12 per hit on an MBT roof (HEAT top 100), ~7 hits per 14 HP tank.
# No vanilla AA gun round has OverpressureRadius > 0 (Derivatsiya 57 mm HE 201 = 0). After: side HEAT 200 = 0.66, front ~0.02-0.03.
ok(U[952]['HUDName']=='JRVG-1' and _A[2009953]['HUDName']=='76 mm HE (proximity)' and _A[2009953]['OverpressureRadius']==4.5,'JRVG-1 proximity HE, OP 4.5')
ok({r['UnitId'] for r in _WA.values() if r['AmmunitionId']==2009953}=={952},'ammo 2009953 used by JRVG-1 only')
ok(_A[201]['Name']=='Round 57 2A91 Derivatsiya AAG HE T3' and _A[201]['OverpressureRadius']==0,'vanilla Derivatsiya HE has no overpressure')
g.put('AmmunitionsJson',2009953,{'OverpressureRadius':0.0})
ok(_A[2009953]['OverpressureRadius']==0.0,'JRVG-1 proximity HE OP 0')
rec['jrvg1_he_no_overpressure']={'ammo':2009953,'unit':952,'OverpressureRadius':[4.5,0.0],'why':'direct hits with OP > 0 always use roof armour','verified':'data checks only; not seen in game'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
