"""Build36 over exact Build35 (Osama 12 Nov 01:36 PST).

1. "Just copy nuclear Khinzal for the DF-31": the DF-31 round (ammo 2010399, the ID
   the nuclear warning watches) takes the warhead, effect and supply fields of native
   ammo 340 (Kh-47M2 Kinzhal Nuke). Launch and flight fields stay ballistic, so the
   missile still launches from the ground and stays in the ballistic-warning poll.
2. "If we don't have models for the drone helos, don't add it": AR-2000, CR-500 Recon,
   CR-500B and Z-6B UAV used the vanilla Termit stand-in and are removed.
3. ZBD-251 keeps its Kurganets model (Osama: model is correct); description updated.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-35.json').read_text())['sha256']
DF31,DF31_AMMO,KINZHAL_NUKE=1032,2010399,340
DRONES=[1084,1085,1086,1105]
WARHEAD=['Damage','CriticMultiplier','DamageOverTimeDuration','HealthAOERadius','OverpressureRadius','StressAOERadius','StressDamage',
         'PenetrationAtGroundRange','PenetrationAtMinRange','IsTopArmorArmorAttack','AudioPreset','FXPreset','VfxCountPerShotMax','SupplyCost','ResupplyTime']
enc=lambda d:(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
with zipfile.ZipFile(a.base) as z:
 read=lambda n:json.loads(z.read('UserData/FreedomArrow/'+n))
 assert json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'))['build']==35
 t={};patches={};native={}
 for tab,fn in FIELD_TO_FILE.items():
  t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
  for k,v in patches[tab].items():
   if v is None:t[tab].pop(int(k),None)
   else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
 before=copy.deepcopy(t);g=Graph(t,patches,native)
 A=t['AmmunitionsJson'];assert A[KINZHAL_NUKE]['Name']=='Missile Cruise Kh47M2 Kinzhal Nuke'
 assert [r['AmmunitionId'] for r in g.rows('WeaponAmmunitionsJson',DF31)]==[DF31_AMMO]
 g.put('AmmunitionsJson',DF31_AMMO,{**{k:copy.deepcopy(A[KINZHAL_NUKE][k]) for k in WARHEAD},'HUDName':'DF-31A nuclear warhead'})
 g.put('Units',DF31,{'Description':'Nuclear missile; one availability. Warhead copies native Kh-47M2 Kinzhal Nuke (666 damage, 350 m health radius); ground-launched ballistic flight retained.'})
 specs=read('pla-spec-assignments.json');arm=read('pla-vehicle-armament.json')
 for uid in DRONES:
  assert t['Units'][uid]['ModelFileName']=='DLC3_MDP01_Termit'
  for pool in g.rows('SpecializationAvailabilitiesJson',uid):
   for tr in list(t['TransportAvailabilitiesJson'].values()):
    if tr['SpecializationAvailabilityId']==pool['Id']:g.remove('TransportAvailabilitiesJson',tr['Id'])
   g.remove('SpecializationAvailabilitiesJson',pool['Id'])
  for tr in list(t['TransportAvailabilitiesJson'].values()):
   if tr['UnitId']==uid:g.remove('TransportAvailabilitiesJson',tr['Id'])
  g.put('Units',uid,{'DisplayInArmory':False});specs['assignments'][str(uid)]=[]
 g.put('Units',1056,{'Description':'Airborne ZBD-251: laser designator, two HJ-10 and four ABZ-13 anti-personnel missiles. Kurganets model approved by Osama. Missile performance is a provisional game analogy.'})
 specs['carriers']={sid:[u for u in ids if u not in DRONES] for sid,ids in specs['carriers'].items()}
 specs['pool_counts']={str(s):sum(r['SpecializationId']==s for r in t['SpecializationAvailabilitiesJson'].values()) for s in range(17,23)};specs['build']=36
 for e in arm['entries']:
  if e['unit'] in DRONES:e.update(specs=[],active=False)
  if e['unit']==DF31:
   for w in e['weapons']:
    for s in w['stocks']:
     if s['ammo']==DF31_AMMO:s['name']='DF-31A nuclear warhead'
 arm['build']=36
 def save(n,data):
  # Keep each file's existing escaping so the diff shows only real changes.
  f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True)
  f.write_bytes((json.dumps(data,ensure_ascii=z.read(n).isascii(),indent=2)+'\n').encode())
 for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
 save('UserData/FreedomArrow/pla-spec-assignments.json',specs);save('UserData/FreedomArrow/pla-vehicle-armament.json',arm)
 for name in ['pla-build.json','pla-specializations.json','pla-infantry-designer.json','pla-model-catalogue.json']:
  data=read(name);data['build']=36
  if 'label' in data:data['label']='PLA TEST Build 36'
  if name=='pla-model-catalogue.json':
   for e in data['entries']:
    if e.get('unit') in DRONES:e['specs']=[]
  save('UserData/FreedomArrow/'+name,data)
 roster=read('pla-roster-revision.json');roster['build']=36
 roster['nuclear_effect']='DF-31 warhead copies native ammo 340 Kh-47M2 Kinzhal Nuke; ballistic flight retained'
 roster['removed_units']=sorted(set(roster['removed_units'])|set(DRONES))
 roster['drone_model_audit_result']='All four used DLC3_MDP01_Termit with no custom model; removed (Osama 12 Nov)'
 save('UserData/FreedomArrow/pla-roster-revision.json',roster)
 checks=0;visible=[]
 def ok(value,label):
  global checks
  assert value,label;checks+=1
 shared=specs['shared_transports']
 for u in t['Units'].values():
  if u.get('CountryId')!=4 or not u.get('DisplayInArmory') or u.get('IsUnitModification'):continue
  uid=u['Id'];actual=sorted(r['SpecializationId'] for r in g.rows('SpecializationAvailabilitiesJson',uid))
  ok(actual==sorted(specs['assignments'].get(str(uid),[])),('metadata mismatch',uid))
  ok(actual==sorted(shared[str(uid)]) if str(uid) in shared else len(actual)==1,('wrong spec count',uid,actual))
  visible.append({'unit':uid,'name':u['HUDName'],'specs':actual})
 for uid in DRONES:
  ok(not t['Units'][uid]['DisplayInArmory'] and not g.rows('SpecializationAvailabilitiesJson',uid),('drone visible',uid))
  ok(not any(r['UnitId']==uid for r in t['TransportAvailabilitiesJson'].values()),('drone carrier',uid))
 n=A[DF31_AMMO]
 for k in WARHEAD:ok(n[k]==A[KINZHAL_NUKE][k],('warhead field',k))
 for k in ['TrajectoryType','MaxSpeed','LoftHeight','LoftAngle','MinimalRange','ModelFileName','MuzzleVelocity']:ok(n[k]==before['AmmunitionsJson'][DF31_AMMO][k],('flight field changed',k))
 ok(A[KINZHAL_NUKE]==before['AmmunitionsJson'][KINZHAL_NUKE],'native Kinzhal untouched')
 changed={('AmmunitionsJson',DF31_AMMO),('Units',DF31),('Units',1056)}|{('Units',u) for u in DRONES}
 for tab in FIELD_TO_FILE:
  for key,row in before[tab].items():
   if (tab,key) in changed:continue
   if tab in ['SpecializationAvailabilitiesJson','TransportAvailabilitiesJson'] and key not in t[tab]:
    ok(row['UnitId'] in DRONES or t[tab].get(key) is None and before['SpecializationAvailabilitiesJson'].get(row.get('SpecializationAvailabilityId'),{}).get('UnitId') in DRONES,('unexpected removal',tab,key));continue
   ok(t[tab].get(key)==row,('existing row drift',tab,key))
 single=read('pla-single-spec.json')
 single.update(build=36,base_build=35,base_sha256=BASE,visible_units=visible,single_spec_units=len(visible)-len(shared),checks=checks)
 save('UserData/FreedomArrow/pla-single-spec.json',single)
 receipt={'build':36,'base_build':35,'base_sha256':BASE,'df31_ammo':{k:n[k] for k in WARHEAD+['TrajectoryType','HUDName']},'removed_drones':DRONES,'visible_units':len(visible),'checks':checks,'native_verified':False}
 (ROOT/'tools/pla-specs/build36-checks.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))
