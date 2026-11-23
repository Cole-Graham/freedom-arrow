"""Freedom Arrow 0.8.0-dev.2 over exact 0.8.0-dev.1 (Osama 12 Nov 13:38 PST: "CSK-131 doesn't have the correct seats?
Shaanxi sx2190 removed everywehere").

- CSK-131 Mengshi (900) and CSK-131 Transport (1229) use the vanilla Tigr model; Tigr has 7 seats, ours had 4.
  Both get 7 seats and carry every squad in their specializations that has 7 or fewer men.
- Shaanxi SX2190 (912) removed: hidden, no specialization or carrier rows. Shaanxi Troop Truck (1231) stays.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.1.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];SM=t['SquadMembersJson']
CSK=[900,1229];SX=912;TIGR=194
assert [U[u]['HUDName'] for u in CSK]==['CSK-131 Mengshi','CSK-131 Transport'] and U[SX]['HUDName']=='Shaanxi SX2190' and U[TIGR]['HUDName']=='Tigr'
assert all(U[u]['ModelFileName']==U[TIGR]['ModelFileName'] for u in CSK)
receipt={'version':'0.8.0-dev.2','base':'0.8.0-dev.1','base_sha256':BASE,'request':'Osama 12 Nov 13:38 PST','csk131':{},'sx2190':{}}
men=lambda uid:sum(1 for m in SM.values() if m['UnitId']==uid)
tmpl=next(iter(TA.values()))
for uid in CSK:
    old=U[uid]['InfantrySlots'];g.put('Units',uid,{'InfantrySlots':U[TIGR]['InfantrySlots']});added=[]
    specs={r['SpecializationId'] for r in SA.values() if r['UnitId']==uid}
    for pool in [r for r in list(SA.values()) if r['SpecializationId'] in specs and U[r['UnitId']]['Type'] in (1,2) and U[r['UnitId']]['DisplayInArmory']]:
        n=men(pool['UnitId'])
        if 0<n<=U[uid]['InfantrySlots'] and not any(x['SpecializationAvailabilityId']==pool['Id'] and x['UnitId']==uid for x in TA.values()):
            g.add('TransportAvailabilitiesJson',tmpl,{'SpecializationAvailabilityId':pool['Id'],'UnitId':uid});added.append(f"{U[pool['UnitId']]['HUDName']} ({n})")
    receipt['csk131'][U[uid]['HUDName']]={'seats':[old,U[uid]['InfantrySlots']],'now_carries':added}
g.put('Units',SX,{'DisplayInArmory':False});gone=[]
for r in [r for r in SA.values() if r['UnitId']==SX]:
    for x in [x for x in TA.values() if x['SpecializationAvailabilityId']==r['Id']]:g.remove('TransportAvailabilitiesJson',x['Id'])
    gone.append(r['SpecializationId']);g.remove('SpecializationAvailabilitiesJson',r['Id'])
carried=[U[SA[x['SpecializationAvailabilityId']]['UnitId']]['HUDName'] for x in TA.values() if x['UnitId']==SX]
for x in [x for x in TA.values() if x['UnitId']==SX]:g.remove('TransportAvailabilitiesJson',x['Id'])
receipt['sx2190']={'specs_removed':gone,'was_carrier_for':carried}
n='UserData/FreedomArrow/pla-spec-assignments.json';spec=json.loads(z.read(n));spec['assignments'][str(SX)]=[];(spec.get('shared_transports') or {}).pop(str(SX),None)
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
had=lambda tabs,rid:any(x['SpecializationAvailabilityId']==rid for x in tabs['TransportAvailabilitiesJson'].values())
for r in SA.values():
    if had(before,r['Id']):ok(had(t,r['Id']),('squad lost every carrier',U[r['UnitId']]['HUDName']))
ok(not any(r['UnitId']==SX for r in SA.values()) and not any(x['UnitId']==SX for x in TA.values()),'SX2190 gone')
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-China unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(n,spec);save('UserData/FreedomArrow/pla-0.8.0-dev.2.json',receipt)
(ROOT/'tools/pla-specs/0.8.0-dev.2-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))
