"""Freedom Arrow 0.8.0-dev.83 over exact 0.8.0-dev.82 (Osama 13 Nov 20:34-21:05 PST, thread 1571014792016171120).
Osama's new downloads, converted static at seller scale with seller paint (work/pla-0.8/osama-20261113b):
- ZTZ-99 card: seller ZTZ-99 (woodland "Mix"); the ZTZ-99A keeps its model.
- ZTZ-59D and ZTZ-59D1: seller ZTZ-59A (replaces the untextured 500k-vertex Type 59D model that kept vanishing).
- PGZ-95 ("Mix"), VT-5 + VT-5 Recon ("Camo"), PLZ-07 + PLZ-07B ("Camo", was the PLZ-89 model), Z-9, all six Z-19 cards.
- Z-20: navy grey for PLAN SOF and PLAAF cards (Z-20J, Z-20T, Z-20KA, Z-20S), army green for PLAGF (Osama 20:59).
- ZBD-86 (all three Type 86 cards) and ZBD-03 + ZBD-03 Recon ("ZBD-03 uses the ZBD-86 model", Osama 21:04).
- CSK-181 Transport and the hidden catalogue CSK-181: the 4x4 CSK-181 with QJC-88 (Osama 20:41 "4. yes").
- New unit ZTZ-85-II in PLARF Rocket/Reservist: ZTZ-85-III (956) stats, Type 85-II model (seller woodland "mid").
- PLZ-83 model 75% (Osama 20:46); PHL-191 Ballistic model 90% and vanilla glass on its windows (Osama 20:48).
Glass on the new aircraft/vehicle windows uses the vanilla F-16 glass (FAModels 0.3.22 falls back to clear glass).
Held: recon Mengshi (F006, doors modelled open), PHL-191 AR3 (launcher raised, missile in flight, no paint), HQ-9 (.max only).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.83';PREV='0.8.0-dev.82'
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
g=Graph(t,patches,native);U=t['Units'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def clone_unit(parent,fields):
    uid=max(U)+1;d=copy.deepcopy(U[parent]);d.pop('Id');d.update(fields);g.put('Units',uid,d);defs={}
    for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
        for r in rows(table,parent):
            if (target,r[field]) not in defs:defs[target,r[field]]=g.add(target,t[target][r[field]])
            g.add(table,r,{'UnitId':uid,field:defs[target,r[field]]})
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
        for r in rows(table,parent):g.add(table,r,{'UnitId':uid})
    assert not rows('ModificationsJson',parent);return uid
# New ZTZ-85-II (PLARF) from the hidden ZTZ-85-III
ok(U[956]['HUDName']=='ZTZ-85-III' and not rows('SpecializationAvailabilitiesJson',956),'956 hidden ZTZ-85-III')
NEW_NAME='PLA ZTZ-85-II';ok(not any(u.get('Name')==NEW_NAME for u in U.values()),'name free')
nu=clone_unit(956,{'Name':NEW_NAME,'HUDName':'ZTZ-85-II','DisplayInArmory':True})
src=[r for r in rows('SpecializationAvailabilitiesJson',1061) if r['SpecializationId']==19];ok(len(src)==1,'PLARF template row')
g.add('SpecializationAvailabilitiesJson',src[0],{'UnitId':nu});assign['assignments'][str(nu)]=[19]
ok([r['SpecializationId'] for r in rows('SpecializationAvailabilitiesJson',nu)]==[19] and U[nu]['Cost']==U[956]['Cost'],'85-II card')
rec['ztz85ii']={'unit':nu,'from':956,'cost':U[nu]['Cost'],'spec':19}
# models.json
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw)
MAP={'ztz99':['PLA Catalogue ZTZ-99'],'ztz59a':['PLA Catalogue Type 59D','PLA ZTZ-59D1'],'pgz95':['PLA Catalogue PGZ-95'],
 'vt5s':['PLA VT-5','PLA VT-5 Recon'],'plz07':['PLA PLZ-07B','PLA Catalogue PLZ-07'],'z9':['PLA Catalogue Z-9'],
 'z19':['PLA Z-19E','PLA Catalogue Z-19','PLA Recon Z-19E','PLA Recon Z-19','PLA SF Z-19','PLA SF Recon Z-19'],
 'z20n':['PLA Z-20','PLA Z-20S','PLA SF Z-20','PLA Z-20T'],'z20a':['PLA PLAGF Z-20'],
 'csk4':['PLA CSK-181 Transport','PLA Catalogue CSK-181'],'zbd86':['PLA Catalogue Type 86 — original turret','PLA Catalogue ZBD-03 / ZLC-2000'],
 'type85':[NEW_NAME]}
names={u.get('Name') for u in U.values()}
before={}
for slug,keys in MAP.items():
    for k in keys:
        ok(k in names,('unit name exists',k));before[k]=models.get(k)
        e={kk:vv for kk,vv in (models.get(k) or {}).items() if kk=='hide'}
        models[k]={'file':f'm_{slug}_static.fam','battle':f'm_{slug}_lo_static.fam','align':False,**e}
for k,s in (('PLA Catalogue PLZ-83',0.75),('PLA Catalogue PHL-191 / AR3',0.9)):
    ok('scale' not in models[k],(k,'had no scale'));before[k]=dict(models[k]);models[k]['scale']=s
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
# PHL-191 Ballistic windows: vanilla glass
glass={}
for n in ('m_phl191b_static','m_phl191b_lo_static'):
    mj=json.loads(z.read(f'UserData/FAModels/{n}.mat.json'));gk=[k for k,v in mj.items() if v.get('clearGlass')];ok(len(gk)==1,(n,gk))
    mj[gk[0]].update(cockpitDonor='US_F16_Glass');glass[f'UserData/FAModels/{n}.mat.json']=mj
# staged files
files={'UserData/FAModels/'+f.name:str(f) for f in sorted(a.stage.iterdir()) if f.suffix in ('.fam','.json','.png')}
need={f'm_{s}_{q}static.{e}' for s in MAP for q in ('','lo_') for e in ('fam','mat.json')}
ok(need<={k.split('/')[-1] for k in files},('staged',sorted(need-{k.split('/')[-1] for k in files})))
ok(not any(k in z.namelist() for k in files),'no staged file overwrites a shipped file')
for slug in MAP:
    for q in ('','lo_'):
        for key in json.loads(Path(files[f'UserData/FAModels/m_{slug}_{q}static.mat.json']).read_text()):
            tex=key.split('|')[0]
            if tex:ok('UserData/FAModels/'+tex in files,('texture staged',tex))
gdir=ROOT/f'tools/pla-specs/{V}-glass';gdir.mkdir(exist_ok=True)
for k,mj in glass.items():
    f=gdir/k.split('/')[-1];f.write_text(json.dumps(mj,indent=1)+'\n');files[k]=str(f)
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 20:34-21:05 PST model batch',
 held={'recon Mengshi F006':'doors modelled open in one mesh','PHL-191 AR3 F016':'launcher raised, missile in flight, texture links missing; Cruise loadout undefined','HQ-9':'3ds Max file only'},
 files=len(files),checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign)
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files),'new unit',nu)
