"""Freedom Arrow 0.8.0-dev.65 over exact 0.8.0-dev.64 (Osama 13 Nov 18:0x PST, thread 1567745029781454889):
- AP 500-550 for ZTL-191, VT-5 and ZTQ-15 (and their Recon copies): 105 mm DU APFSDS penetration 550 at close range and
  500 at full range. ZTQ-15/VT-5 ammo 2009131 was 500/475; ZTL-191 ammo 2011301 was 575/550.
- FH-97A (1253) and MD-22 (976): SEAD loadouts removed (Light SEAD and Heavy SEAD), with the mounts and ammo rows only
  they used; remaining loadouts renumbered in order.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.65'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.64.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,WA,A,O,M,TU,TW=(t[k] for k in ('Units','WeaponAmmunitionsJson','AmmunitionsJson','OptionsJson','ModificationsJson','TurretUnitsJson','TurretWeaponsJson'))
log={}
# ---- AP
ALLOWED={2009131:{906,1240,1261,1262},2011301:{1080,1263}}
for aid,units in ALLOWED.items():
    users={r['UnitId'] for r in WA.values() if r['AmmunitionId']==aid};assert users<=units|{u for u in users if not U.get(u,{}).get('DisplayInArmory')},(aid,users)
    assert A[aid]['HUDName']=='105 mm DU APFSDS';log[aid]=[A[aid]['PenetrationAtMinRange'],A[aid]['PenetrationAtGroundRange'],sorted(users)]
    g.put('AmmunitionsJson',aid,{'PenetrationAtMinRange':550.0,'PenetrationAtGroundRange':500.0})
# ---- SEAD removal
removed={}
for uid,name in ((976,'MD-22'),(1253,'FH-97A')):
    assert U[uid]['HUDName']==name
    mods=[m for m in M.values() if m['UnitId']==uid];opts=[o for o in O.values() if o['ModificationId'] in {m['Id'] for m in mods}]
    sead=[o for o in opts if 'SEAD' in (o.get('UIName') or '')];assert len(sead)==2,(name,[o['UIName'] for o in sead])
    keep=[o for o in opts if o not in sead]
    used=lambda tid:any(tid in [o.get(f'Turret{i}Id') for i in range(21)] for o in keep)
    gone_t=[]
    for o in sead:g.remove('OptionsJson',o['Id'])
    for r in [r for r in TU.values() if r['UnitId']==uid]:
        if any(r['TurretId'] in [o.get(f'Turret{i}Id') for i in range(21)] for o in sead) and not used(r['TurretId']) and r['TurretId']!=160:
            g.remove('TurretUnitsJson',r['Id']);gone_t.append(r['TurretId'])
    mounted={tw['WeaponId'] for r in TU.values() if r['UnitId']==uid for tw in TW.values() if tw['TurretId']==r['TurretId']}
    gone_w=[]
    for r in [r for r in WA.values() if r['UnitId']==uid]:
        if r['WeaponId'] not in mounted:g.remove('WeaponAmmunitionsJson',r['Id']);gone_w.append(r['WeaponId'])
    for m in mods:
        for i,o in enumerate(sorted([o for o in O.values() if o['ModificationId']==m['Id']],key=lambda o:(o['Order'],o['Id']))):
            if o['Order']!=i:g.put('OptionsJson',o['Id'],{'Order':i})
    removed[name]={'options':[(o['Id'],o['UIName']) for o in sead],'turret_rows_for':gone_t,'ammo_rows_for_weapons':gone_w}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for aid in ALLOWED:ok((A[aid]['PenetrationAtMinRange'],A[aid]['PenetrationAtGroundRange'])==(550.0,500.0),('AP',aid))
for uid in (976,1253):
    opts=[o for o in O.values() if o['ModificationId'] in {m['Id'] for m in M.values() if m['UnitId']==uid}]
    ok(not any('SEAD' in (o.get('UIName') or '') for o in opts),('no SEAD',uid))
    ok(sorted(o['Order'] for o in opts)==list(range(len(opts))),('order',uid))
    for o in opts:
        for i in range(21):
            tid=o.get(f'Turret{i}Id')
            if tid:ok(any(r['UnitId']==uid and r['TurretId']==tid for r in TU.values()),('option mount on unit',o['Id'],tid))
    mounted={tw['WeaponId'] for r in TU.values() if r['UnitId']==uid for tw in TW.values() if tw['TurretId']==r['TurretId']}
    for w in mounted:ok(any(r['UnitId']==uid and r['WeaponId']==w for r in WA.values()),('ammo row for mounted weapon',uid,w))
receipt={'version':V,'base':'0.8.0-dev.64','base_sha256':BASE,'request':'Osama 13 Nov 18:0x PST: ZTL-191 needs AP 500-550, same for VT-5 and ZTQ-15; FH-97, MD-22 remove SEAD loadouts',
 'ap_before':{str(k):v for k,v in log.items()},'removed':removed,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(log),json.dumps(removed))
