"""Freedom Arrow 0.9.0-dev.16 data over exact 0.9.0-dev.15 (local test build 188, installed on Osama's PC 16 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.16';PREV='0.9.0-dev.15'
# dev.15 was built in out/local-dev15 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev15/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev15/FreedomArrow-{PREV}-complete.bamod'
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
W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];A=t['AmmunitionsJson'];MOB=t['MobilityJson'];UP=t['UnitPropulsionsJson'];TW=t['TurretWeaponsJson']
# ---------- ZTZ-59D cards get ZTZ-80 stats, faster (Osama 16 Nov 2026 02:0x PST: "change the ZTZ-80 stats to match and make it a faster end tank";
# "Please change the ZTZ-59D to the T-80 stat"). The ZTZ-59D (1061) and ZTZ-59D1 (1260) show the ZTZ-80 model since dev.14. Real Type 80:
# 105 mm rifled gun (ZPL-79/83), 38 t, 730 hp, 57 km/h (en.wikipedia.org/wiki/Type_80/88_main_battle_tank); Type 59D ~36 t, 520-580 hp,
# ~50 km/h. Their gun 2010845 and its 3 rounds are used by these two cards only. Changes (names and prices unchanged):
# - gun "105 mm rifled tank gun"; AP round -> "105 mm APFSDS" 400 close / 375 at range (was 100 mm 350/325; Type 83 APFSDS, about
#   ZTZ-88A level: War Thunder Type-83 APDS 352 mm at 10 m); HEAT 450 and HE 100 unchanged.
# - speed: off-road 45 (unchanged), road 50 -> 72 (road = 1.6 x off-road, the 0.8.0-dev.61 tracked rule); weight 38 t.
ok(sorted({r['UnitId'] for r in WA.values() if r['WeaponId']==2010845})==[1061,1260] and [x['TurretId'] for x in TW.values() if x['WeaponId']==2010845]==[2010846],'59D gun on the two 59D cards only')
_ap=sorted({r['AmmunitionId'] for r in WA.values() if r['WeaponId']==2010845 and A[r['AmmunitionId']]['ArmorTargeted']==1})
ok(_ap==[2010849] and (A[2010849]['PenetrationAtMinRange'],A[2010849]['PenetrationAtGroundRange'])==(350.0,325.0) and sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==2010849})==[1061,1260],'59D AP 350/325, own round')
g.put('WeaponsJson',2010845,{'HUDName':'105 mm rifled tank gun'})
g.put('AmmunitionsJson',2010849,{'HUDName':'105 mm APFSDS','PenetrationAtMinRange':400.0,'PenetrationAtGroundRange':375.0})
for _r in [r for r in WA.values() if r['WeaponId']==2010845 and r['AmmunitionId']!=2010849]:g.put('AmmunitionsJson',_r['AmmunitionId'],{'HUDName':A[_r['AmmunitionId']]['HUDName'].replace('100 mm rifled tank gun','105 mm rifled tank gun')})
for _u in (1061,1260):
    _m=[r['MobilityId'] for r in UP.values() if r['UnitId']==_u];ok(len(_m)==1 and sum(1 for r in UP.values() if r['MobilityId']==_m[0])==1 and (MOB[_m[0]]['MaxSpeedRoad'],MOB[_m[0]]['MaxCrossCountrySpeed'])==(50.0,45.0),(_u,'own mobility 50/45'))
    g.put('MobilityJson',_m[0],{'MaxSpeedRoad':72.0});g.put('Units',_u,{'Weight':38000})
rec['ztz80_stats']={'units':[1061,1260],'gun':'105 mm rifled','apfsds':[400,375],'speed':{'road':[50,72],'offroad':45}}
# ---------- ZBD-20 120 -> 130 points (Osama 16 Nov 2026 02:1x PST: "ZBD-20 to 130 points"). Unit 945 only; the ZBD-20 Recon (1256, 180) keeps its price.
ok(U[945]['HUDName']=='ZBD-20' and U[945]['Cost']==120,'ZBD-20 945 at 120');g.put('Units',945,{'Cost':130});rec['zbd20_cost']=[120,130]
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
