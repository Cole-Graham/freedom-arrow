"""Build45 over exact Build44 (Osama 12 Nov 04:29 and 04:40): squad edits and renames, FH-97A as an F-35B with 4 AMRAAMs, tripod PF-98 with DZD98A, GAM-102LR Spike icon, removals, ZSD-89 for PLAN, PLARF Infantry gear icon, Godswords PF-89.

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
BASE=json.loads((REL/'out/PLA-TEST-Build-44.json').read_text())['sha256']
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


A=t['AmmunitionsJson'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson']
QBZ191,QBU10,QBU191,QJY,PF89,PF98,QTSGL=2003998,2012054,2004000,2012411,2011887,2011832,2004006
def members(uid):return rows('SquadMembersJson',uid)
def donor_ammo(wid,exclude):
    return [r for r in WA.values() if r['WeaponId']==wid and r['UnitId']!=exclude and U.get(r['UnitId'],{}).get('Type')==2][:0] or            [r for r in before['WeaponAmmunitionsJson'].values() if r['WeaponId']==wid and r['UnitId']==min(x['UnitId'] for x in before['WeaponAmmunitionsJson'].values() if x['WeaponId']==wid and x['UnitId']!=exclude)]
def sync(uid):
    """SquadWeapons and ammo rows follow what the members carry."""
    carried={m[f] for m in members(uid) for f in ('PrimaryWeaponId','SpecialWeaponId') if m[f]}
    for sw in rows('SquadWeaponsJson',uid):
        if sw['WeaponId'] not in carried:g.remove('SquadWeaponsJson',sw['Id'])
    for wa in rows('WeaponAmmunitionsJson',uid):
        if wa['WeaponId'] not in carried:g.remove('WeaponAmmunitionsJson',wa['Id'])
    have={sw['WeaponId'] for sw in rows('SquadWeaponsJson',uid)}
    for wid in sorted(carried-have):
        g.add('SquadWeaponsJson',rows('SquadWeaponsJson',uid)[0],{'WeaponId':wid,'Order':max(x['Order'] for x in rows('SquadWeaponsJson',uid))+1})
        if not any(r['WeaponId']==wid for r in rows('WeaponAmmunitionsJson',uid)):
            for r in donor_ammo(wid,uid):g.add('WeaponAmmunitionsJson',r,{'UnitId':uid})
    for ar in rows('UnitArmorsJson',uid):g.put('ArmorsJson',ar['ArmorId'],{'MaxHealthPoints':5*len(members(uid))})
def plain(uid):return [m for m in members(uid) if m['PrimaryWeaponId']==QBZ191 and not m['SpecialWeaponId']]
def rename(uid,n):log.append({'unit':uid,'name':n,'change':'renamed from '+U[uid]['HUDName']});g.put('Units',uid,{'HUDName':n});byid.get(uid,{}).update(name=n)

# ---------- names ----------
for uid,n in {1149:'Recon 侦察组',1164:'Forward Observers 前观组',1163:'Mech. Rifles 机步班'}.items():rename(uid,n)
# ---------- squads ----------
g.put('SquadMembersJson',plain(1136)[0]['Id'],{'PrimaryWeaponId':QBU10});sync(1136);log.append({'unit':1136,'name':U[1136]['HUDName'],'change':'+1 QBU-10'})
for m in members(1139):
    if m['PrimaryWeaponId']==QJY:g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':QBZ191})
sync(1139);log.append({'unit':1139,'name':U[1139]['HUDName'],'change':'QJY-201 removed'})
for m in members(1186):
    if m['PrimaryWeaponId']==QBU191:g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':QBU10})
sync(1186);log.append({'unit':1186,'name':U[1186]['HUDName'],'change':'QBU-191 -> QBU-10'})
g.remove('SquadMembersJson',plain(1156)[0]['Id']);sync(1156);log.append({'unit':1156,'name':U[1156]['HUDName'],'change':'7 men'})
fh=[m for m in members(1177) if m['SpecialWeaponId']==2013057];assert len(fh)==2
g.put('SquadMembersJson',fh[1]['Id'],{'SpecialWeaponId':0});sync(1177);log.append({'unit':1177,'name':U[1177]['HUDName'],'change':'1 FHJ-02'})
for m in members(1181):g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':PF89})
sync(1181);log.append({'unit':1181,'name':U[1181]['HUDName'],'change':'6x PF-89 (special slot; replaces the QTS-11 grenade launcher)'})
for uid in (1136,1139,1186,1156,1177,1181):
    if uid in byid:byid[uid]['men']=len(members(uid))
g.put('Units',1175,{'ThumbnailFileName':'FA_PLA_INF_LINE_RESERVE_GEAR'});log.append({'unit':1175,'name':U[1175]['HUDName'],'change':'conscripts emblem with a gear'})
# ---------- removals ----------
REMOVE={1207:'PF-98 Tank Hunters (Motorized)',1158:'Mechanized GPMG Riflemen',1151:'Mechanized AT Riflemen'}
for uid,why in REMOVE.items():assert pools(uid),uid;remove(uid,why)
# ---------- tripod PF-98 (Mechanized PF-98 Tank Hunters) ----------
MECH=1155;pf=next(m for m in members(MECH) if m['SpecialWeaponId']==PF98)
tri=g.add('WeaponsJson',W[PF98],{'Name':'PLA PF-98 tripod','HUDName':'PF-98 (tripod)','HUDIcon':'FA_PLA_WP_PF98T'})
at=g.add('AmmunitionsJson',A[2011833],{'Name':'PLA PF-98 tripod HEAT','GroundRange':400.0})
he=g.add('AmmunitionsJson',before['AmmunitionsJson'][525],{'Name':'PLA DZD98A HE','HUDName':'DZD98A HE','TargetType':35,'IgnoreCover':1.0})
g.put('SquadMembersJson',pf['Id'],{'SpecialWeaponId':tri})
for wa in rows('WeaponAmmunitionsJson',MECH):
    if wa['WeaponId']==PF98:g.put('WeaponAmmunitionsJson',wa['Id'],{'WeaponId':tri,'AmmunitionId':at});g.add('WeaponAmmunitionsJson',wa,{'WeaponId':tri,'AmmunitionId':he})
for sw in rows('SquadWeaponsJson',MECH):
    if sw['WeaponId']==PF98:g.put('SquadWeaponsJson',sw['Id'],{'WeaponId':tri})
hud['entries'].append({**next(e for e in hud['entries'] if e['weapon']==PF98),'weapon':tri,'mode':'custom','profile':'PF98T','address':'FA_PLA_WP_PF98T','basis':"Osama-supplied tripod PF-98 image (12 Nov 04:40), measured source edges"})
for key,vals in [('profiles',['PF98T']),('resources',['FA_PLA_WP_PF98T','FA_PLA_WP_PF98T_OUTLINE'])]:
    if isinstance(hud.get(key),list):hud[key]+=[v for v in vals if v not in hud[key]]
hud['custom_icon_entries']=sum(e['mode']=='custom' for e in hud['entries']);hud['native_icon_entries']=sum(e['mode']=='native' for e in hud['entries']);hud['build']=45
log.append({'unit':MECH,'name':U[MECH]['HUDName'],'change':'tripod PF-98: HEAT 800 m + DZD98A HE (SPG-9 OG-9V copy, 1000 m, ignores cover, no vehicles)'})
# ---------- GAM-102LR uses the vanilla Spike LR card ----------
g.put('WeaponsJson',2014292,{'HUDIcon':W[697]['HUDIcon']});log.append({'weapon':2014292,'change':'GAM-102LR Spike icon'})
# ---------- FH-97A acts as an F-35B with 4 AMRAAMs ----------
FH,F35=973,295;keepU={k:U[FH][k] for k in ['Name','HUDName','CountryId','DisplayInArmory','ContentMembership','IsUnitModification','OriginalName','OriginalCost','OwnerInfantryID','ModelFileName','PortraitFileName','ThumbnailFileName','CategoryType','Cost','Description']}
g.put('Units',FH,{**{k:copy.deepcopy(v) for k,v in U[F35].items() if k!='Id'},**keepU})
for table in ['UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson','UnitAbilitiesJson']:
    for r in rows(table,FH):g.remove(table,r['Id'])
    for r in rows(table,F35):g.add(table,r,{'UnitId':FH})
am=g.add('WeaponsJson',W[118],{'Name':'PLA FH-97A AMRAAM'})
tw=[r for r in t['TurretWeaponsJson'].values() if r['TurretId']==2010224];assert len(tw)==1;g.put('TurretWeaponsJson',tw[0]['Id'],{'WeaponId':am})
wa=rows('WeaponAmmunitionsJson',FH);assert len(wa)==1;g.put('WeaponAmmunitionsJson',wa[0]['Id'],{'WeaponId':am,'AmmunitionId':89,'Quantity':4})
log.append({'unit':FH,'name':'FH-97A','change':'F-35B flight, armor, stealth, sensors and ECM; 4 AMRAAM'})
# ---------- ZSD-89 also for PLAN SOF ----------
zs=clone_unit(1064,{'Name':'PLA PLAN ZSD-89'});g.add('SpecializationAvailabilitiesJson',pools(1064)[0],{'UnitId':zs,'SpecializationId':20});assign['assignments'][str(zs)]=[20]
if U[1064]['Name'] in models:models['PLA PLAN ZSD-89']=copy.deepcopy(models[U[1064]['Name']])
assign['carriers']['20'].append(zs);tmpl=next(iter(t['TransportAvailabilitiesJson'].values()))
for pool in [r for r in t['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==20 and U[r['UnitId']]['Type']==2]:
    if U[zs]['InfantrySlots']>=len(members(pool['UnitId'])):g.add('TransportAvailabilitiesJson',tmpl,{'SpecializationAvailabilityId':pool['Id'],'UnitId':zs})
log.append({'unit':zs,'name':'ZSD-89','change':'PLAN SOF copy (Type 89 APC; Osama said ZBD-89)'})

checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
links={}
for r in t['SpecializationAvailabilitiesJson'].values():links.setdefault(r['UnitId'],[]).append(r['SpecializationId'])
SHARED={int(k):v for k,v in assign['shared_transports'].items()}
for uid in REMOVE:ok(not U[uid]['DisplayInArmory'] and uid not in links and not any(r['UnitId']==uid for r in t['TransportAvailabilitiesJson'].values()),('removed',uid))
kit=lambda uid:sorted((m['PrimaryWeaponId'],m['SpecialWeaponId']) for m in members(uid))
ok(sum(m['PrimaryWeaponId']==QBU10 for m in members(1136))==1,'Airborne Riflemen QBU-10')
ok(not any(QJY in (m['PrimaryWeaponId'],m['SpecialWeaponId']) for m in members(1139)),'Tank Hunters no QJY')
ok(not any(m['PrimaryWeaponId']==QBU191 for m in members(1186)) and any(m['PrimaryWeaponId']==QBU10 for m in members(1186)),'Mountain Leopards QBU-10')
ok(len(members(1156))==7,'engineers 7');ok(sum(m['SpecialWeaponId']==2013057 for m in members(1177))==1,'1 FHJ-02')
ok(len(members(1181))==6 and all(m['SpecialWeaponId']==PF89 and m['PrimaryWeaponId']==2004004 for m in members(1181)),'Godswords PF-89')
ok(sorted(A[r['AmmunitionId']]['GroundRange'] for r in rows('WeaponAmmunitionsJson',MECH) if r['WeaponId']==tri)==[400.0,500.0] and A[he]['TargetType']==35,'tripod PF-98')
ok([r['WeaponId'] for r in rows('WeaponAmmunitionsJson',FH)]==[am] and rows('WeaponAmmunitionsJson',FH)[0]['Quantity']==4 and U[FH]['Stealth']==U[F35]['Stealth'],'FH-97A')
for uid in {r['UnitId'] for r in t['SquadMembersJson'].values() if U.get(r['UnitId'],{}).get('CountryId')==4 and r['UnitId'] in links}:
    carried={m[f] for m in members(uid) for f in ('PrimaryWeaponId','SpecialWeaponId') if m[f]}
    ok(carried=={sw['WeaponId'] for sw in rows('SquadWeaponsJson',uid)} and carried<={wa['WeaponId'] for wa in rows('WeaponAmmunitionsJson',uid)},('squad weapons consistent',uid))
for u in U.values():
    if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification') or u['Id'] not in links:continue
    ok(len(links[u['Id']])==1 or sorted(links[u['Id']])==sorted(SHARED.get(u['Id'],[])),('one spec',u['Id']))
    ok(sorted(links[u['Id']])==sorted(assign['assignments'].get(str(u['Id']),[])),('assignment metadata',u['Id']))
for rid,r in t['TransportAvailabilitiesJson'].items():
    pool=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]
    if pool['SpecializationId']>=17:
        ok(U[r['UnitId']]['DisplayInArmory'] and pool['SpecializationId'] in links.get(r['UnitId'],[]),('carrier visible',rid))
        ok(U[r['UnitId']]['InfantrySlots']>=len(members(pool['UnitId'])),('carrier too small',rid))
for tu in t['TurretUnitsJson'].values():
    if U.get(tu['UnitId'],{}).get('CountryId')!=4 or tu['UnitId'] in (1102,1228):continue
    ws={x['WeaponId'] for x in t['TurretWeaponsJson'].values() if x['TurretId']==tu['TurretId']}
    ok(all(any(wa['WeaponId']==w for wa in rows('WeaponAmmunitionsJson',tu['UnitId'])) for w in ws),('mounted weapon without ammo row',tu['Id']))

def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
assign['build']=45;designer['build']=45;identity['build']=45
for n,dd in [('pla-infantry-designer.json',designer),('pla-spec-assignments.json',assign),('pla-infantry-identity.json',identity),('pla-weapon-hud.json',hud)]:save('UserData/FreedomArrow/'+n,dd)
save('UserData/FAModels/models.json',models)
receipt={'build':45,'base_build':44,'base_sha256':BASE,'changes':log,'checks':checks,'native_verified':False,'new_ids':{'pf98_tripod':tri,'dzd98a':he,'tripod_heat':at,'fh97a_amraam':am,'plan_zsd89':zs},
 'provisional':['tripod PF-98: 10 HEAT + 10 DZD98A','FH-97A keeps its 180 cost and recon tab']}
save('UserData/FreedomArrow/pla-build45.json',receipt);(ROOT/'tools/pla-specs/build45-checks.json').write_bytes(enc(receipt))
print(json.dumps({'checks':checks,'changes':len(log),'new':receipt['new_ids']},indent=1))
