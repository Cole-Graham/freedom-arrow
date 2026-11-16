"""Freedom Arrow 0.9.0-dev.25 data over exact 0.9.0-dev.24 (16 Nov 2026). Opened by BA Codex thread 1571554273639006392 (Lateralus).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.25';PREV='0.9.0-dev.24'
# dev.24 was built in out/local-dev24 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev24/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev24/FreedomArrow-{PREV}-complete.bamod'
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
W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];AM=t['AmmunitionsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson']
# ---------- Lateralus SPAAG/SAM vs SEAD data (15 Nov 2026), queued for dev.13 but missing from every package dev.13-dev.24 (found 16 Nov 06:0x
# PST: 116 weapon fields and 12 gun-round damages still dev.12; the dev.13 receipt has no spaag_sead key). Lateralus 16 Nov 06:07 PST: "queue it
# for the next build along with all the missing changes". Values and old-value checks: lateralus/spaag_sead_data.py. The packager's
# lateralus/queued_checks.py fails the build if these values are not in the finished package.
sys.path.insert(0,str(Path(__file__).parent/'lateralus'))
import spaag_sead_data
rec['spaag_sead']=spaag_sead_data.apply(t,lambda tab,i,f:g.put(tab,i,f),ok)
# ---------- Lateralus SEAD prices (16 Nov 2026 08:3x PST, "looks good, queue it up for the next build"; sheet 1Y0rUZ0Do1uMdGyENd1TsnvSWi4ecTLYMQSBLrEiLCC4):
# 13 SEAD planes -20% base (strike/multirole planes exempt), 54 SEAD options lose half of their SEAD share, helicopters options only.
import sead_prices
rec['sead_prices']=sead_prices.apply(t,lambda tab,i,f:g.put(tab,i,f),ok)
# ---------- Plane ECM pods 10% each (same message: "make ECM pods give 10% ECM per pod on planes"): 26 pod options, see lateralus/ecm_pods.py.
import ecm_pods
rec['ecm_pods']=ecm_pods.apply(t,g,ok)
# The plane sale (Lateralus 16 Nov 06:07 PST, "#23 (plane sale) is no longer a proposal") is runtime only: runtime-qa/PlaneSale.cs,
# ServerMoney.cs and UserData/FreedomArrow/plane-refund.json (shipped by package_0_8_next.py). No table changes.
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
