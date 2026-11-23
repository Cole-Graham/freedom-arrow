"""Freedom Arrow 0.9.0-dev.22 data over exact 0.9.0-dev.21 (local build 194, 16 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.22';PREV='0.9.0-dev.21'
# dev.21 was built in out/local-dev21 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev21/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev21/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- LSDW option button uses the LSDW weapon icon (Osama 16 Nov 2026 04:1x PST, thread 1571014792016171120, dev.21 Arsenal screenshot:
# "the icon for the loadout should use the LSDW weapon icon"). dev.21 showed the square shield ability icon squashed on the wide option button.
# The unit-card APS entry keeps the shield icon (dazzler.json cardIcon).
_ls=[o for o in O.values() if o.get('Name') in ('PLA ZTZ-99A LSDW','PLA ZTZ-99 LSDW')]
ok(len(_ls)==2 and all(o['OptionPicture']=='FA_PLA_ABILITY_LSDW' and o['Cost']==100 for o in _ls),'two LSDW options (+100) with the shield picture')
for _o in _ls:g.put('OptionsJson',_o['Id'],{'OptionPicture':'FA_PLA_WP_LSDW_DAZZLER'})
ok((SRC/'runtime-qa/icons/FA_PLA_WP_LSDW_DAZZLER.png').exists(),'LSDW weapon icon embedded')
rec['lsdw_option_picture']={'options':sorted(o['Id'] for o in _ls),'picture':'FA_PLA_WP_LSDW_DAZZLER'}
# ---------- LSDW laser on the 12.7 mm mount, not the coax (Osama 16 Nov 2026 04:2x PST, dev.21 test: "the laser only shoots if I turn off the main
# gun, I think that means we need to swap the 50 cal, not the 762"). dev.21 put the LSDW weapon in a copy of the main mount (mount 0) in place of
# the 7.62 coax, so it was tied to the main gun. Now the LSDW option keeps the normal main mount and swaps mount 1 (the QJC-88 12.7 mm commander
# mount, its own turret) for a copy with the LSDW weapon; the 7.62 coax stays. The two dev.21 LSDW turret rows are reused as the mount-1 copies.
# Every protection option sets both Turret0Id and Turret1Id (vanilla Bradley pattern).
TJ=t['TurretsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson'];W=t['WeaponsJson']
_lw=[w['Id'] for w in W.values() if w.get('HUDName')=='LSDW'];ok(len(_lw)==1,'one LSDW weapon');_lw=_lw[0]
for _u,_m0,_m1,_t,_mg,_opts,_lsdw in ((904,2009072,2009086,2019389,2009085,(31098,31099),31100),(1083,2011382,2011396,2019395,2011395,(31101,),31102)):
    ok(O[_lsdw]['Turret0Id']==_t and not O[_lsdw].get('Turret1Id') and [r['Order'] for r in TU.values() if r['TurretId']==_t]==[0],f'unit {_u}: dev.21 LSDW option on main-mount copy {_t}')
    ok([x['WeaponId'] for x in TW.values() if x['TurretId']==_m1]==[_mg] and TJ[_m1]['IsDefault'],f'unit {_u}: mount 1 {_m1} = 12.7 mm only')
    g.put('TurretsJson',_t,{k:(TJ[_m1].get(k) if k in TJ[_m1] else None) for k in set(TJ[_t])|set(TJ[_m1]) if k!='Id'}|{'Name':TJ[_m1]['Name']+' LSDW','IsDefault':False})
    for r in [r for r in TU.values() if r['TurretId']==_t]:g.put('TurretUnitsJson',r['Id'],{'Order':1})
    _rows=sorted(x['Id'] for x in TW.values() if x['TurretId']==_t);_ref=[x for x in TW.values() if x['TurretId']==_m1][0]
    g.put('TurretWeaponsJson',_rows[0],{'WeaponId':_lw,'Order':_ref['Order'],'WeaponChannel':_ref['WeaponChannel'],'WeaponPriority':_ref['WeaponPriority']})
    for _r in _rows[1:]:g.remove('TurretWeaponsJson',_r)
    for _o in _opts:g.put('OptionsJson',_o,{'Turret0Id':_m0,'Turret1Id':_m1})
    g.put('OptionsJson',_lsdw,{'Turret0Id':_m0,'Turret1Id':_t})
    ok([x['WeaponId'] for x in TW.values() if x['TurretId']==_t]==[_lw],f'unit {_u}: LSDW mount-1 copy holds only the LSDW weapon')
g.put('WeaponsJson',_lw,{'VerticalRotationSpeed':W[2009085]['VerticalRotationSpeed']})
rec['lsdw_mount1']={'turrets':[2019389,2019395],'weapon':_lw}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
