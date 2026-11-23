"""Freedom Arrow 0.8.0-dev.60 over exact 0.8.0-dev.59 (Osama 13 Nov 16:3x PST, thread 1569806740139282476).
- AFT-09 (1053) is named WZ-550 (its model is the WZ-550 4x4 with HJ-9).
- PGL-625 and FK-2000 guns: ground range 1200 as shown in game (600 in data; the game shows 2x), same on both.
- Spec moves: FK-2000 -> PLAN Navy/SOF (20); GJ-11 -> PLAAF (17); PHL-191 Ballistic -> PLAGF Motorized (21); PHL-03 -> PLAGF
  Ground Force/Armored (18).
- ZTL-191 Recon: new recon copy of ZTL-191 (ZTQ-15 Recon pattern: CategoryType 0, +5 points, Very Good Optics), Motorized.
- DZD98A HE (ammo 2016261) damage 7.5 -> 10. HJ-8 (951) unit icon: the Kornet-D1 label.
- Infantry weapon models (FAModels infantry-weapons.json): QBZ-95, QBB-95, QBU-88 from the purchased low-poly files, on every squad
  that carries them (primary/special slot taken from the squad member rows).
- Models: ZTL-191 gun raised 0.27 m back to its source height; DF-17 body/cab opaque (small utility doors were cut by alpha);
  FAModels 0.3.20 re-hides the stand-in every frame until the replacement is built.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.60';PREV='0.8.0-dev.59'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser();p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson'];A=t['AmmunitionsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(i,n):assert U[i]['HUDName']==n,(i,U[i]['HUDName'],n)
hud(1053,'AFT-09');g.put('Units',1053,{'HUDName':'WZ-550'})
for aid in (2009369,2009603):g.put('AmmunitionsJson',aid,{'GroundRange':600.0})
ok(A[2009369]['GroundRange']==A[2009603]['GroundRange']==600.0,'gun range')
moves={}
for uid,n,sp in ((935,'FK-2000',20),(967,'GJ-11',17),(1036,'PHL-191 Ballistic',21),(908,'PHL-03',18)):
    hud(uid,n);rs=rows('SpecializationAvailabilitiesJson',uid);ok(len(rs)==1,('one card',n,len(rs)));old=rs[0]['SpecializationId']
    g.put('SpecializationAvailabilitiesJson',rs[0]['Id'],{'SpecializationId':sp});assign['assignments'][str(uid)]=[sp];moves[n]=[old,sp]
    for k in assign.get('carriers',{}):assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=uid]
rec['spec_moves']=moves
# ZTL-191 Recon (build43 clone pattern)
def clone_unit(parent,fields):
    uid=max(U)+1;d=copy.deepcopy(U[parent]);d.pop('Id');d.update(fields);g.put('Units',uid,d);defs={}
    for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
        for r in rows(table,parent):
            if (target,r[field]) not in defs:defs[target,r[field]]=g.add(target,t[target][r[field]])
            g.add(table,r,{'UnitId':uid,field:defs[target,r[field]]})
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
        for r in rows(table,parent):g.add(table,r,{'UnitId':uid})
    assert not rows('ModificationsJson',parent);return uid
hud(1080,'ZTL-191');zr=clone_unit(1080,{'Name':'PLA ZTL-191 Recon','HUDName':'ZTL-191 Recon','CategoryType':0,'Cost':U[1080]['Cost']+5,'OriginalCost':U[1080]['Cost']+5})
src=rows('SpecializationAvailabilitiesJson',1080)[0];g.add('SpecializationAvailabilitiesJson',src,{'UnitId':zr});assign['assignments'][str(zr)]=[src['SpecializationId']]
for su in rows('SensorUnitsJson',zr):g.put('SensorUnitsJson',su['Id'],{'SensorId':3})
ok(U[zr]['CategoryType']==0 and [r['SpecializationId'] for r in rows('SpecializationAvailabilitiesJson',zr)]==[src['SpecializationId']],'ztl191 recon')
rec['ztl191_recon']={'unit':zr,'cost':U[zr]['Cost'],'spec':src['SpecializationId'],'optics':'Very Good Optics (3)'}
ok(A[2016261]['HUDName']=='DZD98A HE','dzd');rec['dzd98a']=[A[2016261]['Damage'],10.0];g.put('AmmunitionsJson',2016261,{'Damage':10.0})
hud(951,'HJ-8');g.put('Units',951,{'ThumbnailFileName':U[151]['ThumbnailFileName']})
# models.json and infantry weapon rules
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ));models['PLA ZTL-191 Recon']=copy.deepcopy(models['PLA Catalogue ZTL-191'])
IW='UserData/FAModels/infantry-weapons.json';rules=json.loads(z.read(IW));SM=t['SquadMembersJson'];SW=t['SquadWeaponsJson']
WPN={2012205:('w_qbz95',[0,-0.2,-0.06]),2012207:('w_qbb95',[0,-0.2,-0.04]),2012821:('w_qbu88',[0,-0.17,-0.06])}
have={(r['unitId'],r['weaponId'],r['slot']) for r in rules};added=[]
for r in SW.values():
    if r['WeaponId'] not in WPN:continue
    uid=r['UnitId'];mem=[m for m in SM.values() if m['UnitId']==uid]
    slots={'primary' for m in mem if m.get('PrimaryWeaponId')==r['WeaponId']}|{'special' for m in mem if m.get('SpecialWeaponId')==r['WeaponId']} or {'primary'}
    for sl in sorted(slots):
        if (uid,r['WeaponId'],sl) in have:continue
        f,off=WPN[r['WeaponId']];rules.append({'unitId':uid,'soldierIndex':-1,'slot':sl,'weaponId':r['WeaponId'],'file':f+'.fam','battle':f+'_lo.fam','scale':1,'offset':off,'rotation':[0,0,0]});added.append((uid,U[uid]['HUDName'],r['WeaponId'],sl));have.add((uid,r['WeaponId'],sl))
ok(len(added)>=15,('weapon rules',len(added)));rec['infantry_weapon_rules']=added
files=sorted(x.name for x in a.stage.iterdir())
rec.update({'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 16:3x PST list','files':files,'checks':checks,
 'not_done':{'CSK-181':'needs the purchased 4x4 model (subscription sheet row 14); the current file is a 6x6 Mengshi'}})
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign)
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-infantry-weapons.json').write_bytes((json.dumps(rules,indent=2,ensure_ascii=z.read(IW).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps({k:rec[k] for k in ('spec_moves','ztl191_recon','dzd98a')}),'rules',len(added))
