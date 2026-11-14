"""Freedom Arrow 0.8.0-dev.94 over exact 0.8.0-dev.93 (Osama 13 Nov 22:45 PST "fix it all all the open models, I redownloaded
PHL-191", thread 1571014792016171120).
- WZ-550 (AFT-09 card): seller SketchUp model rebuilt. Its colours were applied as linear values (pale green) and its library
  textures (leather, aluminium) gave brown hatches and white marks; now flat seller olive in linear colour (dark, as the listing
  picture), the displaced display missile (group 46) removed, translucent windows as clear glass.
- PHL-191 AR3 (F016; the re-download is byte-identical inside): smoke plume (165 parts), flying missile and the missile sliding
  out of the launcher removed; launcher lowered 24.4 deg to travel position on the bed; painted with the woodland digital
  pattern (the seller's map links point to files not in the package; preview shows woodland digital); clear windows.
  New card "PHL-191 Cruise" (PLAGF Motorized) on this model, a copy of the PHL-191 Ballistic card (same 225 points and the two
  Fire Dragon loadouts) until Osama gives the cruise loadout.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.94';PREV='0.8.0-dev.93'
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
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
P=1036;ok(U[P]['HUDName']=='PHL-191 Ballistic','1036');NAME='PLA PHL-191 Cruise';ok(not any(u.get('Name')==NAME for u in U.values()),'free')
uid=max(U)+1;d=copy.deepcopy(U[P]);d.pop('Id');d.update({'Name':NAME,'HUDName':'PHL-191 Cruise'});g.put('Units',uid,d);defs={}
for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
    for r0 in rows(table,P):
        if (target,r0[field]) not in defs:defs[target,r0[field]]=g.add(target,t[target][r0[field]])
        g.add(table,r0,{'UnitId':uid,field:defs[target,r0[field]]})
for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
    for r0 in rows(table,P):g.add(table,r0,{'UnitId':uid})
amap={x['ArmorId']:y['ArmorId'] for x,y in zip(rows('UnitArmorsJson',P),rows('UnitArmorsJson',uid))}
newopts=[]
for m in rows('ModificationsJson',P):
    mid=g.add('ModificationsJson',m,{'UnitId':uid})
    for o in sorted([o for o in O.values() if o.get('ModificationId')==m['Id']],key=lambda o:o.get('Order',0)):
        oid=g.add('OptionsJson',o,{'ModificationId':mid,'Name':o['Name'].replace('PHL-191','PHL-191 Cruise'),'ArmorId':amap.get(o.get('ArmorId'),o.get('ArmorId'))});ok(oid<=32767,'short id');newopts.append(oid)
for r0 in rows('SpecializationAvailabilitiesJson',P):g.add('SpecializationAvailabilitiesJson',r0,{'UnitId':uid})
assign['assignments'][str(uid)]=assign['assignments'].get(str(P),[r0['SpecializationId'] for r0 in rows('SpecializationAvailabilitiesJson',P)])
ok([r0['SpecializationId'] for r0 in rows('SpecializationAvailabilitiesJson',uid)]==[21] and len(newopts)==2,'cruise card')
rec['phl191_cruise']={'unit':uid,'from':P,'cost':U[uid]['Cost'],'options':newopts,'spec':21,'note':'loadout copied from the Ballistic until Osama specifies the cruise loadout'}
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
k='PLA Catalogue AFT-09';ok(models[k]['file']=='m_aft09_static.fam',k);before[k]=dict(models[k]);models[k]={'file':'m_aft09f_static.fam','battle':'m_aft09f_lo_static.fam','align':False}
before[NAME]=None;models[NAME]={'file':'m_phl191cf_static.fam','battle':'m_phl191cf_lo_static.fam','align':False}
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={'UserData/FAModels/'+f.name:str(f) for f in sorted(a.stage.iterdir()) if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_aft09f','m_phl191cf')}
ok(len([k for k in files if k.endswith('.fam')])==4,sorted(files));ok(not any(k in z.namelist() for k in files),'no overwrite')
for k in [k for k in files if k.endswith('.mat.json')]:
    mj=json.loads(Path(files[k]).read_text());ok(not any(v.get('cockpitDonor') for v in mj.values()),('clear glass',k))
    for key in mj:
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 22:45 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec['phl191_cruise']))
