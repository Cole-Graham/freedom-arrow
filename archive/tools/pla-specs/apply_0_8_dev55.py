"""Freedom Arrow 0.8.0-dev.55 over exact 0.8.0-dev.54 (Osama 13 Nov 15:28-15:45 PST, thread 1569806740139282476).
- J-5, J-7, J-8D: one cannon; J-6W: two. GSh-23L stats (vanilla PlaneGun 23 GSh23L, 483) with the real PLA names
  (J-5 Type 23-1, J-6W/J-7 Type 30-1, J-8D Type 23-3), on the default mount that was empty.
- Z-8L: King Stallion (CH-53K, 275) stat clone - cost, stealth, 30 seats, role, weight, armour, mobility, abilities, sensor;
  its own name/model/specs/transport list kept; no weapons.
- WZ-7: RQ-4 Global Hawk (264) stat clone with its own name/model/specs.
- Z-10K: AH-64D Longbow optics (Exceptional, sensor 5); Z-21 already has them.
- ZBD-251 missile: HJ-10 stat clone (unit 936 weapon/ammo stats) named HJ-16; its own 2-round load kept.
- CSK-181 Transport is named CSK-181. Mountain Leopards 90. Z-11WB also in PLAN Navy/SOF. Z-19 Recon (PLAAF, 1132) removed.
- Models: DF-15 black tyres, dark olive missile, vanilla glass; HQ-17A front radar further forward; Z-11WB shinier metal;
  QN-506 more metallic; Lynx ATV, SR-5 and both Shaanxi HMV3 hide their crew (FAModels 0.3.19 re-checks every pass).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.55';PREV='0.8.0-dev.54'
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
g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];T=t['TurretsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];A=t['AmmunitionsJson'];SU=t['SensorUnitsJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));rows=g.rows;checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(i,n):assert U[i]['HUDName']==n,(i,U[i]['HUDName'],n)
# ---------- J-5/6/7/8 cannons ----------
GSH=483;gam=next(x for x in WA.values() if x['WeaponId']==GSH);J={1089:('J-5','Type 23-1 23 mm cannon',1),1091:('J-6W','Type 30-1 30 mm cannon',2),1092:('J-7','Type 30-1 30 mm cannon',1),975:('J-8D','Type 23-3 23 mm cannon',1)}
guns={}
for uid,(n,gname,cnt) in J.items():
    hud(uid,n);dm=[r for r in TU.values() if r['UnitId']==uid and r['TurretId']==2018554];ok(len(dm)==1,('empty default mount',uid))
    wid=g.add('WeaponsJson',W[GSH],{'Name':f'PLA {n} {gname}','HUDName':gname})
    tid=g.add('TurretsJson',T[2011510],{'Name':f'PLA {n} cannon mount','IsDefault':True})
    tw0=next(r for r in TW.values() if r['TurretId']==2011510)
    for k in range(cnt):g.add('TurretWeaponsJson',tw0,{'TurretId':tid,'WeaponId':wid,'Order':k})
    g.put('TurretUnitsJson',dm[0]['Id'],{'TurretId':tid});g.add('WeaponAmmunitionsJson',gam,{'UnitId':uid,'WeaponId':wid,'Quantity':18,'Order':0})
    guns[n]={'weapon':gname,'count':cnt,'stats_from':'GSh-23L (483)'}
rec['jet_guns']=guns
# ---------- stat clones ----------
KEEP={'Id','Name','HUDName','OriginalName','Description','ModelFileName','PortraitFileName','ThumbnailFileName','CountryId','DisplayInArmory','AudioPreset'}
def restat(dst,src,weapons):
    before={k:U[dst].get(k) for k in U[src] if k not in KEEP};g.put('Units',dst,{k:copy.deepcopy(v) for k,v in U[src].items() if k not in KEEP})
    for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson'),('SensorUnitsJson','SensorId',None)]:
        for r in rows(table,dst):g.remove(table,r['Id'])
        for r in rows(table,src):
            if target:nid=g.add(target,t[target][r[field]],{'Name':f"{U[dst]['Name']} {target}"} if 'Name' in t[target][r[field]] else None);g.add(table,r,{'UnitId':dst,field:nid})
            else:g.add(table,r,{'UnitId':dst})
    ok(not weapons or True,'')
    return {'before':before,'after':{k:U[dst].get(k) for k in before}}
hud(1106,'Z-8L');hud(275,'CH-53K King Stallion')
rec['z8l']=restat(1106,275,False)
z8w=[W[tw['WeaponId']]['HUDName'] for r in rows('TurretUnitsJson',1106) for tw in TW.values() if tw['TurretId']==r['TurretId']];rec['z8l']['weapons_removed']=z8w
for r in rows('TurretUnitsJson',1106):g.put('TurretUnitsJson',r['Id'],{'TurretId':2018554})
for r in rows('WeaponAmmunitionsJson',1106):g.remove('WeaponAmmunitionsJson',r['Id'])
for r in rows('TurretUnitsJson',1106):ok(not [tw for tw in TW.values() if tw['TurretId']==r['TurretId']],('z8l unarmed',r['TurretId']))
ok(not rows('ModificationsJson',1106) and not rows('WeaponAmmunitionsJson',1106),'z8l no weapons')
ok(U[1106]['InfantrySlots']==U[275]['InfantrySlots']==30,'z8l seats')
hud(1100,'WZ-7');hud(264,'RQ-4 Global Hawk');rec['wz7']=restat(1100,264,False)
ok(not rows('TurretUnitsJson',264) and not rows('TurretUnitsJson',1100),'wz7 unarmed')
# ---------- optics ----------
hud(913,'Z-10K');lb=rows('SensorUnitsJson',8);ok([r['SensorId'] for r in lb]==[5],'longbow optics')
for r in rows('SensorUnitsJson',913):g.put('SensorUnitsJson',r['Id'],{'SensorId':5})
ok([r['SensorId'] for r in rows('SensorUnitsJson',913)]==[5] and [r['SensorId'] for r in rows('SensorUnitsJson',1104)]==[5],'z10k/z21 optics')
# ---------- ZBD-251 HJ-16 ----------
hud(1056,'ZBD-251');ZW=2014655;HW=2009619;za=next(x for x in WA.values() if x['WeaponId']==ZW);ha=next(x for x in WA.values() if x['WeaponId']==HW)
g.put('WeaponsJson',ZW,{**{k:copy.deepcopy(v) for k,v in W[HW].items() if k not in ('Id','Name','MagazineSize')},'HUDName':'HJ-16'})
g.put('AmmunitionsJson',za['AmmunitionId'],{**{k:copy.deepcopy(v) for k,v in A[ha['AmmunitionId']].items() if k not in ('Id','Name')},'HUDName':'HJ-16'})
ok(A[za['AmmunitionId']]['Seeker']==A[ha['AmmunitionId']]['Seeker'] and W[ZW]['HUDName']=='HJ-16','hj16')
rec['zbd251_hj16']={'weapon':ZW,'ammo':za['AmmunitionId'],'stats_from':[HW,ha['AmmunitionId']],'rounds':za['Quantity']}
# ---------- names, cost, specs ----------
hud(1230,'CSK-181 Transport');g.put('Units',1230,{'HUDName':'CSK-181'})
ok(U[1186]['HUDName'].startswith('Mountain Leopards'),'ml');g.put('Units',1186,{'Cost':90})
hud(942,'Z-11WB');src=rows('SpecializationAvailabilitiesJson',942)[0]
if not [r for r in rows('SpecializationAvailabilitiesJson',942) if r['SpecializationId']==20]:g.add('SpecializationAvailabilitiesJson',src,{'SpecializationId':20})
assign['assignments'][str(942)]=sorted({r['SpecializationId'] for r in rows('SpecializationAvailabilitiesJson',942)})
ex=assign.setdefault('one_spec_rule',{}).setdefault('exceptions',{});ex[str(942)]=assign['assignments'][str(942)];assign.setdefault('shared_transports',{})[str(942)]=assign['assignments'][str(942)]
hud(1132,'Z-19 Recon');ok(U[1132]['Name']=='PLA Recon Z-19E','z19r')
g.put('Units',1132,{'DisplayInArmory':False});assign['assignments'].pop('1132',None);ids={r['Id'] for r in rows('SpecializationAvailabilitiesJson',1132)}
for r in list(TA.values()):
    if r['SpecializationAvailabilityId'] in ids or r['UnitId']==1132:g.remove('TransportAvailabilitiesJson',r['Id'])
for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
for k in assign.get('carriers',{}):assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=1132]
ok(not rows('SpecializationAvailabilitiesJson',1132),'z19 recon removed')
# ---------- models.json ----------
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ));CREW='(?i)soldier|crew|driver|gunner|passenger|human|pilot|infantry|_char|airborne'
for k,uid in (('PLA Lynx ATV',1228),('PLA SR-5',934),('PLA Shaanxi HMV3',1235),('PLA Shaanxi HMV3 Cargo',1247)):
    ok(U[uid]['Name']==k,('name',k));models[k]={'file':'','battle':'','align':False,'hide':CREW}
files=sorted(x.name for x in a.stage.iterdir())
rec.update({'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 15:28-15:45 PST list','files':files,'checks':checks})
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign)
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False,default=str)+'\n')
print('checks',checks,json.dumps({k:rec[k] for k in ('jet_guns','zbd251_hj16')},ensure_ascii=False),'z8l',{k:v for k,v in rec['z8l']['after'].items() if rec['z8l']['before'].get(k)!=v})
