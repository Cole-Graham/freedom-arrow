"""Build50 over exact Build49 (Osama 12 Nov 05:24 and 05:31): Airborne name, Godswords QTS-11 grenade launchers back (option A), Mountain Leopards recon, HQ-7 and HQ-9A removed, aircraft spec/tab moves, PHL-16 loadout options, SR-5 as HIMARS with Chinese munition names in PLAN SOF, HMV3 Cargo on PLS statistics with the HEMTT model, squad weapon order rifle/AT/MG.

Previous header:
Build44 over exact Build43 (Osama 12 Nov 04:18): J-11BS/J-11BHG/J-11D with lighter J-11 skins; removals and renames; Z-8L in every spec; Z-20 family (Z-20S recon, Z-20KA and Z-20T armed with DAP-style loadouts, PLAGF Z-20, unarmed Z-20J); CM-501G and CM-502; TY-90 as a Sidewinder.

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
BASE=json.loads((REL/'out/PLA-TEST-Build-49.json').read_text())['sha256']
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


A=t['AmmunitionsJson'];W=t['WeaponsJson'];TU=t['TurretsJson']
def members(uid):return rows('SquadMembersJson',uid)
def move(uid,sid,cat=None):
    ps=pools(uid);assert len(ps)==1,(uid,len(ps));old=ps[0]['SpecializationId']
    if old!=sid:g.put('SpecializationAvailabilitiesJson',ps[0]['Id'],{'SpecializationId':sid});assign['assignments'][str(uid)]=[sid]
    if cat is not None:g.put('Units',uid,{'CategoryType':cat})
    log.append({'unit':uid,'name':U[uid]['HUDName'],'change':f'spec {old} -> {sid}'+(f', tab {cat}' if cat is not None else '')})
# ---------- infantry ----------
g.put('Units',1136,{'HUDName':'Airborne 空降兵'});byid.get(1136,{}).update(name='Airborne 空降兵');log.append({'unit':1136,'name':'Airborne 空降兵','change':'renamed from Airborne Riflemen'})
GW,QTSR,QTSGL,PF89=1181,2004004,2004006,2011887
for m in members(GW):g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':QTSR,'SpecialWeaponId':QTSGL})
for sw in rows('SquadWeaponsJson',GW):
    if sw['WeaponId']==PF89:g.put('SquadWeaponsJson',sw['Id'],{'WeaponId':QTSGL})
for wa in rows('WeaponAmmunitionsJson',GW):
    if wa['WeaponId']==PF89:g.remove('WeaponAmmunitionsJson',wa['Id'])
for r in [r for r in before['WeaponAmmunitionsJson'].values() if r['WeaponId']==QTSGL and r['UnitId']==1185] or [r for r in before['WeaponAmmunitionsJson'].values() if r['WeaponId']==QTSGL][:1]:
    if not any(x['WeaponId']==QTSGL for x in rows('WeaponAmmunitionsJson',GW)):g.add('WeaponAmmunitionsJson',r,{'UnitId':GW})
log.append({'unit':GW,'name':U[GW]['HUDName'],'change':'6x QTS-11 with grenade launcher; PF-89 removed (option A)'})
g.put('Units',1186,{'CategoryType':0,'Role':32});byid.get(1186,{}).update(recon=True);log.append({'unit':1186,'name':U[1186]['HUDName'],'change':'recon tab'})
# ---------- removals ----------
REMOVE={961:'HQ-7 (HQ-7B stays)',1234:'HQ-9A stowed (rows kept)'}
for uid,why in REMOVE.items():assert pools(uid),uid;remove(uid,why)
# ---------- aircraft and UAV spec/tab moves (CategoryType 0 recon, 6 air) ----------
for uid,sid,cat in [(916,17,None),(1242,21,None),(977,17,None),(973,17,6),(967,21,None),(976,20,6),(972,20,None)]:move(uid,sid,cat)
# ---------- HMV3 Cargo: M1075A1 PLS statistics, HEMTT model and mounts ----------
CG,PLS,HM=1247,241,1235;assert U[PLS]['HUDName']=='M1075A1 PLS'
keepU={k:U[CG][k] for k in ['Name','HUDName','CountryId','DisplayInArmory','ContentMembership','IsUnitModification','OriginalName','OriginalCost','OwnerInfantryID','ModelFileName','PortraitFileName','ThumbnailFileName','Description']}
g.put('Units',CG,{**{k:copy.deepcopy(v) for k,v in U[PLS].items() if k!='Id'},**keepU,'InfantrySlots':0})
for table in ['UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson','UnitAbilitiesJson']:
    for r in rows(table,CG):g.remove(table,r['Id'])
    for r in rows(table,PLS):g.add(table,r,{'UnitId':CG})
log.append({'unit':CG,'name':'Shaanxi HMV3 Cargo','change':'M1075A1 PLS statistics on the HEMTT model and mounts'})
# ---------- launcher loadouts via option sets (vanilla HIMARS pattern) ----------
def loadouts(uid,base_turret,items,mod_template=None):
    """items: (label, weapon_template, ammo_id, qty, cost, default). One launcher mount per item; an option picks it."""
    for r in rows('TurretUnitsJson',uid):
        if r['TurretId']==base_turret:g.remove('TurretUnitsJson',r['Id'])
    for r in rows('WeaponAmmunitionsJson',uid):
        if any(tw['TurretId']==base_turret and tw['WeaponId']==r['WeaponId'] for tw in t['TurretWeaponsJson'].values()):g.remove('WeaponAmmunitionsJson',r['Id'])
    tw0=next(x for x in t['TurretWeaponsJson'].values() if x['TurretId']==base_turret)
    mid=g.add('ModificationsJson',t['ModificationsJson'][next(m['Id'] for m in before['ModificationsJson'].values() if m['UnitId']==11 and 'Weapons' in m['Name'])],{'UnitId':uid,'Name':'Weapons '+U[uid]['HUDName']})
    opt=next(o for o in before['OptionsJson'].values() if o['Name']=='Loadout HIMARS HE');out=[]
    for order,(label,wtmpl,ammo,qty,cost,default) in enumerate(items):
        w=g.add('WeaponsJson',W[wtmpl],{'Name':'PLA '+U[uid]['HUDName']+' '+label,'HUDName':label})
        tr=g.add('TurretsJson',TU[base_turret],{'Name':TU[base_turret]['Name']+' '+label})
        g.add('TurretWeaponsJson',tw0,{'TurretId':tr,'WeaponId':w})
        g.add('TurretUnitsJson',rows('TurretUnitsJson',uid)[0] if rows('TurretUnitsJson',uid) else next(iter(t['TurretUnitsJson'].values())),{'UnitId':uid,'TurretId':tr,'Order':len(rows('TurretUnitsJson',uid))})
        g.add('WeaponAmmunitionsJson',next(iter(t['WeaponAmmunitionsJson'].values())),{'UnitId':uid,'WeaponId':w,'AmmunitionId':ammo,'Quantity':qty})
        f={'ModificationId':mid,'Order':order,'Name':'Loadout '+U[uid]['HUDName']+' '+label,'UIName':label,'Cost':cost,'IsDefault':default}
        for i in range(21):f[f'Turret{i}Id']=tr if i==0 else 0
        g.add('OptionsJson',opt,f);out.append((label,w,tr,ammo,qty))
    return out
# PHL-16: two modular cells -> 10x BRE3 300 mm, 8x BRE6/BRE8 370 mm (current), or 2x Fire Dragon 480 (750 mm TBM, ATACMS copy).
PHL,PT=1035,2010436;cur=next(r for r in rows('WeaponAmmunitionsJson',PHL));assert cur['Quantity']==8
bre3=g.add('AmmunitionsJson',before['AmmunitionsJson'][430],{'Name':'PLA BRE3 300 mm','HUDName':'BRE3 300 mm rocket'})
fd480=g.add('AmmunitionsJson',before['AmmunitionsJson'][34],{'Name':'PLA Fire Dragon 480','HUDName':'Fire Dragon 480'})
g.put('AmmunitionsJson',cur['AmmunitionId'],{'HUDName':'BRE6/BRE8 370 mm rocket'})
phl=loadouts(PHL,PT,[('10x BRE3 300 mm',cur['WeaponId'],bre3,10,0,False),('8x BRE6/BRE8 370 mm',cur['WeaponId'],cur['AmmunitionId'],8,0,True),('2x Fire Dragon 480',37,fd480,2,30,False)])
log.append({'unit':PHL,'name':'PHL-16','change':'loadouts: 10x BRE3 300 mm (Smerch 300 mm copy), 8x BRE6/BRE8 370 mm, 2x Fire Dragon 480 (ATACMS copy)'})
# SR-5: vanilla M142 HIMARS copy (weapons, cupola, armor/loadout options) with Chinese munition names; PLAN SOF.
SR,HIM=934,11
keepS={k:U[SR][k] for k in ['Name','HUDName','CountryId','DisplayInArmory','ContentMembership','IsUnitModification','OriginalName','OriginalCost','OwnerInfantryID','PortraitFileName','ThumbnailFileName','Description']}
g.put('Units',SR,{**{k:copy.deepcopy(v) for k,v in U[HIM].items() if k!='Id'},**keepS})
for table in ['UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson','UnitAbilitiesJson','TurretUnitsJson','WeaponAmmunitionsJson']:
    for r in rows(table,SR):g.remove(table,r['Id'])
g.clear_options(SR)
NAMES={928:'Fire Dragon 70 220 mm',929:'Fire Dragon 70 220 mm cluster',34:'Fire Dragon 300',427:'Fire Dragon 480'}
ammo_map={a:g.add('AmmunitionsJson',before['AmmunitionsJson'][a],{'Name':'PLA SR-5 '+n,'HUDName':n}) for a,n in NAMES.items()}
for table in ['UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson','UnitAbilitiesJson','TurretUnitsJson']:
    for r in rows(table,HIM):g.add(table,r,{'UnitId':SR})
for r in rows('WeaponAmmunitionsJson',HIM):g.add('WeaponAmmunitionsJson',r,{'UnitId':SR,'AmmunitionId':ammo_map.get(r['AmmunitionId'],r['AmmunitionId'])})
for mod in rows('ModificationsJson',HIM):
    mid=g.add('ModificationsJson',mod,{'UnitId':SR})
    for o in sorted([o for o in t['OptionsJson'].values() if o['ModificationId']==mod['Id']],key=lambda o:(o['Order'],o['Id'])):
        g.add('OptionsJson',o,{'ModificationId':mid,'UIName':{'Loadout HIMARS HE':'Fire Dragon 70','Loadout HIMARS CLUS':'Fire Dragon 70 cluster','Loadout HIMARS ATACMS CLU':'Fire Dragon 300','Loadout HIMARS PrSM':'Fire Dragon 480'}.get(o['Name'],o['UIName'])})
move(SR,20);log.append({'unit':SR,'name':'SR-5','change':'M142 HIMARS copy; Fire Dragon 70 / 70 cluster / 300 / 480 names'})
# ---------- squad weapon order: base rifle, AT, MG, then the rest ----------
AT,MG={62,63,80},{26,28,30}
def rank(uid,wid):
    base=max({m['PrimaryWeaponId'] for m in members(uid)},key=lambda w:sum(m['PrimaryWeaponId']==w for m in members(uid)))
    ty=W[wid]['Type'];return 0 if wid==base else 1 if ty in AT else 2 if ty in MG else 3
reordered=0
for uid in sorted({r['UnitId'] for r in t['SquadWeaponsJson'].values() if U.get(r['UnitId'],{}).get('CountryId')==4}):
    sws=sorted(rows('SquadWeaponsJson',uid),key=lambda r:r['Order']);new=sorted(sws,key=lambda r:(rank(uid,r['WeaponId']),r['Order']))
    for i,r in enumerate(new):
        if r['Order']!=i:g.put('SquadWeaponsJson',r['Id'],{'Order':i});reordered+=1
log.append({'change':f'squad weapon order rifle/AT/MG ({reordered} rows reordered)'})

checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
links={}
for r in t['SpecializationAvailabilitiesJson'].values():links.setdefault(r['UnitId'],[]).append(r['SpecializationId'])
SHARED={int(k):v for k,v in assign['shared_transports'].items()}
for uid in REMOVE:ok(not U[uid]['DisplayInArmory'] and uid not in links,('removed',uid))
for uid,sid in [(916,17),(1242,21),(977,17),(973,17),(967,21),(976,20),(972,20),(934,20)]:ok(links[uid]==[sid],('moved',uid))
ok(U[973]['CategoryType']==6 and U[976]['CategoryType']==6 and U[1186]['CategoryType']==0,'tabs')
ok(all(m['PrimaryWeaponId']==QTSR and m['SpecialWeaponId']==QTSGL for m in members(GW)) and {r['WeaponId'] for r in rows('SquadWeaponsJson',GW)}=={QTSR,QTSGL},'Godswords A')
ok(len([o for o in t['OptionsJson'].values() if o['ModificationId'] in {m['Id'] for m in rows('ModificationsJson',PHL)}])==3,'PHL-16 loadouts')
ok(sorted(r['TurretId'] for r in rows('TurretUnitsJson',SR))==sorted(r['TurretId'] for r in rows('TurretUnitsJson',HIM)),'SR-5 HIMARS mounts')
for uid in {r['UnitId'] for r in t['SquadMembersJson'].values() if U.get(r['UnitId'],{}).get('CountryId')==4 and r['UnitId'] in links}:
    carried={m[f] for m in members(uid) for f in ('PrimaryWeaponId','SpecialWeaponId') if m[f]}
    ok(carried=={sw['WeaponId'] for sw in rows('SquadWeaponsJson',uid)} and carried<={wa['WeaponId'] for wa in rows('WeaponAmmunitionsJson',uid)},('squad weapons consistent',uid))
    o=[rank(uid,r['WeaponId']) for r in sorted(rows('SquadWeaponsJson',uid),key=lambda r:r['Order'])];ok(o==sorted(o),('weapon order',uid))
for u in U.values():
    if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification') or u['Id'] not in links:continue
    ok(len(links[u['Id']])==1 or sorted(links[u['Id']])==sorted(SHARED.get(u['Id'],[])),('one spec',u['Id']))
    ok(sorted(links[u['Id']])==sorted(assign['assignments'].get(str(u['Id']),[])),('assignment metadata',u['Id']))
for rid,r in t['TransportAvailabilitiesJson'].items():
    pool=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]
    if pool['SpecializationId']>=17:ok(U[r['UnitId']]['DisplayInArmory'] and pool['SpecializationId'] in links.get(r['UnitId'],[]),('carrier visible',rid))
for tu in t['TurretUnitsJson'].values():
    if U.get(tu['UnitId'],{}).get('CountryId')!=4 or tu['UnitId'] in (1102,1228,934,1235,1247):continue
    ws={x['WeaponId'] for x in t['TurretWeaponsJson'].values() if x['TurretId']==tu['TurretId']}
    ok(all(any(wa['WeaponId']==w for wa in rows('WeaponAmmunitionsJson',tu['UnitId'])) for w in ws),('mounted weapon without ammo row',tu['Id']))

def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
assign['build']=50;designer['build']=50;identity['build']=50
for n,dd in [('pla-infantry-designer.json',designer),('pla-spec-assignments.json',assign),('pla-infantry-identity.json',identity)]:save('UserData/FreedomArrow/'+n,dd)
receipt={'build':50,'base_build':49,'base_sha256':BASE,'changes':log,'checks':checks,'native_verified':False,
 'notes':['HMV3 Cargo supply capacity comes from the model or a runtime component, not a table field; PLS statistics are copied, capacity must be checked in game','SR-5 munition names from defence press (Fire Dragon 70, Fire Dragon 300, Fire Dragon 480), not Norinco primary sources']}
save('UserData/FreedomArrow/pla-build50.json',receipt);(ROOT/'tools/pla-specs/build50-checks.json').write_bytes(enc(receipt))
print(json.dumps({'checks':checks,'changes':len(log),'reordered':reordered},indent=1))
