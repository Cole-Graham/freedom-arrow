"""Build62 over exact Build61 (Osama 12 Nov 12:09-12:25): PLARF size correction (Conscripts, QJZ-89, QLZ-87 and Thermobaric back to 12; Ambush Team 4 and Sharp Blades 6 as in Build60; HJ-73D, FN-6, PF-98 stay 7); Conscripts cost 25; ZSD-89A as four separate cards with 12 seats (PLARF olive, PLAGF green, PLAAF desert, PLAN SOF marine); ZBD-86 also in PLAAF airborne.

Previous header:
Build61 over exact Build60 (Osama 12 Nov 12:02): PLARF "Malyutka Recon Ambush Team" is renamed "Ambush Team 伏击组"; PLARF Infantry gets one PF-89 (an extra QBZ-95 rifleman carries it; the HJ-73D stays).
Osama 12 Nov 12:10: every PLARF infantry card is 7 men; QBZ-95, QBB-95 and QBU-88 fire 30% slower (conscripts are meat shields).

Previous header:
Build60 over exact Build59 (Osama 12 Nov 11:54): the PLARF PF-98 Team and the Mechanized PF-98 Tank Hunters swap PF-98 versions; PLARF gets the tripod PF-98 (HEAT 800 m + DZD98A HE), Mechanized gets the plain PF-98. Rifles, size and price stay with each squad.

Previous header:
Build59 over exact Build58 (Osama 12 Nov 11:46): Blood Wolves become armour hunters (QBZ-192 x4, HJ-12, PF-89 x2, QBU-10); Falcons become desert raiders (QBZ-192 x3, QJZ-171, QLB-06 x2, QBU-10, PF-89).

Previous header:
Build50 over exact Build49 (Osama 12 Nov 05:24 and 05:31): Airborne name, Godswords QTS-11 grenade launchers back (option A), Mountain Leopards recon, HQ-7 and HQ-9A removed, aircraft spec/tab moves, PHL-16 loadout options, SR-5 as HIMARS with Chinese munition names in PLAN SOF, HMV3 Cargo on PLS statistics with the HEMTT model, squad weapon order rifle/AT/MG.

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
BASE=json.loads((REL/'out/PLA-TEST-Build-61.json').read_text())['sha256']
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


W=t['WeaponsJson']
REF=zipfile.ZipFile(ROOT/'releases/0.6/out/PLA-TEST-Build-60.bamod')
ref={}
for tab in ('SquadMembersJson','ArmorsJson','TransportAvailabilitiesJson','UnitArmorsJson'):
    fn=FIELD_TO_FILE[tab];ref[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())}
    for k,v in json.loads(REF.read('UserData/FreedomArrow/constants/'+fn)).items():
        if v is None:ref[tab].pop(int(k),None)
        else:ref[tab].setdefault(int(k),{'Id':int(k)}).update(v)
refdesigner={e['unit']:e for e in json.loads(REF.read('UserData/FreedomArrow/pla-infantry-designer.json'))['entries']}
# ---------- 1. restore Build60 squads ----------
RESTORE={1166:12,1170:12,1171:12,1177:12,1173:4,1174:6}
for uid,men in RESTORE.items():
    old=[r for r in ref['SquadMembersJson'].values() if r['UnitId']==uid];assert len(old)==men,(uid,len(old))
    for r in rows('SquadMembersJson',uid):g.remove('SquadMembersJson',r['Id'])
    for r in old:g.put('SquadMembersJson',r['Id'],{k:v for k,v in r.items() if k!='Id'})
    for ar in rows('UnitArmorsJson',uid):g.put('ArmorsJson',ar['ArmorId'],{'MaxHealthPoints':ref['ArmorsJson'][ar['ArmorId']]['MaxHealthPoints']})
    pids={r['Id'] for r in pools(uid)}
    now={r['Id'] for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId'] in pids}
    was={r['Id'] for r in ref['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId'] in pids}
    for i in now-was:g.remove('TransportAvailabilitiesJson',i)
    for i in was-now:g.put('TransportAvailabilitiesJson',i,{k:v for k,v in ref['TransportAvailabilitiesJson'][i].items() if k!='Id'})
    byid[uid]['men']=refdesigner[uid]['men'];byid[uid]['weapons']=copy.deepcopy(refdesigner[uid]['weapons'])
    log.append({'unit':uid,'name':U[uid]['HUDName'],'change':f'back to {men} men as in Build60 (HP {5*men}, Build60 transport links)'})
g.put('Units',1166,{'Cost':25});log.append({'unit':1166,'name':U[1166]['HUDName'],'change':'cost 65 -> 25'})
# ---------- 2. ZSD-89A: four cards, 12 seats ----------
Z89A=1065;assert U[Z89A]['HUDName']=='ZSD-89A' and links_of(Z89A)==[19]
g.put('Units',Z89A,{'InfantrySlots':12})
zsd={19:Z89A}
for sids,skin in (((18,21),'green digital'),((17,),'desert digital'),((20,),'marine blue digital')):
    uid=clone_unit(Z89A,{});zsd[sids[0]]=uid
    for sid in sids:add_pool(uid,sid,Z89A)
    log.append({'unit':uid,'name':'ZSD-89A','change':f'new card for specs {list(sids)} ({skin} skin once the model is bought); 12 seats, QJC-88 12.7 mm'})
log.append({'unit':Z89A,'name':'ZSD-89A','change':'PLARF card (olive skin once bought); 10 -> 12 seats'})
for uid in zsd.values():
    for sid in links_of(uid):carry(uid,sid)
# ---------- 3. ZBD-86 also airborne ----------
assert U[1063]['HUDName']=='ZBD-86' and links_of(1063)==[20]
add_pool(1063,17,1063);carry(1063,17)
log.append({'unit':1063,'name':'ZBD-86','change':'also in PLAAF airborne (sand camo model needs the CGTrader purchase; BMD-2 body until then)'})
for uid in (1248,1063):assign['shared_transports'][str(uid)]=sorted(links_of(uid))
assign['one_spec_rule']['exceptions']=assign['shared_transports'];assign['one_spec_rule']['basis']+='; ZSD-89A PLAGF card in both PLAGF specs, ZBD-86 in PLAN SOF and PLAAF (Osama 12 Nov 12:09-12:16)'
checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
for uid,men in RESTORE.items():
    ok(sorted(r['Id'] for r in rows('SquadMembersJson',uid))==sorted(r['Id'] for r in ref['SquadMembersJson'].values() if r['UnitId']==uid),('members',uid))
    ok(all(t['SquadMembersJson'][r['Id']]==r for r in ref['SquadMembersJson'].values() if r['UnitId']==uid),('member rows',uid))
for uid in (1168,1169,1172,1175,1176):ok(len(rows('SquadMembersJson',uid))==7,('still 7',uid))
csk=next(r for r in pools(1166) if r['SpecializationId']==19)['Id']
ok(any(r['UnitId']==1230 and r['SpecializationAvailabilityId']==csk for r in t['TransportAvailabilitiesJson'].values()),'conscripts ride CSK-181')
for sid,uid in zsd.items():
    ok(U[uid]['InfantrySlots']==12 and U[uid]['HUDName']=='ZSD-89A',('zsd',uid))
    n12=[r for r in t['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==sid and U[r['UnitId']]['Type']==2 and sum(m['UnitId']==r['UnitId'] for m in t['SquadMembersJson'].values())==12]
    ok(all(any(x['UnitId']==uid and x['SpecializationAvailabilityId']==r['Id'] for x in t['TransportAvailabilitiesJson'].values()) for r in n12),('12-man fit',sid))
    ok({tw['WeaponId'] for tu in rows('TurretUnitsJson',uid) for tw in t['TurretWeaponsJson'].values() if tw['TurretId']==tu['TurretId']}=={2010929},('hmg',uid))
ok(sorted(links_of(1063))==[17,20],'zbd86 specs')
for tab in FIELD_TO_FILE:
    if tab not in ('Units','SquadMembersJson','ArmorsJson','TransportAvailabilitiesJson','SpecializationAvailabilitiesJson','UnitArmorsJson','UnitPropulsionsJson','UnitAbilitiesJson','MobilityJson','AbilitiesJson','TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson'):ok(t[tab]==before[tab],('no drift',tab))
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-spec-assignments.json',assign);save('UserData/FreedomArrow/pla-infantry-designer.json',designer)
receipt={'build':62,'base_build':61,'base_sha256':BASE,'changes':log,'checks':checks,'native_verified':False}
save('UserData/FreedomArrow/pla-build62.json',receipt);(ROOT/'tools/pla-specs/build62-checks.json').write_bytes(enc(receipt))
print(json.dumps({'checks':checks,'changes':log},indent=1,ensure_ascii=False))
