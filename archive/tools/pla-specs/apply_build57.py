"""Build57 over exact Build56 (Osama 12 Nov).

1. "Airborne troops should all be wearing googles down desert models."
Targets: every infantry squad available in PLAAF Air Force (spec 17), plus the unused
"Airborne ..." squad rows, so they match if they return. Each copies the existing
SF goggles down desert preset (lods, +0.01558 body offset, anchorHands) exactly as the
Build30 presets did. Weapon bindings/offsets and models are unchanged.
2. "in all the PLAGF name, remove all the 'Mechanized' in the names": the word is removed from
   the displayed name (HUDName) of every PLAGF squad and unused PLAGF squad row. Internal Name
   fields and all other table values are unchanged.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
BASE=json.loads((REL/'out/PLA-TEST-Build-56.json').read_text())['sha256']
LODS=[f'pla2_sf_goggles_down_desert_{i}.fas' for i in range(3)]
UNUSED_AIRBORNE=[1138,1141,1147,1148,1150]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};units_patch=json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE['Units']))
for tab in ['Units','SpecializationAvailabilitiesJson']:
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())}
    for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE[tab])).items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
U=t['Units']
KEY='UserData/FAModels/infantry-bodies.json'
bodies=json.loads(z.read(KEY));by={b['unitId']:b for b in bodies}
preset=[b for b in bodies if b['lods']==LODS]
assert preset and all({k:v for k,v in b.items() if k!='unitId'}=={k:v for k,v in preset[0].items() if k!='unitId'} for b in preset)
preset={k:v for k,v in preset[0].items() if k!='unitId'}
spec17=sorted({r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==17} & set(by))
for uid in UNUSED_AIRBORNE:assert 'Airborne' in U[uid]['HUDName'] and uid in by,uid
targets=spec17+UNUSED_AIRBORNE
receipt={'build':57,'base_build':56,'base_sha256':BASE,'request':'Osama 12 Nov: "Airborne troops should all be wearing googles down desert models."',
         'preset':'SF goggles down desert','preset_body':preset,'changed':[],'unchanged_already':[],'gameplay_values_unchanged':True,'weapon_bindings_and_offsets_unchanged':True,'native_verified':False}
for uid in targets:
    b=by[uid];old=b['lods'][0].removesuffix('_0.fas')
    if {k:v for k,v in b.items() if k!='unitId'}==preset:receipt['unchanged_already'].append(uid);continue
    b.clear();b.update({'unitId':uid,**preset})
    receipt['changed'].append({'unit':uid,'name':U[uid]['HUDName'],'playable':uid in spec17,'from':old})
# checks: only target entries changed; order and count kept
before=json.loads(z.read(KEY))
assert [b['unitId'] for b in before]==[b['unitId'] for b in bodies]
for x,y in zip(before,bodies):
    assert x==y or x['unitId'] in targets,x['unitId']
    if x['unitId'] in targets:assert {k:v for k,v in y.items() if k!='unitId'}==preset
assert z.read('UserData/FAModels/infantry-weapons.json')==(SRC/'UserData/FAModels/infantry-weapons.json').read_bytes()
for fn in FIELD_TO_FILE.values():
    n='UserData/FreedomArrow/constants/'+fn;assert (SRC/n).read_bytes()==z.read(n),n
# 2. PLAGF names
sa=t['SpecializationAvailabilitiesJson'].values()
plagf={r['UnitId'] for r in sa if r['SpecializationId'] in (18,21)}
unused={u['Id'] for u in U.values() if u.get('CountryId')==4 and not any(r['UnitId']==u['Id'] for r in sa)}
before_units=copy.deepcopy(units_patch);receipt['renamed']=[]
for uid in sorted(plagf|unused):
    old=U[uid]['HUDName'] or ''
    if 'Mechanized' not in old:continue
    new=' '.join(old.replace('Mechanized','').split())
    units_patch[str(uid)]['HUDName']=new;U[uid]['HUDName']=new;receipt['renamed'].append({'unit':uid,'from':old,'to':new,'playable':uid in plagf})
receipt['left_for_osama']=[{'unit':u,'name':U[u]['HUDName'],'why':'abbreviation "Mech." not the word "Mechanized"'} for u in sorted(plagf) if 'Mech.' in (U[u]['HUDName'] or '')]
for k,v in units_patch.items():
    assert v==before_units[k] or (set(v)==set(before_units[k]) and all(v[f]==before_units[k][f] for f in v if f!='HUDName')),k
assert not any('Mechanized' in (U[u]['HUDName'] or '') for u in plagf)
n='UserData/FreedomArrow/constants/'+FIELD_TO_FILE['Units']
(SRC/n).write_bytes((json.dumps(units_patch,indent=2,ensure_ascii=z.read(n).isascii())+'\n').encode())
(SRC/KEY).write_bytes((json.dumps(bodies,indent=2)+'\n').encode())
(SRC/'UserData/FreedomArrow/pla-build57.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
(ROOT/'tools/pla-specs/build57-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
for c in receipt['changed']:print(c)
print('already',receipt['unchanged_already'])
for c in receipt['renamed']:print(c)
print('left',receipt['left_for_osama'])
