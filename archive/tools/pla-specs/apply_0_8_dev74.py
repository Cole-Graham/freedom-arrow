"""Freedom Arrow 0.8.0-dev.74 over exact 0.8.0-dev.73 (Osama 13 Nov 19:4x PST, thread 1567745029781454889: "JRVG needs radar"):
The native loader keeps only the FIRST default ability row of a unit (LoadAbility RVA 0x285E50; vanilla has no unit with two).
JRVG-1 had its smoke row first and the vanilla Radar SHORAD (60) second, so the radar never loaded. PGZ-09, HJ-10 and AFT-10
had the same smoke-then-radar pair. Fix: copy the radar fields (Radar SHORAD values) into each unit's own first ability,
which keeps its smoke, and remove the second link. Ability 60 itself is unchanged.
Left alone: ZBD-251 (its options name smoke + laser in Ability1/2, so both load), HQ-7/HQ-7B (two radars; the first loads),
and units whose extra default rows are exact duplicates.
"""
import argparse,hashlib,json,sys,zipfile,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.74'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.73.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,AB,UA,O=(t[k] for k in ('Units','AbilitiesJson','UnitAbilitiesJson','OptionsJson'))
RADAR=('IsRadar','RadarLowAltOpticsModifier','RadarHighAltOpticsModifier','RadarLowAltWeaponRangeModifier','RadarHighAltWeaponRangeModifier','RadarSwitchCooldown','IsRadarStatic')
users=collections.defaultdict(set)
for r in UA.values():users[r['AbilityId']].add(r['UnitId'])
def defaults(uid):return sorted((r for r in UA.values() if r['UnitId']==uid and AB[r['AbilityId']].get('IsDefault')),key=lambda r:r['Id'])
slots={x for o in O.values() for x in (o['Ability1Id'],o['Ability2Id'],o['Ability3Id'])}
fixed={}
for uid,name in ((952,'JRVG-1'),(909,'PGZ-09'),(936,'HJ-10'),(1055,'AFT-10')):
    assert U[uid]['HUDName']==name
    rs=defaults(uid);assert len(rs)==2,(name,rs)
    first,second=AB[rs[0]['AbilityId']],AB[rs[1]['AbilityId']]
    assert first['IsSmoke'] and not first['IsRadar'] and second['IsRadar'] and not second['IsSmoke'] and users[first['Id']]=={uid}
    assert not {first['Id'],second['Id']}&slots and not any(r['UnitId']==uid for r in t['ModificationsJson'].values())
    g.put('AbilitiesJson',first['Id'],{k:second[k] for k in RADAR})
    g.remove('UnitAbilitiesJson',rs[1]['Id'])
    fixed[name]={'ability':first['Id'],'radar_from':second['Id'],'removed_link':rs[1]['Id']}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for name,f in fixed.items():
    uid=next(u for u in U if U[u]['HUDName']==name);rs=defaults(uid);ab=AB[rs[0]['AbilityId']]
    ok(len(rs)==1 and ab['IsSmoke'] and ab['IsRadar'] and ab['SmokeAmmunitionId']==268,name+' one default ability with smoke and radar')
    ok(all(ab[k]==AB[60][k] for k in RADAR if k!='IsRadarStatic') and not ab['IsRadarStatic'],name+' radar values = Radar SHORAD')
ok(AB[60]['IsRadar'] and AB[60]['IsDefault'] and '60' not in patches['AbilitiesJson'],'vanilla Radar SHORAD unchanged')
receipt={'version':V,'base':'0.8.0-dev.73','base_sha256':BASE,'request':'Osama 13 Nov 19:4x PST: JRVG needs radar','fixed':fixed,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(fixed))
