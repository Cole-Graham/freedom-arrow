"""Build39 over exact Build38 (Osama 12 Nov 02:04 PST).

1. Sheet import (same per-row logic as Build35): Whistling Arrows swaps QBU-191 for QN-202
   (Osama's sheet edit); the five LG export test squads are struck in the sheet and removed.
2. QN-202 becomes a Javelin-like anti-infantry missile: guidance, flight and top attack copy the
   game's Javelin row (2000149); the warhead copies the RPG-7 OG-7V HE round (476); it targets
   infantry only; Whistling Arrows carries 12 shots. The CTL-181 launcher (unit 1054) fires this
   same munition. QN-202 and QBU-88 get new weapon cards traced from Osama's photos.
4. QBU-88 for conscript marksmen: one each in Conscripts and Missile Site Security (sheet).
3. GAM-102LR is the Chinese Spike LR clone: its missile copies the game's Spike LR row (2000177).
   The test GAM-102LR team becomes "Motorized GAM-102LR Team" in Motorized, priced like the
   Spike LR team (75).
"""
import argparse,copy,hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-38.json').read_text())['sha256']
HMV3=1235
enc=lambda d:(json.dumps(d,indent=2)+'\n').encode()  # same encoding as earlier builds
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--sheet',type=Path,required=True);a=p.parse_args()
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
designer=read('UserData/FreedomArrow/pla-infantry-designer.json');assign=read('UserData/FreedomArrow/pla-spec-assignments.json');identity=read('UserData/FreedomArrow/pla-infantry-identity.json')
armament=read('UserData/FreedomArrow/pla-vehicle-armament.json');catalogue=read('UserData/FreedomArrow/pla-model-catalogue.json');models=read('UserData/FAModels/models.json')
byid={e['unit']:e for e in designer['entries']};byname={e['name']:e for e in designer['entries']}
rows=lambda tab,uid:g.rows(tab,uid)

# ---------- 1. Infantry: rows changed since the Build32 import ----------
sheet=[r for r in json.loads(a.sheet.read_text())[7:] if len(r['cells'])>1 and r['cells'][1]]
def weapon(label,uid,munitions):
    name=label.split(' (')[0].strip();candidates=[(wid,r) for wid,r in t['WeaponsJson'].items() if r.get('HUDName')==name]
    if name=='QBZ-191':return 2014501 if byid[uid]['troop_type']=='Conscripts' else 2014500 if uid in [1149,1164] else 2003998
    if name=='QBZ-95':return 2014501 if byid[uid]['troop_type']=='Conscripts' else 2012205  # Sam: reservists carry plain QBZ-191
    if name=='FHJ-02':return 2014406 if 'smoke' in munitions.lower() else 2013057
    if name=='PF-98A':return 2011919 if any(x in munitions.lower() for x in ['mixed','mix:','dzt-98','also thermo']) else 2013157
    existing=next((x['weapon'] for x in byid[uid]['weapons'] if x['name']==name),None)
    if existing:return existing
    valid={int(w) for w in designer['weapon_sources']}|{2013087,2012205,2014501,2003998,2014500}
    candidates=[(wid,r) for wid,r in candidates if wid in valid];assert candidates,(uid,name,'No infantry weapon donor')
    return min(wid for wid,r in candidates)
def slot(wid):
    for entry in designer['entries']:
        for w in entry['weapons']:
            if w['weapon']==wid:return w['slot']
    return 'primary'
def ammo_template(wid,uid):
    same=[r for r in before['WeaponAmmunitionsJson'].values() if r.get('UnitId')==uid and r.get('WeaponId')==wid]
    if same:return same
    donors=[r['UnitId'] for r in before['WeaponAmmunitionsJson'].values() if r.get('WeaponId')==wid and r.get('UnitId') in byid];assert donors,(uid,wid)
    return [r for r in before['WeaponAmmunitionsJson'].values() if r.get('UnitId')==min(donors) and r.get('WeaponId')==wid]
def hide(uid):
    g.put('Units',uid,{'DisplayInArmory':False});assign['assignments'].pop(str(uid),None);pools={r['Id'] for r in rows('SpecializationAvailabilitiesJson',uid)}
    for r in list(t['TransportAvailabilitiesJson'].values()):
        if r['SpecializationAvailabilityId'] in pools:g.remove('TransportAvailabilitiesJson',r['Id'])
    for rid in pools:g.remove('SpecializationAvailabilitiesJson',rid)
def kit(e):return sorted((w['name'],w['quantity']) for w in e['weapons'])
def sheet_kit(c):return sorted((c[i].split(' (')[0].strip(),int(c[i+1])) for i in (6,8,10) if c[i] and c[i]!='None' and c[i+1] not in ('','0'))
changed=[]
for r in sheet:
    c=r['cells'];name=c[1].strip();struck=len(r['strike'])>1 and r['strike'][1]
    e=byname.get(name)
    if e is None or e['unit']==1162:continue  # Thermobaric Breachers is the engineer loadout (Build32)
    uid=e['unit'];active=bool(rows('SpecializationAvailabilitiesJson',uid))
    if struck:
        if active:hide(uid);e['removed_by_sheet_strikethrough']=True;changed.append({'unit':uid,'name':name,'change':'removed (struck in sheet)'})
        continue
    if not active:continue
    men=int(c[4]);typ=c[3];recon=c[2]=='Yes'
    if men==e['men'] and kit(e)==sheet_kit(c) and typ==e['troop_type'] and recon==e['recon']:continue
    base=weapon(c[5],uid,c[12]);requested=[]
    for col in [6,8,10]:
        if not c[col] or c[col]=='None' or c[col+1] in ('','0'):continue
        qty=int(c[col+1]);assert 0<qty<=men,(uid,c[col],qty)
        wid=weapon(c[col],uid,c[12]);requested.append((wid,slot(wid),qty,c[col].split(' (')[0]))
    template=copy.deepcopy(rows('SquadMembersJson',uid)[0]);members=[{**template,'UnitId':uid,'PrimaryWeaponId':base,'SpecialWeaponId':0} for _ in range(men)];prim=set();spec=set();selected=[]
    for wid,sl,qty,wname in sorted(requested,key=lambda q:q[1]!='primary'):
        used=prim if sl=='primary' else spec;available=[i for i in range(men) if i not in used]
        if sl=='special':available.sort(key=lambda i:members[i]['PrimaryWeaponId']!=base if wname=='QLG-10A' else i in prim)
        assert len(available)>=qty,(uid,wname)
        for i in available[:qty]:
            members[i]['PrimaryWeaponId' if sl=='primary' else 'SpecialWeaponId']=wid;used.add(i)
            if wname=='QTS-11':members[i]['SpecialWeaponId']=2004006;spec.add(i)
        selected.append({'name':wname,'weapon':wid,'quantity':qty,'slot':sl,'native_weapon':designer['weapon_sources'].get(str(wid),wid)})
    carried={m[k] for m in members for k in ['PrimaryWeaponId','SpecialWeaponId'] if m[k]};stock={wid:ammo_template(wid,uid) for wid in carried}
    g.clear_unit(uid,['SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson'])
    for m in members:g.add('SquadMembersJson',m)
    for order,wid in enumerate(sorted(carried)):
        g.add('SquadWeaponsJson',next(iter(before['SquadWeaponsJson'].values())),{'UnitId':uid,'WeaponId':wid,'Order':order})
        for ar in stock[wid]:g.add('WeaponAmmunitionsJson',ar,{'UnitId':uid,'WeaponId':wid})
    for ar in rows('UnitArmorsJson',uid):g.put('ArmorsJson',ar['ArmorId'],{'MaxHealthPoints':men*5})
    # Carriers: drop links that no longer fit, add the spec's carriers that do.
    for tr in list(t['TransportAvailabilitiesJson'].values()):
        pool=t['SpecializationAvailabilitiesJson'].get(tr['SpecializationAvailabilityId'])
        if pool and pool['UnitId']==uid and t['Units'][tr['UnitId']]['InfantrySlots']<men:g.remove('TransportAvailabilitiesJson',tr['Id'])
    linktemplate=next(iter(t['TransportAvailabilitiesJson'].values()))
    for pool in rows('SpecializationAvailabilitiesJson',uid):
        present={r['UnitId'] for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==pool['Id']}
        for carrier in assign['carriers'][str(pool['SpecializationId'])]:
            if carrier!=HMV3 and carrier not in present and t['Units'][carrier]['InfantrySlots']>=men:g.add('TransportAvailabilitiesJson',linktemplate,{'SpecializationAvailabilityId':pool['Id'],'UnitId':carrier})
    changed.append({'unit':uid,'name':name,'men':[e['men'],men],'kit':[kit(e),sheet_kit(c)]})
    e.update(row=r['row'],men=men,weapons=selected,health=men*5,munitions=c[12],notes=c[13] if len(c)>13 else e.get('notes'))
# ---------- 2/3. QN-202 anti-infantry Javelin, CTL-181 shares it; GAM-102LR = Spike LR ----------
A=t['AmmunitionsJson'];QN,JAV,GAM,SPIKE,CTL,GAMTEAM=2014237,2000149,2014293,2000177,1054,1221
assert A[JAV]['HUDName']=='Javelin' and A[SPIKE]['HUDName']=='Spike LR' and A[QN]['HUDName']=='QN-202 HE-fragmentation'
FLIGHT=['ModelFileName','AudioPreset','Seeker','SeekerAngle','MaxSeekerDistance','LaserGuided','CanReaquire','TrajectoryType','LoftAngle','LoftHeight','MinimalRange','GroundRange',
        'MaxSpeed','Acceleration','MuzzleVelocity','AimStartDelay','MainEngineIgnitionDelay','RotationSpeed','BurnTime','PreEgnitionRotationSpeed','LaunchMarginAngle',
        'DispersionHorizontalRadius','DispersionVerticalRadius','DispersionMinimal','TopArmorAttack','IsTopArmorArmorAttack','CanBeIntercepted','PreventReloadWhileTracked']
RPGHE=476;assert A[RPGHE]['HUDName']=='OG-7V 40mm HE'
WARHEAD=['Damage','PenetrationAtMinRange','PenetrationAtGroundRange','ArmorTargeted','HealthAOERadius','StressDamage','StressAOERadius','OverpressureRadius','CriticMultiplier','DamageOverTimeDuration','NoDamageFalloff','Airburst','IgnoreCover']
# Osama 02:10: 12 shots, same HE as the RPG HE round, fires like Javelin, only hits infantry.
# TargetType 3 = the Flashbang's infantry-only value (bits inferred from data, not yet seen in a game).
g.put('AmmunitionsJson',QN,{**{k:copy.deepcopy(A[JAV][k]) for k in FLIGHT},**{k:copy.deepcopy(A[RPGHE][k]) for k in WARHEAD},'TargetType':3,'HUDName':'QN-202 anti-personnel missile'})
g.put('WeaponsJson',2014236,{'HUDIcon':'FA_PLA_WP_QN202'});t['WeaponsJson'][2012821]['HUDIcon']=='FA_PLA_WP_QBU88' or g.put('WeaponsJson',2012821,{'HUDIcon':'FA_PLA_WP_QBU88'})
ctl=[r for r in rows('WeaponAmmunitionsJson',CTL)];assert len(ctl)==1
g.put('WeaponAmmunitionsJson',ctl[0]['Id'],{'AmmunitionId':QN})
g.put('Units',CTL,{'Description':'CTL-181 launcher on CSK-181: fires the QN-202 anti-infantry guided missile (same munition as the infantry QN-202).'})
g.put('AmmunitionsJson',GAM,{k:copy.deepcopy(v) for k,v in A[SPIKE].items() if k not in ('Id','Name','HUDName','HUDIcon')})
pools=rows('SpecializationAvailabilitiesJson',GAMTEAM);assert [p['SpecializationId'] for p in pools]==[22]
for tr in list(t['TransportAvailabilitiesJson'].values()):
    if tr['SpecializationAvailabilityId']==pools[0]['Id']:g.remove('TransportAvailabilitiesJson',tr['Id'])
g.put('SpecializationAvailabilitiesJson',pools[0]['Id'],{'SpecializationId':21})
g.put('Units',GAMTEAM,{'HUDName':'Motorized GAM-102LR Team','Cost':75,'Description':'Motorized long-range ATGM team. GAM-102LR is the Chinese Spike LR clone; missile copies the Spike LR row.'})
men=sum(m['UnitId']==GAMTEAM for m in t['SquadMembersJson'].values())
for carrier in assign['carriers']['21']:
    if carrier!=HMV3 and t['Units'][carrier]['InfantrySlots']>=men:g.add('TransportAvailabilitiesJson',next(iter(t['TransportAvailabilitiesJson'].values())),{'SpecializationAvailabilityId':pools[0]['Id'],'UnitId':carrier})
assign['assignments'][str(GAMTEAM)]=[21]
e=byid[GAMTEAM];e.update(name='Motorized GAM-102LR Team',spec=21,source_design_name='Motorized GAM-102LR Team',munitions="Tandem HEAT; copies the game's Spike LR missile",carriers=[r['UnitId'] for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==pools[0]['Id']])
changed.append({'unit':GAMTEAM,'name':'Motorized GAM-102LR Team','change':'Test -> Motorized; Spike LR missile; 75 pts'})
for ent in armament['entries']:
    if ent['unit']==CTL:
        for w in ent['weapons']:
            for st in w['stocks']:st.update(ammo=QN,name=A[QN]['HUDName'])
wa=[r for r in rows('WeaponAmmunitionsJson',1184) if r['AmmunitionId']==QN];assert len(wa)==1
g.put('WeaponAmmunitionsJson',wa[0]['Id'],{'Quantity':12})
for x in byid[1184]['weapons']:
    if x['name']=='QN-202':x['shots']=12
for x in byid[1219]['weapons']:
    if x['name']=='QN-202':x['shots']=6
for entry in identity['units']:
    if byid.get(entry['unit'],{}).get('removed_by_sheet_strikethrough'):entry['removed_by_sheet_strikethrough']=True

# ---------- checks ----------
checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
for r in sheet:
    c=r['cells'];e=byname.get(c[1].strip())
    if not e or e['unit']==1162:continue
    struck=len(r['strike'])>1 and r['strike'][1];active=bool(rows('SpecializationAvailabilitiesJson',e['unit']))
    ok(active!=struck,('sheet strike vs build',c[1]))
    if active:
        ok(sum(m['UnitId']==e['unit'] for m in t['SquadMembersJson'].values())==int(c[4]),('size',c[1]))
        ok(kit(e)==sheet_kit(c),('kit',c[1],kit(e),sheet_kit(c)))
for u in t['Units'].values():
    if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification'):continue
    n=len(rows('SpecializationAvailabilitiesJson',u['Id']))
    ok(n==1 or u['Id'] in (1227,HMV3),('one spec',u['Id'],n))
ok(t['Units'][HMV3]['HUDName']=='Shaanxi HMV3','Build34 HMV3 kept')
for tab in FIELD_TO_FILE:
    if tab not in ['Units','SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson','ArmorsJson','SpecializationAvailabilitiesJson','TransportAvailabilitiesJson','WeaponsJson','AmmunitionsJson']:ok(t[tab]==before[tab],('unrelated drift',tab))
ok({k:v for k,v in t['WeaponsJson'].items() if k!=2014236}=={k:v for k,v in before['WeaponsJson'].items() if k!=2014236},'only the QN-202 weapon icon changed')
ok(t['WeaponsJson'][2014236]['HUDIcon']=='FA_PLA_WP_QN202' and {k:v for k,v in t['WeaponsJson'][2014236].items() if k!='HUDIcon'}=={k:v for k,v in before['WeaponsJson'][2014236].items() if k!='HUDIcon'},'QN-202 icon only')
ok(t['AmmunitionsJson'][QN]['TargetType']==3 and all(t['AmmunitionsJson'][QN][k]==A[RPGHE][k] for k in WARHEAD),'QN-202 RPG HE warhead, infantry only')
ok([r['Quantity'] for r in rows('WeaponAmmunitionsJson',1184) if r['AmmunitionId']==QN]==[12],'Whistling Arrows 12 QN-202 shots')
ok({k:v for k,v in t['AmmunitionsJson'].items() if k not in (QN,GAM)}=={k:v for k,v in before['AmmunitionsJson'].items() if k not in (QN,GAM)},'only QN-202 and GAM-102LR ammo changed')
ok(all(t['AmmunitionsJson'][QN][k]==A[JAV][k] for k in FLIGHT) and True,'QN-202 = Javelin flight + QN warhead')
ok(all(t['AmmunitionsJson'][GAM][k]==A[SPIKE][k] for k in A[SPIKE] if k not in ('Id','Name','HUDName','HUDIcon')),'GAM-102LR = Spike LR')
ok([r['AmmunitionId'] for r in rows('WeaponAmmunitionsJson',CTL)]==[QN],'CTL-181 fires QN-202')
ok(any(w['name']=='QN-202' for w in byid[1184]['weapons']) and any(r['AmmunitionId']==QN for r in rows('WeaponAmmunitionsJson',1184)),'Whistling Arrows QN-202')
ok([r['SpecializationId'] for r in rows('SpecializationAvailabilitiesJson',GAMTEAM)]==[21],'GAM team Motorized')
for uid in [1214,1215,1216,1217,1218]:ok(not t['Units'][uid]['DisplayInArmory'] and not rows('SpecializationAvailabilitiesJson',uid),('LG test squad removed',uid))
for rid in list(t['TransportAvailabilitiesJson']):
    r=t['TransportAvailabilitiesJson'][rid];pool=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]
    men=sum(m['UnitId']==pool['UnitId'] for m in t['SquadMembersJson'].values())
    if pool['SpecializationId']>=17 and t['Units'][pool['UnitId']]['Type']==2:ok(t['Units'][r['UnitId']]['InfantrySlots']>=men,('carrier too small',rid))

def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
hud=read('UserData/FreedomArrow/pla-weapon-hud.json');hud['build']=39
for ent in hud['entries']:
    if ent['weapon']==2014236:ent.update(mode='custom',profile='QN202',address='FA_PLA_WP_QN202',basis="Osama-supplied QN-202 launcher photo, measured source edges")
    if ent['weapon']==2012821:ent.update(basis="Osama-supplied QBU-88 photo (Wikimedia Qbu-88-0), measured source edges")
for key in ['profiles','custom_icon_entries','resources']:
    if isinstance(hud.get(key),list):
        for v in (['QN202'] if key=='profiles' else ['FA_PLA_WP_QN202','FA_PLA_WP_QN202_OUTLINE'] if key=='resources' else []):
            if v not in hud[key]:hud[key].append(v)
hud['custom_icon_entries']=sum(e['mode']=='custom' for e in hud['entries']);hud['native_icon_entries']=sum(e['mode']=='native' for e in hud['entries'])
save('UserData/FreedomArrow/pla-weapon-hud.json',hud)
for n,dd in [('pla-infantry-designer.json',designer),('pla-spec-assignments.json',assign),('pla-infantry-identity.json',identity),('pla-vehicle-armament.json',armament)]:
    dd['build']=39;save('UserData/FreedomArrow/'+n,dd)
for n in ['pla-build.json','pla-specializations.json','pla-roster-revision.json','pla-model-catalogue.json','pla-single-spec.json']:
    dd=read('UserData/FreedomArrow/'+n);dd['build']=39
    if 'label' in dd:dd['label']='PLA TEST Build 39'
    save('UserData/FreedomArrow/'+n,dd)
receipt={'build':39,'base_build':38,'base_sha256':BASE,'infantry_changes':changed,'sheet_snapshot':'tools/pla-specs/build39-sheet-snapshot.json','checks':checks,'native_verified':False}
save('UserData/FreedomArrow/pla-build39.json',receipt);(ROOT/'tools/pla-specs/build39-checks.json').write_bytes(enc(receipt))
print(json.dumps(receipt,ensure_ascii=False,indent=2))
