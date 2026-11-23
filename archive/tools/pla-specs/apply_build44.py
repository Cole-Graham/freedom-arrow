"""Build44 over exact Build43 (Osama 12 Nov 04:18): J-11BS/J-11BHG/J-11D with lighter J-11 skins; removals and renames; Z-8L in every spec; Z-20 family (Z-20S recon, Z-20KA and Z-20T armed with DAP-style loadouts, PLAGF Z-20, unarmed Z-20J); CM-501G and CM-502; TY-90 as a Sidewinder.

Previous header:
Build43 over exact Build42 (Osama 12 Nov 03:41-03:57): four-tier MANPAD ladder; Tank Hunters DZT-98; removals; moves; ZTQ-15 Recon; ZTQ-15 autoloader; HJ-10 name; Lynx ATV loadouts; Z-19 names; J-35/J-31 model swap.

Previous header:
Build42 over exact Build41 (Osama 12 Nov 03:33-03:45): Z-10K and a Z-10 copy in Air Force, no Z-10 recon cards; QLB-06 for Assault Raiders; PF-98 weapon card; spec badges (star removed on Air Force and Armored, small star on Navy).

Original Build41 header follows.
Build41 over exact Build40 (Osama, 12 Nov 2026 03:08-03:30 PST, thread 1567745029781454889).

Equipment: removals, spec moves, designation renames (no "Type", no seller/package names),
SF copies of Z-19, Z-19 Recon and Z-20, Y-8 as a Harvest Hawk-style SF gunship, J-11B shows
the J-16 model, Mi-8 Cargo moves from the hidden Logistic tab to Helicopters.
Infantry: QBZ-95 for every Rocket Force rifle, Godswords 6 men with 6 QTS-11, tab moves,
names with at most 4 Chinese characters, Whistling Arrows emblem.
Specs: Osama's spec names; logistic slots 0 as in vanilla (removes the LOGISTIC row).
"""
import argparse,copy,hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-43.json').read_text())['sha256']
HMV3,MI8=1235,1227
enc=lambda d:(json.dumps(d,indent=2)+'\n').encode()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native)
read=lambda n:json.loads(z.read(n))
designer=read('UserData/FreedomArrow/pla-infantry-designer.json');assign=read('UserData/FreedomArrow/pla-spec-assignments.json')
identity=read('UserData/FreedomArrow/pla-infantry-identity.json');models=read('UserData/FAModels/models.json');hud=read('UserData/FreedomArrow/pla-weapon-hud.json')
byid={e['unit']:e for e in designer['entries']}
rows=lambda tab,uid:g.rows(tab,uid)
U=t['Units'];log=[]
W_name=lambda wid:t['WeaponsJson'][wid]['HUDName']
def pools(uid):return rows('SpecializationAvailabilitiesJson',uid)

def remove(uid,why):
    g.put('Units',uid,{'DisplayInArmory':False});assign['assignments'].pop(str(uid),None)
    ids={r['Id'] for r in pools(uid)}
    for r in list(t['TransportAvailabilitiesJson'].values()):
        if r['SpecializationAvailabilityId'] in ids or r['UnitId']==uid:g.remove('TransportAvailabilitiesJson',r['Id'])
    for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
    for k in assign['carriers']:assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=uid]
    log.append({'unit':uid,'name':U[uid]['HUDName'],'change':'removed: '+why})
# ---------- clone helper (pla_catalogue pattern: own armor/mobility/ability definitions) ----------
def clone_unit(parent,fields):
    uid=max(U)+1;assert uid not in U
    d=copy.deepcopy(U[parent]);d.pop('Id');d.update(fields);g.put('Units',uid,d);defs={}
    for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
        for r in rows(table,parent):
            if (target,r[field]) not in defs:defs[target,r[field]]=g.add(target,t[target][r[field]])
            g.add(table,r,{'UnitId':uid,field:defs[target,r[field]]})
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
        for r in rows(table,parent):g.add(table,r,{'UnitId':uid})
    for mod in rows('ModificationsJson',parent):
        opts=sorted([o for o in t['OptionsJson'].values() if o['ModificationId']==mod['Id'] and not o.get('ReplaceUnitId')],key=lambda o:(o['Order'],o['Id']))
        if not opts:continue
        mid=g.add('ModificationsJson',mod,{'UnitId':uid})
        for order,o in enumerate(opts):
            f={'ModificationId':mid,'Order':order}
            for key,target in [('ArmorId','ArmorsJson'),('MobilityId','MobilityJson'),('Ability1Id','AbilitiesJson'),('Ability2Id','AbilitiesJson'),('Ability3Id','AbilitiesJson')]:
                if (target,o[key]) in defs:f[key]=defs[target,o[key]]
            g.add('OptionsJson',o,f)
    return uid


A=t['AmmunitionsJson'];W=t['WeaponsJson'];TU=t['TurretsJson']
def links_of(uid):return [r['SpecializationId'] for r in pools(uid)]
def carry(uid,sid):
    """Make uid a carrier for every infantry pool of spec sid that fits."""
    if uid not in assign['carriers'][str(sid)]:assign['carriers'][str(sid)].append(uid)
    tmpl=next(iter(t['TransportAvailabilitiesJson'].values()))
    for pool in [r for r in t['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==sid and U[r['UnitId']]['Type']==2]:
        men=sum(m['UnitId']==pool['UnitId'] for m in t['SquadMembersJson'].values())
        if U[uid]['InfantrySlots']>=men and not any(r['SpecializationAvailabilityId']==pool['Id'] and r['UnitId']==uid for r in t['TransportAvailabilitiesJson'].values()):
            g.add('TransportAvailabilitiesJson',tmpl,{'SpecializationAvailabilityId':pool['Id'],'UnitId':uid})
def add_pool(uid,sid,template_uid):
    g.add('SpecializationAvailabilitiesJson',pools(template_uid)[0],{'UnitId':uid,'SpecializationId':sid});assign['assignments'][str(uid)]=sorted(set(assign['assignments'].get(str(uid),[]))|{sid})

# ---------- J-11 family ----------
J11,J16D,SU35=923,977,169
g.put('Units',J11,{'HUDName':'J-11BS'});models['PLA J-11B']={'file':'m_j11_cg.fam','battle':'m_j11_lo2.fam','align':False}
log.append({'unit':J11,'name':'J-11BS','change':'renamed from J-11B; 4th-gen (Su-27SM stats); lighter J-11 skin on the J-16 model'})
hg=clone_unit(J11,{'Name':'PLA J-11BHG','HUDName':'J-11BHG','Cost':U[SU35]['Cost'],'Description':'J-11BHG: 4.5-gen J-11. PLA weapons of the J-11B; flight and ECM copied from the vanilla Su-35S.'})
for table in ['UnitPropulsionsJson','UnitAbilitiesJson']:
    for r in rows(table,hg):g.remove(table,r['Id'])
    for r in rows(table,SU35):g.add(table,r,{'UnitId':hg})
add_pool(hg,17,J11);models['PLA J-11BHG']={'file':'m_j11_cg.fam','battle':'m_j11_lo2.fam','align':False}
log.append({'unit':hg,'name':'J-11BHG','change':'new 4.5-gen J-11 (Su-35S flight and ECM); Air Force'})
jd=clone_unit(J16D,{'Name':'PLA J-11D','HUDName':'J-11D','Description':'J-11D: 4.5-gen SEAD aircraft. Same loadout as the J-16D.'})
add_pool(jd,17,J16D);models['PLA J-11D']={'file':'m_j11d_cg.fam','battle':'m_j11d_lo.fam','align':False}
log.append({'unit':jd,'name':'J-11D','change':'new SEAD aircraft, copy of J-16D; lighter J-11 skin on the J-16D model; Air Force'})

# ---------- removals and renames ----------
REMOVE={1101:'Y-20B',1093:'J-7E',1094:'J-8II',1090:'JJ-5',1098:'J-2'}
for uid,why in REMOVE.items():assert pools(uid),uid;remove(uid,why)
for uid,n in {975:'J-8D',1091:'J-6W'}.items():log.append({'unit':uid,'name':n,'change':'renamed from '+U[uid]['HUDName']});g.put('Units',uid,{'HUDName':n})

# ---------- Z-8L in every spec (third shared card; 27 seats on the CH-53 body) ----------
Z8=1106;assert links_of(Z8)==[17] and U[Z8]['InfantrySlots']==27
for sid in (18,19,20,21):add_pool(Z8,sid,Z8)
for sid in range(17,22):carry(Z8,sid)
assign['shared_transports'][str(Z8)]=list(range(17,22));assign['one_spec_rule']['exceptions']=assign['shared_transports']
assign['one_spec_rule']['basis']+='; Z-8L in every spec (Osama 12 Nov 04:18)'
log.append({'unit':Z8,'name':'Z-8L','change':'all five specs; carrier for infantry that fits 27 seats'})

# ---------- missiles: TY-90 = helicopter AIM-9 (AH-1Z); CM-502 = LMUR; CM-501G = anti-infantry LMUR ----------
AIM9,LMUR=398,449
def copy_from(dst,src):g.put('AmmunitionsJson',dst,{k:copy.deepcopy(v) for k,v in before['AmmunitionsJson'][src].items() if k not in ('Id','Name','HUDName','HUDIcon')})
TY=[k for k,a in A.items() if 'TY-90' in a.get('HUDName','')]
for k in TY:copy_from(k,AIM9)
ty_ammo=g.add('AmmunitionsJson',before['AmmunitionsJson'][AIM9],{'Name':'PLA TY-90 (Z-20)','HUDName':'TY-90'})
cm502=g.add('AmmunitionsJson',before['AmmunitionsJson'][LMUR],{'Name':'PLA CM-502','HUDName':'CM-502'})
cm501=g.add('AmmunitionsJson',before['AmmunitionsJson'][LMUR],{'Name':'PLA CM-501G','HUDName':'CM-501G','Damage':20.0,'IgnoreCover':1.0,'TargetType':35})
log.append({'ammo':TY+[ty_ammo],'change':'TY-90 = vanilla helicopter AIM-9 Sidewinder'});log.append({'ammo':[cm501,cm502],'change':'CM-501G anti-infantry LMUR (20 damage, ignores cover, no vehicle/helicopter targets); CM-502 = LMUR'})
# Weapons and pylons from the vanilla MH-60M DAP: ATAS pylon (486/weapon 354) and JAGM x2 pylon (1418/weapon 1028).
def pylon(turret,weapon,hud,ammo):
    w=g.add('WeaponsJson',W[weapon],{'Name':'PLA Z-20 '+hud,'HUDName':hud.split(' x')[0]})
    tr=g.add('TurretsJson',TU[turret],{'Name':TU[turret]['Name'].strip()+' PLA '+hud})
    tw=next(r for r in t['TurretWeaponsJson'].values() if r['TurretId']==turret);g.add('TurretWeaponsJson',tw,{'TurretId':tr,'WeaponId':w})
    return tr,w,ammo
P={'TY1':pylon(486,354,'TY-90 x1',ty_ammo),'TY3':pylon(486,354,'TY-90 x3',ty_ammo),'C501':pylon(1418,1028,'CM-501G x2',cm501),'C502':pylon(1418,1028,'CM-502 x2',cm502)}
QTY={'TY1':1,'TY3':3,'C501':2,'C502':2}
LOADOUTS=[('2x TY-90, 4x CM-501G','HELLFIRE_X2',['TY1','TY1','C501','C501'],60,True),('2x TY-90, 4x CM-502','HELLFIRE_X2',['TY1','TY1','C502','C502'],70,False),('6x TY-90','STINGER_x2_WINGTIP',['TY3','TY3'],50,False)]
def arm(uid):
    g.put('Units',uid,{'ModelFileName':'US_MH60M_IDAP'})  # DAP airframe carries the pylon attachment points
    for key,(tr,w,ammo) in P.items():
        g.add('TurretUnitsJson',next(iter(t['TurretUnitsJson'].values())),{'UnitId':uid,'TurretId':tr,'Order':len(rows('TurretUnitsJson',uid))})
        g.add('WeaponAmmunitionsJson',next(r for r in before['WeaponAmmunitionsJson'].values() if r['UnitId']==272 and r['WeaponId']==1028),{'UnitId':uid,'WeaponId':w,'AmmunitionId':ammo,'Quantity':QTY[key]})
    mid=g.add('ModificationsJson',t['ModificationsJson'][270],{'UnitId':uid,'Name':'Weapons Pylons PLA Z-20','UIName':'Custom_Slot_Outer_pylons'})
    for order,(label,pic,keys,cost,default) in enumerate(LOADOUTS):
        f={'ModificationId':mid,'Order':order,'Name':'Pylons PLA Z-20 '+label,'UIName':label,'OptionPicture':pic,'Cost':cost,'IsDefault':default}
        for i in range(21):f[f'Turret{i}Id']=P[keys[i]][0] if i<len(keys) else 0
        g.add('OptionsJson',t['OptionsJson'][2093],f)
# ---------- Z-20 family ----------
Z20,Z20SF=914,1238;assert U[Z20]['HUDName']=='Z-20' and U[Z20SF]['HUDName']=='Z-20'
zs=clone_unit(Z20,{'Name':'PLA Z-20S','HUDName':'Z-20S','CategoryType':0,'InfantrySlots':0,'Description':'Z-20S reconnaissance helicopter (Osama 12 Nov): Exceptional optics, door guns only.'})
for su in rows('SensorUnitsJson',zs):g.put('SensorUnitsJson',su['Id'],{'SensorId':5})
add_pool(zs,17,Z20);models['PLA Z-20S']=copy.deepcopy(models['PLA Z-20'])
zg=clone_unit(Z20,{'Name':'PLA PLAGF Z-20','Description':'Z-20 utility helicopter for PLAGF (Osama 12 Nov).'})
add_pool(zg,18,Z20);carry(zg,18);models['PLA PLAGF Z-20']=copy.deepcopy(models['PLA Z-20'])
zt=clone_unit(Z20,{'Name':'PLA Z-20T','HUDName':'Z-20T','Description':'Z-20T armed transport, used like the MH-60M DAP (Osama 12 Nov).'})
add_pool(zt,20,Z20);carry(zt,20);models['PLA Z-20T']=copy.deepcopy(models['PLA Z-20']);arm(zt)
g.put('Units',Z20,{'HUDName':'Z-20KA','Description':'Z-20KA armed transport for PLAAF (Osama 12 Nov).'});arm(Z20)
for r in rows('WeaponAmmunitionsJson',Z20SF)+rows('TurretUnitsJson',Z20SF):g.remove('WeaponAmmunitionsJson' if 'WeaponId' in r else 'TurretUnitsJson',r['Id'])
g.put('Units',Z20SF,{'HUDName':'Z-20J','Description':'Z-20J unarmed transport for PLAN SOF (Osama 12 Nov).'})
log+=[{'unit':zs,'name':'Z-20S','change':'new Air Force recon helicopter, Exceptional Optics'},{'unit':zg,'name':'Z-20','change':'new PLAGF Armored Z-20'},
      {'unit':zt,'name':'Z-20T','change':'new PLAN SOF armed transport with 3 loadouts'},{'unit':Z20,'name':'Z-20KA','change':'Air Force armed transport with 3 loadouts'},
      {'unit':Z20SF,'name':'Z-20J','change':'PLAN SOF unarmed transport (door guns removed)'}]

checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
links={}
for r in t['SpecializationAvailabilitiesJson'].values():links.setdefault(r['UnitId'],[]).append(r['SpecializationId'])
SHARED={int(k):v for k,v in assign['shared_transports'].items()}
for uid in REMOVE:ok(not U[uid]['DisplayInArmory'] and uid not in links and not any(r['UnitId']==uid for r in t['TransportAvailabilitiesJson'].values()),('removed',uid))
ok(sorted(links[Z8])==list(range(17,22)),'Z-8L everywhere')
for uid,sid in {hg:17,jd:17,zs:17,zg:18,zt:20}.items():ok(links[uid]==[sid],('new card spec',uid))
ok(U[zs]['CategoryType']==0 and [r['SensorId'] for r in rows('SensorUnitsJson',zs)]==[5],'Z-20S recon optics')
ok(not rows('WeaponAmmunitionsJson',Z20SF) and not rows('TurretUnitsJson',Z20SF),'Z-20J unarmed')
for uid in (Z20,zt):
    mods=rows('ModificationsJson',uid);opts=[o for o in t['OptionsJson'].values() if o['ModificationId'] in {m['Id'] for m in mods}]
    ok(len(mods)==1 and len(opts)==3 and sum(o['IsDefault'] for o in opts)==1,('armed Z-20 loadouts',uid))
    for o in opts:
        for i in range(21):
            tid=o[f'Turret{i}Id']
            if tid:ok(any(r['TurretId']==tid for r in rows('TurretUnitsJson',uid)),('option turret mounted',uid,tid))
for k in TY:ok(all(A[k][f]==before['AmmunitionsJson'][AIM9][f] for f in A[k] if f not in ('Id','Name','HUDName','HUDIcon')),('TY-90 sidewinder',k))
ok(A[cm501]['TargetType']==35 and A[cm501]['IgnoreCover']==1.0 and A[cm501]['Damage']==20.0,'CM-501G')
for u in U.values():
    if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification') or u['Id'] not in links:continue
    ok(len(links[u['Id']])==1 or sorted(links[u['Id']])==sorted(SHARED.get(u['Id'],[])),('one spec',u['Id']))
    ok(sorted(links[u['Id']])==sorted(assign['assignments'].get(str(u['Id']),[])),('assignment metadata',u['Id']))
for rid,r in t['TransportAvailabilitiesJson'].items():
    pool=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]
    if pool['SpecializationId']>=17:
        ok(U[r['UnitId']]['DisplayInArmory'] and pool['SpecializationId'] in links.get(r['UnitId'],[]),('carrier visible',rid))
        ok(U[r['UnitId']]['InfantrySlots']>=sum(m['UnitId']==pool['UnitId'] for m in t['SquadMembersJson'].values()),('carrier too small',rid))
for tu in t['TurretUnitsJson'].values():
    if U.get(tu['UnitId'],{}).get('CountryId')!=4 or tu['UnitId'] in (1102,1228):continue
    ws={tw['WeaponId'] for tw in t['TurretWeaponsJson'].values() if tw['TurretId']==tu['TurretId']}
    ok(all(any(wa['WeaponId']==w for wa in rows('WeaponAmmunitionsJson',tu['UnitId'])) for w in ws),('mounted weapon without ammo row',tu['Id']))
for tab in ['FlyPresetsJson','CountriesJson','SpecializationsJson']:ok(t[tab]==before[tab],('no drift',tab))

def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
assign['build']=44;designer['build']=44;identity['build']=44
for n,dd in [('pla-infantry-designer.json',designer),('pla-spec-assignments.json',assign),('pla-infantry-identity.json',identity)]:save('UserData/FreedomArrow/'+n,dd)
save('UserData/FAModels/models.json',models)
receipt={'build':44,'base_build':43,'base_sha256':BASE,'changes':log,'checks':checks,'native_verified':False,
 'new_ids':{'J-11BHG':hg,'J-11D':jd,'Z-20S':zs,'PLAGF Z-20':zg,'Z-20T':zt,'ammo':{'TY-90 Z-20':ty_ammo,'CM-501G':cm501,'CM-502':cm502},'pylons':{k:list(v) for k,v in P.items()}},
 'provisional':['J-11BHG cost 155 (Su-35S)','Z-20 loadout costs 60/70/50','CM-501G IgnoreCover 1.0 (vanilla 84 mm thermobaric value)']}
save('UserData/FreedomArrow/pla-build44.json',receipt);(ROOT/'tools/pla-specs/build44-checks.json').write_bytes(enc(receipt))
print(json.dumps({'checks':checks,'changes':len(log),'new':receipt['new_ids']},indent=1))
