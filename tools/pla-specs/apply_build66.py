"""Build66 over exact Build65 (Osama 12 Nov 13:03 PST).

- J-31, J-35 (and MD-22, which copies the J-31 menu): 6x PL-15/PL-15C loadouts removed; names and
  default re-set with the Build65 role rules.
- Removed from the Arsenal (hidden, no specialization rows): SH-16, ZTZ-20, PGZ-04, ZTZ-59, PLZ-07
  (it was only in Armored). Z-10 moved to Airborne: the Armored card 978 is removed; Airborne keeps
  its Z-10 (1239).
- ZTZ tanks get Abrams mobility (vanilla M1A2 70 km/h row: road 70, reverse 35, cross-country 55,
  turn 60, acceleration 10); ZTZ-96B 80 forward / 40 reverse, cross-country scaled to 63.
  ZTZ-100 keeps its T-14 mobility (80/40), which is already above Abrams.
- PTZ-89 main gun autoloaded, 5 s reload.
- Shaanxi HMV3 Cargo: LVSR mobility (already) and a default resupply ability of 15,000 (vanilla cargo
  ability copy). Supply capacity of trucks may come from the model; the card shows which.
"""
import argparse,copy,hashlib,json,re,sys,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-65.json').read_text())['sha256']
lib=(ROOT/'tools/pla-specs/apply_build47_air.py').read_text()
exec(lib[lib.index('# ---- weapon catalogue'):lib.index('# ---- unit plan')])
C['PL-16']=dict(C['PL-15'],cost=22.5);C['LD-8A']=dict(ammo=298,w=395,vis={1:'Weapon/R77/R77'},pic='AGM88_HARM',cost=40,cls='agm');C['LS-6 250kg']=dict(C['250 kg bomb'],cost=7.5)
J31,J35,MD22=1251,921,976
REMOVE={933:'SH-16',927:'ZTZ-20',1050:'PGZ-04',1060:'ZTZ-59',1038:'PLZ-07',978:'Z-10 (Armored; Airborne keeps 1239)'}
ZTZ={904:'ZTZ-99A',1083:'ZTZ-99',1082:'ZTZ-96A',949:'ZTZ-96',905:'ZTZ-96B'}
MOBF=('Acceleration','Agility','TurnRate','MaxSpeedRoad','MaxSpeedReverse','MaxCrossCountrySpeed','ClimbRate')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];O=t['OptionsJson'];M=t['ModificationsJson'];Mo=t['MobilityJson'];AB=t['AbilitiesJson']
receipt={'build':66,'base_build':65,'base_sha256':BASE,'request':'Osama 12 Nov 13:03 PST','removed_options':[],'removed_units':{},'mobility':{},'names':{}}
assert U[J31]['HUDName']=='J-31' and U[J35]['HUDName']=='J-35' and U[MD22]['HUDName']=='MD-22'
for uid,n in REMOVE.items():assert U[uid]['HUDName'].startswith(n.split(' ')[0]),(uid,U[uid]['HUDName'])
for uid,n in ZTZ.items():assert U[uid]['HUDName']==n,(uid,U[uid]['HUDName'])
# ---- loadouts
twmap={}
for r in t['TurretWeaponsJson'].values():twmap.setdefault(r['TurretId'],[]).append(r)
HUD={}
def load_of(o):
    ld=Counter()
    for i in range(21):
        for r in twmap.get(o[f'Turret{i}Id'],[]):
            m=re.fullmatch(r'PLA air (.+) x(\d+)',W[r['WeaponId']]['Name'] or '')
            if m:ld[m.group(1)]+=int(m.group(2));HUD.setdefault(m.group(1),W[r['WeaponId']]['HUDName'])
    return ld
disp=lambda k:HUD.get(k,k)
ARM={'LD-8A','YJ-91','Kh-31P'};SHIP={'YJ-83K','YJ-12','YJ-15','YJ-21','Kh-31A'};STANDOFF={'CJ-10K','KD-63','KD-88','Kh-59M'}
def role(ld):
    cls=Counter()
    for k,n in ld.items():cls[C[k]['cls']]+=n
    arm=sum(n for k,n in ld.items() if k in ARM)
    if arm:return ('Light' if arm<=2 else 'Heavy')+' SEAD'
    if set(ld)&SHIP:return 'Anti-ship'
    if set(ld)&STANDOFF:return 'Standoff strike'
    gnd=cls['bomb']+cls['agm']
    if gnd:return ('Light' if gnd<=4 else 'Heavy')+' strike'
    if cls['rocket']:return 'CAS'
    return ('Light' if cls['bvr']+cls['ir']<=4 else 'Heavy')+' CAP'
def tag(nm,ld,level):
    aa=nm.endswith('CAP');pool=[k for k in ld if (C[k]['cls'] in('bvr','ir'))==aa] or list(ld)
    main=max(pool,key=lambda k:C[k]['cost']*ld[k])
    if level==1:return f'{nm} ({disp(main)})'
    if level==2:return f'{nm} ({ld[main]}x {disp(main)})'
    return f"{nm} ({', '.join(f'{n}x {disp(k)}' for k,n in sorted(ld.items(),key=lambda x:-C[x[0]]['cost']*x[1]))})"
for uid in (J31,J35,MD22):
    mid=next(m['Id'] for m in M.values() if m['UnitId']==uid and m['Type']==3 and m['Name'].startswith('PLA loadout'))
    opts=lambda:sorted([o for o in O.values() if o['ModificationId']==mid],key=lambda o:o['Order'])
    for o in opts():
        ld=load_of(o)
        if ld['PL-15']+ld['PL-15C']>=6:
            receipt['removed_options'].append({'unit':U[uid]['HUDName'],'option':o['UIName'],'load':dict(ld)});g.remove('OptionsJson',o['Id'])
    os_=opts();assert os_
    base=[role(load_of(o)) for o in os_];names=list(base)
    for level in(1,2,3):
        dup=Counter(names);names=[tag(b0,load_of(o),level) if dup[nm]>1 else nm for o,b0,nm in zip(os_,base,names)]
    dflt=next((o for o in os_ if o['IsDefault']),None) or next((o for o,b0 in zip(os_,base) if b0.endswith('CAP')),os_[0])
    for i,(o,nm) in enumerate(zip(os_,names)):g.put('OptionsJson',o['Id'],{'UIName':nm,'Order':i,'IsDefault':o['Id']==dflt['Id']})
    receipt['names'][U[uid]['HUDName']]=[(O[o['Id']]['UIName'],{disp(k):n for k,n in load_of(O[o['Id']]).items()},O[o['Id']]['IsDefault']) for o in opts()]
# ---- removals
spec=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'))
for uid,n in REMOVE.items():
    g.put('Units',uid,{'DisplayInArmory':False});gone=[]
    for r in [r for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId']==uid]:
        for tr in [x for x in t['TransportAvailabilitiesJson'].values() if x['SpecializationAvailabilityId']==r['Id']]:g.remove('TransportAvailabilitiesJson',tr['Id'])
        gone.append(r['SpecializationId']);g.remove('SpecializationAvailabilitiesJson',r['Id'])
    for r in [x for x in t['TransportAvailabilitiesJson'].values() if x['UnitId']==uid]:g.remove('TransportAvailabilitiesJson',r['Id'])
    spec['assignments'][str(uid)]=[];(spec.get('shared_transports') or {}).pop(str(uid),None)
    receipt['removed_units'][n]={'unit':uid,'specs_removed':gone}
# ---- mobility
abrams=Mo[1];assert abrams['Name'].startswith('Tracks M1A2 Abrams 70kph')
for uid,n in ZTZ.items():
    rows=[r for r in t['UnitPropulsionsJson'].values() if r['UnitId']==uid];assert len(rows)==1
    mid=rows[0]['MobilityId'];assert {r['UnitId'] for r in t['UnitPropulsionsJson'].values() if r['MobilityId']==mid}=={uid}
    new={f:abrams[f] for f in MOBF}
    if uid==905:new.update(MaxSpeedRoad=80.0,MaxSpeedReverse=40.0,MaxCrossCountrySpeed=round(abrams['MaxCrossCountrySpeed']*80/70,1))
    receipt['mobility'][n]={'before':{f:Mo[mid][f] for f in MOBF},'after':new};g.put('MobilityJson',mid,new)
# ---- PTZ-89 autoloader
gun=2009851;assert W[gun]['HUDName']=='120 mm smoothbore gun' and {r['UnitId'] for r in t['WeaponAmmunitionsJson'].values() if r['WeaponId']==gun}=={947}
receipt['ptz89']={'before':{f:W[gun][f] for f in ('AutoLoaded','MagazineReloadTimeMin','MagazineReloadTimeMax')}}
g.put('WeaponsJson',gun,{'AutoLoaded':True,'MagazineReloadTimeMin':5.0,'MagazineReloadTimeMax':5.0})
# ---- Shaanxi HMV3 Cargo: 15,000 supplies
cargo=1247;assert U[cargo]['HUDName']=='Shaanxi HMV3 Cargo' and U[cargo]['ModelFileName']=='US_HEMTT'
assert not any(AB[r['AbilityId']].get('IsDefault') for r in t['UnitAbilitiesJson'].values() if r['UnitId']==cargo)
aid=g.add('AbilitiesJson',AB[108],{'Name':'PLA Shaanxi HMV3 Cargo Supply Default','IsDefault':True,'ResupplyPoints':15000})
g.add('UnitAbilitiesJson',next(iter(t['UnitAbilitiesJson'].values())),{'UnitId':cargo,'AbilityId':aid})
receipt['hmv3_cargo']={'ability':aid,'ResupplyPoints':15000,'model':'US_HEMTT','mobility':Mo[next(r['MobilityId'] for r in t['UnitPropulsionsJson'].values() if r['UnitId']==cargo)]['Name']}
# ---- checks
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for uid in (J31,J35,MD22):
    os_=[o for o in O.values() if M.get(o['ModificationId'],{}).get('UnitId')==uid]
    ok(sum(o['IsDefault'] for o in os_)==1 and len({o['UIName'] for o in os_})==len(os_),('menu',uid))
    for o in os_:ld=load_of(o);ok(ld['PL-15']+ld['PL-15C']<6,('6x PL-15 left',uid))
for uid in REMOVE:ok(not U[uid]['DisplayInArmory'] and not any(r['UnitId']==uid for r in t['SpecializationAvailabilitiesJson'].values()),('removed',uid))
ok(any(r['UnitId']==1239 and r['SpecializationId']==17 for r in t['SpecializationAvailabilitiesJson'].values()),'Airborne Z-10')
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-China unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-spec-assignments.json',spec);save('UserData/FreedomArrow/pla-build66.json',receipt)
(ROOT/'tools/pla-specs/build66-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks);print(json.dumps({k:receipt[k] for k in ('removed_options','removed_units','names')},ensure_ascii=False,indent=0)[:3000])
