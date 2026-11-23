"""Build41 over exact Build40 (Osama, 12 Nov 2026 03:08-03:30 PST, thread 1567745029781454889).

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
BASE=json.loads((REL/'out/PLA-TEST-Build-40.json').read_text())['sha256']
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

# ---------- removals ----------
def remove(uid,why):
    g.put('Units',uid,{'DisplayInArmory':False});assign['assignments'].pop(str(uid),None)
    ids={r['Id'] for r in pools(uid)}
    for r in list(t['TransportAvailabilitiesJson'].values()):
        if r['SpecializationAvailabilityId'] in ids or r['UnitId']==uid:g.remove('TransportAvailabilitiesJson',r['Id'])
    for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
    for k in assign['carriers']:assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=uid]
    log.append({'unit':uid,'name':U[uid]['HUDName'],'change':'removed: '+why})
REMOVE={1055:'duplicate of HJ-10 card 936 (AFT-10 is the HJ-10 carrier)',1088:'J-20B seller package',956:'ZTZ-85-III',1081:'ZTZ-80',
        953:'VT-5',1078:'ZBL-19 seller name',1077:'ZBL-09',1058:'CSK-181 stays only as the Rocket Force transport (unit 1230)'}
for uid,why in REMOVE.items():assert pools(uid),uid;remove(uid,why)

# ---------- spec moves ----------
def move(uid,sid):
    ps=pools(uid);assert len(ps)==1,(uid,len(ps));old=ps[0]['SpecializationId']
    g.put('SpecializationAvailabilitiesJson',ps[0]['Id'],{'SpecializationId':sid});assign['assignments'][str(uid)]=[sid]
    log.append({'unit':uid,'name':U[uid]['HUDName'],'change':f'spec {old} -> {sid}'})
MOVES={1087:21,973:20,977:20,1095:20,919:17,1102:20}  # J-10CE Motorized; FH-97A, J-16D, Jiutian, Y-8 PLAN SF; H-6K Air Force
for uid,sid in MOVES.items():move(uid,sid)
assert [r['SpecializationId'] for r in pools(949)]==[19]  # ZTZ-96 base already Rocket Force (no change)

# ---------- designation renames ----------
RENAME={936:'AFT-10',1028:'DF-17/ZF',1063:'ZBD-86',1060:'ZTZ-59',1061:'ZTZ-59D',1062:'ZSD-63',1064:'ZSD-89',1065:'ZSD-89A',
        1102:'Y-8',1090:'JJ-5',1098:'J-2'}
for uid,name in RENAME.items():
    log.append({'unit':uid,'name':name,'change':'renamed from '+U[uid]['HUDName']});g.put('Units',uid,{'HUDName':name})

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

# ---------- SF copies: Z-19, Z-19 Recon, Z-20 ----------
template_pool=lambda uid:pools(uid)[0]
SF={}
for parent,name in [(1103,'PLA SF Z-19'),(1134,'PLA SF Recon Z-19'),(914,'PLA SF Z-20')]:
    uid=clone_unit(parent,{'Name':name,'Description':U[parent]['Description']+' PLAN SOF copy (Osama 12 Nov).'})
    g.add('SpecializationAvailabilitiesJson',template_pool(parent),{'UnitId':uid,'SpecializationId':20});assign['assignments'][str(uid)]=[20]
    if U[parent]['Name'] in models:models[name]=copy.deepcopy(models[U[parent]['Name']])
    SF[parent]=uid;log.append({'unit':uid,'name':U[uid]['HUDName'],'change':f'new PLAN SF copy of {parent}'})
# Z-20 SF copy carries SF infantry like the Airforce Z-20 carries airborne infantry.
z20=SF[914];assign['carriers']['20'].append(z20);link=next(iter(t['TransportAvailabilitiesJson'].values()))
for pool in [r for r in t['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==20 and U[r['UnitId']]['Type']==2]:
    men=sum(m['UnitId']==pool['UnitId'] for m in t['SquadMembersJson'].values())
    if U[z20]['InfantrySlots']>=men:g.add('TransportAvailabilitiesJson',link,{'SpecializationAvailabilityId':pool['Id'],'UnitId':z20})

# ---------- recon helicopters: guns and unguided rocket pods only (Osama 03:37) ----------
A=t['AmmunitionsJson'];RECON_HELOS=[]
for u in list(U.values()):
    if u.get('CountryId')!=4 or u.get('Type')!=8 or u.get('CategoryType')!=0 or not u.get('DisplayInArmory') or [r['SpecializationId'] for r in pools(u['Id'])] in ([],[22]):continue
    uid=u['Id'];RECON_HELOS.append(uid)
    for wa in rows('WeaponAmmunitionsJson',uid):
        if A[wa['AmmunitionId']].get('Seeker'):
            wid=wa['WeaponId'];g.remove('WeaponAmmunitionsJson',wa['Id'])
            for tu in rows('TurretUnitsJson',uid):
                if {tw['WeaponId'] for tw in t['TurretWeaponsJson'].values() if tw['TurretId']==tu['TurretId']}=={wid}:g.remove('TurretUnitsJson',tu['Id'])
            log.append({'unit':uid,'name':u['HUDName'],'change':'removed guided weapon '+W_name(wid)})
# Drop turret definitions no unit mounts any more (new rows only).
used={r['TurretId'] for r in t['TurretUnitsJson'].values()}|{o.get('TurretId') for o in t['OptionsJson'].values() if o.get('TurretId')}
for tid in [k for k in list(t['TurretsJson']) if k not in native['TurretsJson'] and k not in used and t['TurretsJson'][k].get('ParentTurretId') not in used]:
    if any(x.get('ParentTurretId')==tid for x in t['TurretsJson'].values()):continue
    for tw in [x for x in t['TurretWeaponsJson'].values() if x['TurretId']==tid]:g.remove('TurretWeaponsJson',tw['Id'])
    g.remove('TurretsJson',tid)

# ---------- Y-8 as a Harvest Hawk-style gunship (native KC-130J Harvest Hawk, unit 303) ----------
HH,Y8=303,1102;assert U[HH]['HUDName']=='KC-130J Harvest Hawk'
for table in ['UnitArmorsJson','UnitPropulsionsJson','UnitAbilitiesJson','TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
    for r in rows(table,Y8):g.remove(table,r['Id'])
g.clear_options(Y8);tmp=clone_unit(HH,{})
for table in ['UnitArmorsJson','UnitPropulsionsJson','UnitAbilitiesJson','TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson','ModificationsJson']:
    for r in rows(table,tmp):g.put(table,r['Id'],{'UnitId':Y8})
g.remove('Units',tmp)
keep={k:U[Y8][k] for k in ['Name','HUDName','CountryId','DisplayInArmory','ContentMembership','IsUnitModification','OriginalName','OriginalCost','OwnerInfantryID']}
g.put('Units',Y8,{**{k:copy.deepcopy(v) for k,v in U[HH].items() if k!='Id'},**keep,'Description':'Y-8 gunship used like the KC-130J Harvest Hawk: copies its weapons, sensors, armor and flight. Native C-130 Harvest Hawk model as the Y-8 stand-in.'})
models.pop(U[Y8]['Name'],None)
log.append({'unit':Y8,'name':'Y-8','change':'Harvest Hawk loadout and model; PLAN SF'})

# ---------- J-11B uses the J-16 model; Mi-8 Cargo to Helicopters ----------
models['PLA J-11B']=copy.deepcopy(models['PLA J-16']);log.append({'unit':923,'name':'J-11B','change':'J-16 model (visual only)'})
assert U[MI8]['CategoryType']==4;g.put('Units',MI8,{'CategoryType':5});log.append({'unit':MI8,'name':'Mi-8 Cargo','change':'Logistic (hidden tab) -> Helicopters'})

# ---------- specs ----------
SPEC={17:'PLAAF Air Force',18:'PLAGF Ground Force/Armored',19:'PLARF Rocket/Reservist',20:'PLAN Navy/SOF',21:'PLAGF Motorized'}
for sid,name in SPEC.items():g.put('SpecializationsJson',sid,{'UIName':name,'Name':'PLA '+name,'LogisticsSlots':0})

# ---------- infantry ----------
NAMES={1137:'HJ-12 Team',1139:'Tank Hunters 坦克杀手',1140:'QLU-11 Team',1142:'Pathfinders 先遣队',1144:'Snipers 狙击组',
       1145:'HN-6 Patrol 防空巡逻',1146:'Assault Raiders 突击队',1149:'Target Observers 观察组',
       1151:'Mechanized AT Riflemen 反坦克班',1156:'Mechanized Combat Engineers 工兵班',1158:'Mechanized GPMG Riflemen 机枪班',
       1160:'Armored Scouts 装甲侦察',1161:'Armored Sniper Pair 狙击组',1162:'Thermobaric Breachers 温压工兵',1163:'Mechanized Riflemen 机步班',
       1164:'Armored Forward Observers 前观组',
       1168:'HJ-73D Team',1169:'HN-6 Team',1170:'QJZ-89 Team',1171:'QLZ-87 Team',1172:'PF-98 Team',1177:'Thermobaric Team',
       1173:'Malyutka Recon Ambush Team 侦察伏击',1175:'Infantry 步兵',1176:'Counter-Raid Team 反袭击队',
       1192:'Marines 陆战队',
       1196:'Motorized Line Infantry 摩步班',1197:'Motorized AA Troopers 防空班',1198:'Motorized AT Troopers 反坦克组',
       1201:'Motorized Recon Patrol 侦察班',1202:'Motorized Snipers 狙击组',1205:'Motorized Light AT Riflemen 轻反坦克',
       1206:'Air Defense Scouts 防空侦察',1209:'Thermobaric Assault 温压突击',
       1211:'Test Export Riflemen 出口步枪',1212:'Test SMG Assault 冲锋枪组',1213:'Test Suppressed Scouts 消声侦察',1224:'Test QTS Recon Cell 数字侦察'}
for uid,name in NAMES.items():
    old=U[uid]['HUDName'];g.put('Units',uid,{'HUDName':name})
    if uid in byid:byid[uid]['name']=name
    for e in identity.get('units',[]):
        if e.get('unit')==uid:
            for k in ('name','display_name'):
                if k in e:e[k]=name
    log.append({'unit':uid,'name':name,'change':'renamed from '+old})
# Tabs: recon flag = recon tab + recon role (32); SF line role 36 (importer rule).
for uid,recon in [(1183,False),(1191,False),(1187,True)]:
    g.put('Units',uid,{'CategoryType':0 if recon else 1,'Role':32 if recon else 36});byid[uid]['recon']=recon
    log.append({'unit':uid,'name':U[uid]['HUDName'],'change':'recon tab' if recon else 'infantry tab'})
g.put('Units',1184,{'ThumbnailFileName':'FA_PLA_INF_XIANGJIAN'});log.append({'unit':1184,'name':U[1184]['HUDName'],'change':'Whistling Arrows emblem'})
# QBZ-95 for every Rocket Force rifle: 2014501 is a renamed copy of QBZ-95 2012205 (same stats and 5.8 mm ammo 2012206).
QBZ95,PLAIN191,OPTIC191,AMMO58=2012205,2014501,2003998,2012206
W=t['WeaponsJson'];assert {k:v for k,v in W[QBZ95].items() if k not in ('Id','Name','HUDName','HUDIcon')}=={k:v for k,v in W[PLAIN191].items() if k not in ('Id','Name','HUDName','HUDIcon')}
rifle_ammo=[r for r in t['WeaponAmmunitionsJson'].values() if r['WeaponId']==PLAIN191];assert {(r['AmmunitionId'],r['Quantity']) for r in rifle_ammo}=={(AMMO58,120)}
r19=[r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==19 and U[r['UnitId']]['Type']==2]
for uid in r19:
    for m in rows('SquadMembersJson',uid):
        if m['PrimaryWeaponId'] in (PLAIN191,OPTIC191):g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':QBZ95})
    left={m['PrimaryWeaponId'] for m in rows('SquadMembersJson',uid)}|{m['SpecialWeaponId'] for m in rows('SquadMembersJson',uid)}
    for sw in rows('SquadWeaponsJson',uid):
        if sw['WeaponId'] in (PLAIN191,OPTIC191):
            if QBZ95 in {x['WeaponId'] for x in rows('SquadWeaponsJson',uid)}:g.remove('SquadWeaponsJson',sw['Id'])
            else:g.put('SquadWeaponsJson',sw['Id'],{'WeaponId':QBZ95})
    for wa in rows('WeaponAmmunitionsJson',uid):
        if wa['WeaponId'] in (PLAIN191,OPTIC191):g.remove('WeaponAmmunitionsJson',wa['Id'])
    if QBZ95 in left:g.add('WeaponAmmunitionsJson',rifle_ammo[0],{'UnitId':uid,'WeaponId':QBZ95})
    if uid in byid:
        for w in byid[uid]['weapons']:
            if w['weapon'] in (PLAIN191,OPTIC191):w.update(weapon=QBZ95,name='QBZ-95')
        byid[uid]['base_rifle']='QBZ-95'
log.append({'units':r19,'change':'Rocket Force rifles -> QBZ-95 (2012205)'})
# Godswords: 6 men, all six carry QTS-11 (rifle 2004004 + grenade launcher 2004006). QLU-11 removed.
GW=1181;ms=rows('SquadMembersJson',GW);assert len(ms)==8
for m in ms[6:]:g.remove('SquadMembersJson',m['Id'])
for m in ms[:6]:g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':2004004,'SpecialWeaponId':2004006})
carried={2004004,2004006}
for sw in rows('SquadWeaponsJson',GW):
    if sw['WeaponId'] not in carried:g.remove('SquadWeaponsJson',sw['Id'])
for wa in rows('WeaponAmmunitionsJson',GW):
    if wa['WeaponId'] not in carried:g.remove('WeaponAmmunitionsJson',wa['Id'])
assert {sw['WeaponId'] for sw in rows('SquadWeaponsJson',GW)}==carried and {wa['WeaponId'] for wa in rows('WeaponAmmunitionsJson',GW)}==carried
for ar in rows('UnitArmorsJson',GW):g.put('ArmorsJson',ar['ArmorId'],{'MaxHealthPoints':30})
byid[GW].update(men=6,health=30,weapons=[w for w in byid[GW]['weapons'] if w['name']=='QTS-11'])
for w in byid[GW]['weapons']:w['quantity']=6
log.append({'unit':GW,'name':U[GW]['HUDName'],'change':'6 men, 6x QTS-11 only'})

# Falcons get a PF-98 (Osama 03:33): one QBZ-192 rifleman carries it in the special slot, ammo as Airborne Riflemen.
FAL,PF98=1185,2011832
m=next(m for m in rows('SquadMembersJson',FAL) if m['PrimaryWeaponId']==2013087 and not m['SpecialWeaponId']);g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':PF98})
g.add('SquadWeaponsJson',rows('SquadWeaponsJson',FAL)[0],{'WeaponId':PF98,'Order':max(x['Order'] for x in rows('SquadWeaponsJson',FAL))+1})
for wa in [r for r in rows('WeaponAmmunitionsJson',1136) if r['WeaponId']==PF98]:g.add('WeaponAmmunitionsJson',wa,{'UnitId':FAL})
byid[FAL]['weapons'].append({'name':'PF-98','weapon':PF98,'quantity':1,'slot':'special','native_weapon':172})
log.append({'unit':FAL,'name':U[FAL]['HUDName'],'change':'adds 1 PF-98'})
# QBU-191 suppressed (Osama 03:35): vanilla suppressed DMRs are Silent with a suppressed sound; Mk12 is the 5.56 suppressed DMR preset.
QBU191=2004000;assert W[QBU191]['HUDName']=='QBU-191' and not W[QBU191]['Silent']
g.put('WeaponsJson',QBU191,{'Silent':True,'AudioPreset':W[55]['AudioPreset']});log.append({'weapon':QBU191,'name':'QBU-191','change':'suppressed (Silent, Mk12 suppressed sound)'})

# ---------- QJY-201 weapon card ----------
QJY=2012411;assert W[QJY]['HUDName']=='QJY-201' and W[QJY]['HUDIcon']=='M240'
g.put('WeaponsJson',QJY,{'HUDIcon':'FA_PLA_WP_QJY201'})
for ent in hud['entries']:
    if ent['weapon']==QJY:ent.update(mode='custom',profile='QJY201',address='FA_PLA_WP_QJY201',basis="Osama-supplied QJY-201 model render (12 Nov 03:08), measured source edges")
for key,vals in [('profiles',['QJY201']),('resources',['FA_PLA_WP_QJY201','FA_PLA_WP_QJY201_OUTLINE'])]:
    if isinstance(hud.get(key),list):hud[key]+= [v for v in vals if v not in hud[key]]
hud['custom_icon_entries']=sum(e['mode']=='custom' for e in hud['entries']);hud['native_icon_entries']=sum(e['mode']=='native' for e in hud['entries']);hud['build']=41

# ---------- checks ----------
checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
links={}
for r in t['SpecializationAvailabilitiesJson'].values():links.setdefault(r['UnitId'],[]).append(r['SpecializationId'])
for uid in REMOVE:ok(not U[uid]['DisplayInArmory'] and uid not in links and not any(r['UnitId']==uid for r in t['TransportAvailabilitiesJson'].values()),('removed',uid))
for uid,sid in MOVES.items():ok(links[uid]==[sid],('moved',uid))
for uid,n in RENAME.items():ok(U[uid]['HUDName']==n,('rename',uid))
for u in U.values():
    if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification') or u['Id'] not in links:continue
    ok(len(links[u['Id']])==1 or u['Id'] in (MI8,HMV3),('one spec',u['Id']))
    ok(not re.search(r'\bType\b|—|seller|package',u['HUDName']) or links[u['Id']]==[22],('designation name',u['Id'],u['HUDName']))
    ok(len(''.join(re.findall(r'[一-鿿]',u['HUDName'])))<=4,('chinese <=4',u['Id'],u['HUDName']))
    ok(sorted(links[u['Id']])==sorted(assign['assignments'].get(str(u['Id']),[])),('assignment metadata',u['Id']))
for uid in SF.values():ok(links[uid]==[20],('SF copy',uid))
ok(not any(u.get('CategoryType')==4 and u.get('CountryId')==4 and u['Id'] in links and links[u['Id']]!=[22] for u in U.values()),'no China card in the Logistic tab')
for sid,name in SPEC.items():ok(t['SpecializationsJson'][sid]['UIName']==name and t['SpecializationsJson'][sid]['LogisticsSlots']==0,('spec',sid))
for uid in r19:ok(not any(m['PrimaryWeaponId'] in (PLAIN191,OPTIC191) for m in rows('SquadMembersJson',uid)),('QBZ-95',uid))
ok(len(rows('SquadMembersJson',GW))==6 and all(m['PrimaryWeaponId']==2004004 and m['SpecialWeaponId']==2004006 for m in rows('SquadMembersJson',GW)),'Godswords')
for rid,r in t['TransportAvailabilitiesJson'].items():
    pool=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]
    if pool['SpecializationId']>=17:
        ok(U[r['UnitId']]['DisplayInArmory'] and pool['SpecializationId'] in links.get(r['UnitId'],[]),('carrier visible in spec',rid))
        ok(U[r['UnitId']]['InfantrySlots']>=sum(m['UnitId']==pool['UnitId'] for m in t['SquadMembersJson'].values()),('carrier too small',rid))
ok({k:v for k,v in U[Y8].items() if k not in keep and k not in ('Id','Description')}=={k:v for k,v in U[HH].items() if k not in keep and k not in ('Id','Description')},'Y-8 = Harvest Hawk')
ok(len(rows('TurretUnitsJson',Y8))==len(rows('TurretUnitsJson',HH)) and len(rows('WeaponAmmunitionsJson',Y8))==len(rows('WeaponAmmunitionsJson',HH)),'Y-8 HH weapons')
touched={'TurretsJson','TurretWeaponsJson','Units','SpecializationAvailabilitiesJson','TransportAvailabilitiesJson','SpecializationsJson','SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson','ArmorsJson','WeaponsJson',
         'UnitArmorsJson','UnitPropulsionsJson','UnitAbilitiesJson','MobilityJson','AbilitiesJson','TurretUnitsJson','SensorUnitsJson','ModificationsJson','OptionsJson'}
for tab in FIELD_TO_FILE:
    if tab not in touched:ok(t[tab]==before[tab],('unrelated drift',tab))
for tab in ['AmmunitionsJson','SensorsJson','FlyPresetsJson','CountriesJson']:ok(t[tab]==before[tab],('no definition drift',tab))
for tab in ['TurretsJson','TurretWeaponsJson']:ok(set(t[tab])<=set(before[tab]) and all(t[tab][k]==before[tab][k] for k in t[tab]),('turret definitions only removed',tab))
for uid in RECON_HELOS:ok(not any(A[wa['AmmunitionId']].get('Seeker') for wa in rows('WeaponAmmunitionsJson',uid)) and rows('WeaponAmmunitionsJson',uid),('recon helo unguided only',uid))
for tu in t['TurretUnitsJson'].values():
    ws={tw['WeaponId'] for tw in t['TurretWeaponsJson'].values() if tw['TurretId']==tu['TurretId']}
    if tu['UnitId']==Y8 and tu['TurretId'] in {x['TurretId'] for x in before['TurretUnitsJson'].values() if x['UnitId']==HH and not any(w['UnitId']==HH and w['WeaponId'] in ws for w in before['WeaponAmmunitionsJson'].values())}:continue  # vanilla Harvest Hawk base-turret Hellfire, copied as is
    if U.get(tu['UnitId'],{}).get('CountryId')==4:ok(all(any(wa['WeaponId']==w for wa in rows('WeaponAmmunitionsJson',tu['UnitId'])) for w in ws),('mounted weapon without ammo row',tu['Id']))
ok({k:v for k,v in W.items() if k not in (QJY,QBU191)}=={k:v for k,v in before['WeaponsJson'].items() if k not in (QJY,QBU191)},'only QJY-201 card and QBU-191 suppression changed in WeaponsJson')
ok(W[QBU191]['Silent'] and 'Suppressor' in W[QBU191]['AudioPreset'],'QBU-191 suppressed')
ok(sum(m['SpecialWeaponId']==PF98 for m in rows('SquadMembersJson',FAL))==1 and any(r['WeaponId']==PF98 for r in rows('WeaponAmmunitionsJson',FAL)),'Falcons PF-98')

# ---------- save ----------
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
assign['build']=41;assign['pool_counts']={str(s):sum(r['SpecializationId']==s for r in t['SpecializationAvailabilitiesJson'].values()) for s in range(17,23)}
designer['build']=41;identity['build']=41
for n,dd in [('pla-infantry-designer.json',designer),('pla-spec-assignments.json',assign),('pla-infantry-identity.json',identity),('pla-weapon-hud.json',hud)]:save('UserData/FreedomArrow/'+n,dd)
save('UserData/FAModels/models.json',models)
receipt={'build':41,'base_build':40,'base_sha256':BASE,'changes':log,'checks':checks,'native_verified':False,
         'not_done':{'ZBD-03 BMD-3 hull':'no BMD-3 in the game; BMD-4 hull has its turret built in','Z-20 marine skin':'no marine Z-20 skin found','ZBD-98':'no such unit in the roster'}}
save('UserData/FreedomArrow/pla-build41.json',receipt);(ROOT/'tools/pla-specs/build41-checks.json').write_bytes(enc(receipt))
print(json.dumps({'checks':checks,'changes':len(log)},indent=1))
