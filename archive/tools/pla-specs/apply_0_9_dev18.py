"""Freedom Arrow 0.9.0-dev.18 data over exact 0.9.0-dev.17 (local test build 190, 16 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.18';PREV='0.9.0-dev.17'
# dev.17 was built in out/local-dev17 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev17/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev17/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- ZTZ-99A laser dazzler (Osama 16 Nov 2026 01:5x-02:2x PST, thread 1571014792016171120: "how can we model the laser dazzler?",
# "make it look like APS but shoots at ATGMs", "maybe 100m is fine ... like an APS that has a longer range", "we don't want it stopping rpgs
# and recoilless rounds", "make it bright red", "add it to our current build I'll test it"). Every ZTZ-99A (904) gets a native APS in its
# default ability 2009067 (smoke stays): 2 charges, 10 s cooldown, refill 200 supply / 10 s like FA's 2-charge APS rows (Drozd2, Afghanit; FA cooldown 10, vanilla 6). APSHitboxProportion 1.0
# so the native code never grows the box; runtime-qa/Dazzler.cs (dazzler.json, units [904], reach 100 m) grows it only for guided
# interceptable missiles and lets unguided rounds (RPG, recoilless) through. Both protection options (None / JD-3) keep 2009067.
_d=AB[2009067];ok(_d['IsDefault'] and _d.get('IsSmoke') and not _d.get('IsAPS') and [r['AbilityId'] for r in UAB.values() if r['UnitId']==904 and AB[r['AbilityId']].get('IsDefault')]==[2009067],'ZTZ-99A: default ability 2009067 smoke, no APS')
ok(all(AB[x].get('IsAPS') and AB[x]['APSQuantity']==2 and AB[x]['APSCooldown']==10.0 and AB[x]['APSSupplyCost']==200.0 and AB[x]['APSResupplyTime']==10.0 for x in (13,15)),'FA 2-charge APS rows (Drozd2, Afghanit): 10 s, 200 supply, 10 s')
g.put('AbilitiesJson',2009067,{'IsAPS':True,'APSHitboxProportion':1.0,'APSQuantity':2,'APSCooldown':10.0,'APSSupplyCost':200.0,'APSResupplyTime':10.0})
ok(AB[2009067]['IsAPS'] and AB[2009067]['APSQuantity']==2 and AB[2009067]['IsSmoke'],'ZTZ-99A: smoke + 2-charge dazzler APS')
_dz=json.loads((SRC/'UserData/FreedomArrow/dazzler.json').read_text());ok(_dz['units']==[904] and U[904]['HUDName']=='ZTZ-99A' and _dz['reachMeters']==100,'dazzler.json: ZTZ-99A, 100 m')
rec['ztz99a_dazzler']={'unit':904,'ability':2009067,'aps':{'charges':2,'cooldown':10.0,'hitbox':1.0},'runtime':'Dazzler.cs + dazzler.json (100 m, guided only, red beam)'}
# ---------- Hard shading on 17 seller vehicles (Osama 16 Nov 2026 02:3x PST, thread 1567745029781454889: "double check that same balloon and
# shading effect on the ZTQ ... and check all the other units by him"). Models only (62 .fam files, work/pla-0.9/dev18/sharpen.py, corners
# over 45 degrees hard); no data change. Merged into this dev.18 with the dazzler after both threads started dev.18 at once.
rec['models_sharpened']={'files':62,'angle':45}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
