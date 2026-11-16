"""Freedom Arrow 0.9.0-dev.24 data over exact 0.9.0-dev.23 (local build 197, 16 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.24';PREV='0.9.0-dev.23'
# dev.23 was built in out/local-dev23 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev23/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev23/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- LSDW child turret weapon at list position 0 (Osama 16 Nov 2026 04:56 PST on dev.23: "the APS is missing from the unit card and the
# weapon is missing ... when I load the APS loadout on the tank ... will not start the scenario"). dev.23 copied the laser's TurretWeapons row from
# mount 1 with Order 2. The game puts each weapon at index Order of the turret's weapon list, so the child turret had Weapons = [null, LSDW]
# (TurretDiag log on Osama's PC), and copying that null threw NullReferenceException in Turrets.CloneWithClonedWeaponsAndTurrets (unit card,
# editor, RefundSystem). The vanilla T-90M cupola 414 has its only weapon at Order 0. Measured on Osama's PC with this one change (05:0x PST):
# Arsenal cards show the LSDW weapon and the laser APS icon, the editor scenario loads and plays, the laser APS intercepts HJ-8 at 230-241 m.
TW=t['TurretWeaponsJson'];TJ=t['TurretsJson'];W=t['WeaponsJson']
_lw=[w['Id'] for w in W.values() if w.get('HUDName')=='LSDW'];ok(len(_lw)==1,'one LSDW weapon');_lw=_lw[0]
ok([r['Order'] for r in TW.values() if r['TurretId']==414]==[0],'vanilla T-90M cupola 414: its one weapon at Order 0')
for _u,_c,_r in ((904,2019404,2019405),(1083,2019408,2019409)):
    ok(TJ[_c].get('ParentTurretId') in (2019389,2019395),f'unit {_u}: {_c} is the LSDW child turret')
    ok([x['Id'] for x in TW.values() if x['TurretId']==_c]==[_r] and TW[_r]['WeaponId']==_lw and TW[_r]['Order']==2,f'unit {_u}: dev.23 LSDW row {_r} at Order 2')
    g.put('TurretWeaponsJson',_r,{'Order':0})
    ok(TW[_r]['Order']==0,f'unit {_u}: LSDW row {_r} now at Order 0')
# Every child turret's weapon orders must be 0..n-1, or its weapon list has a null hole. All 86 vanilla child turrets follow this (57 vanilla
# top-level turrets do not, and work, so the check is for child turrets only).
_tw={}
for x in TW.values():_tw.setdefault(x['TurretId'],[]).append(x.get('Order',0))
_holes=sorted(k for k,v in _tw.items() if TJ.get(k,{}).get('ParentTurretId') and sorted(v)!=list(range(len(v))))
ok(not _holes,f'child turrets with a hole in the weapon order: {_holes[:20]}')
rec['lsdw_child_order']={'rows':[2019405,2019409],'order':0,'note':'child turret weapon list was [null, LSDW]'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
