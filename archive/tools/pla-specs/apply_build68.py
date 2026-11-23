"""Build68 over exact Build67 (Osama 12 Nov 13:25 PST: "Just use the naval gun but we'll tune the stats down").

JRVG-1's 76 mm gun becomes a copy of the vanilla Arleigh Burke Mark 45 naval gun (sound, autoloader,
elevation, muzzle flash, shell model and 127 mm HE impact effect), tuned down to Osama's AA numbers:
8 damage, 20 m blast, proximity fuse 7 m, low-altitude range 1200 in data (2400 m displayed), ground 550.
Kept from the AA gun so it still engages aircraft: autocannon weapon type, direct trajectory, air+ground
targets, 1 shot per second (about 8 damage per second). The armour-piercing round is unchanged.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-67.json').read_text())['sha256']
IDENT=('Id','Name','HUDName')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson']
JRVG=952;assert U[JRVG]['HUDName']=='JRVG-1'
mk45w,mk45a=W[598],A[446];assert mk45w['HUDName']=='Mark 45' and mk45a['HUDName']=='127mm HE'
he=next(r for r in WA.values() if r['UnitId']==JRVG and A[r['AmmunitionId']]['LowAltRange']>0)
wid,aid=he['WeaponId'],he['AmmunitionId']
for f,v in(('WeaponId',wid),('AmmunitionId',aid)):assert {r['UnitId'] for r in WA.values() if r[f]==v}=={JRVG}
old_w,old_a=copy.deepcopy(W[wid]),copy.deepcopy(A[aid])
KEEP_W=('Type','MagazineSize','MagazineReloadTimeMin','MagazineReloadTimeMax','ShotsPerBurstMin','ShotsPerBurstMax','TimeBetweenBurstsMin','TimeBetweenBurstsMax','TimeBetweenShotsInBurst','IsLowAltDirectWeapon','IsHighAltDirectWeapon','MultiTargetTracking','SimultaneousTracking')
g.put('WeaponsJson',wid,{**{k:copy.deepcopy(v) for k,v in mk45w.items() if k not in IDENT+KEEP_W},
    'HUDName':'76 mm naval AA gun','Type':old_w['Type'],'MagazineSize':1,'MagazineReloadTimeMin':1.0,'MagazineReloadTimeMax':1.0,'ShotsPerBurstMin':1,'ShotsPerBurstMax':1,
    'TimeBetweenBurstsMin':0.0,'TimeBetweenBurstsMax':0.0,'TimeBetweenShotsInBurst':0.0,**{k:old_w[k] for k in KEEP_W[9:]}})
KEEP_A=('TargetType','TrajectoryType','ArmorTargeted','MuzzleVelocity','MinimalRange','DispersionHorizontalRadius','DispersionVerticalRadius','DispersionMinimal','LaunchMarginAngle','CanBeIntercepted','CanBeTargeted','Seeker')
g.put('AmmunitionsJson',aid,{**{k:copy.deepcopy(v) for k,v in mk45a.items() if k not in IDENT+KEEP_A},'HUDName':'76 mm HE (proximity)',**{k:old_a[k] for k in KEEP_A},
    'Damage':8.0,'HealthAOERadius':20.0,'StressAOERadius':20.0,'RadioFuseDistance':7.0,'GroundRange':550.0,'LowAltRange':1200.0,'HighAltRange':old_a['HighAltRange'],'PenetrationAtMinRange':60.0,'PenetrationAtGroundRange':60.0})
w=W[wid];rate=1/(w['MagazineReloadTimeMin'])
receipt={'build':68,'base_build':67,'base_sha256':BASE,'request':'Osama 12 Nov 13:25 PST',
 'weapon':{k:[old_w.get(k),w[k]] for k in w if old_w.get(k)!=w[k]},'ammo':{k:[old_a.get(k),A[aid][k]] for k in A[aid] if old_a.get(k)!=A[aid][k]},'shots_per_second':rate,'dps_est':8.0*rate}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(A[aid]['TargetType']==old_a['TargetType'] and A[aid]['LowAltRange']==1200.0 and W[wid]['Type']==old_w['Type'],'still an AA gun')
ok(W[wid]['AudioPreset']==mk45w['AudioPreset'] and A[aid]['FXPreset']==mk45a['FXPreset'],'naval gun look and sound')
for uid,u in before['Units'].items():ok(t['Units'][uid]==u,('unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-build68.json',receipt)
(ROOT/'tools/pla-specs/build68-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))
