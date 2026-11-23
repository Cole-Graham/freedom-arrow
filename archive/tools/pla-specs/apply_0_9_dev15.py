"""Freedom Arrow 0.9.0-dev.15 data over exact 0.9.0-dev.14 (local test build 187, 16 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.15';PREV='0.9.0-dev.14'
# dev.14 was built in out/local-dev14 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev14/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev14/FreedomArrow-{PREV}-complete.bamod'
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
W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];TJ=t['TurretsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson']
# ---------- J-36: slot 0 empty in every loadout (Osama 16 Nov 2026 01:4x PST, Arsenal screenshot of Heavy CAP showing PL-16 x12 instead of 8:
# "its the empty pylon issue, you added 4X Pl-16 onto a pylon that the other loadouts don't clear"). The J-36 (929) is on the Su-57 body,
# whose slot 0 is the gun mount (vanilla Su-57: MainTurret SU57, IsDefault True, GSh-30-1; its loadouts never set slot 0). The J-36 has no
# gun and no default mount, and none of its 7 loadouts set slot 0, so the game puts one of its pylons there: since dev.12 the newest one,
# the PL-16 x4 (2019296) -> 4 extra PL-16 in every loadout (Heavy CAP 8 + 4 = 12). Fix as vanilla does it: a default mount for slot 0, here
# an empty one (copy of 'Turret Empty' 160 with IsDefault True, no model, no weapons). Loadouts keep slot 0 unset like every vanilla Su-57
# loadout (check_mount_weapons refuses loadouts that use a slot the body's loadouts never use).
_jo=[o for o in O.values() if M[o['ModificationId']]['UnitId']==929]
ok(len(_jo)==7 and all(not o.get('Turret0Id') for o in _jo) and not any(TJ[r['TurretId']]['IsDefault'] for r in TU.values() if r['UnitId']==929) and not [x for x in TW.values() if x['TurretId']==160] and not TJ[160]['IsDefault'],'J-36: 7 loadouts, slot 0 unset, no default mount; 160 empty')
_e0=g.add('TurretsJson',TJ[160],{'Name':'PLA J-36 empty gun slot','IsDefault':True})
g.add('TurretUnitsJson',{'UnitId':929,'TurretId':_e0,'Order':0})
ok([r['TurretId'] for r in TU.values() if r['UnitId']==929 and TJ[r['TurretId']]['IsDefault']]==[_e0],'J-36: one default mount, empty')
rec['j36_slot0_empty']={'unit':929,'default_empty_mount':_e0,'extra_removed':'PL-16 x4 (turret 2019296) in slot 0'}
AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
# ---------- JD-3: every China jammer option has that name (Osama 16 Nov 2026 01:4x PST: "All chinese jammers called JD-3, ZTZ-99A gets an option for
# this for +20"). The four jammer options (ZTL-191 31078, ZBL-191 31080, ZTL-191 Recon 31093, ZBD-20 31094) were the vanilla
# 'Custom_Option_ANVLQ6_jammer' (AN/VLQ-6 Hardhat, ability 80, ECM 0.7 = 30%). They show "JD-3 jammer" (custom text, as "GL-5 APS").
_jm={31078:1080,31080:979,31093:1263,31094:945}
ok(all(O[o]['UIName']=='Custom_Option_ANVLQ6_jammer' and O[o]['Ability2Id']==80 and M[O[o]['ModificationId']]['UnitId']==u for o,u in _jm.items()) and AB[80]['ECMAccuracyMultiplier']==0.7,'four China jammer options on ECM Hardhat 80')
for _o in _jm:g.put('OptionsJson',_o,{'UIName':'JD-3 jammer'})
# ZTZ-99A (904): no options yet, one default ability 2009067 (no ECM). New protection slot like the ZBD-20's (vanilla Type 6
# 'Custom_Slot_Protection_system'): None (default ability + empty 4) / JD-3 jammer +20 (default ability + 80). Like vanilla protection slots,
# no option is default. Each option ability gets a non-default unit link (audit_mp_equipment).
ok(not [m for m in M.values() if m['UnitId']==904] and [r['AbilityId'] for r in UAB.values() if r['UnitId']==904]==[2009067] and AB[2009067]['IsDefault'] and not AB[2009067]['ECMAccuracyMultiplier'],'ZTZ-99A: no options, one default ability without ECM')
_pm=g.add('ModificationsJson',M[2019016],{'UnitId':904,'Name':'PLA ZTZ-99A protection','Order':0})
_pn=g.add('OptionsJson',O[31065],{'ModificationId':_pm,'Name':'PLA ZTZ-99A No jammer','Ability1Id':2009067,'Ability2Id':4,'IsDefault':False,'Order':0,'Cost':0})
_pj=g.add('OptionsJson',O[31094],{'ModificationId':_pm,'Name':'PLA ZTZ-99A JD-3 jammer','UIName':'JD-3 jammer','Ability1Id':2009067,'Ability2Id':80,'IsDefault':False,'Order':1,'Cost':20})
for _a in (4,80):g.add('UnitAbilitiesJson',{'UnitId':904,'AbilityId':_a})
ok(all(not O[x].get(f'Turret{i}Id') for x in (_pn,_pj) for i in range(21)),'no turret swap')
rec['jd3']={'renamed':sorted(_jm),'ztz99a':{'modification':_pm,'options':{'None':[_pn,0],'JD-3 jammer':[_pj,20]},'ecm':0.3}}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
