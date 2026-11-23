"""Freedom Arrow 0.8.0-dev.69 over exact 0.8.0-dev.68 (Osama 13 Nov 18:4x PST, thread 1567745029781454889):
PLZ-05 (907) is a 2S35 Koalitsiya-SV (232) copy, options included, with Chinese munition names.
- Stats: Koalitsiya default armour, mobility, optics, smoke ability and cost (200 -> 260). Its own model, size and names stay.
- Weapons and menu (the vanilla Koalitsiya pattern, as PCL-181 in Build67):
  - Default "HE rounds": 155 mm L/54 howitzer with 70x 155 mm ERFB-BB (Koalitsiya 152 mm HE stats).
  - "Extended range" (+70): 50x 155 mm ERFB-BB-RA (HE-RAP stats) and 20x GP155 laser-guided (Krasnopol-D stats).
  - Both carry a QJC-88 12.7 mm roof gun with the Koalitsiya Kord RWS stats (200 rounds).
  Names: ERFB-BB base-bleed, ERFB-BB-RA rocket-assisted and the NORINCO GP155 laser-homing projectile (Wikipedia PLZ-05;
  Janes on NORINCO SH-15 projectiles).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.69'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.68.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native)
U,T,W,TW,TU,WA,A,M,O,AR,MOB,S,UA,UP,UAB,SU=(t[k] for k in ('Units','TurretsJson','WeaponsJson','TurretWeaponsJson','TurretUnitsJson','WeaponAmmunitionsJson','AmmunitionsJson','ModificationsJson','OptionsJson','ArmorsJson','MobilityJson','SensorsJson','UnitArmorsJson','UnitPropulsionsJson','UnitAbilitiesJson','SensorUnitsJson'))
K,P=232,907
assert U[K]['HUDName']=='2S35 Koalitsiya-SV' and U[P]['HUDName']=='PLZ-05' and not [m for m in M.values() if m['UnitId']==P]
KEEP={'Id','Name','HUDName','HUDIcon','ModelFileName','AudioPreset','FXPreset'}
def stats(tab,dst,src,extra=None):g.put(tab,dst,{**{k:copy.deepcopy(v) for k,v in t[tab][src].items() if k not in KEEP},**(extra or {})})
# ---- unit stats
karm=[r['ArmorId'] for r in UA.values() if r['UnitId']==K and AR[r['ArmorId']].get('IsDefault')];assert len(karm)==1
parm=[r['ArmorId'] for r in UA.values() if r['UnitId']==P];pmob=[r['MobilityId'] for r in UP.values() if r['UnitId']==P];psen=[r['SensorId'] for r in SU.values() if r['UnitId']==P]
for tab,field,ids in (('UnitArmorsJson','ArmorId',parm),('UnitPropulsionsJson','MobilityId',pmob),('SensorUnitsJson','SensorId',psen)):
    assert len(ids)==1 and sorted({r['UnitId'] for r in t[tab].values() if r[field]==ids[0]})==[P],(tab,ids)
kmob=[r['MobilityId'] for r in UP.values() if r['UnitId']==K][0];ksen=[r['SensorId'] for r in SU.values() if r['UnitId']==K][0];kab=[r['AbilityId'] for r in UAB.values() if r['UnitId']==K]
assert kab==[5] and not [r for r in UAB.values() if r['UnitId']==P]
before={'cost':U[P]['Cost'],'mobility':{k:MOB[pmob[0]][k] for k in ('MaxSpeedRoad','MaxCrossCountrySpeed','MaxSpeedReverse')}}
stats('ArmorsJson',parm[0],karm[0]);stats('MobilityJson',pmob[0],kmob);stats('SensorsJson',psen[0],ksen)
g.add('UnitAbilitiesJson',[r for r in UAB.values() if r['UnitId']==K][0],{'UnitId':P})
g.put('Units',P,{'Cost':U[K]['Cost'],'OriginalCost':U[K]['Cost']})
# ---- weapons: drop the old single mount, add HE and extended-range mounts with roof guns
old_tu=[r for r in TU.values() if r['UnitId']==P];old_wa=[r for r in WA.values() if r['UnitId']==P];assert len(old_tu)==len(old_wa)==1
MOUNT=old_tu[0]['TurretId']
def weapon(src,name,hud):return g.add('WeaponsJson',W[src],{'Name':'PLA PLZ-05 '+name,'HUDName':hud})
def ammo(src,hud):return g.add('AmmunitionsJson',A[src],{'Name':'PLA PLZ-05 '+hud,'HUDName':hud})
def mount(name,default,parent=None,src=None):return g.add('TurretsJson',T[src or MOUNT],{'Name':'PLA PLZ-05 '+name,'IsDefault':default,'ParentTurretId':parent,'ModelFileName':None})
def link(tid,wid,order=0):
    g.add('TurretWeaponsJson',[x for x in TW.values() if x['TurretId']==393][0],{'TurretId':tid,'WeaponId':wid,'Order':order});g.add('TurretUnitsJson',old_tu[0],{'TurretId':tid})
def stock(wid,aid,q):g.add('WeaponAmmunitionsJson',old_wa[0],{'WeaponId':wid,'AmmunitionId':aid,'Quantity':q})
qty={(r['WeaponId'],r['AmmunitionId']):r['Quantity'] for r in WA.values() if r['UnitId']==K}
GUN_HE=weapon(325,'155 mm L/54 howitzer HE','155 mm L/54 howitzer');GUN_ER=weapon(326,'155 mm L/54 howitzer ER','155 mm L/54 howitzer')
HE=ammo(228,'155 mm ERFB-BB');RA=ammo(229,'155 mm ERFB-BB-RA');GP=ammo(412,'GP155 laser-guided')
MG=weapon(268,'QJC-88 12.7 mm','QJC-88 12.7 mm');MGA=ammo(70,'QJC-88 12.7 mm ammunition')
T_HE=mount('HE mount',True);T_ER=mount('extended range mount',False)
C_HE=mount('roof gun 1',False,T_HE,395);C_ER=mount('roof gun 2',False,T_ER,396)
link(T_HE,GUN_HE);link(T_ER,GUN_ER);link(C_HE,MG);link(C_ER,MG)
stock(GUN_HE,HE,qty[(325,228)]);stock(GUN_ER,RA,qty[(326,229)]);stock(GUN_ER,GP,qty[(326,412)]);stock(MG,MGA,qty[(268,70)])
g.remove('TurretUnitsJson',old_tu[0]['Id']);g.remove('WeaponAmmunitionsJson',old_wa[0]['Id'])
mid=g.add('ModificationsJson',M[208],{'UnitId':P,'Name':'PLA PLZ-05 Weapons Koalitsiya'})
blank={f'Turret{i}Id':0 for i in range(21)}
o1=g.add('OptionsJson',O[544],{**blank,'ModificationId':mid,'Name':'PLA PLZ-05 HE rounds','Order':0,'Turret0Id':T_HE,'ReplaceUnitName':None})
o2=g.add('OptionsJson',O[545],{**blank,'ModificationId':mid,'Name':'PLA PLZ-05 Extended range','Order':1,'Turret0Id':T_ER,'ReplaceUnitName':None})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
same=lambda tab,x,y,skip=():all(t[tab][x].get(k)==v for k,v in t[tab][y].items() if k not in KEEP|set(skip))
ok(same('ArmorsJson',parm[0],karm[0]) and same('MobilityJson',pmob[0],kmob) and same('SensorsJson',psen[0],ksen),'Koalitsiya armour, mobility, optics')
ok(U[P]['Cost']==260 and [r['AbilityId'] for r in UAB.values() if r['UnitId']==P]==[5],'cost and smoke')
for x,y in ((GUN_HE,325),(GUN_ER,326),(MG,268)):ok(same('WeaponsJson',x,y),('weapon stats',x))
for x,y in ((HE,228),(RA,229),(GP,412),(MGA,70)):ok(same('AmmunitionsJson',x,y),('ammo stats',x))
ok(sorted((r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in WA.values() if r['UnitId']==P)==sorted([(GUN_HE,HE,70),(GUN_ER,RA,50),(GUN_ER,GP,20),(MG,MGA,200)]),'stocks')
ok([(o['Cost'],o['Turret0Id']) for o in sorted([o for o in O.values() if o['ModificationId']==mid],key=lambda o:o['Order'])]==[(0,T_HE),(70,T_ER)],'menu')
ok(all(o<=32767 for o in (o1,o2)),'short option ids')
for c,par in ((C_HE,T_HE),(C_ER,T_ER)):ok(T[c]['ParentTurretId']==par and any(r['UnitId']==P and r['TurretId']==par for r in TU.values()),('roof gun parent on unit',c))
ok(sum(T[r['TurretId']]['IsDefault'] for r in TU.values() if r['UnitId']==P)==1,'one default mount')
receipt={'version':V,'base':'0.8.0-dev.68','base_sha256':BASE,'request':'Osama 13 Nov 18:4x PST: PLZ-05 should be a Koalitsiya copy and the options also copied; weapon names Chinese names found online',
 'before':before,'after':{'cost':260,'mobility':{k:MOB[pmob[0]][k] for k in ('MaxSpeedRoad','MaxCrossCountrySpeed','MaxSpeedReverse')}},
 'rows':{'turrets':[T_HE,T_ER,C_HE,C_ER],'weapons':[GUN_HE,GUN_ER,MG],'ammo':{'ERFB-BB':HE,'ERFB-BB-RA':RA,'GP155':GP,'12.7':MGA},'options':[o1,o2],'modification':mid},
 'names_source':['https://en.wikipedia.org/wiki/PLZ-05','https://www.janes.com/defence-intelligence-insights/defence-news/norinco-marketing-sh-15-155-mm-artillery-system-for-export'],'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['before'],receipt['after'])
