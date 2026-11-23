"""Freedom Arrow 0.8.0-dev.61 over exact 0.8.0-dev.60 (Osama 13 Nov 16:37 PST, thread 1570945828829405345):
"Tracked vehicles should get a +60% speed bonus on the road. Wheeled should be about double."
The game has no global road multiplier (GameConfig has only GlobalForestSpeedMultiplier 0.5 and
InfantryForestSpeedMultiplier 1.0); road speed is MobilityJson.MaxSpeedRoad per row.
- Tracked: ground-vehicle rows (all linked units Type 4) with road/off-road below 1.6 (vanilla tracked rows are 1.09-1.40)
  get MaxSpeedRoad = round(MaxCrossCountrySpeed * 1.6). Off-road, reverse and water speeds are unchanged.
- Wheeled rows (1.82-2.33, almost all exactly 2.0) are already about double and stay unchanged.
- Infantry, helicopters, aircraft, naval and the C-17 takeoff rows are not touched.
"""
import argparse,hashlib,json,sys,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
V='0.8.0-dev.61';PREV='0.8.0-dev.60'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
U,M=t['Units'],t['MobilityJson']
links=defaultdict(set)
for r in t['UnitPropulsionsJson'].values():
    if r['UnitId'] in U:links[r['MobilityId']].add(r['UnitId'])
changes={};wheeled={}
for mid,m in sorted(M.items()):
    us=links.get(mid)
    if not us or any(U[u]['Type']!=4 for u in us):continue
    road,cc=m['MaxSpeedRoad'],m['MaxCrossCountrySpeed']
    if cc<=0 or road>200:continue   # C-17 takeoff dummy rows
    names=sorted({U[u]['HUDName'] for u in us if U[u].get('DisplayInArmory')})
    if road/cc>=1.6:wheeled[mid]={'road':road,'off_road':cc,'ratio':round(road/cc,2),'units':names};continue
    new=float(round(cc*1.6))
    patches['MobilityJson'].setdefault(str(mid),{})['MaxSpeedRoad']=new;M[mid]['MaxSpeedRoad']=new
    changes[mid]={'before':road,'after':new,'off_road':cc,'units':names}
tracked={n for c in changes.values() for n in c['units']};wnames={n for c in wheeled.values() for n in c['units']}
for n in ('M1A2 SEP v2','T-90M','BMP-3','M2A2 Bradley ESV','T-80U','ZTZ-99A','ZTQ-15','PLZ-05','M109A6 Paladin','Spartan','PT-76'):assert any(x.startswith(n) for x in tracked),n
for n in ('BTR-82','Stryker ESV','Humvee','PGL-625','JRVG-1','Tigr','BTR-80'):assert any(x.startswith(n) for x in wnames) and not any(x.startswith(n) for x in tracked),n
assert all(abs(c['after']-1.6*c['off_road'])<=0.5 for c in changes.values())
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':__doc__.split('\n')[1],'tracked_rows':len(changes),'wheeled_rows_unchanged':len(wheeled),
 'by_offroad':{str(cc):sorted({c['after'] for c in changes.values() if c['off_road']==cc}) for cc in sorted({c['off_road'] for c in changes.values()})},
 'changes':{str(k):v for k,v in changes.items()},'wheeled_unchanged':{str(k):v for k,v in wheeled.items()}}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes(z.read('UserData/FAModels/models.json'))
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('tracked rows',len(changes),'wheeled rows unchanged',len(wheeled));print(json.dumps(receipt['by_offroad']))
for k,c in changes.items():print(k,c['before'],'->',c['after'],'off',c['off_road'],c['units'][:4])
