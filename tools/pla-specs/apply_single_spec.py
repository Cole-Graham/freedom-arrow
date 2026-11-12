"""Build33: exactly one playable PLA specialization; Mi-8 Cargo is shared.

Primary equipment assignments come from the user's live sheet snapshot. The
explicit moves in the current Discord batch take priority over historical
shared-primary labels. Infantry and appearance fixtures retain their sole spec.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE='8f537832f6d8a0e52c20ac83d6faf486d4a71af1148c7e3f7fba27dda1e09024'
LABELS={'Airforce / Airborne':17,'Ground Force / Armored':18,'Rocket Force / Conscripts':19,'Marines / SF':20,'Motorized':21}
EXPLICIT={906:21,1079:21,1232:21,917:21,955:21,971:21,1049:20,909:19,961:20,925:20,943:20,974:20,918:20,1063:20,1058:19,1230:19,1054:20}
enc=lambda d:(json.dumps(d,indent=2)+'\n').encode()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--sheet',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
with zipfile.ZipFile(a.base) as z:
 t={};patches={};native={}
 for tab,fn in FIELD_TO_FILE.items():
  t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
  for k,v in patches[tab].items():
   if v is None:t[tab].pop(int(k),None)
   else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
 before=copy.deepcopy(t);g=Graph(t,patches,native)
 identity_repairs=[]
 for key,u in t['Units'].items():
  if u['Id']!=key:
   assert key in range(1226,1235),(key,u['Id'])
   identity_repairs.append({'unit':key,'incorrect_donor_id':u['Id']})
   u['Id']=key;patches['Units'][str(key)].pop('Id',None)
 for uid in [1058,1230]:g.put('Units',uid,{'InfantrySlots':12})
 specs=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'))
 sheet=json.loads(a.sheet.read_text());equipment={int(r[0]):LABELS[r[2]] for r in sheet[1:] if len(r)>2 and str(r[0]).isdigit() and r[2] in LABELS}
 changed=[]
 for k,old in specs['assignments'].items():
  uid=int(k)
  if not old:continue
  wanted=list(range(17,22)) if uid==1227 else [EXPLICIT.get(uid,equipment.get(uid,old[0]))]
  assert uid==1227 or len(wanted)==1
  pools=g.rows('SpecializationAvailabilitiesJson',uid)
  if old!=wanted:changed.append({'unit':uid,'name':t['Units'][uid]['HUDName'],'before':old,'after':wanted,'basis':'explicit current batch' if uid in EXPLICIT else 'sheet primary spec' if uid in equipment else 'existing sole spec'})
  kept=set()
  for pool in pools:
   sid=pool['SpecializationId']
   if sid in wanted and sid not in kept:kept.add(sid);continue
   for tr in list(t['TransportAvailabilitiesJson'].values()):
    if tr['SpecializationAvailabilityId']==pool['Id']:g.remove('TransportAvailabilitiesJson',tr['Id'])
   g.remove('SpecializationAvailabilitiesJson',pool['Id'])
  for sid in set(wanted)-kept:g.add('SpecializationAvailabilitiesJson',pools[0],{'SpecializationId':sid,'UnitId':uid})
  specs['assignments'][k]=wanted
 # Carrier links must respect the carrier's own sole spec too, otherwise the
 # deck builder can still expose a vehicle from the wrong specialization.
 removed_carriers=0
 for row in list(t['TransportAvailabilitiesJson'].values()):
  pool=t['SpecializationAvailabilitiesJson'][row['SpecializationAvailabilityId']]
  if pool['SpecializationId']>=17:
   allowed=specs['assignments'].get(str(row['UnitId']),[])
   if pool['SpecializationId'] not in allowed:g.remove('TransportAvailabilitiesJson',row['Id']);removed_carriers+=1
 for pool in list(t['SpecializationAvailabilitiesJson'].values()):
  uid=pool['UnitId']
  if pool['SpecializationId']==19 and t['Units'][uid]['Type']==2 and not t['Units'][uid].get('IsUnitModification') and t['Units'][uid].get('BaseSquadSize',0)<=12:
   for carrier in [1058,1230]:
    if not any(r['UnitId']==carrier and r['SpecializationAvailabilityId']==pool['Id'] for r in t['TransportAvailabilitiesJson'].values()):g.add('TransportAvailabilitiesJson',next(iter(t['TransportAvailabilitiesJson'].values())),{'UnitId':carrier,'SpecializationAvailabilityId':pool['Id']})
 for carrier in [1058,1230]:
  if carrier not in specs['carriers']['19']:specs['carriers']['19'].append(carrier)
 specs['carriers']={sid:[uid for uid in ids if int(sid) in specs['assignments'].get(str(uid),[])] for sid,ids in specs['carriers'].items()}
 specs['shared_transports']={'1227':list(range(17,22))};specs['pool_counts']={str(s):sum(r['SpecializationId']==s for r in t['SpecializationAvailabilitiesJson'].values()) for s in range(17,23)}
 specs['build']=33;specs['one_spec_rule']={'exception':1227,'all_other_active_units':1,'basis':'Sam 12 Nov: deck building requires one spec'}
 def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(d))
 for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
 save('UserData/FreedomArrow/pla-spec-assignments.json',specs)
 for name in ['pla-vehicle-armament.json','pla-model-catalogue.json']:
  d=json.loads(z.read('UserData/FreedomArrow/'+name));d['build']=33
  for e in d['entries']:
   e['specs']=specs['assignments'].get(str(e['unit']),[])
   if 'slots' in e:e['slots']=t['Units'][e['unit']]['InfantrySlots']
  save('UserData/FreedomArrow/'+name,d)
 for name in ['pla-build.json','pla-specializations.json','pla-infantry-designer.json','pla-roster-revision.json']:
  d=json.loads(z.read('UserData/FreedomArrow/'+name));d['build']=33
  if 'label' in d:d['label']='PLA TEST Build 33'
  save('UserData/FreedomArrow/'+name,d)
 checks=0;visible=[]
 def ok(value,label):
  global checks
  assert value,label;checks+=1
 for u in t['Units'].values():
  if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification'):continue
  uid=u['Id'];pools=g.rows('SpecializationAvailabilitiesJson',uid);actual=[r['SpecializationId'] for r in pools]
  ok(sorted(actual)==sorted(specs['assignments'].get(str(uid),[])),('metadata mismatch',uid))
  ok(sorted(actual)==list(range(17,22)) if uid==1227 else len(actual)==1,('wrong spec count',uid,actual))
  visible.append({'unit':uid,'name':u['HUDName'],'specs':actual})
 for r in t['TransportAvailabilitiesJson'].values():
  pool=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]
  if pool['SpecializationId']>=17:ok(pool['SpecializationId'] in specs['assignments'].get(str(r['UnitId']),[]),('cross-spec carrier',r))
 for tab in FIELD_TO_FILE:
  if tab=='Units':
   for key,u in t[tab].items():
    old=copy.deepcopy(before[tab][key]);old['Id']=key
    if key in [1058,1230]:old['InfantrySlots']=12
    ok(u==old,('non-identity unit drift',key))
  elif tab not in ['SpecializationAvailabilitiesJson','TransportAvailabilitiesJson']:ok(t[tab]==before[tab],('unrelated gameplay drift',tab))
 receipt={'build':33,'base_build':32,'base_sha256':BASE,'changes':changed,'removed_cross_spec_carrier_links':removed_carriers,'visible_units':visible,'single_spec_units':len(visible)-1,'shared_exception':1227,'identity_repairs':identity_repairs,'checks':checks,'native_verified':False}
 save('UserData/FreedomArrow/pla-single-spec.json',receipt);(ROOT/'tools/pla-specs/build33-single-spec-checks.json').write_bytes(enc(receipt));print(json.dumps({k:v for k,v in receipt.items() if k not in ['changes','visible_units']},indent=2))
