"""Freedom Arrow 0.8.0-dev.72 over exact 0.8.0-dev.71 (Osama 13 Nov 19:0x PST, thread 1567745029781454889):
PGZ-88 (1051) takes the ZTZ-59D armour profile (armour 2010839: HEAT 600/200/100/60, KE 400/100/100/60, 12 HP;
was HEAT/KE 30/20/20/15, 14 HP).
ZSD-89A (all four cards 1065, 1248, 1249, 1250; Osama wrote "ZSD-98A"): M1283 AMPV base stats with no weapons. Default AMPV
armour (2000025), mobility (206), optics (sensor 2) and cost (35 -> 25); 12 seats already match; the QJC-88 mount and its ammo
rows are removed. Smoke ability and models kept.
ZTZ-100 (968): front kinetic armour 800 -> 750 (armour 2010183; HEAT 1200 unchanged)."""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.72'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.71.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);AR,UA,U=t['ArmorsJson'],t['UnitArmorsJson'],t['Units']
DST,SRCA=2010651,2010839
assert U[1051]['HUDName']=='PGZ-88' and [r['ArmorId'] for r in UA.values() if r['UnitId']==1051]==[DST] and sorted({r['UnitId'] for r in UA.values() if r['ArmorId']==DST})==[1051]
assert [r['ArmorId'] for r in UA.values() if r['UnitId']==1061]==[SRCA]
F=[k for k in AR[SRCA] if k not in ('Id','Name','ModelFileName','IsDefault')];before={k:AR[DST][k] for k in F}
g.put('ArmorsJson',DST,{k:AR[SRCA][k] for k in F})
assert all(AR[DST][k]==AR[SRCA][k] for k in F)
Mo,SU,S,TU,WA,UP=t['MobilityJson'],t['SensorUnitsJson'],t['SensorsJson'],t['TurretUnitsJson'],t['WeaponAmmunitionsJson'],t['UnitPropulsionsJson']
ZSD=(1065,1248,1249,1250);KEEPF=('Id','Name','ModelFileName','IsDefault');zlog={}
assert U[41]['HUDName']=='M1283 AMPV' and AR[2000025]['IsDefault']
for uid in ZSD:
    assert U[uid]['HUDName']=='ZSD-89A' and U[uid]['InfantrySlots']==12
    arm=[r['ArmorId'] for r in UA.values() if r['UnitId']==uid];mob=[r['MobilityId'] for r in UP.values() if r['UnitId']==uid]
    assert len(arm)==len(mob)==1 and sorted({r['UnitId'] for r in UA.values() if r['ArmorId']==arm[0]})==[uid] and sorted({r['UnitId'] for r in UP.values() if r['MobilityId']==mob[0]})==[uid]
    g.put('ArmorsJson',arm[0],{k:v for k,v in AR[2000025].items() if k not in KEEPF})
    g.put('MobilityJson',mob[0],{k:v for k,v in Mo[206].items() if k not in KEEPF})
    zlog[uid]={'cost':[U[uid]['Cost'],25],'removed_turret_rows':[r['Id'] for r in TU.values() if r['UnitId']==uid],'removed_ammo_rows':[r['Id'] for r in WA.values() if r['UnitId']==uid]}
    for r in [r for r in TU.values() if r['UnitId']==uid]:g.remove('TurretUnitsJson',r['Id'])
    for r in [r for r in WA.values() if r['UnitId']==uid]:g.remove('WeaponAmmunitionsJson',r['Id'])
    g.put('Units',uid,{'Cost':25,'OriginalCost':25})
sens={r['SensorId'] for r in SU.values() if r['UnitId'] in ZSD};assert sens=={2010927} and sorted({r['UnitId'] for r in SU.values() if r['SensorId']==2010927})==list(ZSD)
g.put('SensorsJson',2010927,{k:v for k,v in S[2].items() if k not in KEEPF})
for uid in ZSD:
    assert not any(r['UnitId']==uid for r in TU.values()) and not any(r['UnitId']==uid for r in WA.values()) and U[uid]['Cost']==25
    assert all(AR[[r['ArmorId'] for r in UA.values() if r['UnitId']==uid][0]][k]==AR[2000025][k] for k in AR[2000025] if k not in KEEPF)
    assert all(Mo[[r['MobilityId'] for r in UP.values() if r['UnitId']==uid][0]][k]==Mo[206][k] for k in Mo[206] if k not in KEEPF)
assert [r['ArmorId'] for r in UA.values() if r['UnitId']==968]==[2010183] and sorted({r['UnitId'] for r in UA.values() if r['ArmorId']==2010183})==[968] and AR[2010183]['KinArmorFront']==800
g.put('ArmorsJson',2010183,{'KinArmorFront':750});assert AR[2010183]['KinArmorFront']==750
receipt={'version':V,'zsd89a':zlog,'ztz100_ke_front':[800,750],'base':'0.8.0-dev.71','base_sha256':BASE,'request':'Osama 13 Nov 19:0x PST: PGZ-88 should have same armor profile as ZTZ-59D; ZSD-98A same stats as AMPV base just no weapons; ZTZ-100 front armor KE 750','before':before,'after':{k:AR[DST][k] for k in F},'checks':1,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('ok')
