"""Freedom Arrow 0.8.0-dev.85 over exact 0.8.0-dev.84 (Osama 13 Nov 21:15-21:35 PST, thread 1571014792016171120).
Stats:
- J-20 (915), J-20S (966) and the hidden J-20B (1088): stealth 2 on the card (raw 0.5, as F-35/F-22). J-31/J-35 already 0.5.
- ZTD-05 (930) removed (card and transport links deleted, hidden), as the dev.77 ZSD-63C removal.
- HJ-10 missiles (2009623 HJ-10, 2010725 AFT-10): 1600 m (raw 900 -> 800). QN-506's QN-502 (2009651): HJ-10 copy at 1600 m.
- QN-506 (937): Recon category, laser designator (vanilla laser values merged into its only default ability, because the
  game loads only the first default ability, dev.74), optics 2000 m (raw 700 -> 1000), NLOS fire like the HJ-10 (nlos.json).
- ZBD-20 + ZBD-20 Recon: the precision launcher is replaced by HJ-16, a copy of the vanilla vehicle Spike LR launcher (716)
  firing a Spike LR copy (2000177) at 1600 m, top attack, semi-active (Seeker 100 as the HJ-10), 8 missiles.
Models:
- J-20S canopy and Z-19 canopy panes split to glass; armed Z-20KA and Z-20T on the seller's armed navy Z-20.
- Seller part positions fixed (FBX animation offsets): PGZ-95 guns, ZBD-20/Recon (VN-17) gun, ZTZ-99 right track and MG, VT-5 MG.
- PGZ-95 90%, ZTZ-99A 90%, ZBD-251 85% (Osama 21:36). Desert ZSD-89A paint MASK instead of BLEND (the see-through glitch).
- Helicopter and ground-vehicle windows use FAModels clear glass instead of the copied F-16 canopy material ("very wavy");
  aircraft (category 6) keep the vanilla F-16 glass.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.85';PREV='0.8.0-dev.84'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];AB=t['AbilitiesJson'];SN=t['SensorsJson'];rows=g.rows
SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];TW=t['TurretWeaponsJson'];WA=t['WeaponAmmunitionsJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(i,n):ok(U[i]['HUDName']==n,(i,U[i]['HUDName'],n))
# stealth
for uid,n in ((915,'J-20'),(966,'J-20S'),(1088,'J-20B — seller package')):
    hud(uid,n);g.put('Units',uid,{'Stealth':0.5,'CurrentStealth':0.5})
ok(U[921]['Stealth']==U[1251]['Stealth']==0.5,'J-35/J-31 already 0.5')
rec['stealth']={'J-20':[0.666,0.5],'J-20S':[0.666,0.5],'J-20B':[1.0,0.5]}
# ZTD-05 removed
Z=930;hud(Z,'ZTD-05');ids=[r['Id'] for r in SA.values() if r['UnitId']==Z];nta=0
for r in list(TA.values()):
    if r.get('SpecializationAvailabilityId') in ids or r.get('UnitId')==Z:g.remove('TransportAvailabilitiesJson',r['Id']);nta+=1
for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
g.put('Units',Z,{'DisplayInArmory':False});assign['assignments'].pop(str(Z),None)
for k in assign.get('carriers',{}):assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=Z]
ok(not [r for r in SA.values() if r['UnitId']==Z] and not U[Z]['DisplayInArmory'],'ZTD-05 removed');rec['ztd05_removed']={'cards':len(ids),'transport_links':nta}
# HJ-10 1600 m; QN-502 = HJ-10 copy at 1600 m
for aid in (2009623,2010725):ok(A[aid]['HUDName']=='HJ-10 guided missile' and A[aid]['GroundRange']==900.0,aid);g.put('AmmunitionsJson',aid,{'GroundRange':800.0})
Q=2009651;ok(A[Q]['HUDName'].startswith('QN-502'),A[Q]['HUDName'])
g.put('AmmunitionsJson',Q,{k:v for k,v in A[2009623].items() if k not in ('Id','Name','HUDName')})
g.put('AmmunitionsJson',Q,{'GroundRange':800.0})
for k in A[2009623]:
    if k not in ('Id','Name','HUDName'):ok(A[Q].get(k)==A[2009623].get(k),('qn502',k))
rec['hj10_range_m']=[1800,1600];rec['qn502']='HJ-10 copy, 1600 m'
# QN-506
U937=U[937];hud(937,'QN-506');g.put('Units',937,{'CategoryType':0})
ab=[r for r in t['UnitAbilitiesJson'].values() if r['UnitId']==937];ok(len(ab)==1 and ab[0]['AbilityId']==2009629,'one ability');ok([r['UnitId'] for r in t['UnitAbilitiesJson'].values() if r['AbilityId']==2009629]==[937],'ability not shared')
g.put('AbilitiesJson',2009629,{k:AB[10][k] for k in ('IsLaserDesignator','LaserMaxRange','LaserUsableInMove')})
su=[r for r in t['SensorUnitsJson'].values() if r['UnitId']==937];ok(len(su)==1 and su[0]['SensorId']==2009631 and [r['UnitId'] for r in t['SensorUnitsJson'].values() if r['SensorId']==2009631]==[937],'own sensor')
g.put('SensorsJson',2009631,{'OpticsGround':1000.0})
rec['qn506']={'category':[2,0],'laser':{k:AB[2009629][k] for k in ('IsLaserDesignator','LaserMaxRange','LaserUsableInMove')},'optics_raw':[700,1000]}
NJ='UserData/FreedomArrow/nlos.json';nl=json.loads(z.read(NJ))
qw=[r['WeaponId'] for r in WA.values() if r.get('UnitId')==937 and r['AmmunitionId']==Q];ok(len(qw)==1,'qn-502 weapon')
for key,val in (('ammunition',Q),('fire_weapons',qw[0]),('weapons',qw[0]),('fire_units',937)):
    if val not in nl[key]:nl[key].append(val)
nl['units']['937']='QN-506';nl['version']=V
# ZBD-20 HJ-16
tw=[r for r in TW.values() if r['TurretId']==2009820 and r['WeaponId']==2018440];ok(len(tw)==1,'precision launcher row')
ok(sorted({r['UnitId'] for r in t['TurretUnitsJson'].values() if r['TurretId']==2009820})==[945,1256],'turret users')
ok(W[716]['HUDName']=='Spike LR' and A[2000177]['HUDName']=='Spike LR' and A[2000177]['GroundRange']==800.0,'spike rows')
nw=g.add('WeaponsJson',W[716],{'Name':'PLA ZBD-20 HJ-16 launcher','HUDName':'HJ-16'})
na=g.add('AmmunitionsJson',A[2000177],{'Name':'PLA ZBD-20 HJ-16','HUDName':'HJ-16','GroundRange':800.0,'Seeker':100,'IsTopArmorArmorAttack':True})
g.put('TurretWeaponsJson',tw[0]['Id'],{'WeaponId':nw})
for uid in (945,1256):
    r=[r for r in WA.values() if r.get('UnitId')==uid and r['WeaponId']==2018440];ok(len(r)==1,('ammo row',uid))
    g.put('WeaponAmmunitionsJson',r[0]['Id'],{'WeaponId':nw,'AmmunitionId':na,'Quantity':8})
ok(not [r for r in WA.values() if r['WeaponId']==2018440 and r.get('UnitId') in (945,1256)],'old launcher gone')
rec['zbd20_hj16']={'weapon':nw,'ammo':na,'range_m':1600,'seeker':100,'top_attack':True,'missiles':8,'icon':W[nw].get('HUDIcon')}
# models.json
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
names={u.get('Name') for u in U.values()}
MAP={'j20sg':['PLA J-20S'],'z19g':['PLA Z-19E','PLA Catalogue Z-19','PLA Recon Z-19E','PLA Recon Z-19','PLA SF Z-19','PLA SF Recon Z-19'],
 'z20na':['PLA Z-20','PLA Z-20T'],'pgz95b':['PLA Catalogue PGZ-95'],'vn17sb':['PLA ZBD-20'],'vn17db':['PLA ZBD-20 Recon'],
 'ztz99b':['PLA Catalogue ZTZ-99'],'vt5b':['PLA VT-5','PLA VT-5 Recon']}
for slug,keys in MAP.items():
    for k in keys:
        ok(k in names,k);before[k]=models.get(k);e={kk:vv for kk,vv in (models.get(k) or {}).items() if kk in ('hide','scale')}
        models[k]={'file':f'm_{slug}_static.fam','battle':f'm_{slug}_lo_static.fam','align':False,**e}
for k,s in (('PLA Catalogue PGZ-95',0.9),('PLA ZTZ-99A',0.9),('PLA Catalogue ZBD-251',0.85)):
    ok('scale' not in models[k],k);before.setdefault(k,dict(models[k]));models[k]['scale']=s
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={'UserData/FAModels/'+f.name:str(f) for f in sorted(a.stage.iterdir()) if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in {'m_'+s for s in MAP}}
ok(len([k for k in files if k.endswith('.fam')])==2*len(MAP),sorted(k for k in files if k.endswith('.fam')))
ok(not any(k in z.namelist() for k in files),'no overwrite of shipped files')
staged={k.split('/')[-1]:json.loads(Path(v).read_text()) for k,v in files.items() if k.endswith('.mat.json')}
# glass: aircraft keep the F-16 glass; helicopters and ground vehicles use clear glass
cat={}
for u in U.values():
    e=models.get(u.get('Name'))
    if e and e.get('file'):
        for q in ('file','battle'):
            if e.get(q):cat.setdefault(e[q].replace('.fam','.mat.json'),set()).add(u.get('CategoryType'))
over={};changed=[]
mats={n.split('/')[-1]:json.loads(z.read(n)) for n in z.namelist() if n.startswith('UserData/FAModels/') and n.endswith('.mat.json')}
mats.update(staged)
for n,mj in mats.items():
    if not any(v.get('cockpitDonor') for v in mj.values()):continue
    cs=cat.get(n,set())
    if not cs or 6 in cs:continue
    for v in mj.values():
        if v.get('cockpitDonor'):v.pop('cockpitDonor');v.update(clearGlass=True,opacity=0.3,alpha='BLEND',metallic=0.0,smoothness=0.95)
    over[n]=mj;changed.append((n,sorted(cs)))
rec['clear_glass']=changed
for n in ('m_zsd89ad_static.mat.json','m_zsd89ad_lo_static.mat.json'):
    mj=over.get(n) or mats[n];nb=0
    for v in mj.values():
        if v.get('alpha')=='BLEND' and not v.get('clearGlass') and not v.get('cockpitDonor'):v['alpha']='MASK';v['cutoff']=0.5;nb+=1
    ok(nb>=4,(n,nb));over[n]=mj
gdir=ROOT/f'tools/pla-specs/{V}-mats';gdir.mkdir(exist_ok=True)
for n,mj in over.items():
    f=gdir/n;f.write_text(json.dumps(mj,indent=1)+'\n');files['UserData/FAModels/'+n]=str(f)
for n in staged:
    for key in staged[n]:
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 21:15-21:35 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(NJ,nl)
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files),'clear glass',len(changed));print(json.dumps(rec['zbd20_hj16']));print([c[0] for c in changed])
