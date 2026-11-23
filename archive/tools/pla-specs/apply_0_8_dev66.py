"""Freedom Arrow 0.8.0-dev.66 over exact 0.8.0-dev.65 (Osama 13 Nov 18:1x PST, thread 1567745029781454889):
- "All the tank speeds got fucked ... fix the unit speeds and use a hook or edit the engine to make roads faster without
  touching unit speed." The 152 tracked mobility rows that 0.8.0-dev.61 raised (MaxSpeedRoad = 1.6x off-road) go back to
  their dev.60 values (tools/pla-specs/0.8.0-dev.61-checks.json "before"). Only rows still at dev.61's value are restored.
  The road bonus will come back as a runtime rule, not as unit data.
- ZTZ-100 (968) gun 2010191: reload 5-6 s -> 4 s.
- ZBD-251 (1056): new "Protection system" slot like the vanilla M2A3 Bradley's: None (+0, default) or APS (+60, the vanilla
  light APS ability 88, 2 charges). Both options keep its smoke and laser designator abilities.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.66'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.65.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,MOB,W,M,O,UAB,AB=(t[k] for k in ('Units','MobilityJson','WeaponsJson','ModificationsJson','OptionsJson','UnitAbilitiesJson','AbilitiesJson'))
# ---- revert dev.61
d61=json.loads((ROOT/'tools/pla-specs/0.8.0-dev.61-checks.json').read_text())['changes'];assert len(d61)==152
restored,skipped=[],[]
for mid,c in d61.items():
    m=MOB[int(mid)]
    if m['MaxSpeedRoad']==c['after']:g.put('MobilityJson',int(mid),{'MaxSpeedRoad':c['before']});restored.append(mid)
    else:skipped.append((mid,m['MaxSpeedRoad'],c))
assert not skipped,skipped
# ---- ZTZ-100 reload
ZG=2010191;assert U[968]['HUDName']=='ZTZ-100' and W[ZG]['HUDName']=='Prototype 125 mm gun'
g.put('WeaponsJson',ZG,{'MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':4.0})
# ---- ZBD-251 APS option
ZBD=1056;assert U[ZBD]['HUDName']=='ZBD-251' and not [m for m in M.values() if m['UnitId']==ZBD]
own=[r['AbilityId'] for r in sorted([r for r in UAB.values() if r['UnitId']==ZBD],key=lambda r:r['Id'])];assert own==[2010731,2014663],own
APS=88;assert AB[APS]['IsAPS'] and AB[APS]['APSQuantity']==2 and not AB[APS]['IsDefault']
mid=g.add('ModificationsJson',M[483],{'UnitId':ZBD,'Name':'Ability ZBD-251'})
blank={f'Turret{i}Id':0 for i in range(21)}
none=g.add('OptionsJson',O[38],{**blank,'ModificationId':mid,'Name':'Ability ZBD-251 Base','Order':0,'Cost':0,'Ability1Id':own[0],'Ability2Id':own[1],'Ability3Id':0})
aps=g.add('OptionsJson',O[37],{**blank,'ModificationId':mid,'Name':'Ability ZBD-251 APS','Order':1,'Cost':60,'Ability1Id':own[0],'Ability2Id':own[1],'Ability3Id':APS})
g.add('UnitAbilitiesJson',[r for r in UAB.values() if r['UnitId']==ZBD][0],{'AbilityId':APS})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(all(MOB[int(m)]['MaxSpeedRoad']==c['before'] for m,c in d61.items()),'152 road speeds back to dev.60')
ok((W[ZG]['MagazineReloadTimeMin'],W[ZG]['MagazineReloadTimeMax'])==(4.0,4.0),'ZTZ-100 4 s')
opts=sorted([o for o in O.values() if o['ModificationId']==mid],key=lambda o:o['Order'])
ok([(o['Cost'],o['Ability3Id']) for o in opts]==[(0,0),(60,APS)] and all(o['Id']<=32767 for o in opts),'ZBD-251 APS option +60')
for o in opts:
    for k in ('Ability1Id','Ability2Id','Ability3Id'):
        if o[k]:ok(any(r['UnitId']==ZBD and r['AbilityId']==o[k] for r in UAB.values()),('option ability linked',o['Id'],o[k]))
ok(sum(AB[r['AbilityId']]['IsDefault'] for r in UAB.values() if r['UnitId']==ZBD)==2,'no new default ability (APS is non-default)')
receipt={'version':V,'base':'0.8.0-dev.65','base_sha256':BASE,'request':'Osama 13 Nov 18:1x PST: tank speeds broken by the road speed change, fix unit speeds and do road speed by hook; ZTZ-100 4 second reload; ZBD-251 APS as an option for +60',
 'road_speed_rows_restored':len(restored),'examples':{m:[d61[m]['after'],d61[m]['before'],d61[m]['units'][:3]] for m in restored[:6]},'ztz100_reload':[[5,6],[4,4]],'zbd251':{'modification':mid,'options':{'None':none,'APS +60':aps},'aps_ability':APS},'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,len(restored),receipt['zbd251'])
