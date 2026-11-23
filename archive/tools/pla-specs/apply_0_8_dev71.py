"""Freedom Arrow 0.8.0-dev.71 over exact 0.8.0-dev.70 (Osama 13 Nov 18:5x PST, thread 1567745029781454889):
- PGL-625 (920) gun: 20 damage per second. With the Pantsir 2A38M cycle (400-round magazine, 7-10 round bursts 0.2 s apart,
  1.5-2.0 s between bursts, 4-6 s reload) it fires 2.561 rounds/s sustained (dpm_visualizer rate_of_fire_second), so damage
  per round 3.0 -> 7.8 (19.98/s). FB-10 missile unchanged.
- PGL-625 armour: the ZBL-191 profile (armour 2010315: HEAT 700/700/130/20, KE 80/60/30/20, 12 HP).
- WZ-8 (1252) stays high: own copy of its mobility row (169 is shared with the vanilla MiG-31s and MD-22) with
  IsChangeAltitude false, as the vanilla RQ-4, RQ-170 and MQ-9. Its MiG-31 flight preset already defaults to high altitude.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(ROOT.parent/'model-pack-v1/dev-tools')]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
from dpm_visualizer import calculations as calc
V='0.8.0-dev.71'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.70.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,W,A,AR,UA,UP,MOB,WA=(t[k] for k in ('Units','WeaponsJson','AmmunitionsJson','ArmorsJson','UnitArmorsJson','UnitPropulsionsJson','MobilityJson','WeaponAmmunitionsJson'))
PGL,GW,GA,PARM,ZBLARM=920,2009365,2009369,2009357,2010315
assert U[PGL]['HUDName']=='PGL-625' and sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==GA})==[PGL]
rof=calc.rate_of_fire_second(W[GW]);dmg=round(20/rof,1);before_dmg=A[GA]['Damage']
g.put('AmmunitionsJson',GA,{'Damage':dmg})
assert [r['ArmorId'] for r in UA.values() if r['UnitId']==PGL]==[PARM] and sorted({r['UnitId'] for r in UA.values() if r['ArmorId']==PARM})==[PGL]
assert [r['ArmorId'] for r in UA.values() if r['UnitId']==979]==[ZBLARM]
g.put('ArmorsJson',PARM,{k:v for k,v in AR[ZBLARM].items() if k not in ('Id','Name','ModelFileName','IsDefault')})
WZ8=1252;rows=[r for r in UP.values() if r['UnitId']==WZ8];assert len(rows)==1 and rows[0]['MobilityId']==169 and U[WZ8]['HUDName']=='WZ-8'
newmob=g.add('MobilityJson',MOB[169],{'Name':'PLA WZ-8 MobilityJson (high only)','IsChangeAltitude':False})
g.put('UnitPropulsionsJson',rows[0]['Id'],{'MobilityId':newmob})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(abs(calc.rate_of_fire_second(W[GW])*A[GA]['Damage']-20)<0.1,'PGL-625 gun 20 dps')
ok(all(AR[PARM][k]==AR[ZBLARM][k] for k in AR[ZBLARM] if k not in ('Id','Name','ModelFileName','IsDefault')),'ZBL-191 armour profile')
ok(MOB[newmob]['IsChangeAltitude'] is False and MOB[169]['IsChangeAltitude'] is True and all(MOB[newmob][k]==MOB[169][k] for k in MOB[169] if k not in ('Id','Name','IsChangeAltitude')),'WZ-8 high only; MiG-31 row untouched')
ok([r['MobilityId'] for r in UP.values() if r['UnitId']==WZ8]==[newmob],'WZ-8 uses its own row')
receipt={'version':V,'base':'0.8.0-dev.70','base_sha256':BASE,'request':'Osama 13 Nov 18:5x PST: PGL-625 gun 20 damage per second, armour profile same as ZBL-191; WZ-8 remove low altitude, only high',
 'pgl625':{'rounds_per_s':round(rof,3),'damage':[before_dmg,dmg],'dps':round(rof*dmg,2),'armour_from':ZBLARM},'wz8_mobility':newmob,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['pgl625'],newmob)
