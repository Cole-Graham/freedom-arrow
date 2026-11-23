"""Build65 over exact Build64 (Osama 12 Nov 12:39 PST, aircraft and CTL batch).

1. Pylons clear: every PLA loadout sets every pylon its menu uses; pylons it leaves bare get the
   vanilla "Turret Empty" (160), as vanilla loadouts do. Before, a 0 slot kept whatever an earlier
   loadout had mounted.
2. Loadouts are named by role: Light/Heavy CAP, Light/Heavy SEAD, Anti-ship, Standoff strike,
   Light/Heavy strike, CAS; helicopters Light/Heavy anti-armor, Multirole, Fire support, Air escort.
   Same name twice on one aircraft: the main weapon is added in brackets.
3. LT-2 and LS-6 are one bomb: both show "LS-6 500kg" with the LS-6 values. The J-16 32-bomb load
   is "LS-6 250kg": FAB-250 warhead with the guided-bomb fields of KAB-500 (range, accuracy, laser
   guidance).
4. J-20 air-to-air only; J-20S keeps the ground attack loads. J-20/J-20S: at most 4 PL-15/PL-15C
   internal (PL-16 gives 6), no PL-17. YJ-91 removed from every stealth aircraft.
5. MD-22: MiG-31 flight profile (MiG-31BM mobility), J-31 loadouts in its two bays, J-31 stealth.
6. J-50 hidden. J-36 turns like the F-35 (F-35A fly preset on a J-36 copy of its mobility row).
7. CTL-181 (Osama: "CTL-191") NLOS launcher: indirect, laser-guided like the 120 mm PGMM, so it
   fires at targets other units spot. Displayed range 2000 m (1000 in data), 48 missiles,
   15 damage, penetration 20 (low against armour), 50% ignore cover.
8. CSK-181 transport also in Motorized.
"""
import argparse,copy,hashlib,json,re,sys,zipfile
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-64.json').read_text())['sha256']
lib=(ROOT/'tools/pla-specs/apply_build47_air.py').read_text()
exec(lib[lib.index('# ---- weapon catalogue'):lib.index('# ---- unit plan')])          # C, CANON, DROP, SLOTS
C['PL-16']=dict(C['PL-15'],cost=22.5)
C['LD-8A']=dict(ammo=298,w=395,vis={1:'Weapon/R77/R77'},pic='AGM88_HARM',cost=40,cls='agm')
GUIDED=['GroundRange','DispersionHorizontalRadius','DispersionVerticalRadius','LaunchMarginAngle','LaserGuided','SeekerAngle','MaxSeekerDistance','CanReaquire','RotationSpeed']
EMPTY=160
J20,J20S,J16,MD22,J31,J36,J50,CTL,CSK=915,966,916,976,1251,929,944,1054,1230
STEALTH={915,921,929,944,966,967,1251,976}
ARM={'LD-8A','YJ-91','Kh-31P'};SHIP={'YJ-83K','YJ-12','YJ-15','YJ-21','Kh-31A'};STANDOFF={'CJ-10K','KD-63','KD-88','Kh-59M'}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];A=t['AmmunitionsJson'];W=t['WeaponsJson'];T=t['TurretsJson'];O=t['OptionsJson'];M=t['ModificationsJson']
exec(lib[lib.index('ammo_rows={};'):lib.index('# ---- per aircraft')])            # ammo/weapon/turret/assign helpers
for x in A.values():                                                                  # reuse the Build47 ammunition library
    m=re.fullmatch(r'PLA air (.+?)( heli)?',x.get('Name') or '')
    if m and m.group(1) in C:ammo_rows[(m.group(1),bool(m.group(2)))]=x['Id']
receipt={'build':65,'base_build':64,'base_sha256':BASE,'request':'Osama 12 Nov 12:39 PST aircraft/CTL batch; 12:42 CSK-181 in Motorized','removed_options':[],'added_options':[],'names':{},'pylons_filled':0}
# ---- 3. LS-6 500kg / LS-6 250kg
ls6=A[ammo_rows[('LS-6',False)]];IDENT=('Id','Name','HUDName','HUDIcon')
for x in A.values():
    if x.get('Name') in('PLA air LT-2','PLA air LS-6'):
        g.put('AmmunitionsJson',x['Id'],{**({k:copy.deepcopy(v) for k,v in ls6.items() if k not in IDENT} if x['Name']=='PLA air LT-2' else {}),'HUDName':'LS-6 500kg'})
for x in W.values():
    if re.fullmatch(r'PLA air (LT-2|LS-6) x\d+',x.get('Name') or ''):g.put('WeaponsJson',x['Id'],{'HUDName':'LS-6 500kg'})
C['LS-6 250kg']=dict(C['250 kg bomb'],cost=7.5,over={'HUDName':'LS-6 250kg',**{k:A[325][k] for k in GUIDED}})
SHOW={'LT-2':'LS-6 500kg','LS-6':'LS-6 500kg'}
# ---- helpers over the existing menus
twmap=defaultdict(list)
for r in t['TurretWeaponsJson'].values():twmap[r['TurretId']].append(r)
def load_of(o):
    ld=Counter()
    for i in range(21):
        for r in twmap.get(o[f'Turret{i}Id'],[]):
            m=re.fullmatch(r'PLA air (.+) x(\d+)',W[r['WeaponId']]['Name'] or '')
            if m:ld[m.group(1)]+=int(m.group(2));HUD.setdefault(m.group(1),W[r['WeaponId']]['HUDName'])
    return ld
HUD={}
def disp(k):return HUD.get(k,SHOW.get(k,k))
def menus():
    for m in M.values():
        if m['Type']==3 and m['Name'].startswith('PLA loadout') and U.get(m['UnitId'],{}).get('CountryId')==4:yield m
def opts(mid):return sorted([o for o in O.values() if o['ModificationId']==mid],key=lambda o:o['Order'])
def drop(o,why):
    receipt['removed_options'].append({'unit':U[M[o['ModificationId']]['UnitId']]['HUDName'],'option':o['UIName'],'why':why});g.remove('OptionsJson',o['Id'])
def add_option(uid,mid,load,stealth):
    heli=U[uid]['Type']==8;plan=assign(uid,load,stealth,heli);opt={k:(0 if k.startswith('Turret') else copy.deepcopy(v)) for k,v in OPT_T.items() if k!='Id'}
    for (s,kind),parts in plan.items():
        tid=turret(parts,heli,kind);opt[f'Turret{s}Id']=tid;twmap.setdefault(tid,[r for r in t['TurretWeaponsJson'].values() if r['TurretId']==tid])
        if not any(r['TurretId']==tid for r in g.rows('TurretUnitsJson',uid)):g.add('TurretUnitsJson',TU_T,{'UnitId':uid,'TurretId':tid,'Order':0})
        for n,q in parts:
            wid,aid=weapon(n,q,heli),ammo(n,heli)
            if not any(r['WeaponId']==wid for r in g.rows('WeaponAmmunitionsJson',uid)):g.add('WeaponAmmunitionsJson',WA_T,{'UnitId':uid,'WeaponId':wid,'AmmunitionId':aid,'Quantity':q})
    raw=sum(C[k]['cost']*n for k,n in load.items());raw=raw if raw<=150 else 150+(raw-150)/2
    main=max(load,key=lambda k:C[k]['cost']*load[k]);order=len(opts(mid))
    opt.update(ModificationId=mid,Name=f'PLA loadout {U[uid]["HUDName"]} b65 {order}',Order=order,UIName='',Cost=int(round(raw/5.0)*5),OptionPicture=C[main]['pic'],IsDefault=False)
    oid=g.add('OptionsJson',OPT_T,opt);receipt['added_options'].append({'unit':U[uid]['HUDName'],'load':dict(load),'cost':O[oid]['Cost']});return oid
mod_of={m['UnitId']:m['Id'] for m in menus()}
# ---- 4. J-20 / J-20S / stealth
for uid in sorted(STEALTH&set(mod_of)):
    for o in opts(mod_of[uid]):
        ld=load_of(o);aa=all(C[k]['cls'] in('bvr','ir') for k in ld)
        if 'YJ-91' in ld:drop(o,'YJ-91 off stealth aircraft')
        elif uid in(J20,J20S) and 'PL-17' in ld:drop(o,'J-20/J-20S fly internal loads only; no PL-17')
        elif uid in(J20,J20S) and ld['PL-15']+ld['PL-15C']>4:drop(o,'J-20 bays hold 4 PL-15; PL-16 gives 6')
        elif uid==J20 and not aa:drop(o,'J-20 is air-to-air only')
add_option(J20,mod_of[J20],{'PL-15':2,'PL-10':2},True)
add_option(J20S,mod_of[J20S],{'LS-6 250kg':8,'PL-10':2},True)
# J-16: 32x 250 kg are LS-6 250kg
for o in opts(mod_of[J16]):
    ld=load_of(o)
    if ld['250 kg bomb']==32:
        new={('LS-6 250kg' if k=='250 kg bomb' else k):v for k,v in ld.items()};was_default=o['IsDefault'];order=o['Order']
        drop(o,'rebuilt as LS-6 250kg');oid=add_option(J16,mod_of[J16],new,False);g.put('OptionsJson',oid,{'Order':order,'IsDefault':was_default})
# ---- 5. MD-22: MiG-31 flight, J-31 loads, J-31 stealth
mig=[r for r in t['UnitPropulsionsJson'].values() if r['UnitId']==315]
for r in g.rows('UnitPropulsionsJson',MD22):g.remove('UnitPropulsionsJson',r['Id'])
for r in mig:g.add('UnitPropulsionsJson',r,{'UnitId':MD22})
g.put('Units',MD22,{'Stealth':U[J31]['Stealth'],'CurrentStealth':U[J31]['CurrentStealth']})
for r in g.rows('TurretUnitsJson',MD22):
    tr=T[r['TurretId']]
    if not(tr['ModelFileName'] is None and tr['IsDefault']):
        for tw in twmap.get(tr['Id'],[]):
            for wa in [x for x in g.rows('WeaponAmmunitionsJson',MD22) if x['WeaponId']==tw['WeaponId']]:g.remove('WeaponAmmunitionsJson',wa['Id'])
        g.remove('TurretUnitsJson',r['Id'])
mod_of[MD22]=g.add('ModificationsJson',MOD_T,{'UnitId':MD22,'Name':'PLA loadout MD-22','Type':3,'UIName':'Custom_Slot_Weapon_package','ThumbnailFileName':None,'Order':0})
for o in opts(mod_of[J31]):
    oid=add_option(MD22,mod_of[MD22],dict(load_of(o)),True);g.put('OptionsJson',oid,{'IsDefault':o['IsDefault']})
# ---- 6. J-50 hidden; J-36 turns like the F-35
g.put('Units',J50,{'DisplayInArmory':False})
for r in [r for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId']==J50]:
    for tr in [x for x in t['TransportAvailabilitiesJson'].values() if x['SpecializationAvailabilityId']==r['Id']]:g.remove('TransportAvailabilitiesJson',tr['Id'])
    g.remove('SpecializationAvailabilitiesJson',r['Id'])
f35=next(t['MobilityJson'][r['MobilityId']] for r in t['UnitPropulsionsJson'].values() if r['UnitId']==294)
for r in g.rows('UnitPropulsionsJson',J36):
    old=t['MobilityJson'][r['MobilityId']];mid_=g.add('MobilityJson',old,{'Name':'PLA J-36 '+old['Name'],'FlyPresetId':f35['FlyPresetId']});g.put('UnitPropulsionsJson',r['Id'],{'MobilityId':mid_})
# ---- 1+2. clear pylons, role names, defaults
def role(uid,ld):
    cls=Counter();[cls.update({C[k]['cls']:n}) for k,n in ld.items()]
    names=set(ld);aa=cls['bvr']+cls['ir']
    if U[uid]['Type']==8:
        if cls['atgm'] and cls['rocket']:return 'Multirole'
        if cls['atgm']:return ('Light' if cls['atgm']<=4 else 'Heavy')+' anti-armor'
        if cls['rocket'] or cls['bomb']:return 'Fire support'
        return 'Air escort'
    arm=sum(n for k,n in ld.items() if k in ARM)
    if arm:return ('Light' if arm<=2 else 'Heavy')+' SEAD'
    if names&SHIP:return 'Anti-ship'
    if names&STANDOFF:return 'Standoff strike'
    gnd=cls['bomb']+cls['agm']
    if gnd:return ('Light' if gnd<=4 else 'Heavy')+' strike'
    if cls['rocket']:return 'CAS'
    return ('Light' if aa<=4 else 'Heavy')+' CAP'
for uid,mid in sorted(mod_of.items()):
    # LT-2 and LS-6 are now one bomb: identical menus entries collapse to one
    seen={}
    for o in opts(mid):
        key=tuple(sorted(Counter({disp(k):n for k,n in load_of(o).items()}).items()))
        if key in seen:
            keep=seen[key]
            if o['IsDefault']:g.put('OptionsJson',keep['Id'],{'IsDefault':True})
            drop(o,'same load as another entry once LT-2 is LS-6 500kg')
        else:seen[key]=o
    os_=opts(mid);assert os_,('menu left empty',uid)
    slots=sorted({i for o in os_ for i in range(21) if o[f'Turret{i}Id']})
    if not any(r['TurretId']==EMPTY for r in g.rows('TurretUnitsJson',uid)):g.add('TurretUnitsJson',TU_T,{'UnitId':uid,'TurretId':EMPTY,'Order':0})
    base=[role(uid,load_of(o)) for o in os_];names=list(base)
    def tag(nm,ld,level):
        # tell same-role loads apart by the weapon that defines the role
        aa=nm.endswith('CAP') or nm=='Air escort'
        pool=[k for k in ld if (C[k]['cls'] in('bvr','ir','heliaa'))==aa] or list(ld)
        main=max(pool,key=lambda k:C[k]['cost']*ld[k])
        if level==1:return f'{nm} ({disp(main)})'
        if level==2:return f'{nm} ({ld[main]}x {disp(main)})'
        return f"{nm} ({', '.join(f'{n}x {disp(k)}' for k,n in sorted(ld.items(),key=lambda x:-C[x[0]]['cost']*x[1]))})"
    for level in(1,2,3):
        dup=Counter(names)
        names=[tag(b0,load_of(o),level) if dup[nm]>1 else nm for o,b0,nm in zip(os_,base,names)]
    if not any(o['IsDefault'] for o in os_):g.put('OptionsJson',os_[0]['Id'],{'IsDefault':True})
    for i,(o,nm) in enumerate(zip(os_,names)):
        fill={f'Turret{s}Id':EMPTY for s in slots if not o[f'Turret{s}Id']};receipt['pylons_filled']+=len(fill)
        g.put('OptionsJson',o['Id'],{**fill,'UIName':nm,'Order':i})
    receipt['names'][U[uid]['HUDName']]=[(O[o['Id']]['UIName'],', '.join(f"{n}x {disp(k)}" for k,n in load_of(O[o['Id']]).items()),O[o['Id']]['Cost'],O[o['Id']]['IsDefault']) for o in opts(mid)]
# ---- 7. CTL-181 NLOS
pgmm=next(r for r in t['WeaponAmmunitionsJson'].values() if r['UnitId']==5 and 'PGMM' in A[r['AmmunitionId']]['HUDName'])
rows=[r for r in g.rows('WeaponAmmunitionsJson',CTL)];assert len(rows)==1;r=rows[0]
old_a,old_w=A[r['AmmunitionId']],W[r['WeaponId']]
aid=g.add('AmmunitionsJson',A[pgmm['AmmunitionId']],{'Name':'PLA CTL-181 NLOS missile','HUDName':'NLOS missile','HUDIcon':old_a['HUDIcon'],'ModelFileName':'Ammo\\AGM-114_Hellfire_Main_LOD',
    'Damage':15.0,'PenetrationAtMinRange':20.0,'PenetrationAtGroundRange':20.0,'IgnoreCover':0.5,'GroundRange':1000.0,'TargetType':1,'HealthAOERadius':12.5,'StressAOERadius':25.0})
wid=g.add('WeaponsJson',W[pgmm['WeaponId']],{'Name':'PLA CTL-181 NLOS launcher','HUDName':'CTL-181 NLOS launcher','HUDIcon':old_w['HUDIcon'],'AudioPreset':old_w['AudioPreset'],
    'MagazineSize':4,'MagazineReloadTimeMin':8.0,'MagazineReloadTimeMax':12.0})
for tw in [x for x in t['TurretWeaponsJson'].values() if x['WeaponId']==r['WeaponId'] and any(tu['TurretId']==x['TurretId'] for tu in g.rows('TurretUnitsJson',CTL))]:g.put('TurretWeaponsJson',tw['Id'],{'WeaponId':wid})
g.put('WeaponAmmunitionsJson',r['Id'],{'WeaponId':wid,'AmmunitionId':aid,'Quantity':48})
receipt['ctl181']={'model':'indirect, laser-guided (vanilla PGMM 120 mm mortar round behaviour)','range_data':1000,'range_displayed_m':2000,'missiles':48,'damage':15,'penetration':20,'ignore_cover':0.5,'magazine':4}
# ---- 8. CSK-181 transport in Motorized
src=next(r for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId']==CSK and r['SpecializationId']==19)
if not any(r['UnitId']==CSK and r['SpecializationId']==21 for r in t['SpecializationAvailabilitiesJson'].values()):g.add('SpecializationAvailabilitiesJson',src,{'SpecializationId':21})
n='UserData/FreedomArrow/pla-spec-assignments.json';spec=json.loads(z.read(n))
spec['assignments'][str(CSK)]=[19,21];spec['assignments'][str(J50)]=[]
spec.setdefault('shared_transports',{})[str(CSK)]=[19,21]
# ---- checks
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for uid,mid in mod_of.items():
    os_=opts(mid);slots={i for o in os_ for i in range(21) if o[f'Turret{i}Id']}
    ok(sum(bool(o['IsDefault']) for o in os_)==1,('one default',uid))
    for o in os_:
        ok(all(o[f'Turret{s}Id'] for s in slots),('pylon left open',uid,o['Id']));ok(o['Id']<=32767,('option id',o['Id']))
        ld=load_of(o)
        if uid in STEALTH:ok('YJ-91' not in ld and all(dict(SLOTS[U[uid]['ModelFileName']]).get(i) in('b','s') for i in range(21) if o[f'Turret{i}Id'] not in(0,EMPTY)),('stealth load',uid))
        if uid in(J20,J20S):ok('PL-17' not in ld and ld['PL-15']+ld['PL-15C']<=4,('J-20 bay',uid))
        if uid==J20:ok(all(C[k]['cls'] in('bvr','ir') for k in ld),'J-20 AA only')
        for tid in [o[f'Turret{i}Id'] for i in range(21) if o[f'Turret{i}Id']]:
            ok(any(r['TurretId']==tid for r in g.rows('TurretUnitsJson',uid)),('turret link',uid,tid))
            for tw in [x for x in t['TurretWeaponsJson'].values() if x['TurretId']==tid]:ok(any(r['WeaponId']==tw['WeaponId'] for r in g.rows('WeaponAmmunitionsJson',uid)),('ammo row',uid,tw['WeaponId']))
ok(any(not C[k]['cls'] in('bvr','ir') for o in opts(mod_of[J20S]) for k in load_of(o)),'J-20S keeps ground attack')
ok(len(opts(mod_of[MD22]))==len(opts(mod_of[J31])),'MD-22 has the J-31 menu')
ok(not U[J50]['DisplayInArmory'] and not any(r['UnitId']==J50 for r in t['SpecializationAvailabilitiesJson'].values()),'J-50 hidden')
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-China unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(n,spec);save('UserData/FreedomArrow/pla-build65.json',receipt)
(ROOT/'tools/pla-specs/build65-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'pylons filled',receipt['pylons_filled'],'removed',len(receipt['removed_options']),'added',len(receipt['added_options']))
for k in ['J-20','J-20S','J-16','MD-22','J-31','Z-10']:
    for x in receipt['names'].get(k,[]):print(k,'|',x)
