"""Build43 over exact Build42 (Osama 12 Nov 03:41-03:57): four-tier MANPAD ladder; Tank Hunters DZT-98; removals; moves; ZTQ-15 Recon; ZTQ-15 autoloader; HJ-10 name; Lynx ATV loadouts; Z-19 names; J-35/J-31 model swap.

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
BASE=json.loads((REL/'out/PLA-TEST-Build-42.json').read_text())['sha256']
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


A=t['AmmunitionsJson'];W=t['WeaponsJson']
# ---------- four-tier MANPAD ladder (Osama 03:41, spec work/pla-audit-20261112/BUILD42-MANPAD-TIERS) ----------
spec=json.loads((ROOT/'tools/pla-specs/manpad-tiers.json').read_text())
def copy_ammo(dst,van):
    g.put('AmmunitionsJson',dst,{k:copy.deepcopy(v) for k,v in before['AmmunitionsJson'][van].items() if k not in ('Id','Name','HUDName','HUDIcon')})
tier_weapon={}
for tier in spec['tiers']:
    if tier['new']:
        w=g.add('WeaponsJson',W[tier['clone_weapon']],{'Name':'PLA infantry '+tier['weapon'],'HUDName':tier['weapon']})
        a=g.add('AmmunitionsJson',A[tier['clone_ammo']],{'Name':'PLA '+tier['weapon']+' missile','HUDName':tier['weapon']})
    else:
        w=tier['clone_weapon'] if 'clone_weapon' in tier else next(r['WeaponId'] for r in t['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==tier['ammo'])
        a=tier['ammo']
    copy_ammo(a,tier['ammo_from_vanilla']);tier_weapon[tier['weapon']]=(w,a)
    assert A[a]['LowAltRange']==tier['LowAltRange'] and A[a]['Damage']==tier['Damage'],tier['weapon']
MAN={x for x,_ in tier_weapon.values()}|{2012081,2012288}
def swap(uid,to):
    w,a=tier_weapon[to];old=None
    for m in rows('SquadMembersJson',uid):
        for f in ('PrimaryWeaponId','SpecialWeaponId'):
            if m[f] in MAN and m[f]!=w:old=m[f];g.put('SquadMembersJson',m['Id'],{f:w})
    for sw in rows('SquadWeaponsJson',uid):
        if sw['WeaponId'] in MAN and sw['WeaponId']!=w:g.put('SquadWeaponsJson',sw['Id'],{'WeaponId':w})
    for wa in rows('WeaponAmmunitionsJson',uid):
        if wa['WeaponId'] in MAN and wa['WeaponId']!=w:g.put('WeaponAmmunitionsJson',wa['Id'],{'WeaponId':w,'AmmunitionId':a})
    if uid in byid:
        for x in byid[uid]['weapons']:
            if x['weapon']==old:x.update(weapon=w,name=to)
    return old
for tier in spec['tiers']:
    for u in tier['units']:
        uid=u['unit'];swap(uid,tier['weapon'])
        if 'rename' in u:
            g.put('Units',uid,{'HUDName':u['rename']})
            if uid in byid:byid[uid]['name']=u['rename']
        log.append({'unit':uid,'name':U[uid]['HUDName'],'change':tier['weapon']+' tier ('+tier['vanilla_name']+')'})
for k,(w,a) in tier_weapon.items():
    if k=='FN-6':g.put('WeaponsJson',w,{'HUDIcon':W[2012081]['HUDIcon']})
    if k=='QW-12':g.put('WeaponsJson',w,{'HUDIcon':W[2012288]['HUDIcon']})

# ---------- Tank Hunters DZT-98: 6 rockets, 600 m, infantry/ground only (Ground 1 + Infantry 2 + Ship 32) ----------
TH=1139;row=next(r for r in rows('WeaponAmmunitionsJson',TH) if r['AmmunitionId']==2011921)
dzt=g.add('AmmunitionsJson',A[2011921],{'Name':'PLA DZT-98 thermobaric (Tank Hunters)','GroundRange':300.0,'TargetType':35})
g.put('WeaponAmmunitionsJson',row['Id'],{'AmmunitionId':dzt,'Quantity':6})
log.append({'unit':TH,'name':U[TH]['HUDName'],'change':'DZT-98: 6 rockets, 600 m, no vehicles or helicopters'})

# ---------- removals and moves ----------
REMOVE={1165:'PLAGF has no recon HJ-8 teams',939:'ZTZ-99A2',948:'ZTZ-99G',1072:'VT-4',1087:'J-10CE'}
for uid,why in REMOVE.items():assert pools(uid),uid;remove(uid,why)
def move(uid,sid):
    ps=pools(uid);assert len(ps)==1;old=ps[0]['SpecializationId'];g.put('SpecializationAvailabilitiesJson',ps[0]['Id'],{'SpecializationId':sid});assign['assignments'][str(uid)]=[sid]
    log.append({'unit':uid,'name':U[uid]['HUDName'],'change':f'spec {old} -> {sid}'})
MOVES={976:20,1233:19}
for uid,sid in MOVES.items():move(uid,sid)

# ---------- ZTQ-15: autoloaded 4-5 s (vanilla 2A88 autoloader values); recon copy in PLAGF Armored ----------
g.put('WeaponsJson',2009127,{'AutoLoaded':True,'MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':5.0})
zr=clone_unit(906,{'Name':'PLA ZTQ-15 Recon','HUDName':'ZTQ-15 Recon','CategoryType':0,'Role':11})
g.add('SpecializationAvailabilitiesJson',pools(906)[0],{'UnitId':zr,'SpecializationId':18});assign['assignments'][str(zr)]=[18]
for su in rows('SensorUnitsJson',zr):g.put('SensorUnitsJson',su['Id'],{'SensorId':3})  # vanilla Very Good Optics (M1A2 SEP v2 TUA)
if U[906]['Name'] in models:models['PLA ZTQ-15 Recon']=copy.deepcopy(models[U[906]['Name']])
log.append({'unit':zr,'name':'ZTQ-15 Recon','change':'new Armored recon copy of ZTQ-15; Very Good Optics'})

# ---------- names ----------
for uid,n in {936:'HJ-10',940:'Z-19',1132:'Z-19 Recon'}.items():log.append({'unit':uid,'name':n,'change':'renamed from '+U[uid]['HUDName']});g.put('Units',uid,{'HUDName':n})

# ---------- Lynx ATV gets the M1301 ISV weapons and loadout options ----------
LYNX,ISV=1228,82;assert not rows('TurretUnitsJson',LYNX) and not rows('ModificationsJson',LYNX)
for table in ['TurretUnitsJson','WeaponAmmunitionsJson']:
    for r in rows(table,ISV):g.add(table,r,{'UnitId':LYNX})
for mod in rows('ModificationsJson',ISV):
    mid=g.add('ModificationsJson',mod,{'UnitId':LYNX})
    for o in sorted([o for o in t['OptionsJson'].values() if o['ModificationId']==mod['Id']],key=lambda o:(o['Order'],o['Id'])):g.add('OptionsJson',o,{'ModificationId':mid})
log.append({'unit':LYNX,'name':'Lynx ATV','change':'M1301 ISV weapons and M240/M2/Mk19 options'})

# ---------- J-35 and J-31 swap models; J-31 uses the J-35 model with the low-vis (no markings) texture ----------
models['PLA J-35'],models['PLA J-31']={'file':'m_j35_cg.fam','battle':'m_j35_lo.fam','align':False},{'file':'m_j31_lowvis.fam','battle':'m_j31_lowvis_lo.fam','align':False}
log.append({'units':[921,971],'change':'J-35 uses the former J-31 model; J-31 uses the J-35 model with the low-vis texture'})

checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
links={}
for r in t['SpecializationAvailabilitiesJson'].values():links.setdefault(r['UnitId'],[]).append(r['SpecializationId'])
for uid in REMOVE:ok(not U[uid]['DisplayInArmory'] and uid not in links and not any(r['UnitId']==uid for r in t['TransportAvailabilitiesJson'].values()),('removed',uid))
for uid,sid in MOVES.items():ok(links[uid]==[sid],('moved',uid))
for tier in spec['tiers']:
    w,a=tier_weapon[tier['weapon']]
    ok(all(A[a][k]==before['AmmunitionsJson'][tier['ammo_from_vanilla']][k] for k in A[a] if k not in ('Id','Name','HUDName','HUDIcon')),('tier = vanilla',tier['weapon']))
    for u in tier['units']:
        ws={m[f] for m in rows('SquadMembersJson',u['unit']) for f in ('PrimaryWeaponId','SpecialWeaponId')}&MAN
        ok(ws=={w} and all(wa['AmmunitionId']==a for wa in rows('WeaponAmmunitionsJson',u['unit']) if wa['WeaponId']==w),('tier units',u['unit'],ws))
ok([ (r['Quantity'],A[r['AmmunitionId']]['GroundRange'],A[r['AmmunitionId']]['TargetType']) for r in rows('WeaponAmmunitionsJson',TH) if r['AmmunitionId']==dzt]==[(6,300.0,35)],'DZT-98')
ok(A[2011921]==before['AmmunitionsJson'][2011921],'shared DZT-98 row untouched')
ok(links[zr]==[18] and U[zr]['CategoryType']==0,'ZTQ-15 Recon')
ok(W[2009127]['AutoLoaded'] and (W[2009127]['MagazineReloadTimeMin'],W[2009127]['MagazineReloadTimeMax'])==(4.0,5.0),'ZTQ-15 reload')
ok(len(rows('TurretUnitsJson',LYNX))==3 and len(rows('WeaponAmmunitionsJson',LYNX))==3 and len([o for o in t['OptionsJson'].values() if o['ModificationId'] in {m['Id'] for m in rows('ModificationsJson',LYNX)}])==3,'Lynx loadouts')
for u in U.values():
    if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification') or u['Id'] not in links:continue
    ok(len(links[u['Id']])==1 or u['Id'] in (MI8,HMV3),('one spec',u['Id']))
    ok(sorted(links[u['Id']])==sorted(assign['assignments'].get(str(u['Id']),[])),('assignment metadata',u['Id']))
for rid,r in t['TransportAvailabilitiesJson'].items():
    pool=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]
    if pool['SpecializationId']>=17:ok(U[r['UnitId']]['DisplayInArmory'] and pool['SpecializationId'] in links.get(r['UnitId'],[]),('carrier visible',rid))
for tu in t['TurretUnitsJson'].values():
    if U.get(tu['UnitId'],{}).get('CountryId')!=4 or tu['UnitId']==1102:continue
    ws={tw['WeaponId'] for tw in t['TurretWeaponsJson'].values() if tw['TurretId']==tu['TurretId']}
    if tu['UnitId']==LYNX and all(any(x['WeaponId']==w for x in before['WeaponAmmunitionsJson'].values() if x['UnitId']==ISV) for w in ws):continue
    ok(all(any(wa['WeaponId']==w for wa in rows('WeaponAmmunitionsJson',tu['UnitId'])) for w in ws),('mounted weapon without ammo row',tu['Id']))
for tab in ['FlyPresetsJson','CountriesJson','SpecializationsJson','TurretsJson','TurretWeaponsJson']:ok(t[tab]==before[tab],('no drift',tab))

def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
assign['build']=43;designer['build']=43;identity['build']=43
for n,dd in [('pla-infantry-designer.json',designer),('pla-spec-assignments.json',assign),('pla-infantry-identity.json',identity)]:save('UserData/FreedomArrow/'+n,dd)
save('UserData/FAModels/models.json',models)
receipt={'build':43,'base_build':42,'base_sha256':BASE,'changes':log,'checks':checks,'native_verified':False,'new_ids':{'ztq15_recon':zr,'dzt98_tank_hunters':dzt,'manpad':{k:list(v) for k,v in tier_weapon.items()}}}
save('UserData/FreedomArrow/pla-build43.json',receipt);(ROOT/'tools/pla-specs/build43-checks.json').write_bytes(enc(receipt))
print(json.dumps({'checks':checks,'changes':len(log),'new':receipt['new_ids']},indent=1))
