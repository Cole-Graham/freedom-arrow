"""Freedom Arrow 0.8.0-dev.35 over exact 0.8.0-dev.34 (Osama 13 Nov 11:33 PST, thread 1567745029781454889):
- ZTQ-62-I (958) removed: hidden from the armory and its PLARF card (spec 19) deleted.
- New ZTZ-59D1: a recon copy of ZTZ-59D (1061) in PLARF (spec 19), the ZTQ-15 Recon pattern: recon category,
  vanilla Very Good Optics (sensor 3), parent cost + 5 (60 -> 65), parent availability (6). Same gun, armour and model.
- ZFB-05 (954) uses the Russian BPM-97 model (Osama 11:41): vanilla BPM-97 (219) model, portrait, label, sound and size;
  its 12.7 mm mount uses the BPM-97 Kord turret model; the custom m_zfb05 FAModels mapping is dropped (complete package).
- ZTQ-15 camo (Osama 11:44): ZTQ-15 (906, Motorized) = desert digital m_ztq15_ddigi_*, ZTQ-15 Recon (1240, PLAGF Armored) =
  woodland digital m_ztq15_wdigi_*. New hull/turret albedo from work/ztq15-digi-20261113/gen.py (complete package).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.35'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.34.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];rows=lambda tab,uid:g.rows(tab,uid)
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN))
pools=lambda uid:rows('SpecializationAvailabilitiesJson',uid)
ZTQ62,ZTZ59D,PLARF,VGO=958,1061,19,3
assert U[ZTQ62]['HUDName']=='ZTQ-62-I' and U[ZTQ62]['DisplayInArmory'] and [r['SpecializationId'] for r in pools(ZTQ62)]==[PLARF]
assert U[ZTZ59D]['HUDName']=='ZTZ-59D' and U[ZTZ59D]['Cost']==60 and [r['SpecializationId'] for r in pools(ZTZ59D)]==[PLARF]
assert not rows('ModificationsJson',ZTZ59D) and not any(u['HUDName']=='ZTZ-59D1' for u in U.values())
# ---------- remove ZTQ-62-I (build43 remove() pattern) ----------
g.put('Units',ZTQ62,{'DisplayInArmory':False});assign['assignments'].pop(str(ZTQ62),None)
ids={r['Id'] for r in pools(ZTQ62)}
for r in list(t['TransportAvailabilitiesJson'].values()):
    if r['SpecializationAvailabilityId'] in ids or r['UnitId']==ZTQ62:g.remove('TransportAvailabilitiesJson',r['Id'])
for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
for k in assign['carriers']:assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=ZTQ62]
# ---------- ZTZ-59D1 recon (build43 clone_unit pattern: own armour/mobility/ability definitions) ----------
NEW=max(U)+1;d=copy.deepcopy(U[ZTZ59D]);d.pop('Id')
d.update({'Name':'PLA ZTZ-59D1','HUDName':'ZTZ-59D1','CategoryType':0,'Role':11,'Cost':65,'OriginalCost':65})
if 'OriginalName' in d and d['OriginalName']:d['OriginalName']='PLA ZTZ-59D1'
g.put('Units',NEW,d);defs={}
for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
    for r in rows(table,ZTZ59D):
        if (target,r[field]) not in defs:defs[target,r[field]]=g.add(target,t[target][r[field]])
        g.add(table,r,{'UnitId':NEW,field:defs[target,r[field]]})
for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
    for r in rows(table,ZTZ59D):g.add(table,r,{'UnitId':NEW})
for su in rows('SensorUnitsJson',NEW):g.put('SensorUnitsJson',su['Id'],{'SensorId':VGO})
g.add('SpecializationAvailabilitiesJson',pools(ZTZ59D)[0],{'UnitId':NEW,'SpecializationId':PLARF});assign['assignments'][str(NEW)]=[PLARF]
# ---------- ZFB-05 on the BPM-97 model ----------
ZFB,BPM,ZMOUNT=954,219,2009992
assert U[ZFB]['HUDName']=='ZFB-05' and U[ZFB]['ModelFileName']=='DLC3_Tigr' and U[BPM]['ModelFileName']=='DLC3_BPM97'
assert [r['TurretId'] for r in rows('TurretUnitsJson',ZFB)]==[ZMOUNT] and t['TurretsJson'][368]['ModelFileName']=='DLC3_BPM97/DLC3_BPM97_Kord'
MODEL_FIELDS=('ModelFileName','PortraitFileName','ThumbnailFileName','AudioPreset','Length','Width','Height')
zfb_before={k:U[ZFB][k] for k in MODEL_FIELDS}
g.put('Units',ZFB,{k:U[BPM][k] for k in MODEL_FIELDS});g.put('TurretsJson',ZMOUNT,{'ModelFileName':'DLC3_BPM97/DLC3_BPM97_Kord'})
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ));assert 'PLA ZFB-05' in models;models.pop('PLA ZFB-05')
ZTQ,ZTQR=906,1240
assert (U[ZTQ]['Name'],[r['SpecializationId'] for r in pools(ZTQ)])==('PLA ZTQ-15',[21]) and (U[ZTQR]['Name'],[r['SpecializationId'] for r in pools(ZTQR)])==('PLA ZTQ-15 Recon',[18])
assert models['PLA ZTQ-15']['file']==models['PLA ZTQ-15 Recon']['file']=='m_ztq15_green_static.fam'
models['PLA ZTQ-15'].update(file='m_ztq15_ddigi_static.fam',battle='m_ztq15_ddigi_lo_static.fam')
models['PLA ZTQ-15 Recon'].update(file='m_ztq15_wdigi_static.fam',battle='m_ztq15_wdigi_lo_static.fam')
assign['pool_counts']={str(s):sum(r['SpecializationId']==s for r in t['SpecializationAvailabilitiesJson'].values()) for s in range(17,23)}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(not U[ZTQ62]['DisplayInArmory'] and not pools(ZTQ62),'ZTQ-62-I removed')
ok(not any(r['UnitId']==ZTQ62 for r in t['TransportAvailabilitiesJson'].values()),'no ZTQ-62-I transport rows')
n=U[NEW];ok((n['HUDName'],n['CategoryType'],n['Cost'],n['DisplayInArmory'],n['ModelFileName'])==('ZTZ-59D1',0,65,True,U[ZTZ59D]['ModelFileName']),'59D1 card')
ok([r['SpecializationId'] for r in pools(NEW)]==[PLARF] and pools(NEW)[0]['MaxAvailabilityXp0']==pools(ZTZ59D)[0]['MaxAvailabilityXp0'],'59D1 PLARF availability')
ok([r['SensorId'] for r in rows('SensorUnitsJson',NEW)]==[VGO],'59D1 Very Good Optics')
for tab in ('TurretUnitsJson','WeaponAmmunitionsJson','UnitArmorsJson','UnitPropulsionsJson','UnitAbilitiesJson'):
    ok(len(rows(tab,NEW))==len(rows(tab,ZTZ59D)),('copied',tab))
key=lambda r:(r['TurretId'],r.get('Order'))
ok(sorted(map(key,rows('TurretUnitsJson',NEW)))==sorted(map(key,rows('TurretUnitsJson',ZTZ59D))),'same turrets')
ok(sorted((r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in rows('WeaponAmmunitionsJson',NEW))==sorted((r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in rows('WeaponAmmunitionsJson',ZTZ59D)),'same ammo')
for tab,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
    for r,q in zip(rows(tab,NEW),rows(tab,ZTZ59D)):ok({k:v for k,v in t[target][r[field]].items() if k not in('Id','Name')}=={k:v for k,v in t[target][q[field]].items() if k not in('Id','Name')},('same',target))
ok(all(U[ZFB][k]==U[BPM][k] for k in MODEL_FIELDS) and t['TurretsJson'][ZMOUNT]['ModelFileName']=='DLC3_BPM97/DLC3_BPM97_Kord','ZFB-05 BPM-97 model')
ok('PLA ZFB-05' not in models and not any(k.startswith('PLA ZFB') for k in models),'ZFB-05 FAModels mapping dropped')
ok(models['PLA ZTQ-15']['file']=='m_ztq15_ddigi_static.fam' and models['PLA ZTQ-15 Recon']['file']=='m_ztq15_wdigi_static.fam','ZTQ-15 camo mapping')
ok(assign['assignments'].get(str(NEW))==[PLARF] and str(ZTQ62) not in assign['assignments'],'assignment metadata')
receipt={'version':V,'base':'0.8.0-dev.34','base_sha256':BASE,'request':'Osama 13 Nov 11:33 PST: remove ZTQ-62 from the game; make a ZTZ-59 recon called ZTZ-59D1',
 'removed':{'unit':ZTQ62,'name':'ZTQ-62-I','spec':PLARF},'added':{'unit':NEW,'name':'ZTZ-59D1','parent':ZTZ59D,'spec':PLARF,'category':'recon','cost':65,
 'availability':pools(NEW)[0]['MaxAvailabilityXp0'],'sensor':'vanilla Very Good Optics (3): ground 2300 m, low alt 1250 m, high alt 1000 m (ZTZ-59D: 600/800/1000)'},
 'zfb05':{'unit':ZFB,'model_from':'BPM-97 (219)','before':zfb_before,'after':{k:U[ZFB][k] for k in MODEL_FIELDS},'mount':[ZMOUNT,'DLC3_BPM97/DLC3_BPM97_Kord'],'famodels_mapping_removed':'PLA ZFB-05'},
 'ztq15_camo':{'906 ZTQ-15 (Motorized)':'desert digital m_ztq15_ddigi','1240 ZTQ-15 Recon (PLAGF Armored)':'woodland digital m_ztq15_wdigi'},
 'pool_counts':assign['pool_counts'],'famusic_default_db':-3.1,'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign)
out=ROOT/'tools/pla-specs/0.8.0-dev.35-models.json';out.write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['added'],receipt['pool_counts'])
