"""Freedom Arrow 0.8.0-dev.36 over exact 0.8.0-dev.35 (Osama 13 Nov 11:52-12:00 PST, thread 1567745029781454889):
- ZTQ-15 (906) and ZTQ-15 Recon (1240) serve PLAGF Armored (spec 18): the ZTQ-15 card moves from Motorized (21) to 18 and
  takes the woodland digital model (PLAGF theme).
- New VT-5 and VT-5 Recon serve Motorized (21), desert digital (ZTQ-15 model until the bought VT-5 model is converted).
  Stat clones of ZTQ-15 / ZTQ-15 Recon except: APS (vanilla light APS: 2 charges, 10 s cooldown, as Bradley Iron Fist and
  Bumerang Afghanit), ZTZ-96A front armour (KE 600 / HEAT 700) and SRAT II side armour (HEAT 700; KE sides stay 100).
  The VT-5 card is also in PLAN Navy/SOF (20) (Osama 11:52 "VT-5 for SOF PLAN").
  Price 140 / 145 (estimate: vanilla T-80U with APS and 650 front is 135; recon +5 as ZTQ-15 Recon).
- The old hidden VT-5 draft (953) is renamed so its Name does not collide with the new card's model key.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.36'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.35.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];AR=t['ArmorsJson'];AB=t['AbilitiesJson'];rows=lambda tab,uid:g.rows(tab,uid)
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN))
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ))
pools=lambda uid:rows('SpecializationAvailabilitiesJson',uid)
ZTQ,ZTQR,OLDVT5,ZTZ96A,SRAT_UNIT,LIGHT_APS=906,1240,953,1082,979,88
ARMORED,PLAN,MOTO=18,20,21
assert U[ZTQ]['HUDName']=='ZTQ-15' and [r['SpecializationId'] for r in pools(ZTQ)]==[MOTO]
assert U[ZTQR]['HUDName']=='ZTQ-15 Recon' and [r['SpecializationId'] for r in pools(ZTQR)]==[ARMORED]
assert U[OLDVT5]['HUDName']=='VT-5' and not U[OLDVT5]['DisplayInArmory'] and not pools(OLDVT5)
assert not any(u['HUDName'] in ('VT-5 Recon',) or (u['HUDName']=='VT-5' and u['Id']!=OLDVT5) for u in U.values())
def armor(uid):r=rows('UnitArmorsJson',uid);assert len(r)==1;return AR[r[0]['ArmorId']]
def ability(uid):r=rows('UnitAbilitiesJson',uid);assert len(r)==1;return AB[r[0]['AbilityId']]
a96=armor(ZTZ96A);srat=armor(SRAT_UNIT);aps=AB[LIGHT_APS]
assert (a96['KinArmorFront'],a96['HeatArmorFront'])==(600,700) and srat['HeatArmorSides']==700 and aps['IsAPS'] and aps['APSQuantity']==2
# ---------- ZTQ-15 to PLAGF Armored, woodland digital ----------
g.put('SpecializationAvailabilitiesJson',pools(ZTQ)[0]['Id'],{'SpecializationId':ARMORED});assign['assignments'][str(ZTQ)]=[ARMORED]
models['PLA ZTQ-15'].update(file='m_ztq15_wdigi_static.fam',battle='m_ztq15_wdigi_lo_static.fam')
g.put('Units',OLDVT5,{'Name':'PLA VT-5 draft (retired)'})
# ---------- clone helper (build43 pattern: own armour/mobility/ability definitions) ----------
def clone_unit(parent,fields):
    uid=max(U)+1;d=copy.deepcopy(U[parent]);d.pop('Id');d.update(fields);g.put('Units',uid,d);defs={}
    for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
        for r in rows(table,parent):
            if (target,r[field]) not in defs:defs[target,r[field]]=g.add(target,t[target][r[field]])
            g.add(table,r,{'UnitId':uid,field:defs[target,r[field]]})
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
        for r in rows(table,parent):g.add(table,r,{'UnitId':uid})
    assert not rows('ModificationsJson',parent);return uid
APS_FIELDS=['IsAPS','APSHitboxProportion','APSQuantity','APSCooldown','APSSupplyCost','APSResupplyTime']
def vt5(parent,name,hud,cost,specs):
    uid=clone_unit(parent,{'Name':name,'HUDName':hud,'Cost':cost,'OriginalCost':cost})
    ar=armor(uid);g.put('ArmorsJson',ar['Id'],{'Name':name+' ArmorsJson','KinArmorFront':a96['KinArmorFront'],'HeatArmorFront':a96['HeatArmorFront'],'HeatArmorSides':srat['HeatArmorSides']})
    ab=ability(uid);g.put('AbilitiesJson',ab['Id'],{'Name':name+' AbilitiesJson',**{k:aps[k] for k in APS_FIELDS}})
    src=pools(parent)[0]
    for s in specs:g.add('SpecializationAvailabilitiesJson',src,{'UnitId':uid,'SpecializationId':s})
    assign['assignments'][str(uid)]=list(specs)
    models[name]={**models['PLA ZTQ-15'],'file':'m_ztq15_ddigi_static.fam','battle':'m_ztq15_ddigi_lo_static.fam'}
    return uid
VT5=vt5(ZTQ,'PLA VT-5','VT-5',140,[MOTO,PLAN])
VT5R=vt5(ZTQR,'PLA VT-5 Recon','VT-5 Recon',145,[MOTO])
assign['one_spec_rule']['exceptions'][str(VT5)]=[MOTO,PLAN];assign['shared_transports'][str(VT5)]=[PLAN,MOTO]   # the verifier's multi-spec list
assign['one_spec_rule']['basis']+='; VT-5 in Motorized and PLAN Navy/SOF (Osama 13 Nov 11:52-11:56)'
assign['pool_counts']={str(s):sum(r['SpecializationId']==s for r in t['SpecializationAvailabilitiesJson'].values()) for s in range(17,23)}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok([r['SpecializationId'] for r in pools(ZTQ)]==[ARMORED] and [r['SpecializationId'] for r in pools(ZTQR)]==[ARMORED],'ZTQ-15 pair in PLAGF Armored')
ok(sorted(r['SpecializationId'] for r in pools(VT5))==[PLAN,MOTO] and [r['SpecializationId'] for r in pools(VT5R)]==[MOTO],'VT-5 specs')
for new,par in ((VT5,ZTQ),(VT5R,ZTQR)):
    a,b=armor(new),armor(par)
    ok((a['KinArmorFront'],a['HeatArmorFront'],a['KinArmorSides'],a['HeatArmorSides'])==(600,700,b['KinArmorSides'],700),('VT-5 armour',new))
    ok({k:v for k,v in a.items() if k not in('Id','Name','KinArmorFront','HeatArmorFront','HeatArmorSides')}=={k:v for k,v in b.items() if k not in('Id','Name','KinArmorFront','HeatArmorFront','HeatArmorSides')},('rest of armour cloned',new))
    x,y=ability(new),ability(par)
    ok(x['IsAPS'] and x['APSQuantity']==2 and x['IsSmoke']==y['IsSmoke'] and x['SmokeAmmunitionId']==y['SmokeAmmunitionId'],('APS plus smoke',new))
    ok({k:v for k,v in x.items() if k not in ['Id','Name']+APS_FIELDS}=={k:v for k,v in y.items() if k not in ['Id','Name']+APS_FIELDS},('rest of ability cloned',new))
    mob=lambda u:{k:v for k,v in t['MobilityJson'][rows('UnitPropulsionsJson',u)[0]['MobilityId']].items() if k not in('Id','Name')}
    ok(mob(new)==mob(par),('mobility clone',new))
    ok(sorted(r['TurretId'] for r in rows('TurretUnitsJson',new))==sorted(r['TurretId'] for r in rows('TurretUnitsJson',par)),('same turrets/weapons',new))
    ok(sorted((r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in rows('WeaponAmmunitionsJson',new))==sorted((r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in rows('WeaponAmmunitionsJson',par)),('same ammo',new))
    ok([r['SensorId'] for r in rows('SensorUnitsJson',new)]==[r['SensorId'] for r in rows('SensorUnitsJson',par)],('same optics',new))
    ok(U[new]['CategoryType']==U[par]['CategoryType'] and U[new]['DisplayInArmory'],('category',new))
ok(models['PLA ZTQ-15']['file']=='m_ztq15_wdigi_static.fam' and models['PLA ZTQ-15 Recon']['file']=='m_ztq15_wdigi_static.fam','ZTQ-15 woodland')
ok(models['PLA VT-5']['file']==models['PLA VT-5 Recon']['file']=='m_ztq15_ddigi_static.fam','VT-5 desert')
ok(sum(u['Name']=='PLA VT-5' for u in U.values())==1,'unique VT-5 model key')
receipt={'version':V,'base':'0.8.0-dev.35','base_sha256':BASE,'request':'Osama 13 Nov 11:52-12:00 PST: VT-5 for PLAN SOF; VT-5 serves Motorized and ZTQ-15 PLAGF, each with a recon and a vehicle version; stat clones except VT-5 gets APS; VT-5 more armour: SRAT II sides, ZTZ-96A front',
 'ztq15':{'unit':ZTQ,'spec':[MOTO,ARMORED],'camo':'woodland digital'},
 'vt5':{'unit':VT5,'parent':ZTQ,'specs':[MOTO,PLAN],'cost':140},'vt5_recon':{'unit':VT5R,'parent':ZTQR,'specs':[MOTO],'cost':145},
 'vt5_changes':{'armour_front':'KE 300->600, HEAT 500->700 (ZTZ-96A)','armour_sides':'HEAT 250->700 (SRAT II); KE 100 unchanged','aps':'2 charges, 10 s cooldown (vanilla light APS)','camo':'desert digital ZTQ-15 model until the VT-5 model is bought'},
 'pool_counts':assign['pool_counts'],'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign)
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,VT5,VT5R,receipt['pool_counts'])
