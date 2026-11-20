"""Freedom Arrow 0.9.2-dev.1 data over exact 0.9.1 (19 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama, QN-506 / Type 86 spawn failure).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.2-dev.1';PREV='0.9.1'
# 0.9.1 was built in out/local-091.
BASE=json.loads((REL/f'out/local-091/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-091/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- Weapon positions on body hull slots (Osama 19 Nov 2026 16:3x PST, thread 1571014792016171120: "can we make sure they're fixed?",
# after End's 0.9.1 log: "CombatSystem initialization for unit=PLA QN-506 failed" and "...PLA Catalogue Type 86 — original turret failed",
# IndexOutOfRange in UnitBuilder.SetupWeaponComponents, then a TurretComponent error every frame). Game code 1.2.2.1:
#  - InitCombatSystem(UnitModelInfo, Units) 0x3470C0 gives the unit's turret i the BODY prefab's turret script MainTurrets[i].
#  - SetupWeaponComponents 0x351B20 walks the turret's weapon list (padded with nulls up to each row's Order, LoadUnits.LoadWeapons) and, for
#    each real weapon at index k, reads that script's weapon point k (bounds check 0x351EEE). Null pads are skipped.
#  So a weapon at Order k on a body slot that vanilla fills with a model-less hull mount needs that hull mount to have more than k points.
#  BMPT slots 1/2 (AGS-17), BMD-2 slot 1 and BMP-3F slot 1 (PKT) have 1 point; Pantsir slot 0 has 2 (2A38M, 57E6E).
#  The dev.7 fix (QN-201 off slot 2) cut the count only; Osama's own GameLogs show QN-506 failing on 15, 16 and 17 Nov after it.
# Fix: each weapon takes the lowest free position its vanilla body slot has. Its muzzle may move to the body's hull weapon point.
_FIX=[  # (turret, weapon, unit names, Order before, Order after)
    (2009642,2009641,'QN-506 mount 1 Type 86 7.62 mm',1,0),
    (2009648,2009647,'QN-506 mount 2 QN-502',2,0),
    (2010896,2010895,'ZBD-86 / ZBD-86 Recon x2 mount 1 Type 86 7.62 mm',1,0),
    (2011202,2011201,'ZBD-05 mount 1 Type 86 7.62 mm',1,0),
    (2009600,2009605,'FK-2000 mount 0 FK-2000 SAM',2,1)]
TW=t['TurretWeaponsJson'];rec['hull_slot_weapon_order']=[]
for tid,wid,name,o0,o1 in _FIX:
    rows=[r for r in TW.values() if r['TurretId']==tid]
    ok([(r['WeaponId'],r['Order']) for r in rows if r['WeaponId']==wid]==[(wid,o0)],(name,[(r['WeaponId'],r['Order']) for r in rows]))
    ok(all(r['Order']!=o1 for r in rows if r['WeaponId']!=wid),(name,'target position taken'))
    rid=next(r['Id'] for r in rows if r['WeaponId']==wid);g.put('TurretWeaponsJson',rid,{'Order':o1});ok(TW[rid]['Order']==o1,name)
    rec['hull_slot_weapon_order'].append({'turret':tid,'weapon':wid,'row':rid,'name':name,'Order':[o0,o1]})
ok(sorted(r['UnitId'] for r in t['TurretUnitsJson'].values() if r['TurretId']==2010896)==[1063,1258,1259],'Type 86 mount 1 is on the 3 ZBD-86 cards')
rec['hull_slot_weapon_order_verified']='data checks only'
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
