"""Freedom Arrow 0.9.0-dev.23 data over exact 0.9.0-dev.22 (local build 195, 16 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.23';PREV='0.9.0-dev.22'
# dev.22 was built in out/local-dev22 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev22/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev22/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- LSDW laser as a child turret of the main mount (Osama 16 Nov 2026 04:4x PST: scenario editor "An error occurred while loading the
# scenario", NullReferenceException in Turrets.CloneWithClonedWeaponsAndTurrets from UnitsInfoService.ApplyCurrentMods, on dev.22). dev.22's
# LSDW option set Turret1Id; the vanilla T-90M body (ZTZ-99A/99 base) never uses loadout slot 1: its roof MG is a child turret of the main turret
# (vanilla 413/414 CupolaTurret, ParentTurretId = main turret, IsDefault False). check_mount_weapons.py refused it; dev.22 wrongly relaxed that
# check (restored). Now, as the vanilla T-90M: the LSDW option sets only Turret0Id = a copy of the main mount (main gun + 7.62 coax, same model)
# with a child turret holding the LSDW laser, so the laser aims and fires on its own (dev.21 problem: as the coax it waited for the main gun).
# The default 12.7 mm mount 1 stays on every option. The dev.21/22 rows 2019389/2019395 become the main-mount copies again.
TJ=t['TurretsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson'];W=t['WeaponsJson']
_lw=[w['Id'] for w in W.values() if w.get('HUDName')=='LSDW'];ok(len(_lw)==1,'one LSDW weapon');_lw=_lw[0]
ok(TJ[414].get('ParentTurretId')==415 and not TJ[414].get('IsDefault') and [r.get('Order',0) for r in TU.values() if r['TurretId']==414]==[0],'vanilla T-90M cupola 414: child of 415, not default, slot 0')
for _u,_m0,_m1,_t,_opts,_lsdw in ((904,2009072,2009086,2019389,(31098,31099),31100),(1083,2011382,2011396,2019395,(31101,),31102)):
    ok(O[_lsdw].get('Turret1Id')==_t and O[_lsdw].get('Turret0Id')==_m0,f'unit {_u}: dev.22 LSDW option uses slot 1')
    g.put('TurretsJson',_t,{k:(TJ[_m0].get(k) if k in TJ[_m0] else None) for k in set(TJ[_t])|set(TJ[_m0]) if k!='Id'}|{'Name':TJ[_m0]['Name']+' LSDW','IsDefault':False})
    for r in [r for r in TU.values() if r['TurretId']==_t]:g.put('TurretUnitsJson',r['Id'],{'Order':0})
    _old=sorted(x['Id'] for x in TW.values() if x['TurretId']==_t);_src=sorted([x for x in TW.values() if x['TurretId']==_m0],key=lambda x:x['Id'])
    g.put('TurretWeaponsJson',_old[0],{k:v for k,v in _src[0].items() if k not in ('Id','TurretId')})
    for x in _src[1:]:g.add('TurretWeaponsJson',x,{'TurretId':_t})
    for _r in _old[1:]:g.remove('TurretWeaponsJson',_r)
    _c=g.add('TurretsJson',TJ[_m1],{'Name':TJ[_m0]['Name']+' LSDW laser','IsDefault':False,'ParentTurretId':_t,'ModelFileName':None})
    _ref=[x for x in TW.values() if x['TurretId']==_m1][0]
    g.add('TurretWeaponsJson',_ref,{'TurretId':_c,'WeaponId':_lw})
    g.add('TurretUnitsJson',{'UnitId':_u,'TurretId':_c,'Order':0})
    for _o in _opts+(_lsdw,):g.put('OptionsJson',_o,{'Turret1Id':0})
    g.put('OptionsJson',_lsdw,{'Turret0Id':_t})
    ok(sorted(W[x['WeaponId']]['HUDName'] for x in TW.values() if x['TurretId']==_t)==sorted(W[x['WeaponId']]['HUDName'] for x in TW.values() if x['TurretId']==_m0),f'unit {_u}: LSDW main-mount copy = main gun + coax')
    ok([x['WeaponId'] for x in TW.values() if x['TurretId']==_c]==[_lw] and TJ[_c]['ParentTurretId']==_t,f'unit {_u}: LSDW laser child turret')
rec['lsdw_child_turret']={'main_copies':[2019389,2019395],'note':'laser on a child turret of the main-mount copy; options use slot 0 only'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
