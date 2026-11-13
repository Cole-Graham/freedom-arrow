"""Freedom Arrow 0.8.0-dev.48 over exact 0.8.0-dev.47 (Osama 13 Nov 14:39 PST, thread 1567745029781454889):
PHL-191 Ballistic (1036) carries 2x ATACMS or 2x PrSM (a loadout choice like the vanilla HIMARS) instead of 8x 370 mm rockets;
unit cost 250 -> 225 with both loadouts at +0.
- 2x ATACMS: vanilla ATACMS weapon (37) cloned with a 2-round magazine; vanilla ATACMS ammo (34), 2 rounds. Default loadout.
- 2x PrSM: vanilla HIMARS PrSM weapon (569, already 2 rounds) cloned with HUD name PrSM; vanilla PrSM ammo (427), 2 rounds.
The old 370 mm rocket mount and ammo row leave this unit.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.48'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.47.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,T,W,TW,TU,WA,M,O,A=(t[k] for k in ('Units','TurretsJson','WeaponsJson','TurretWeaponsJson','TurretUnitsJson','WeaponAmmunitionsJson','ModificationsJson','OptionsJson','AmmunitionsJson'))
rows=lambda tab,uid:g.rows(tab,uid)
PHL,OLDT,OLDW=1036,2010448,2010447
assert U[PHL]['HUDName']=='PHL-191 Ballistic' and U[PHL]['Cost']==250 and not rows('ModificationsJson',PHL)
assert [r['TurretId'] for r in rows('TurretUnitsJson',PHL)]==[OLDT] and [r['WeaponId'] for r in rows('WeaponAmmunitionsJson',PHL)]==[OLDW]
assert W[37]['HUDName']=='ATACMS' and W[37]['MagazineSize']==1 and W[569]['MagazineSize']==2 and A[34]['HUDName']=='ATACMS' and A[427]['HUDName']=='400mm HE PrSM'
old_tu=rows('TurretUnitsJson',PHL)[0];old_wa=rows('WeaponAmmunitionsJson',PHL)[0]
def mount(name,weapon,wfields,ammo,default):
    tid=g.add('TurretsJson',T[OLDT],{'Name':name,'IsDefault':default})
    wid=g.add('WeaponsJson',W[weapon],{'Name':name,**wfields})
    g.add('TurretWeaponsJson',[x for x in TW.values() if x['TurretId']==OLDT][0],{'TurretId':tid,'WeaponId':wid,'Order':0})
    g.add('TurretUnitsJson',old_tu,{'TurretId':tid})
    g.add('WeaponAmmunitionsJson',old_wa,{'WeaponId':wid,'AmmunitionId':ammo,'Quantity':2})
    return tid,wid
TA,WAT=mount('PLA PHL-191 ATACMS x2',37,{'MagazineSize':2},34,True)
TP,WPR=mount('PLA PHL-191 PrSM x2',569,{'HUDName':'PrSM'},427,False)
g.remove('TurretUnitsJson',old_tu['Id']);g.remove('WeaponAmmunitionsJson',old_wa['Id'])
still=[r for r in TU.values() if r['TurretId']==OLDT]   # the old rocket mount stays only if another unit still uses it
mid=g.add('ModificationsJson',M[44],{'UnitId':PHL,'Name':'Weapons PHL-191'})
blank={f'Turret{i}Id':0 for i in range(21)}
OA=g.add('OptionsJson',O[112],{**blank,'ModificationId':mid,'Name':'Loadout PHL-191 ATACMS x2','UIName':'2x ATACMS','ReplaceUnitName':None,'Order':0,'Cost':0,'Turret0Id':TA})
OP=g.add('OptionsJson',O[1603],{**blank,'ModificationId':mid,'Name':'Loadout PHL-191 PrSM x2','UIName':'2x PrSM','Order':1,'Cost':0,'Turret0Id':TP})
g.put('Units',PHL,{'Cost':225,'OriginalCost':225})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(U[PHL]['Cost']==225,'cost 225')
ok(sorted(r['TurretId'] for r in rows('TurretUnitsJson',PHL))==sorted([TA,TP]),'two mounts')
ok(sorted((r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in rows('WeaponAmmunitionsJson',PHL))==sorted([(WAT,34,2),(WPR,427,2)]),'2 rounds each')
ok([o['Turret0Id'] for o in sorted([o for o in O.values() if o['ModificationId']==mid],key=lambda o:o['Order'])]==[TA,TP],'options select the mounts')
ok(all(o['Id']<=32767 for o in O.values() if o['ModificationId']==mid),'short option ids')
ok(sum(T[r['TurretId']]['IsDefault'] for r in rows('TurretUnitsJson',PHL))==1,'one default mount')
ok(W[WAT]['MagazineSize']==2 and W[WPR]['MagazineSize']==2,'2-round magazines')
for tid in (TA,TP):ok(all(any(r['UnitId']==PHL and r['WeaponId']==tw['WeaponId'] for r in WA.values()) for tw in TW.values() if tw['TurretId']==tid),('ammo row for mounted weapon',tid))
receipt={'version':V,'base':'0.8.0-dev.47','base_sha256':BASE,'request':'Osama 13 Nov 14:39 PST: The PHL-191 should have 2x ATACM or 2x PRSM. Please price the unit at 225',
 'unit':PHL,'cost':[250,225],'options':{'2x ATACMS':{'option':OA,'turret':TA,'weapon':WAT,'ammo':34,'default':True},'2x PrSM':{'option':OP,'turret':TP,'weapon':WPR,'ammo':427}},
 'removed':{'turret_unit':old_tu['Id'],'ammo_row':old_wa['Id'],'old_mount_still_used_by':[r['UnitId'] for r in still]},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['options'],receipt['removed'])
