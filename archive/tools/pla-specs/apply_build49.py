"""Build49 over exact Build48 (Osama 12 Nov 05:00-06:00 PST): artillery, infantry weapons, squad prices.

1. Artillery "match what we have in game already with scale (nuclear ballistic missile aside)":
   each PLA tube/rocket system copies the main round, launcher behaviour, ammunition count and
   price of its vanilla counterpart (ART). DF-31 is untouched.
2. Infantry weapons "make sure they're modeled properly": PF-97 takes its MRO-Z stand-in's
   thermobaric values; HJ-8E 700 and HJ-73D 600 penetration on infantry and vehicles alike.
   QLU-11 is left for discussion.
3. "Price everything": each PLA squad takes the distance-weighted average price of the three most
   similar vanilla US/RU squads (size, ATGM/MANPAD/AT/MG/sniper/GL counts, SF, recon);
   tools/pla-specs/build49-infantry-prices.json lists the neighbours.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-48.json').read_text())['sha256']
# uid: (vanilla unit, vanilla ammo, rounds, cost, basis)
ART={908:(93,67,12,250,'Smerch 300 mm'),1035:(93,430,8,250,'Tornado-S 300 mm round, 8 tubes'),1036:(93,430,8,250,'Tornado-S 300 mm round, 8 tubes'),
 922:(92,66,40,100,'Grad 122 mm'),963:(92,66,40,90,'Grad 122 mm, older truck'),934:(223,214,12,175,'Uragan 220 mm round'),
 907:(539,613,30,200,'K9 155/52 autoloader class'),933:(636,910,21,190,'Malva wheeled 152/155'),1034:(636,910,21,175,'Malva class truck howitzer'),
 1033:(205,174,40,75,'2S1 122 mm (truck)'),1038:(205,174,40,80,'2S1 122 mm'),931:(205,174,40,80,'2S1 122 mm'),1040:(205,174,40,65,'2S1 122 mm, older'),
 1042:(205,174,40,75,'2S1 122 mm'),1043:(205,174,40,80,'2S1 122 mm'),1039:(247,261,30,130,'M109A6 155/39-45'),1041:(234,236,30,80,'2S3M1 152 mm'),
 926:(218,190,36,80,'Nona-SVK 120 mm gun-mortar'),1037:(205,174,40,80,'2S1 122 mm (wheeled)'),
 1029:(226,218,1,125,'Iskander round, one missile'),1030:(226,218,1,150,'Iskander round, one heavier missile'),1028:(226,218,1,150,'Iskander round, one glide missile'),
 1129:(226,219,2,225,'Iskander-K (Osama: YJ-18 copies it)')}
IDENT=('Id','Name','HUDName','HUDIcon')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--prices',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];A=t['AmmunitionsJson'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson']
def own(tab,field,uid,row):
    rid=row[field]
    if any(r[field]==rid and r['UnitId']!=uid for r in WA.values()):
        src=t[tab][rid];rid=g.add(tab,src,{'Name':src['Name']+' PLA '+str(uid)})
        for r in [r for r in WA.values() if r['UnitId']==uid and r[field]==row[field]]:g.put('WeaponAmmunitionsJson',r['Id'],{field:rid})
    return rid
receipt={'build':49,'base_build':48,'base_sha256':BASE,'artillery':{},'infantry_weapons':[],'squad_prices':{}}
# 1. artillery
for uid,(vu,vam,rounds,cost,basis) in ART.items():
    rows=sorted([r for r in WA.values() if r['UnitId']==uid and A[r['AmmunitionId']]['GroundRange']>=1000],key=lambda r:-A[r['AmmunitionId']]['Damage'])
    assert rows,uid;main=rows[0];vrow=next(r for r in WA.values() if r['UnitId']==vu and r['AmmunitionId']==vam)
    old={'cost':U[uid]['Cost'],'damage':A[main['AmmunitionId']]['Damage'],'range':A[main['AmmunitionId']]['GroundRange'],'rounds':main['Quantity']}
    aid=own('AmmunitionsJson','AmmunitionId',uid,main);g.put('AmmunitionsJson',aid,{k:copy.deepcopy(v) for k,v in A[vam].items() if k not in IDENT})
    main=WA[main['Id']];wid=own('WeaponsJson','WeaponId',uid,main);g.put('WeaponsJson',wid,{k:copy.deepcopy(v) for k,v in W[vrow['WeaponId']].items() if k not in IDENT+('ModelFileName',)})
    g.put('WeaponAmmunitionsJson',main['Id'],{'Quantity':rounds});g.put('Units',uid,{'Cost':cost})
    receipt['artillery'][str(uid)]={'name':U[uid]['HUDName'],'basis':basis,'vanilla_unit':U[vu]['HUDName'],'old':old,'new':{'cost':cost,'damage':A[vam]['Damage'],'range':A[vam]['GroundRange'],'rounds':rounds}}
# 2. infantry weapons
pla={u['Id'] for u in U.values() if u.get('CountryId')==4}
mroz=next(r['AmmunitionId'] for r in WA.values() if r['WeaponId']==668 and r['UnitId']<900)
for r in [r for r in WA.values() if r['UnitId'] in pla and A[r['AmmunitionId']]['HUDName'].startswith('PF-97')]:
    aid=own('AmmunitionsJson','AmmunitionId',r['UnitId'],r);g.put('AmmunitionsJson',aid,{k:copy.deepcopy(v) for k,v in A[mroz].items() if k not in IDENT})
    receipt['infantry_weapons'].append([U[r['UnitId']]['HUDName'],'PF-97 = MRO-Z values'])
for prefix,pen in [('HJ-8E',700.0),('HJ-73D',600.0)]:
    for r in [r for r in WA.values() if r['UnitId'] in pla and A[r['AmmunitionId']]['HUDName'].startswith(prefix)]:
        if A[r['AmmunitionId']]['PenetrationAtGroundRange']==pen:continue
        aid=own('AmmunitionsJson','AmmunitionId',r['UnitId'],r);g.put('AmmunitionsJson',aid,{'PenetrationAtGroundRange':pen,'PenetrationAtMinRange':pen,'Damage':10.5})
        receipt['infantry_weapons'].append([U[r['UnitId']]['HUDName'],f'{prefix} {pen:g}'])
# 3. squad prices
prices=json.loads(a.prices.read_text())
for k,v in prices['pla'].items():
    uid=int(k);g.put('Units',uid,{'Cost':v['new']});receipt['squad_prices'][k]={'name':v['name'],'old':v['old'],'new':v['new'],'vanilla_neighbours':v['vanilla_neighbours']}
receipt['price_model']={'method':'3 nearest vanilla US/RU squads, distance-weighted','vanilla_squads':prices['n'],'leave_one_out_mean_abs_error':round(prices['mae'],1)}
# checks
checks=0
def ok(c,label):
    global checks
    assert c,label;checks+=1
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-PLA unit changed',uid))
for tab in ['AmmunitionsJson','WeaponsJson']:
    for key,row in before[tab].items():
        users={r['UnitId'] for r in before['WeaponAmmunitionsJson'].values() if r[('AmmunitionId' if tab=='AmmunitionsJson' else 'WeaponId')]==key}
        if any(U.get(x,{}).get('CountryId')!=4 for x in users):ok(t[tab][key]==row,('shared row changed',tab,key))
ok(t['Units'][1032]==before['Units'][1032],'DF-31 untouched')
for uid,(vu,vam,rounds,cost,basis) in ART.items():ok(U[uid]['Cost']==cost,('art cost',uid))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-build49.json',receipt)
(ROOT/'tools/pla-specs/build49-checks.json').write_text(json.dumps({k:v for k,v in receipt.items() if k not in('squad_prices','artillery')},indent=2,ensure_ascii=False)+'\n')
(ROOT/'tools/pla-specs/build49-infantry-prices.json').write_text(json.dumps(prices,indent=1,ensure_ascii=False)+'\n')
print(json.dumps({'checks':checks,'artillery':len(receipt['artillery']),'infantry_weapon_rows':len(receipt['infantry_weapons']),'squads':len(receipt['squad_prices'])},indent=1))
for k,v in receipt['artillery'].items():print(k,v['name'],v['old'],'->',v['new'])
