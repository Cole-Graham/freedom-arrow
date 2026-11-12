"""Build58 over exact Build57 (Osama 12 Nov).

"Motorized GAM team isn't using the right model. remove "motorized" from all the names.
Light AT riflemen renamed "Light Riflemen""
1. GAM-102LR launcher (weapon 2014292) was a TOW-2A clone (model M220, TOW sound, TOW aim and
   reload times); only its missile copied the Spike LR. It now copies the vanilla Spike LR team
   weapon 697 (model SPIKE_LR_Tripod) in full, except identity fields. Ammunition unchanged.
2. "Motorized" is removed from the displayed name (HUDName) of every PLA unit.
3. Motorized Light AT Riflemen 轻反坦克 -> "Light Riflemen", exactly as asked.
4. "SF assault desert should be for motorized": every Motorized (spec 21) squad and unused Motorized
   row copies the existing SF assault desert preset (lods, +0.01558 offset, anchorHands). Taishan
   Eagles stay SF night (Build30 rule: SF class takes priority, all SF wear night vision).
5. "Can you unhide the RU and US units from the PLA build": the PLA build set DisplayInArmory=False on
   every non-China unit. Russian and US units get their normal value back: the vanilla value for
   vanilla units, True for the Freedom Arrow RU/US additions (all visible in live dev.45). Other
   countries stay hidden. China stays the default deck country.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-57.json').read_text())['sha256']
GAM,SPIKE=2014292,697
IDENT=('Id','Name','HUDName','HUDIcon')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson']
receipt={'build':58,'base_build':57,'base_sha256':BASE,'request':'Osama 12 Nov: "Motorized GAM team isn\'t using the right model. remove \\"motorized\\" from all the names. Light AT riflemen renamed \\"Light Riflemen\\""','gam_launcher':{},'renamed':[],'native_verified':False}
# 1. GAM-102LR launcher
assert {r['UnitId'] for r in WA.values() if r['WeaponId']==GAM}=={1221}
old={k:W[GAM][k] for k in W[SPIKE] if k not in IDENT and W[GAM][k]!=W[SPIKE][k]}
g.put('WeaponsJson',GAM,{k:copy.deepcopy(v) for k,v in W[SPIKE].items() if k not in IDENT})
receipt['gam_launcher']={'weapon':GAM,'copies_vanilla':f'{SPIKE} {W[SPIKE]["Name"]}','changed':{k:[old[k],W[GAM][k]] for k in old}}
# 2-3. names
for uid,u in sorted(U.items()):
    name=u.get('HUDName') or ''
    if u.get('CountryId')!=4 or 'Motorized' not in name:continue
    new='Light Riflemen' if uid==1205 else ' '.join(name.replace('Motorized','').split())
    g.put('Units',uid,{'HUDName':new});receipt['renamed'].append({'unit':uid,'from':name,'to':new})
# 5. unhide RU/US
VAN={r['Id']:r for r in json.loads((a.vanilla/'Units.json').read_text())}
receipt['unhidden']={'vanilla':0,'freedom_arrow':[]}
for uid,u in sorted(U.items()):
    if u.get('CountryId') not in (1,2) or u.get('DisplayInArmory'):continue
    if uid in VAN:
        if not VAN[uid]['DisplayInArmory']:continue
        receipt['unhidden']['vanilla']+=1
    else:receipt['unhidden']['freedom_arrow'].append(f"{uid} {u['HUDName']}")
    g.put('Units',uid,{'DisplayInArmory':True})
# 4. Motorized bodies
KEY='UserData/FAModels/infantry-bodies.json';LODS=[f'pla2_sf_assault_desert_{i}.fas' for i in range(3)]
bodies=json.loads(z.read(KEY));by={b['unitId']:b for b in bodies};strip=lambda b:{k:v for k,v in b.items() if k!='unitId'}
preset=[strip(b) for b in bodies if b['lods']==LODS];assert preset and all(x==preset[0] for x in preset);preset=preset[0]
spec21={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==21}
unused={u for u in by if not any(r['UnitId']==u for r in t['SpecializationAvailabilitiesJson'].values())}
mot=sorted(u for u in by if u!=1203 and (u in spec21 or (u in unused and 'Motorized' in (before['Units'][u]['HUDName'] or ''))))
receipt['motorized_bodies']={'preset':'SF assault desert','kept':{'1203':'Taishan Eagles: SF night (SF rule)'},'changed':[]}
for uid in mot:
    if strip(by[uid])==preset:continue
    receipt['motorized_bodies']['changed'].append({'unit':uid,'name':U[uid]['HUDName'],'playable':uid in spec21,'from':by[uid]['lods'][0].removesuffix('_0.fas')})
    by[uid].clear();by[uid].update({'unitId':uid,**preset})
old=json.loads(z.read(KEY));assert [b['unitId'] for b in old]==[b['unitId'] for b in bodies]
for x,y in zip(old,bodies):assert x==y or (x['unitId'] in mot and strip(y)==preset),x['unitId']
(SRC/KEY).write_bytes((json.dumps(bodies,indent=2)+'\n').encode())
# checks
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(U[1205]['HUDName']=='Light Riflemen','light riflemen')
ok(all(u['DisplayInArmory']==(VAN[k]['DisplayInArmory'] if k in VAN else True) for k,u in U.items() if u.get('CountryId') in(1,2)),'RU/US visibility')
ok(not any(u['DisplayInArmory'] for k,u in U.items() if u.get('CountryId') not in(1,2,4)),'other countries hidden')
ok(not any('Motorized' in (u.get('HUDName') or '') for u in U.values() if u.get('CountryId')==4),'motorized left')
ok(all(W[GAM][k]==W[SPIKE][k] for k in W[SPIKE] if k not in IDENT) and W[GAM]['HUDName']=='GAM-102LR','gam copy')
for tab in t:
    for key,row in before[tab].items():
        if (tab,key)==('WeaponsJson',GAM):continue
        if tab=='Units':
            ok({k:v for k,v in t[tab][key].items() if k not in('HUDName','DisplayInArmory')}=={k:v for k,v in row.items() if k not in('HUDName','DisplayInArmory')},('unit changed',key))
            if t[tab][key]['DisplayInArmory']!=row['DisplayInArmory']:ok(row['CountryId'] in(1,2) and t[tab][key]['DisplayInArmory'] and (key not in VAN or VAN[key]['DisplayInArmory']),('unhide',key))
            if t[tab][key]['HUDName']!=row['HUDName']:ok(row['CountryId']==4,('rename',key))
        else:ok(t[tab].get(key)==row,('row changed',tab,key))
    ok(set(t[tab])==set(before[tab]),('rows added/removed',tab))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-build58.json',receipt)
(ROOT/'tools/pla-specs/build58-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'unhidden vanilla',receipt['unhidden']['vanilla'],'FA',len(receipt['unhidden']['freedom_arrow']));print(json.dumps(receipt['gam_launcher'],ensure_ascii=False))
for r in receipt['renamed']:print(r['unit'],r['from'],'->',r['to'])
for r in receipt['motorized_bodies']['changed']:print('body',r)
