"""Build42 over exact Build41 (Osama 12 Nov 03:33-03:45): Z-10K and a Z-10 copy in Air Force, no Z-10 recon cards; QLB-06 for Assault Raiders; PF-98 weapon card; spec badges (star removed on Air Force and Armored, small star on Navy).

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
BASE=json.loads((REL/'out/PLA-TEST-Build-41.json').read_text())['sha256']
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


REMOVE={1130:'Z-10K Recon (Osama: no Z-10 recons)',1131:'Z-10 Recon (Osama: no Z-10 recons)'}
for uid,why in REMOVE.items():assert pools(uid),uid;remove(uid,why)
# Air Force gets a Z-10 card: copy of Armored Z-10 978 (one-spec rule).
assert U[978]['HUDName']=='Z-10' and [r['SpecializationId'] for r in pools(978)]==[18]
z10=clone_unit(978,{'Name':'PLA Air Force Z-10'});g.add('SpecializationAvailabilitiesJson',pools(978)[0],{'UnitId':z10,'SpecializationId':17});assign['assignments'][str(z10)]=[17]
models['PLA Air Force Z-10']=copy.deepcopy(models[U[978]['Name']]) if U[978]['Name'] in models else models.get('PLA Air Force Z-10')
if models.get('PLA Air Force Z-10') is None:models.pop('PLA Air Force Z-10',None)
log.append({'unit':z10,'name':'Z-10','change':'new Air Force copy of 978'})
# QLB-06: handheld 35 mm magazine launcher. Copies the vanilla M32 MGL (weapon 68, ammo 470) and its primary slot.
V68=before['WeaponsJson'][68];assert V68['HUDName']=='M32 MGL'
qlb=g.add('WeaponsJson',V68,{'Name':'PLA infantry QLB-06','HUDName':'QLB-06'})
ammo=g.add('AmmunitionsJson',t['AmmunitionsJson'][470],{'Name':'PLA QLB-06 35 mm grenade','HUDName':'35 mm HE grenade'})
RAID=1146;m=next(m for m in rows('SquadMembersJson',RAID) if m['PrimaryWeaponId']==2013087 and not m['SpecialWeaponId'])
g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':qlb})
g.add('SquadWeaponsJson',rows('SquadWeaponsJson',RAID)[0],{'WeaponId':qlb,'Order':max(x['Order'] for x in rows('SquadWeaponsJson',RAID))+1})
m32=next(r for r in t['WeaponAmmunitionsJson'].values() if r['WeaponId']==68)
g.add('WeaponAmmunitionsJson',m32,{'UnitId':RAID,'WeaponId':qlb,'AmmunitionId':ammo})
byid[RAID]['weapons'].append({'name':'QLB-06','weapon':qlb,'quantity':1,'slot':'primary','native_weapon':68})
log.append({'unit':RAID,'name':U[RAID]['HUDName'],'change':'adds 1 QLB-06 (vanilla M32 MGL copy)'})
# PF-98 / PF-98A weapon card traced from Osama's PF-98 icon (03:43).
PF=[k for k,v in t['WeaponsJson'].items() if v.get('HUDName') in ('PF-98','PF-98A') and k>=2000000];assert len(PF)==4
for k in PF:g.put('WeaponsJson',k,{'HUDIcon':'FA_PLA_WP_PF98'})
for ent in hud['entries']:
    if ent['weapon'] in PF:ent.update(mode='custom',profile='PF98',address='FA_PLA_WP_PF98',basis="Osama-supplied PF-98 icon (12 Nov 03:43), launcher only, measured source edges")
for key,vals in [('profiles',['PF98']),('resources',['FA_PLA_WP_PF98','FA_PLA_WP_PF98_OUTLINE'])]:
    if isinstance(hud.get(key),list):hud[key]+=[v for v in vals if v not in hud[key]]
hud['custom_icon_entries']=sum(e['mode']=='custom' for e in hud['entries']);hud['native_icon_entries']=sum(e['mode']=='native' for e in hud['entries']);hud['build']=42
log.append({'weapons':PF,'change':'PF-98 weapon card'})

checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
links={}
for r in t['SpecializationAvailabilitiesJson'].values():links.setdefault(r['UnitId'],[]).append(r['SpecializationId'])
for uid in REMOVE:ok(not U[uid]['DisplayInArmory'] and uid not in links and not any(r['UnitId']==uid for r in t['TransportAvailabilitiesJson'].values()),('removed',uid))
ok(links[z10]==[17] and links[978]==[18],'Z-10 in Air Force and Armored')
ok(sorted(x['HUDName'] for x in U.values() if x.get('CountryId')==4 and x['Id'] in links and 17 in links[x['Id']] and x.get('Type')==8 and 'Z-10' in x['HUDName'])==['Z-10','Z-10K'],'Air Force Z-10 family')
ok(not any('Z-10' in x['HUDName'] and 'Recon' in x['HUDName'] for x in U.values() if x['Id'] in links),'no Z-10 recon')
for u in U.values():
    if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification') or u['Id'] not in links:continue
    ok(len(links[u['Id']])==1 or u['Id'] in (MI8,HMV3),('one spec',u['Id']))
    ok(sorted(links[u['Id']])==sorted(assign['assignments'].get(str(u['Id']),[])),('assignment metadata',u['Id']))
ok(sum(m['PrimaryWeaponId']==qlb for m in rows('SquadMembersJson',RAID))==1 and any(r['WeaponId']==qlb for r in rows('WeaponAmmunitionsJson',RAID)),'QLB-06')
ok({k:v for k,v in t['WeaponsJson'][qlb].items() if k not in ('Id','Name','HUDName')}=={k:v for k,v in V68.items() if k not in ('Id','Name','HUDName')},'QLB-06 = M32')
for rid,r in t['TransportAvailabilitiesJson'].items():
    pool=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]
    if pool['SpecializationId']>=17:ok(U[r['UnitId']]['DisplayInArmory'] and pool['SpecializationId'] in links.get(r['UnitId'],[]),('carrier visible',rid))
for tu in t['TurretUnitsJson'].values():
    if U.get(tu['UnitId'],{}).get('CountryId')!=4 or tu['UnitId']==1102:continue
    ws={tw['WeaponId'] for tw in t['TurretWeaponsJson'].values() if tw['TurretId']==tu['TurretId']}
    ok(all(any(wa['WeaponId']==w for wa in rows('WeaponAmmunitionsJson',tu['UnitId'])) for w in ws),('mounted weapon without ammo row',tu['Id']))
for tab in ['SensorsJson','FlyPresetsJson','CountriesJson','SpecializationsJson','TurretsJson','TurretWeaponsJson']:ok(t[tab]==before[tab],('no drift',tab))

def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
assign['build']=42;designer['build']=42;identity['build']=42
for n,dd in [('pla-infantry-designer.json',designer),('pla-spec-assignments.json',assign),('pla-infantry-identity.json',identity),('pla-weapon-hud.json',hud)]:save('UserData/FreedomArrow/'+n,dd)
save('UserData/FAModels/models.json',models)
receipt={'build':42,'base_build':41,'base_sha256':BASE,'changes':log,'checks':checks,'native_verified':False,'new_ids':{'z10_air_force':z10,'qlb06_weapon':qlb,'qlb06_ammo':ammo}}
save('UserData/FreedomArrow/pla-build42.json',receipt);(ROOT/'tools/pla-specs/build42-checks.json').write_bytes(enc(receipt))
print(json.dumps({'checks':checks,'changes':len(log),'new':receipt['new_ids']},indent=1))
