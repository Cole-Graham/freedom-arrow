"""Freedom Arrow 0.8.0-dev.90 over exact 0.8.0-dev.89 (Osama 13 Nov 22:13-22:22 PST, thread 1571014792016171120).
- HQ-7B (and the hidden HQ-7): Osama's seller HQ-7 model (woodland digital "Green_mix", static, 7.3 m).
- ZBD-86 (1063) removed from PLAAF (its last card; hidden). ZBD-86 Recon (PLARF) without the Malyutka by default
  (25 -> 15 points); option "HJ-73 Malyutka" +10 puts it back (same 25 total).
- Z-20 (Z-20KA, Z-20J, Z-20, Z-20T) laser designation (vanilla laser values in each card's own ability; Z-20S had it in dev.87).
- CSK-181: the 4x4 no longer replaces the 6x6. CSK-181 Transport and the catalogue CSK-181 are back on the 6x6 model (dev.82
  fixes); new card "CSK-181 4x4" (CSK-181 Transport copy) on the 4x4 model in the same four forces and the same 43 squad
  transport slots. 4x4 model rebuilt: glass only where the seller opacity map marks windows, body opaque (was too bright).
- Mengshi Recon model 75% ("way too big").
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.90';PREV='0.8.0-dev.89'
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
g=Graph(t,patches,native);U=t['Units'];AB=t['AbilitiesJson'];T=t['TurretsJson'];TU=t['TurretUnitsJson'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];O=t['OptionsJson'];M=t['ModificationsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(i,n):ok(U[i]['HUDName']==n,(i,U[i]['HUDName'],n))
def users(tab,field,i):return sorted({r['UnitId'] for r in t[tab].values() if r.get(field)==i})
# ZBD-86 out of PLAAF
hud(1063,'ZBD-86');r=rows('SpecializationAvailabilitiesJson',1063);ok([x['SpecializationId'] for x in r]==[17],'ZBD-86 only PLAAF');nta=0
for x in list(TA.values()):
    if x.get('SpecializationAvailabilityId')==r[0]['Id'] or x.get('UnitId')==1063:g.remove('TransportAvailabilitiesJson',x['Id']);nta+=1
g.remove('SpecializationAvailabilitiesJson',r[0]['Id']);g.put('Units',1063,{'DisplayInArmory':False});assign['assignments'].pop('1063',None)
for k in assign.get('carriers',{}):assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=1063]
rec['zbd86_plaaf_removed']={'card':r[0]['Id'],'transport_links':nta}
# ZBD-86 Recon Malyutka option
R=1258;hud(R,'ZBD-86 Recon');ok(U[R]['Cost']==25 and not rows('ModificationsJson',R),'1258 cost/no options')
mal=[x for x in rows('TurretUnitsJson',R) if x['TurretId']==2010902];ok(len(mal)==1,'HJ-73 mount')
MT=g.add('TurretsJson',T[2010902],{'Name':'PLA Type 86 HJ-73 Malyutka option','IsDefault':False})
for tw in [x for x in t['TurretWeaponsJson'].values() if x['TurretId']==2010902]:g.add('TurretWeaponsJson',tw,{'TurretId':MT})
g.put('TurretUnitsJson',mal[0]['Id'],{'TurretId':MT})
if not any(x['TurretId']==160 for x in rows('TurretUnitsJson',R)):g.add('TurretUnitsJson',mal[0],{'TurretId':160})
arm=[x['ArmorId'] for x in rows('UnitArmorsJson',R)];ok(len(arm)==1,'one armour')
mid=g.add('ModificationsJson',M[208],{'UnitId':R,'Name':'PLA ZBD-86 Recon ATGM','UIName':'Custom_Slot_Weapon_package'})
blank={f'Turret{i}Id':0 for i in range(21)};bo={**blank,'ModificationId':mid,'ArmorId':arm[0],'MobilityId':0,'MainSensorId':0,'ExtraSensorId':0,'ReplaceUnitName':None}
o1=g.add('OptionsJson',O[544],{**bo,'Name':'PLA ZBD-86 Recon no ATGM','UIName':'No ATGM','OptionPicture':'EMPTY','Order':0,'Cost':0,'IsDefault':True,'Turret2Id':160})
o2=g.add('OptionsJson',O[544],{**bo,'Name':'PLA ZBD-86 Recon HJ-73','UIName':'HJ-73 Malyutka','OptionPicture':'MALYUTKA' ,'Order':1,'Cost':10,'IsDefault':False,'Turret2Id':MT})
ok(o1<=32767 and o2<=32767,'short ids');g.put('Units',R,{'Cost':15,'OriginalCost':15})
ok(sum(T[x['TurretId']]['IsDefault'] for x in rows('TurretUnitsJson',R))==2,'gun and MG default, ATGM optional')
rec['zbd86_recon']={'cost':[25,15],'malyutka_option':{'id':o2,'cost':10,'mount':MT},'no_atgm_option':o1}
# Z-20 lasers
for uid,n in ((914,'Z-20KA'),(1238,'Z-20J'),(1244,'Z-20'),(1245,'Z-20T')):
    hud(uid,n);r=rows('UnitAbilitiesJson',uid);ok(len(r)==1 and users('UnitAbilitiesJson','AbilityId',r[0]['AbilityId'])==[uid],(uid,'own ability'))
    g.put('AbilitiesJson',r[0]['AbilityId'],{k:AB[10][k] for k in ('IsLaserDesignator','LaserMaxRange','LaserUsableInMove')})
rec['z20_laser']=[914,1238,1244,1245]
# CSK-181 4x4 card
P=1230;hud(P,'CSK-181');ok(not rows('ModificationsJson',P),'no options');NAME='PLA CSK-181 4x4';ok(not any(u.get('Name')==NAME for u in U.values()),'free')
uid=max(U)+1;d=copy.deepcopy(U[P]);d.pop('Id');d.update({'Name':NAME,'HUDName':'CSK-181 4x4'});g.put('Units',uid,d);defs={}
for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
    for r0 in rows(table,P):
        if (target,r0[field]) not in defs:defs[target,r0[field]]=g.add(target,t[target][r0[field]])
        g.add(table,r0,{'UnitId':uid,field:defs[target,r0[field]]})
for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
    for r0 in rows(table,P):g.add(table,r0,{'UnitId':uid})
cards=rows('SpecializationAvailabilitiesJson',P)
for r0 in cards:g.add('SpecializationAvailabilitiesJson',r0,{'UnitId':uid})
tl=[x for x in TA.values() if x.get('UnitId')==P]
for x in tl:g.add('TransportAvailabilitiesJson',x,{'UnitId':uid})
sp=sorted(r0['SpecializationId'] for r0 in cards);assign['assignments'][str(uid)]=sp;assign.setdefault('shared_transports',{})[str(uid)]=sp
ok(sorted(r0['SpecializationId'] for r0 in rows('SpecializationAvailabilitiesJson',uid))==sp==[17,19,20,21],'4x4 cards')
ok(len([x for x in TA.values() if x.get('UnitId')==uid])==len(tl)==43,'4x4 transport slots')
rec['csk181_4x4']={'unit':uid,'from':P,'specs':sp,'transport_links':len(tl),'cost':U[uid]['Cost']}
# models
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
for k in ('PLA CSK-181 Transport','PLA Catalogue CSK-181'):ok(models[k]['file']=='m_csk4_static.fam',k);before[k]=dict(models[k]);models[k]={'file':'m_csk181_static.fam','battle':'m_csk181_lo_static.fam','align':False}
ok('UserData/FAModels/m_csk181_static.fam' in z.namelist(),'6x6 files shipped')
before[NAME]=None;models[NAME]={'file':'m_csk4b_static.fam','battle':'m_csk4b_lo_static.fam','align':False}
for k in ('PLA HQ-7B','PLA HQ-7'):before[k]=dict(models[k]);models[k]={'file':'m_hq7s_static.fam','battle':'m_hq7s_lo_static.fam','align':False}
k='PLA Mengshi Recon';ok('scale' not in models[k],k);before[k]=dict(models[k]);models[k]['scale']=0.75
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={'UserData/FAModels/'+f.name:str(f) for f in sorted(a.stage.iterdir()) if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_csk4b','m_hq7s')}
ok(len([k for k in files if k.endswith('.fam')])==4,sorted(files));ok(not any(k in z.namelist() for k in files),'no overwrite')
for k in [k for k in files if k.endswith('.mat.json')]:
    mj=json.loads(Path(files[k]).read_text());ok(not any(v.get('cockpitDonor') for v in mj.values()),('ground vehicle uses clear glass',k))
    for key in mj:
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 22:13-22:22 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec['csk181_4x4']),json.dumps(rec['zbd86_recon']))
