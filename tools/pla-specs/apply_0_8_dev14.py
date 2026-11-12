"""Freedom Arrow 0.8.0-dev.14 over exact 0.8.0-dev.13 (Osama 12 Nov PST): "the HJ-10 should be the same bradley hellfire
weapon but doesn't require line of sight, it should be very different from the CTL NLOS" / "build it, CH-901 is basically
same thing as the CTL-181" / "The HJ-10 is not FNF btw its SA. But it should basically ignore LOS" / "It can't fire on the move".
- Ground HJ-10 (unit 936): launcher 2009619 and missile 2009623 go back to their 0.8.0-dev.6 rows, the ground AGM-114M
  Hellfire copy (13 damage, 90 penetration, top attack, 1800 m, TrajectoryType 110, interceptable), with a semi-active
  seeker (Seeker 100) and no firing on the move. The runtime fire hook (NlosTrait.cs, nlos.json fire_units/fire_weapons)
  lets it shoot enemies its side has spotted without its own line of sight; the seeker hook keeps the lock.
- CH-901 (ammo 2018448): CTL-181-style precision munition: laser guided, no seeker (Seeker/angle/distance of the ZBD-20
  precision missile it copies). No hook; not interceptable (dev.13).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.14'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.13.json').read_text())['complete']['sha256']
DEV6=REL/'out/0.8/FreedomArrow-0.8.0-dev.6-complete.bamod'
assert hashlib.file_digest(DEV6.open('rb'),'sha256').hexdigest()==json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.6.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base);z6=zipfile.ZipFile(DEV6)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);A=t['AmmunitionsJson'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson']
HJ10U,HJ10W,HJ10A,CH901,ZBDA=936,2009619,2009623,2018448,2018441
old_a=json.loads(z6.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE['AmmunitionsJson']))[str(HJ10A)]
old_w=json.loads(z6.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE['WeaponsJson']))[str(HJ10W)]
assert old_a['TrajectoryType']==110 and old_a['Seeker']==50 and old_w['Type']==81
assert {x['UnitId'] for x in WA.values() if x['WeaponId']==HJ10W or x['AmmunitionId']==HJ10A}=={HJ10U}
g.put('AmmunitionsJson',HJ10A,{**old_a,'Seeker':100})
g.put('WeaponsJson',HJ10W,{**old_w,'CanShootOnTheMove':False})
g.put('AmmunitionsJson',CH901,{k:A[ZBDA][k] for k in ('Seeker','SeekerAngle','MaxSeekerDistance','LaserGuided')})
nlos={'trait':'NLOS','version':V,'note':'fire_units carrying fire_weapons may shoot enemies their side has spotted without own line of sight; missiles in ammunition keep their seeker lock without line of sight (runtime NlosTrait.cs).',
 'ammunition':[HJ10A],'fire_weapons':[HJ10W],'fire_units':[HJ10U],'weapons':[HJ10W],'units':{str(HJ10U):'HJ-10'}}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
h=A[HJ10A]
ok((h['TrajectoryType'],h['Seeker'],h['Damage'],h['PenetrationAtGroundRange'],h['GroundRange'],h['CanBeIntercepted'],h['IsTopArmorArmorAttack'])==(110,100,13.0,90.0,900.0,True,True),'HJ-10 Hellfire semi-active')
ok(W[HJ10W]['CanShootOnTheMove'] is False and not W[HJ10W]['IsVerticalLauncher'],'HJ-10 launcher')
c=A[CH901];ok((c['TrajectoryType'],c['Seeker'],c['LaserGuided'],c['CanBeIntercepted'],c['HUDName'])==(200,0,True,False,'CH-901'),'CH-901 CTL-style')
for tab in t:
    for key,r in before[tab].items():
        if (tab,key) not in (('AmmunitionsJson',HJ10A),('WeaponsJson',HJ10W),('AmmunitionsJson',CH901)):ok(t[tab].get(key)==r,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.13','base_sha256':BASE,'request':'Osama 12 Nov PST: Hellfire HJ-10 without LOS, semi-active, no fire on the move; CH-901 like CTL-181',
 'hj10':{k:h[k] for k in ('TrajectoryType','Seeker','Damage','PenetrationAtGroundRange','GroundRange','MaxSpeed','CanBeIntercepted')},'hj10_launcher':{k:W[HJ10W][k] for k in ('Type','CanShootOnTheMove','IsVerticalLauncher','MagazineSize')},
 'ch901':{k:c[k] for k in ('TrajectoryType','Seeker','LaserGuided','CanBeIntercepted','Damage','PenetrationAtGroundRange')},'nlos':nlos,'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/nlos.json',nlos);save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='nlos'},indent=1))
