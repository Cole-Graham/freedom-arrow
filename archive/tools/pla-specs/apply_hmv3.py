"""Build34: Shaanxi HMV3 supply truck from the native HEMTT, shared by three specs.

Sam 12 Nov 01:08 PST: "take the HEMTT and call it the Shaanxi. This is for
Rocket force and Armored and Motorized." The HEMTT is a native supply truck
(no transport links in vanilla), so the card stays a supply truck. It is the
second shared exception to the one-spec rule, after Mi-8 Cargo.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE='329c54858cfac03ef5712f6e42334180a696e5872b293e682bb163db99f7f41c'
UID,DONOR,SPECS=1235,242,[18,19,21]
SHARED={'1227':list(range(17,22)),str(UID):SPECS}
enc=lambda d:(json.dumps(d,indent=2)+'\n').encode()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
with zipfile.ZipFile(a.base) as z:
 t={};patches={};native={}
 for tab,fn in FIELD_TO_FILE.items():
  t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
  for k,v in patches[tab].items():
   if v is None:t[tab].pop(int(k),None)
   else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
 before=copy.deepcopy(t);g=Graph(t,patches,native)
 assert UID not in t['Units'] and t['Units'][DONOR]['HUDName']=='HEMTT'
 # Unarmed clone, as for Mi-8 Cargo and Lynx ATV: default armor, mobility and sensor only.
 d=copy.deepcopy(t['Units'][DONOR]);d.pop('Id',None)
 d.update(Name='PLA Shaanxi HMV3',HUDName='Shaanxi HMV3',CountryId=4,DisplayInArmory=True,ContentMembership=-1,IsUnitModification=False,
          Description='Shaanxi HMV3 heavy supply truck. Native HEMTT model and statistics; shared by Armored, Rocket Force and Motorized.')
 g.put('Units',UID,d)
 for tab,target,field in [('UnitArmorsJson','ArmorsJson','ArmorId'),('UnitPropulsionsJson','MobilityJson','MobilityId'),('SensorUnitsJson','SensorsJson','SensorId')]:
  ls=g.rows(tab,DONOR);r=next((r for r in ls if t[target][r[field]].get('IsDefault')),ls[0])
  g.add(tab,r,{'UnitId':UID,field:g.add(target,t[target][r[field]],{'IsDefault':True})})
 template=next(r for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId']==DONOR)
 for sid in SPECS:g.add('SpecializationAvailabilitiesJson',template,{'UnitId':UID,'SpecializationId':sid})
 specs=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'))
 specs['assignments'][str(UID)]=SPECS;specs['shared_transports']=SHARED
 specs['one_spec_rule']={'exceptions':SHARED,'all_other_active_units':1,'basis':'Sam 12 Nov: deck building requires one spec; Mi-8 Cargo and Shaanxi HMV3 explicitly shared'}
 specs['pool_counts']={str(s):sum(r['SpecializationId']==s for r in t['SpecializationAvailabilitiesJson'].values()) for s in range(17,23)};specs['build']=34
 def save(n,data):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(data))
 for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
 save('UserData/FreedomArrow/pla-spec-assignments.json',specs)
 arm=json.loads(z.read('UserData/FreedomArrow/pla-vehicle-armament.json'));arm['build']=34
 arm['entries'].append({'unit':UID,'name':'Shaanxi HMV3','type':d['Type'],'native_parent':DONOR,'weapons':[],'slots':d['InfantrySlots'],'custom_model':None,'armor_basis':'Native HEMTT armor and mobility; not a measured Chinese armor claim.','native_verified':False,'specs':SPECS,'active':True})
 arm['count']=len(arm['entries']);save('UserData/FreedomArrow/pla-vehicle-armament.json',arm)
 for name in ['pla-build.json','pla-specializations.json','pla-infantry-designer.json','pla-model-catalogue.json']:
  data=json.loads(z.read('UserData/FreedomArrow/'+name));data['build']=34
  if 'label' in data:data['label']='PLA TEST Build 34'
  save('UserData/FreedomArrow/'+name,data)
 roster=json.loads(z.read('UserData/FreedomArrow/pla-roster-revision.json'));roster['build']=34;roster['new_units']['Shaanxi HMV3']=UID
 save('UserData/FreedomArrow/pla-roster-revision.json',roster)
 checks=0;visible=[]
 def ok(value,label):
  global checks
  assert value,label;checks+=1
 for u in t['Units'].values():
  if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification'):continue
  uid=u['Id'];actual=sorted(r['SpecializationId'] for r in g.rows('SpecializationAvailabilitiesJson',uid))
  ok(actual==sorted(specs['assignments'].get(str(uid),[])),('metadata mismatch',uid))
  ok(actual==SHARED[str(uid)] if str(uid) in SHARED else len(actual)==1,('wrong spec count',uid,actual))
  visible.append({'unit':uid,'name':u['HUDName'],'specs':actual})
 ok(not g.rows('TurretUnitsJson',UID) and not g.rows('WeaponAmmunitionsJson',UID),'HMV3 unarmed')
 ok(t['Units'][UID]['ModelFileName']=='US_HEMTT' and t['Units'][UID]['CategoryType']==t['Units'][DONOR]['CategoryType'],'HEMTT model and supply category')
 for tab in FIELD_TO_FILE:
  for key,row in before[tab].items():ok(t[tab].get(key)==row,('existing row drift',tab,key))
 single=json.loads(z.read('UserData/FreedomArrow/pla-single-spec.json'))
 single.update(build=34,base_build=33,base_sha256=BASE,visible_units=visible,single_spec_units=len(visible)-len(SHARED),shared_exception=[int(k) for k in SHARED],checks=checks)
 save('UserData/FreedomArrow/pla-single-spec.json',single)
 receipt={'build':34,'base_build':33,'base_sha256':BASE,'unit':UID,'name':'Shaanxi HMV3','donor':DONOR,'specs':SPECS,'cost':d['Cost'],'availability_xp0':template['MaxAvailabilityXp0'],'visible_units':len(visible),'checks':checks,'native_verified':False}
 (ROOT/'tools/pla-specs/build34-hmv3-checks.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))
