"""Freedom Arrow 0.8.0-dev.16 over exact 0.8.0-dev.15 (Osama 12 Nov 15:39 PST): "Shaanxi troop truck is included in this
removal" / "remove ZSD-63".
- Shaanxi Troop Truck (1231) is no longer offered as a squad transport (its TransportAvailabilities rows are deleted); it
  stays as its own card.
- ZSD-63 (1062) leaves the roster: its Rocket card, its 7 squad transport links and its assignment. ZSD-63C (960) stays.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.16'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.15.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U,SA,TA=t['Units'],t['SpecializationAvailabilitiesJson'],t['TransportAvailabilitiesJson']
TRUCK,ZSD63=1231,1062;assert U[TRUCK]['HUDName']=='Shaanxi Troop Truck' and U[ZSD63]['HUDName']=='ZSD-63'
rows=[r for r in list(TA.values()) if r['UnitId'] in (TRUCK,ZSD63)]
for r in rows:g.remove('TransportAvailabilitiesJson',r['Id'])
sas=[r for r in list(SA.values()) if r['UnitId']==ZSD63];assert not any(r['SpecializationAvailabilityId'] in {s['Id'] for s in sas} for r in TA.values())
for r in sas:g.remove('SpecializationAvailabilitiesJson',r['Id'])
g.put('Units',ZSD63,{'DisplayInArmory':False})
n='UserData/FreedomArrow/pla-spec-assignments.json';spec=json.loads(z.read(n));spec['assignments'][str(ZSD63)]=[]
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(not any(r['UnitId'] in (TRUCK,ZSD63) for r in TA.values()),'truck/ZSD-63 still a transport')
ok(not any(r['UnitId']==ZSD63 for r in SA.values()) and not U[ZSD63]['DisplayInArmory'],'ZSD-63 removed')
stranded=[U[s['UnitId']]['HUDName'] for s in SA.values() if s['SpecializationId']>=17 and any(r['SpecializationAvailabilityId']==s['Id'] for r in before['TransportAvailabilitiesJson'].values()) and not any(r['SpecializationAvailabilityId']==s['Id'] for r in TA.values())]
ok(not stranded,('squads left without transport',stranded))
for tab in t:
    for key,row in before[tab].items():
        if not((tab=='TransportAvailabilitiesJson' and key in {r['Id'] for r in rows}) or (tab=='SpecializationAvailabilitiesJson' and key in {r['Id'] for r in sas}) or (tab,key)==('Units',ZSD63)):ok(t[tab].get(key)==row,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.15','base_sha256':BASE,'request':'Osama 12 Nov 15:39 PST: Shaanxi Troop Truck not a transport; remove ZSD-63','removed_transport_links':{'Shaanxi Troop Truck':sum(r['UnitId']==TRUCK for r in rows),'ZSD-63':sum(r['UnitId']==ZSD63 for r in rows)},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(n,spec);save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1))
