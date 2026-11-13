"""Freedom Arrow 0.8.0-dev.46 over exact 0.8.0-dev.45 (Osama 13 Nov 13:58-14:00 PST, thread 1567745029781454889):
- ZBD-251 ABZ-13 (ammo 2014660, weapon 2014659) takes the Bradley ESV BLAAM stats (TOW-BB ammo 2000185, weapon 613):
  damage, stress, blast, supply, target mask, magazine, reload and burst timing; penetration 60. Its own model, effects,
  sound, icons and launch angles (vertical launch from the ZBD-251) stay.
- Penetration 60 for the TOW-BB (2000185) and the other HE/thermobaric ATGM rows of the same family: Kornet-M 9M133FM-2
  (2000184), Khrizantema 9M123F (2000186), Kornet 9M133F (2000187, 2000189), Kokon 9M114F (2000190), Ataka-M 9M120F (2000191),
  Konkurs-M 9M113F (2000192). Were 70-80.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.46'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.45.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);W,A=t['WeaponsJson'],t['AmmunitionsJson']
TOWBB,BLAAM,ABZA,ABZW=2000185,613,2014660,2014659
assert A[TOWBB]['HUDName']=='TOW-BB' and W[BLAAM]['HUDName']=='BLAAM' and A[ABZA]['HUDName']==W[ABZW]['HUDName']=='ABZ-13 anti-personnel'
AMMO_STATS=['Damage','StressDamage','HealthAOERadius','StressAOERadius','OverpressureRadius','AimStartDelay','MuzzleVelocity','ResupplyTime','SupplyCost','TargetType',
 'GroundRange','LowAltRange','HighAltRange','MinimalRange','MaxSpeed','Acceleration','DispersionHorizontalRadius','DispersionVerticalRadius','CanBeIntercepted','CanBeTargeted','IsTopArmorArmorAttack','TopArmorAttack','CriticMultiplier']
WEAPON_STATS=['MagazineSize','MagazineReloadTimeMin','MagazineReloadTimeMax','TimeBetweenBurstsMin','TimeBetweenBurstsMax','TimeBetweenShotsInBurstMin','TimeBetweenShotsInBurstMax','ShotsPerBurstMin','ShotsPerBurstMax','AimTimeMin','AimTimeMax']
abz_before={k:A[ABZA].get(k) for k in AMMO_STATS+['PenetrationAtMinRange','PenetrationAtGroundRange']}|{'w.'+k:W[ABZW].get(k) for k in WEAPON_STATS}
g.put('AmmunitionsJson',ABZA,{k:A[TOWBB][k] for k in AMMO_STATS if k in A[TOWBB]})
g.put('WeaponsJson',ABZW,{k:W[BLAAM][k] for k in WEAPON_STATS if k in W[BLAAM]})
HE={2000184:'9M133FM-2',2000185:'TOW-BB',2000186:'9M123F',2000187:'9M133F',2000189:'9M133F',2000190:'9M114F',2000191:'Ataka-M 9M120F',2000192:'9M113F',ABZA:'ABZ-13 anti-personnel'}
pen_before={}
for aid,hud in HE.items():
    assert A[aid]['HUDName']==hud,(aid,A[aid]['HUDName']);pen_before[aid]=A[aid]['PenetrationAtGroundRange']
    g.put('AmmunitionsJson',aid,{'PenetrationAtMinRange':60.0,'PenetrationAtGroundRange':60.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for k in AMMO_STATS:
    if k in A[TOWBB]:ok(A[ABZA][k]==A[TOWBB][k],('ABZ ammo',k))
for k in WEAPON_STATS:
    if k in W[BLAAM]:ok(W[ABZW][k]==W[BLAAM][k],('ABZ weapon',k))
for aid in HE:ok(A[aid]['PenetrationAtMinRange']==A[aid]['PenetrationAtGroundRange']==60.0,('pen 60',aid))
ok(W[ABZW]['LowerVerticalAngle']==-85 and A[ABZA]['ModelFileName']=='Ammo\\Missile_Kornet_LOD','ABZ-13 launch geometry and model kept')
receipt={'version':V,'base':'0.8.0-dev.45','base_sha256':BASE,'request':'Osama 13 Nov 13:58-14:00 PST: ZBD-251 ABZ-13 same stats as the Bradley ESV BLAAM missiles, 60 mm penetration; TOW-BB and similar HE ATGMs 60 mm penetration too',
 'abz13':{'before':abz_before,'after':{k:A[ABZA].get(k) for k in AMMO_STATS+['PenetrationAtGroundRange']}|{'w.'+k:W[ABZW].get(k) for k in WEAPON_STATS}},
 'penetration_60':{str(k):[HE[k],pen_before[k],60.0] for k in HE},'not_changed':'air-launched HE missiles (Griffin 70, LMUR 100, Hellfire AGM-114M 90, Kh-BPLA 80), Konkurs UAV 9M113F (35), infantry thermobaric rockets','checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks);print(json.dumps(receipt['abz13'],indent=0)[:1500]);print(receipt['penetration_60'])
