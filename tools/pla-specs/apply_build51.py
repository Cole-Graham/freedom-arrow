"""Build51 over exact Build50 (Osama 12 Nov 05:34 PST).

"ZTZ-99 = T-90M, ztz-99a front armor 800mm ke, z-20 you just add dap like loadouts and replace
with Chinese munitions. HJ-73D should be really slow and priced low because of it?"

- ZTZ-99: T-90M armour, gun (+25 close-range KE rule), ammunition counts and price.
- ZTZ-99A: front kinetic armour 800 (rest unchanged); price 300.
- Z-20KA, Z-20T: the MH-60M DAP's two pylon menus with Chinese munitions:
  JAGM -> AKD-10, DAGR -> FS-70A, Hydra -> 70 mm rockets, Stinger -> TY-90, M230 pod -> 30 mm pod;
  door guns stay QJY-201.
- HJ-73D (and HJ-73): slower missile (100 vs Fagot 150); HJ-73D carriers cheaper.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-50.json').read_text())['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];A=t['AmmunitionsJson'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];T=t['TurretsJson'];TW=t['TurretWeaponsJson'];M=t['ModificationsJson'];O=t['OptionsJson']
rows=lambda tab,uid:[r for r in t[tab].values() if r.get('UnitId')==uid]
receipt={'build':51,'base_build':50,'base_sha256':BASE}
def own_ammo(uid,wa):
    aid=wa['AmmunitionId']
    if any(r['AmmunitionId']==aid and r['UnitId']!=uid for r in WA.values()):
        aid=g.add('AmmunitionsJson',A[aid],{'Name':A[aid]['Name']+' PLA '+str(uid)});g.put('WeaponAmmunitionsJson',wa['Id'],{'AmmunitionId':aid})
    return aid
# ---- tanks
T90M=238;t90arm=next(t['ArmorsJson'][r['ArmorId']] for r in rows('UnitArmorsJson',T90M) if t['ArmorsJson'][r['ArmorId']].get('IsDefault'))
ARMF=[k for k in t90arm if k.startswith(('Heat','Kin','Max'))]
for uid,armour,ke,rounds,cost in [(1083,{k:t90arm[k] for k in ARMF},(450,475),dict(ke=14,he=22,heat=6,gl=3),195),(904,{'KinArmorFront':800},None,None,300)]:
    for r in rows('UnitArmorsJson',uid):
        aid=r['ArmorId']
        if any(x['ArmorId']==aid and x['UnitId']!=uid for x in t['UnitArmorsJson'].values()):aid=g.add('ArmorsJson',t['ArmorsJson'][aid],{});g.put('UnitArmorsJson',r['Id'],{'ArmorId':aid})
        g.put('ArmorsJson',aid,armour)
    if ke:
        for wa in rows('WeaponAmmunitionsJson',uid):
            am=A[wa['AmmunitionId']]
            k='gl' if am['Seeker'] in(50,100) else 'ke' if am['ArmorTargeted']==1 and am['Damage']>=8 else 'heat' if am['ArmorTargeted']==2 and am['PenetrationAtGroundRange']>=300 else 'he' if am['Damage']>=8 else None
            if k=='ke':aid=own_ammo(uid,wa);g.put('AmmunitionsJson',aid,{'PenetrationAtGroundRange':float(ke[0]),'PenetrationAtMinRange':float(ke[1])})
            if k=='heat':aid=own_ammo(uid,wa);g.put('AmmunitionsJson',aid,{'PenetrationAtGroundRange':850.0,'PenetrationAtMinRange':850.0})
            if k in rounds:g.put('WeaponAmmunitionsJson',wa['Id'],{'Quantity':rounds[k]})
    g.put('Units',uid,{'Cost':cost})
receipt['tanks']={'ZTZ-99':'T-90M armour/gun/ammo, 195','ZTZ-99A':'front KE 800, 300'}
# ---- Z-20 DAP menus
DAP=272;lib=lambda name:next(x['Id'] for x in A.values() if x.get('Name')==name)
SWAP={'AGM-114K Hellfire':(lib('PLA air AKD-10'),'AKD-10'),'JAGM ':(lib('PLA air AKD-10'),'AKD-10'),'DAGR':(lib('PLA air FS-70A'),'FS-70A'),
      '70mm Hydra':(lib('PLA air 70 mm rocket heli'),'70 mm rocket'),'FIM-92K Stinger':(2016167,'TY-90'),'30×113mm HEDP':(2011583,'30 mm gun pod')}
for k,(aid,_) in SWAP.items():assert aid in A,k
dapw={r['WeaponId']:r for r in rows('WeaponAmmunitionsJson',DAP)}
newmods={}
for uid in (914,1245):
    door=next(r['TurretId'] for r in rows('TurretUnitsJson',uid) if T[r['TurretId']]['IsDefault'])
    for m in rows('ModificationsJson',uid):
        if m['Type']==3:
            for o in [o for o in O.values() if o['ModificationId']==m['Id']]:g.remove('OptionsJson',o['Id'])
            g.remove('ModificationsJson',m['Id'])
    for r in rows('TurretUnitsJson',uid):
        if r['TurretId']!=door:
            for tw in [x for x in TW.values() if x['TurretId']==r['TurretId']]:
                for wa in [x for x in rows('WeaponAmmunitionsJson',uid) if x['WeaponId']==tw['WeaponId']]:g.remove('WeaponAmmunitionsJson',wa['Id'])
            g.remove('TurretUnitsJson',r['Id'])
    tmap={};wmap={};used=set()
    def chinese_turret(tid):
        if tid in tmap:return tmap[tid]
        if not any(x['TurretId']==tid for x in TW.values()):tmap[tid]=tid;return tid   # empty pylon: share vanilla 'Turret Empty'
        if any(W[x['WeaponId']]['HUDName']=='GAU-17' for x in TW.values() if x['TurretId']==tid):tmap[tid]=door;return door
        nt=g.add('TurretsJson',T[tid],{'Name':T[tid]['Name']+' PLA Z-20'})
        for x in [x for x in TW.values() if x['TurretId']==tid]:
            wid=x['WeaponId']
            if wid not in wmap:
                vam=A[dapw[wid]['AmmunitionId']]['HUDName'];aid,label=SWAP[vam]
                wmap[wid]=(g.add('WeaponsJson',W[wid],{'Name':'PLA Z-20 '+label+' '+str(wid),'HUDName':label}),aid,dapw[wid]['Quantity'])
            g.add('TurretWeaponsJson',x,{'TurretId':nt,'WeaponId':wmap[wid][0]})
        tmap[tid]=nt;return nt
    for m in rows('ModificationsJson',DAP):
        mid=g.add('ModificationsJson',m,{'UnitId':uid,'Name':m['Name']+' PLA Z-20'})
        for o in sorted([o for o in O.values() if o['ModificationId']==m['Id']],key=lambda o:o['Order'] or 0):
            f={'ModificationId':mid,'Name':(o['Name'] or '')+' PLA Z-20 '+str(uid)}
            for i in range(21):
                tid=o.get(f'Turret{i}Id')
                if tid:f[f'Turret{i}Id']=chinese_turret(tid);used.add(f[f'Turret{i}Id'])
            label=o['UIName']
            for a0,b0 in [('JAGM','AKD-10'),('DAGR','FS-70A'),('Hydra','70mm rockets'),('StingerAA','TY-90'),('M230','30mm gun pods')]:label=label.replace(a0,b0) if not label.startswith('Custom_Option_') else label
            f['UIName']=label;g.add('OptionsJson',o,f)
    for tid in used:
        if tid!=door and not any(r['TurretId']==tid for r in rows('TurretUnitsJson',uid)):g.add('TurretUnitsJson',next(iter(t['TurretUnitsJson'].values())),{'UnitId':uid,'TurretId':tid,'Order':0})
    for wid,(nw,aid,q) in wmap.items():g.add('WeaponAmmunitionsJson',dapw[wid],{'UnitId':uid,'WeaponId':nw,'AmmunitionId':aid,'Quantity':q})
    newmods[str(uid)]=[m['Name'] for m in rows('ModificationsJson',uid)]
receipt['z20']={'source':'MH-60M DAP (272) inner and outer pylon menus','swap':{k:v[1] for k,v in SWAP.items()},'mods':newmods}
# ---- HJ-73D slow and cheap
slowed=[]
for am in list(A.values()):
    if am.get('HUDName','').startswith(('HJ-73D','HJ-73 ')) and any(r['AmmunitionId']==am['Id'] and U[r['UnitId']].get('CountryId')==4 for r in WA.values()):
        g.put('AmmunitionsJson',am['Id'],{'MaxSpeed':100.0,'Acceleration':30.0});slowed.append(am['Id'])
PRICE={1168:30,1074:40,1063:20}
for uid,c in PRICE.items():g.put('Units',uid,{'Cost':c})
receipt['hj73d']={'ammo_rows':slowed,'MaxSpeed':'150 -> 100 (Fagot 150)','prices':{U[k]['HUDName']:v for k,v in PRICE.items()}}
# ---- recon helicopters: unguided rockets and gun only (Osama 05:40)
RECON=[1132,1134,1237,1133,1135];ROCKETS={'57 mm rocket','70 mm rocket','90 mm rocket','S-8KO','S-13B'};RCOST={'57 mm rocket':0.5,'70 mm rocket':0.6,'90 mm rocket':0.7,'S-8KO':0.7,'S-13B':2}
air=json.loads(z.read('UserData/FreedomArrow/pla-air-loadouts.json'))
def lib_weapon(uid,name,q):
    c=[r['WeaponId'] for r in rows('WeaponAmmunitionsJson',uid) if W[r['WeaponId']].get('Name')==f'PLA air {name} x{q}']
    return c[0] if c else None
receipt['recon_helicopters']={}
for uid in RECON:
    los=air['aircraft'][str(uid)].get('loadouts',[]);keep={}
    for lo in los:
        slots={}
        for s,parts in lo['slots'].items():
            pr=[(n,q) for n,q in parts if n in ROCKETS]
            if pr:slots[int(s)]=pr
        key=tuple(sorted((s,tuple(map(tuple,pr))) for s,pr in slots.items()))
        if slots and key not in keep:keep[key]=slots
    mod=next(m for m in rows('ModificationsJson',uid) if m['Type']==3)
    old=[o for o in O.values() if o['ModificationId']==mod['Id']];tpl=old[0]
    for o in old:g.remove('OptionsJson',o['Id'])
    made=[]
    for i,slots in enumerate(list(keep.values())[:8]):
        f={k:(None if k.startswith('Turret') else v) for k,v in tpl.items() if k!='Id'};tot={}
        for s,parts in slots.items():
            wids=[lib_weapon(uid,n,q) for n,q in parts]
            assert all(wids),(uid,parts)
            tid=next((tt for tt in T if sorted(x['WeaponId'] for x in TW.values() if x['TurretId']==tt)==sorted(wids)),None)
            if tid is None:
                tid=g.add('TurretsJson',T[166],{'Name':'PLA air pylon recon '+' + '.join(f'{n} x{q}' for n,q in parts),'ModelFileName':'Weapon/Hydra','IsDefault':False})
                for j,w in enumerate(wids):g.add('TurretWeaponsJson',next(iter(TW.values())),{'TurretId':tid,'WeaponId':w,'Order':j})
            if not any(r['TurretId']==tid for r in rows('TurretUnitsJson',uid)):g.add('TurretUnitsJson',next(iter(t['TurretUnitsJson'].values())),{'UnitId':uid,'TurretId':tid,'Order':0})
            f[f'Turret{s}Id']=tid
            for n,q in parts:tot[n]=tot.get(n,0)+q
        label=', '.join(f'{v}x {k}' for k,v in tot.items());cost=int(round(sum(RCOST[k]*v for k,v in tot.items())/5)*5)
        f.update(ModificationId=mod['Id'],Name=f'PLA recon loadout {uid} {i}',Order=i,UIName=label,Cost=cost,IsDefault=i==0,OptionPicture='HYDRA_x19_PYLON')
        g.add('OptionsJson',tpl,f);made.append(f'{label} ({cost})')
    if not made:
        f={k:(None if k.startswith('Turret') else v) for k,v in tpl.items() if k!='Id'};f.update(ModificationId=mod['Id'],Name=f'PLA recon loadout {uid} empty',Order=0,UIName='Custom_Option_Empty',Cost=0,IsDefault=True,OptionPicture='EMPTY')
        g.add('OptionsJson',tpl,f);made.append('no pylon weapons')
    receipt['recon_helicopters'][U[uid]['HUDName']+f' ({uid})']=made
# ---- checks
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for uid in RECON:
    for o in [o for o in O.values() if any(o['ModificationId']==m['Id'] for m in rows('ModificationsJson',uid) if m['Type']==3)]:
        for i in range(21):
            tid=o.get(f'Turret{i}Id')
            for x in [x for x in TW.values() if x['TurretId']==tid] if tid else []:
                am=A[next(r['AmmunitionId'] for r in rows('WeaponAmmunitionsJson',uid) if r['WeaponId']==x['WeaponId'])]
                ok(am['Seeker']==0,('guided weapon on recon helicopter',uid,W[x['WeaponId']]['HUDName']))
                ok(any(r['TurretId']==tid for r in rows('TurretUnitsJson',uid)),('recon turret link',uid,tid))
for uid in (914,1245):
    for m in [m for m in rows('ModificationsJson',uid) if m['Type']==3]:
        os_=[o for o in O.values() if o['ModificationId']==m['Id']]
        ok(len(os_)>=4 and all(o['Id']<=32767 for o in os_),('opts',uid))
        for o in os_:
            for i in range(21):
                tid=o.get(f'Turret{i}Id')
                if not tid:continue
                ok(any(r['TurretId']==tid for r in rows('TurretUnitsJson',uid)) or not any(x['TurretId']==tid for x in TW.values()),('turret link',uid,tid))
                for x in [x for x in TW.values() if x['TurretId']==tid]:ok(any(r['WeaponId']==x['WeaponId'] for r in rows('WeaponAmmunitionsJson',uid)),('ammo row',uid,x['WeaponId']))
                for x in [x for x in TW.values() if x['TurretId']==tid]:ok(W[x['WeaponId']]['HUDName'] in {v[1] for v in SWAP.values()}|{W[door]['HUDName'] if door in W else '', 'QJY-201 door guns'},('western weapon left',uid,W[x['WeaponId']]['HUDName']))
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-PLA unit',uid))
for tab in ('ModificationsJson','OptionsJson','TurretsJson','WeaponsJson','AmmunitionsJson','ArmorsJson'):
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-build51.json',receipt)
(ROOT/'tools/pla-specs/build51-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False)[:2500])
