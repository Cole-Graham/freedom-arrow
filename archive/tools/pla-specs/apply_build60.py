"""Build60 over exact Build59 (Osama 12 Nov 11:54): the PLARF PF-98 Team and the Mechanized PF-98 Tank Hunters swap PF-98 versions; PLARF gets the tripod PF-98 (HEAT 800 m + DZD98A HE), Mechanized gets the plain PF-98. Rifles, size and price stay with each squad.

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
BASE=json.loads((REL/'out/PLA-TEST-Build-59.json').read_text())['sha256']
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


W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson']
PLARF,MECH,PF,TRI=1172,1155,2011832,2016259
assert W[TRI]['HUDName']=='PF-98 (tripod)' and W[PF]['HUDName']=='PF-98'
def swap(uid,old,new):
    for m in rows('SquadMembersJson',uid):
        if m['SpecialWeaponId']==old:g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':new})
    for sw in rows('SquadWeaponsJson',uid):
        if sw['WeaponId']==old:g.put('SquadWeaponsJson',sw['Id'],{'WeaponId':new})
    olds=[r for r in rows('WeaponAmmunitionsJson',uid) if r['WeaponId']==old]
    news=[r for r in before['WeaponAmmunitionsJson'].values() if r['WeaponId']==new and r['UnitId']==(MECH if uid==PLARF else PLARF)]
    assert olds and news,(uid,len(olds),len(news))
    for r in olds:g.remove('WeaponAmmunitionsJson',r['Id'])
    for r in news:g.add('WeaponAmmunitionsJson',r,{'UnitId':uid})
swap(PLARF,PF,TRI);swap(MECH,TRI,PF)
log.append({'unit':PLARF,'name':U[PLARF]['HUDName'],'change':'tripod PF-98: HEAT 800 m + DZD98A HE 1000 m'})
log.append({'unit':MECH,'name':U[MECH]['HUDName'],'change':'plain PF-98'})
checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
A=t['AmmunitionsJson']
ok(sorted(A[r['AmmunitionId']]['GroundRange'] for r in rows('WeaponAmmunitionsJson',PLARF) if r['WeaponId']==TRI)==[400.0,500.0],'PLARF tripod ammo')
ok([A[r['AmmunitionId']]['GroundRange'] for r in rows('WeaponAmmunitionsJson',MECH) if r['WeaponId']==PF]==[300.0],'Mech plain PF-98')
for uid in (PLARF,MECH):
    carried={m[f] for m in rows('SquadMembersJson',uid) for f in ('PrimaryWeaponId','SpecialWeaponId') if m[f]}
    ok(carried=={r['WeaponId'] for r in rows('SquadWeaponsJson',uid)}=={r['WeaponId'] for r in rows('WeaponAmmunitionsJson',uid)},('consistent',uid))
for tab in FIELD_TO_FILE:
    if tab not in ('SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson'):ok(t[tab]==before[tab],('no drift',tab))
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
receipt={'build':60,'base_build':59,'base_sha256':BASE,'changes':log,'checks':checks,'native_verified':False}
save('UserData/FreedomArrow/pla-build60.json',receipt);(ROOT/'tools/pla-specs/build60-checks.json').write_bytes(enc(receipt))
print(json.dumps({'checks':checks,'changes':log},indent=1,ensure_ascii=False))
