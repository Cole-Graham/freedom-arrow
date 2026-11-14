"""Freedom Arrow 0.8.0-dev.93 over exact 0.8.0-dev.92 (Osama 13 Nov 22:58 PST, thread 1567745029781454889: "audit and make sure we
won't have issues where armory shows units having certain things like smoke, aps and weapons but it disappears in MP").
tools/pla-specs/audit_mp_equipment.py runs the 0.7 SP/MP guards on the whole package and lists faults vanilla does not have.
On dev.92 it found these; all are fixed here, and the packager now refuses a build with any new fault.
- Only the first default ability row of a unit loads (LoadAbility RVA 0x285E50):
  - ZBD-251 (1056): smoke loaded, laser designator dropped. The laser fields go into its own first ability (smoke + resupply +
    laser); both protection options now grant that one ability (Ability2 laser cleared) and the extra link is removed.
  - ZBD-04A, ZBD-20 and their Recon cards (902, 945, 1255, 1256): two extra identical smoke+resupply defaults removed (nothing lost).
  - HQ-7B (925) and hidden HQ-7 (961): second radar row (static) removed; the first, moving radar is what loaded and stays.
- F-15EX (289): its ECM options grant ability 2001404 (ECM 40%, dev.8) but the unit was linked to 2001402; the link now points
  at 2001404 (vanilla pattern: an option ability needs the unit's UnitAbilities link).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.93'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.92.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,AB,UA,O,M=(t[k] for k in ('Units','AbilitiesJson','UnitAbilitiesJson','OptionsJson','ModificationsJson'))
mods={m['Id']:m['UnitId'] for m in M.values()}
def defaults(uid):return sorted((r for r in UA.values() if r['UnitId']==uid and AB[r['AbilityId']].get('IsDefault')),key=lambda r:r['Id'])
def same(a,b):return all(AB[a].get(k)==AB[b].get(k) for k in AB[a] if k not in ('Id','Name'))
rec={}
# ZBD-251
assert U[1056]['HUDName']=='ZBD-251';rs=defaults(1056);assert [r['AbilityId'] for r in rs]==[2010731,2014663]
LASER=('IsLaserDesignator','LaserMaxRange','LaserUsableInMove');g.put('AbilitiesJson',2010731,{k:AB[2014663][k] for k in LASER})
for o in [o for o in O.values() if mods.get(o['ModificationId'])==1056 and o['Ability2Id']==2014663]:assert o['Ability1Id']==2010731;g.put('OptionsJson',o['Id'],{'Ability2Id':0})
g.remove('UnitAbilitiesJson',rs[1]['Id']);rec['zbd251']='laser merged into 2010731'
# duplicate identical defaults
for uid in (902,945,1255,1256):
    rs=defaults(uid);assert len(rs)==3 and all(same(rs[0]['AbilityId'],r['AbilityId']) for r in rs[1:])
    assert not any(r['AbilityId'] in (o['Ability1Id'],o['Ability2Id'],o['Ability3Id']) for r in rs[1:] for o in O.values())
    for r in rs[1:]:g.remove('UnitAbilitiesJson',r['Id'])
    rec[U[uid]['HUDName']]=f'removed {len(rs)-1} duplicate defaults'
# HQ-7B / HQ-7: keep the first (moving) radar
for uid in (925,961):
    rs=defaults(uid);assert len(rs)==2 and AB[rs[0]['AbilityId']]['IsRadar'] and not AB[rs[0]['AbilityId']]['IsRadarStatic'] and AB[rs[1]['AbilityId']]['IsRadarStatic']
    g.remove('UnitAbilitiesJson',rs[1]['Id']);rec[U[uid]['HUDName']]='second (static) radar link removed'
# F-15EX
assert U[289]['HUDName']=='F-15EX Eagle II';l=[r for r in UA.values() if r['UnitId']==289 and r['AbilityId']==2001402];assert len(l)==1
assert {o['Ability1Id'] for o in O.values() if mods.get(o['ModificationId'])==289 and o['Ability1Id']}=={2001404}
g.put('UnitAbilitiesJson',l[0]['Id'],{'AbilityId':2001404});rec['F-15EX']='ECM link 2001402 -> 2001404'
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for uid in (1056,902,945,1255,1256,925,961):ok(len(defaults(uid))==1,('one default ability',uid))
ok(AB[2010731]['IsSmoke'] and AB[2010731]['IsLaserDesignator'] and AB[2010731]['IsResupplyAbility'],'ZBD-251 smoke+laser+resupply')
ua={(r['UnitId'],r['AbilityId']) for r in UA.values()}
ok(all((mods.get(o['ModificationId']),o[k]) in ua or not o[k] or AB[o[k]]['Name']=='Empty ability' for o in O.values() if mods.get(o['ModificationId']) in (1056,289) for k in ('Ability1Id','Ability2Id','Ability3Id')),'option abilities linked')
receipt={'version':V,'base':'0.8.0-dev.92','base_sha256':BASE,'request':'Osama 13 Nov 22:58 PST: audit armory vs MP equipment (smoke, APS, weapons)','fixes':rec,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec))
