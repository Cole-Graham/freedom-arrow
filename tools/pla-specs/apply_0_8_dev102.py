"""Freedom Arrow 0.8.0-dev.102 over exact 0.8.0-dev.101 (Osama 14 Nov PST, thread 1571014792016171120).
- J-36: two CAP loadouts next to Heavy CAP (4x PL-17, 4x PL-16, 4x PL-21):
  Long-range CAP (8x PL-17, 4x PL-21) on the dev.75 layout of that load (PL-21 pylon 2016479 was pruned, so 2016475 is used);
  Mixed CAP (8x PL-17, 6x PL-16): two PL-17 x4, two PL-16 x2 and two PL-16 x1 pylons, mirrored like the other loadouts.
  Price 255 for both, the Heavy CAP price (dev.75 also had Long-range CAP at 255). Not specified by Osama.
- ZTQ-15 and ZTQ-15 Recon: the QJC-88 12.7 mm on the roof mount is replaced by the Norinco LG3 40 mm AGL. Weapon is the
  vanilla vehicle Mk19 (same class; our infantry LG3 already copies the Mk19), ammunition is our LG3 40 mm round, 320 rounds
  (the vanilla Humvee/Stryker Mk19 count). VT-5 and VT-5 Recon share that mount and keep the QJC-88, so the ZTQ-15 gets its own mount.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.102';PREV='0.8.0-dev.101'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];TU=t['TurretUnitsJson'];TW=t['TurretWeaponsJson'];W=t['WeaponsJson']
WA=t['WeaponAmmunitionsJson'];AM=t['AmmunitionsJson'];TR=t['TurretsJson'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def slots(o):return [o.get(f'Turret{i}Id',0) for i in range(21)]
def load(uid,o):
    c={}
    for tid in slots(o):
        for r in TW.values():
            if tid and r['TurretId']==tid:
                n=W[r['WeaponId']]['HUDName'];q=sum(x['Quantity'] for x in WA.values() if x['UnitId']==uid and x['WeaponId']==r['WeaponId']);c[n]=c.get(n,0)+q
    return c
# ---------- J-36 CAP loadouts ----------
J36,HC,MOD=929,24393,2016469;ok(U[J36]['HUDName']=='J-36','J-36');o=O[HC]
ok(o['UIName']=='Heavy CAP (4x PL-17, 4x PL-16, 4x PL-21)' and o['IsDefault'] and o['ModificationId']==MOD and o['Cost']==255,'dev.101 Heavy CAP')
ok(load(J36,o)=={'PL-16':4,'PL-17':4,'PL-21':4},'Heavy CAP load')
P16x1,P16x2,P17x4,P21=2017956,2018021,2016481,2016475
for tid,n,q in ((P16x1,'PL-16',1),(P16x2,'PL-16',2),(P17x4,'PL-17',4),(P21,'PL-21',1)):
    ok(any(r['UnitId']==J36 and r['TurretId']==tid for r in TU.values()),('TU row',tid))
    tw=[r for r in TW.values() if r['TurretId']==tid];ok([W[r['WeaponId']]['HUDName'] for r in tw]==[n],(tid,n))
    ok([x['Quantity'] for x in WA.values() if x['UnitId']==J36 and x['WeaponId']==tw[0]['WeaponId']]==[q],(tid,'qty',q))
mine=sorted((x['Order'],x['Id']) for x in O.values() if x.get('ModificationId')==MOD);ok(mine[0]==(2,HC) and len(mine)==6,mine)
for _,oid in mine[1:]:g.put('OptionsJson',oid,{'Order':O[oid]['Order']+2})
rec['j36']={}
for order,ui,name,new,want in ((3,'Long-range CAP (8x PL-17, 4x PL-21)','PLA loadout J-36 Long-range CAP 8x PL-17 4x PL-21',
                                [0,P21,P21,P21,P17x4,P17x4,P21,160,160],{'PL-17':8,'PL-21':4}),
                               (4,'Mixed CAP (8x PL-17, 6x PL-16)','PLA loadout J-36 Mixed CAP 8x PL-17 6x PL-16',
                                [0,P16x2,P16x2,P16x1,P17x4,P17x4,P16x1,160,160],{'PL-17':8,'PL-16':6})):
    oid=g.add('OptionsJson',o,{**{f'Turret{i}Id':(new[i] if i<len(new) else 0) for i in range(21)},'IsDefault':False,'Order':order,'UIName':ui,'Name':name,'Cost':255})
    ld=load(J36,O[oid]);ok(ld==want,(ui,ld));rec['j36'][ui]={'option':oid,'load':ld,'slots':new,'cost':255,'order':order}
ok(sorted(x['Order'] for x in O.values() if x.get('ModificationId')==MOD)==list(range(2,10)),'orders')
# ---------- ZTQ-15 LG3 40 mm AGL ----------
MK19,LG3A,OLDW,OLDA,MOUNT=21,2014209,2009141,2009145,2009142
ok(W[MK19]['Name']=='AGL 40  Mk19 (vehicles)' and W[2014208]['HUDName']=='LG3' and AM[LG3A]['Name']=='PLA infantry LG3 0','donors')
ok(W[OLDW]['HUDName']=='QJC-88 12.7 mm' and [r['TurretId'] for r in TW.values() if r['WeaponId']==OLDW]==[MOUNT],'QJC-88')
ok(sorted(r['UnitId'] for r in TU.values() if r['TurretId']==MOUNT)==[906,1240,1261,1262],'mount users')
ok([U[u]['HUDName'] for u in (906,1240,1261,1262)]==['ZTQ-15','ZTQ-15 Recon','VT-5','VT-5 Recon'],'names')
nw=g.add('WeaponsJson',W[MK19],{'Name':'PLA ZTQ-15 LG3 40 mm AGL','HUDName':'LG3 40 mm AGL'})
na=g.add('AmmunitionsJson',AM[LG3A],{'Name':'PLA ZTQ-15 LG3 40 mm','HUDName':'LG3 40 mm ammunition'})
nt=g.add('TurretsJson',TR[MOUNT],{'Name':'PLA ZTQ-15 mount 2 LG3'})
otw=[r for r in TW.values() if r['TurretId']==MOUNT];ok(len(otw)==1,'one weapon on mount');g.add('TurretWeaponsJson',otw[0],{'TurretId':nt,'WeaponId':nw})
rec['ztq15_agl']={'weapon':nw,'ammo':na,'turret':nt,'units':{}}
for u in (906,1240):
    tu=[r for r in TU.values() if r['UnitId']==u and r['TurretId']==MOUNT];ok(len(tu)==1,(u,'tu'));g.put('TurretUnitsJson',tu[0]['Id'],{'TurretId':nt})
    wa=[x for x in WA.values() if x['UnitId']==u and x['WeaponId']==OLDW];ok(len(wa)==1 and wa[0]['Quantity']==100 and wa[0]['AmmunitionId']==OLDA,(u,'wa'))
    g.put('WeaponAmmunitionsJson',wa[0]['Id'],{'WeaponId':nw,'AmmunitionId':na,'Quantity':320})
    arms=sorted(W[r2['WeaponId']]['HUDName'] for r in TU.values() if r['UnitId']==u for r2 in TW.values() if r2['TurretId']==r['TurretId'])
    ok(arms==['105 mm high-pressure rifled gun','LG3 40 mm AGL','Type 86 7.62 mm'],(u,arms))
    ok(not any(x['UnitId']==u and x['WeaponId']==OLDW for x in WA.values()),(u,'no QJC-88 ammo'))
    rec['ztq15_agl']['units'][U[u]['HUDName']]={'weapons':arms,'rounds':[100,320]}
for u in (1261,1262):ok(any(r['UnitId']==u and r['TurretId']==MOUNT for r in TU.values()) and any(x['UnitId']==u and x['WeaponId']==OLDW for x in WA.values()),(u,'VT-5 keeps QJC-88'))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 14 Nov PST',checks=checks,verified='data checks',
  assumptions={'J-36 CAP price':'255 for both (Heavy CAP price; not specified)','AGL':'Norinco LG3 40 mm; Osama did not recall the name','AGL rounds':320})
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
