"""Freedom Arrow 0.8.0-dev.87 over exact 0.8.0-dev.86 (Osama 13 Nov 21:47-21:55 PST, thread 1571014792016171120).
- ZTQ-15 Recon: seller desert digital (Hull_Dust_Camo, m_ztq15d, same size as the green one). ZTQ-15 stays green.
- ZTZ-100 (968): front KE 750 -> 700 (front HEAT 1200 unchanged), side HEAT 500 -> 700, jammer copied from the Abrams X
  ECM Shtora ability (ECMAccuracyMultiplier 0.7) into its only default ability.
- ZSL-92 (both cards) model 90%. ZTL-191 + Recon 105 mm gun reload 5-6 s -> 4-5 s.
- Laser on recon helicopters: Z-19, Z-19 Recon, Z-9WA Recon move from vanilla "ECM Heli 05 Default" (23) to its identical
  laser twin (2000771); Z-11WB (no ability) gets vanilla "Laser Veh Default" (10); Z-20S gets the laser fields in its own
  ability. Z-10, Z-21 and Z-21 Recon already have lasers.
- New recon unit "Mengshi Recon" (F006 seller model, doors modelled open): CSK-131 Mengshi (900) stats, Recon category,
  Very Good optics (sensor 3, as the ZTL-191 Recon), +5 points, in PLAN Navy/SOF, PLAGF Motorized and PLAAF.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.87';PREV='0.8.0-dev.86'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];AB=t['AbilitiesJson'];AR=t['ArmorsJson'];UA=t['UnitAbilitiesJson'];SA=t['SpecializationAvailabilitiesJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def users(tab,field,i):return sorted({r['UnitId'] for r in t[tab].values() if r.get(field)==i})
def hud(i,n):ok(U[i]['HUDName']==n,(i,U[i]['HUDName'],n))
# ZTZ-100
hud(968,'ZTZ-100');ok(users('UnitArmorsJson','ArmorId',2010183)==[968] and users('UnitAbilitiesJson','AbilityId',2010187)==[968],'ZTZ-100 own rows')
ok(AR[2010183]['KinArmorFront']==750 and AR[2010183]['HeatArmorSides']==500 and AR[2010183]['HeatArmorFront']==1200,'ztz100 armour now')
g.put('ArmorsJson',2010183,{'KinArmorFront':700,'HeatArmorSides':700})
ok(AB[2001845]['Name']=='Abrams X ECM Shtora NoModel' and AB[2001845]['ECMAccuracyMultiplier']==0.7,'abrams jammer')
g.put('AbilitiesJson',2010187,{'ECMAccuracyMultiplier':AB[2001845]['ECMAccuracyMultiplier']})
rec['ztz100']={'KinArmorFront':[750,700],'HeatArmorSides':[500,700],'HeatArmorFront':1200,'jammer_ECMAccuracyMultiplier':0.7}
# ZTL-191 reload
ok(W[2011297]['HUDName']=='105 mm high-pressure rifled gun' and users('WeaponAmmunitionsJson','WeaponId',2011297)==[1080,1263],'ztl-191 gun')
g.put('WeaponsJson',2011297,{'MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':5.0});rec['ztl191_reload']=[[5,6],[4,5]]
# helicopter lasers
ok(all(AB[2000771].get(k)==v for k,v in AB[23].items() if k not in ('Id','Name','IsLaserDesignator','LaserMaxRange','LaserUsableInMove')),'23 and 2000771 identical apart from the laser')
sw=[]
for uid,n in ((940,'Z-19'),(1103,'Z-19'),(1236,'Z-19'),(1133,'Z-9WA Recon'),(1134,'Z-19 Recon'),(1237,'Z-19 Recon')):
    hud(uid,n);r=rows('UnitAbilitiesJson',uid);ok(len(r)==1 and r[0]['AbilityId']==23,(uid,'ability 23'));g.put('UnitAbilitiesJson',r[0]['Id'],{'AbilityId':2000771});sw.append(uid)
hud(942,'Z-11WB');ok(not rows('UnitAbilitiesJson',942),'Z-11WB no ability');tpl=[r for r in UA.values() if r['AbilityId']==10][0];g.add('UnitAbilitiesJson',tpl,{'UnitId':942,'AbilityId':10})
hud(1243,'Z-20S');r=rows('UnitAbilitiesJson',1243);ok(len(r)==1 and users('UnitAbilitiesJson','AbilityId',r[0]['AbilityId'])==[1243],'Z-20S own ability')
g.put('AbilitiesJson',r[0]['AbilityId'],{k:AB[10][k] for k in ('IsLaserDesignator','LaserMaxRange','LaserUsableInMove')})
for uid in sw+[942,1243,913,1104,1135,1239]:ok(any(AB[x['AbilityId']].get('IsLaserDesignator') for x in rows('UnitAbilitiesJson',uid)),('laser',uid))
rec['helo_laser']={'swapped_23_to_2000771':sw,'Z-11WB':'ability 10','Z-20S':r[0]['AbilityId']}
# Mengshi Recon
P=900;hud(P,'CSK-131 Mengshi');ok(not rows('ModificationsJson',P),'no options');NAME='PLA Mengshi Recon';ok(not any(u.get('Name')==NAME for u in U.values()),'free')
uid=max(U)+1;d=copy.deepcopy(U[P]);d.pop('Id');d.update({'Name':NAME,'HUDName':'Mengshi Recon','CategoryType':0,'Cost':U[P]['Cost']+5,'OriginalCost':U[P].get('OriginalCost',U[P]['Cost'])+5,'DisplayInArmory':True});g.put('Units',uid,d);defs={}
for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
    for r0 in rows(table,P):
        if (target,r0[field]) not in defs:defs[target,r0[field]]=g.add(target,t[target][r0[field]])
        g.add(table,r0,{'UnitId':uid,field:defs[target,r0[field]]})
for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
    for r0 in rows(table,P):g.add(table,r0,{'UnitId':uid})
for su in rows('SensorUnitsJson',uid):g.put('SensorUnitsJson',su['Id'],{'SensorId':3})
src=rows('SpecializationAvailabilitiesJson',P);ok(len(src)==1,'one template card')
for sp in (20,21,17):g.add('SpecializationAvailabilitiesJson',src[0],{'UnitId':uid,'SpecializationId':sp})
assign['assignments'][str(uid)]=[17,20,21];assign.setdefault('shared_transports',{})[str(uid)]=[17,20,21]
assign.setdefault('one_spec_rule',{}).setdefault('exceptions',{})[str(uid)]=[17,20,21]
ok(sorted(r0['SpecializationId'] for r0 in rows('SpecializationAvailabilitiesJson',uid))==[17,20,21] and U[uid]['CategoryType']==0,'mengshi recon cards')
rec['mengshi_recon']={'unit':uid,'from':P,'cost':U[uid]['Cost'],'specs':[17,20,21],'sensor':3}
# models
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
ok(models['PLA ZTQ-15 Recon']['file']=='m_ztq15_camo_static.fam','ztq15 recon now green');before['PLA ZTQ-15 Recon']=dict(models['PLA ZTQ-15 Recon'])
models['PLA ZTQ-15 Recon']={**models['PLA ZTQ-15 Recon'],'file':'m_ztq15d_static.fam','battle':'m_ztq15d_lo_static.fam'}
for k in ('PLA Catalogue ZSL-92 family','PLA ZSL-92 MG'):ok('scale' not in models[k],k);before[k]=dict(models[k]);models[k]['scale']=0.9
before[NAME]=None;models[NAME]={'file':'m_mengshir_static.fam','battle':'m_mengshir_lo_static.fam','align':False}
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={'UserData/FAModels/'+f.name:str(f) for f in sorted(a.stage.iterdir()) if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_ztq15d','m_mengshir')}
ok(len([k for k in files if k.endswith('.fam')])==4,sorted(files));ok(not any(k in z.namelist() for k in files),'no overwrite')
for k in [k for k in files if k.endswith('.mat.json')]:
    for key in json.loads(Path(files[k]).read_text()):
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 21:47-21:55 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec['mengshi_recon']))
