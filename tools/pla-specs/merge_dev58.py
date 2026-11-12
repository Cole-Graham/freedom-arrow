"""Put the latest main dev build under the PLA TEST pack (Osama 12 Nov: "update the latest build into
our PLA test build, we're getting close to launching").

Inputs: the common base (0.6.0-dev.101), the latest PLA TEST package (ours) and main dev (theirs,
0.7.0-dev.58). Rules:
- Russian/US units and everything keyed to them (abilities, turrets, weapons links, squads,
  modifications/options, specialization rows) come from main dev exactly.
- China units and everything keyed to them come from PLA exactly, including RU/US transports
  linked into China specializations.
- Rows not keyed to a unit (weapons, ammunition, turrets, armour, mobility, sensors, abilities,
  countries, specializations) merge three-way per field; if both sides changed the same field,
  main dev wins and the conflict is listed.
- Four China units whose IDs main dev now uses for other units move: 971 J-31 -> 1251,
  972 WZ-8 -> 1252, 973 FH-97A -> 1253, 985 Type21 woodland -> 1254.
- Option IDs: main dev and PLA both renumbered the 0.6 option IDs to fit the native short range,
  differently. Options are matched by their original 0.6 ID; main dev options keep main dev IDs,
  China options keep PLA IDs unless main dev already uses that ID.
Writes the 24 constant patch files (diff against vanilla) and option-id-migration.json to SRC.
"""
import argparse,copy,hashlib,json,sys,zipfile,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
RENUMBER={971:1251,972:1252,973:1253,985:1254}
CHINA=4
UNIT_KEYED=['UnitAbilitiesJson','UnitPropulsionsJson','TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson','SquadMembersJson','SquadWeaponsJson','ModificationsJson','UnitArmorsJson']
p=argparse.ArgumentParser(description=__doc__)
for x in ('base','pla','dev','vanilla'):p.add_argument('--'+x,type=Path,required=True)
p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
VAN={tab:{r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())} for tab in FIELD_TO_FILE}
def load(pkg):
    z=zipfile.ZipFile(pkg);t={}
    for tab,fn in FIELD_TO_FILE.items():
        t[tab]=copy.deepcopy(VAN[tab])
        for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+fn)).items():
            if v is None:t[tab].pop(int(k),None)
            else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
    n='UserData/FreedomArrow/option-id-migration.json'
    mig={int(k):v for k,v in json.loads(z.read(n)).items()} if n in z.namelist() else {}
    return t,mig,z
B,_,_=load(a.base);O,migO,zO=load(a.pla);T,migT,zT=load(a.dev)
receipt={'inputs':{x:{'file':getattr(a,x).name,'sha256':hashlib.file_digest(getattr(a,x).open('rb'),'sha256').hexdigest()} for x in ('base','pla','dev')},
         'renumbered_china_units':{},'conflicts_dev_wins':[],'delete_vs_change':[],'option_ids_reassigned':{},'counts':{}}
# 1. options back to their original 0.6 IDs so both sides line up
def orig_options(t,mig):
    # A migration maps old IDs (0.6 ID, its 16-bit wrapped form, and merged duplicates) to one new ID.
    # The 0.6 ID that existed in the base is the matching key.
    inv={}
    for k,v in mig.items():
        if k>0 and k in B['OptionsJson']:inv[v]=min(k,inv.get(v,k))  # merged duplicates: lowest 0.6 ID
    t['OptionsJson']={inv.get(k,k):dict(r,Id=inv.get(k,k)) for k,r in t['OptionsJson'].items()}
    assert len(t['OptionsJson'])==len(set(t['OptionsJson']))
    return inv
invO=orig_options(O,migO);invT=orig_options(T,migT)
# 2. move the four clashing China units
for old,new in RENUMBER.items():
    assert O['Units'][old]['CountryId']==CHINA and new not in O['Units'] and new not in T['Units'],(old,new)
    u=O['Units'].pop(old);u['Id']=new;O['Units'][new]=u;receipt['renumbered_china_units'][str(old)]={'to':new,'name':u['HUDName']}
for tab,rows in O.items():
    for r in rows.values():
        for f in ('UnitId','OwnerInfantryID','ReplaceUnitId'):
            if r.get(f) in RENUMBER:r[f]=RENUMBER[r[f]]
china={k for k,u in O['Units'].items() if u['CountryId']==CHINA}
assert not china&set(T['Units']),'China unit ID used by main dev'
china_specs={k for k,s in O['SpecializationsJson'].items() if s['CountryId']==CHINA}
# 3. merge
M={}
def three(tab,k):
    b,o,t=B[tab].get(k),O[tab].get(k),T[tab].get(k)
    if o==t:return o
    if o==b:return t
    if o is None:return t  # PLA's removals of shared rows are not carried: main dev rows may still use them
    if t==b:return o
    if o is None or t is None:
        receipt['delete_vs_change'].append([tab,k,'kept '+('pla' if t is None else 'dev')]);return o if t is None else t
    if b is None:b={}
    r={}
    for f in set(o)|set(t):
        if o.get(f)==t.get(f) or o.get(f)==b.get(f):r[f]=t.get(f)
        elif t.get(f)==b.get(f):r[f]=o.get(f)
        else:r[f]=t.get(f);receipt['conflicts_dev_wins'].append([tab,k,f,o.get(f),t.get(f)])
    return r
for tab in FIELD_TO_FILE:
    if tab=='Units':
        M[tab]={k:r for k,r in T[tab].items()};M[tab].update({k:O[tab][k] for k in china})
    elif tab in UNIT_KEYED:
        M[tab]={k:r for k,r in T[tab].items() if r['UnitId'] not in china}
        for k,r in O[tab].items():
            if r['UnitId'] in china:
                assert k not in M[tab] or M[tab][k]==r,('row id clash',tab,k);M[tab][k]=r
    elif tab=='SpecializationAvailabilitiesJson':
        M[tab]={k:r for k,r in T[tab].items() if r['SpecializationId'] not in china_specs}
        for k,r in O[tab].items():
            if r['SpecializationId'] in china_specs:assert k not in M[tab],('row id clash',tab,k);M[tab][k]=r
    elif tab=='TransportAvailabilitiesJson':
        ours={k for k,r in O['SpecializationAvailabilitiesJson'].items() if r['SpecializationId'] in china_specs}
        M[tab]={k:r for k,r in T[tab].items() if r['SpecializationAvailabilityId'] not in ours}
        for k,r in O[tab].items():
            if r['SpecializationAvailabilityId'] in ours:assert k not in M[tab],('row id clash',tab,k);M[tab][k]=r
    elif tab=='OptionsJson':
        owner=lambda t,r:t['ModificationsJson'].get(r['ModificationId'],{}).get('UnitId')
        M[tab]={k:r for k,r in T[tab].items() if owner(T,r) not in china}
        for k,r in O[tab].items():
            if owner(O,r) in china:assert k not in M[tab],('option clash',k);M[tab][k]=r
    else:
        M[tab]={}
        for k in set(B[tab])|set(O[tab])|set(T[tab]):
            r=three(tab,k)
            if r is not None:M[tab][k]=r
# 4. final option IDs: main dev keeps its IDs, China keeps PLA IDs unless taken
final={};used=set()
for k,r in M['OptionsJson'].items():
    if owner(M,r) not in china:
        fid={v:kk for kk,v in invT.items()}.get(k,k);assert fid not in used;final[k]=fid;used.add(fid)
fwdO={v:kk for kk,v in invO.items()}
nxt=max(used|{fwdO.get(k,k) for k in M['OptionsJson']})+1
for k,r in sorted(M['OptionsJson'].items()):
    if owner(M,r) in china:
        fid=fwdO.get(k,k)
        if fid in used:receipt['option_ids_reassigned'][str(fid)]=nxt;fid=nxt;nxt+=1
        final[k]=fid;used.add(fid)
assert max(final.values())<=32767,max(final.values())
pla_final={fwdO.get(k,k):final[k] for k,r in M['OptionsJson'].items() if owner(M,r) in china}
M['OptionsJson']={final[k]:dict(r,Id=final[k]) for k,r in M['OptionsJson'].items()}
# saved-deck migration: main dev's map, plus PLA's map for China options
migration={str(k):v for k,v in migT.items()}
for k,v in migO.items():
    if v in pla_final and str(k) not in migration:migration[str(k)]=pla_final[v]
for old,new in receipt['option_ids_reassigned'].items():migration.setdefault(old,new)
# 5. reference checks
REF={'UnitId':'Units','OwnerInfantryID':'Units','ReplaceUnitId':'Units','AbilityId':'AbilitiesJson','Ability1Id':'AbilitiesJson','Ability2Id':'AbilitiesJson','Ability3Id':'AbilitiesJson',
     'ArmorId':'ArmorsJson','MobilityId':'MobilityJson','SensorId':'SensorsJson','MainSensorId':'SensorsJson','ExtraSensorId':'SensorsJson','TurretId':'TurretsJson','WeaponId':'WeaponsJson',
     'PrimaryWeaponId':'WeaponsJson','SpecialWeaponId':'WeaponsJson','AmmunitionId':'AmmunitionsJson','ModificationId':'ModificationsJson','SpecializationId':'SpecializationsJson',
     'SpecializationAvailabilityId':'SpecializationAvailabilitiesJson','CountryId':'CountriesJson','FlyPresetId':'FlyPresetsJson','SmokeAmmunitionId':'AmmunitionsJson','ParentTurretId':'TurretsJson',**{f'Turret{i}Id':'TurretsJson' for i in range(21)}}
# PLA's own copies of RU/US rows (for example its older B-21 JATM bay) lose every user once main dev's
# version replaces them. Remove PLA-only rows that nothing references any more.
GC=['AbilitiesJson','AmmunitionsJson','ArmorsJson','MobilityJson','FlyPresetsJson','TurretsJson','WeaponsJson','TurretWeaponsJson','SensorsJson']
cand={(tab,k) for tab in GC for k in M[tab] if k in O[tab] and k not in B[tab] and k not in T[tab]}
live=lambda tab,k:(tab,k) not in cand
while True:
    used=set()
    for tab,rows in M.items():
        for k,r in rows.items():
            if not live(tab,k):continue
            for f,v in r.items():
                if f in REF and isinstance(v,int) and v>0:used.add((REF[f],v))
    for k,r in M['TurretWeaponsJson'].items():
        if ('TurretWeaponsJson',k) in cand and ('TurretsJson',r['TurretId']) in used and live('TurretsJson',r['TurretId']):used.add(('TurretWeaponsJson',k))
    revived=cand&used
    if not revived:break
    cand-=revived
receipt['removed_unused_pla_rows']=collections.Counter(t for t,_ in cand)
for tab,k in cand:del M[tab][k]
bad=collections.Counter();bad_china=[]
for tab,rows in M.items():
    for k,r in rows.items():
        for f,v in r.items():
            if f in REF and isinstance(v,int) and v>0 and v not in M[REF[f]]:
                bad[(tab,f)]+=1
                if f!='CountryId' and (r.get('UnitId') in china or r.get('CountryId')==CHINA):bad_china.append([tab,k,f,v])
# compare with what main dev and PLA already carry, so only merge-made breaks fail the run
def dangling(t):
    c=collections.Counter()
    for tab,rows in t.items():
        for r in rows.values():
            for f,v in r.items():
                if f in REF and isinstance(v,int) and v>0 and v not in t[REF[f]]:c[(tab,f)]+=1
    return c
base_bad=dangling(T)+dangling(O)
new_bad={'/'.join(k):v for k,v in bad.items() if v>base_bad.get(k,0)}
receipt['dangling_refs_new']=new_bad;receipt['dangling_china']=bad_china[:50]
assert not new_bad and not bad_china,(new_bad,bad_china[:10])
# 6. write patches against vanilla
for tab,fn in FIELD_TO_FILE.items():
    patch={}
    for k in sorted(set(VAN[tab])|set(M[tab])):
        v,m=VAN[tab].get(k),M[tab].get(k)
        if m is None:patch[str(k)]=None
        elif v is None:patch[str(k)]={f:x for f,x in m.items() if f!='Id'}
        elif m!=v:
            d={f:x for f,x in m.items() if f!='Id' and v.get(f)!=x}
            assert set(m)==set(v),(tab,k)
            patch[str(k)]=d
    f=SRC/'UserData/FreedomArrow/constants'/fn;f.write_bytes((json.dumps(patch,indent=2,ensure_ascii=False)+'\n').encode())
    receipt['counts'][tab]={'rows':len(M[tab]),'patch_rows':len(patch),'china_rows':sum(1 for r in M[tab].values() if r.get('UnitId') in china or (tab=='Units' and r['Id'] in china))}
(SRC/'UserData/FreedomArrow/option-id-migration.json').write_text(json.dumps(migration,indent=2)+'\n')
# 7. the moved China units in the files that bind by unit ID
for n in ['UserData/FAModels/infantry-bodies.json','UserData/FAModels/infantry-weapons.json']:
    d=json.loads(zO.read(n))
    for e in d:e['unitId']=RENUMBER.get(e['unitId'],e['unitId'])
    (SRC/n).write_bytes((json.dumps(d,indent=2)+'\n').encode())
n='UserData/FreedomArrow/pla-spec-assignments.json';d=json.loads(zO.read(n))
for key in ('assignments','shared_transports'):
    if d.get(key):d[key]={str(RENUMBER.get(int(k),int(k))):v for k,v in d[key].items()}
(SRC/n).write_bytes((json.dumps(d,indent=2,ensure_ascii=zO.read(n).isascii())+'\n').encode())
receipt['china_units']=len(china);receipt['option_migration_entries']=len(migration)
a.receipt.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,default=str)+'\n')
print(json.dumps({k:receipt[k] for k in ('renumbered_china_units','delete_vs_change','option_ids_reassigned','dangling_refs_new','china_units','option_migration_entries')},ensure_ascii=False,indent=1))
print('conflicts',len(receipt['conflicts_dev_wins']));[print(' ',c) for c in receipt['conflicts_dev_wins'][:20]]
