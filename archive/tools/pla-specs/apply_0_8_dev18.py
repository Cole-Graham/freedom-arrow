"""Freedom Arrow 0.8.0-dev.18 over exact 0.8.0-dev.17 (Osama 12 Nov 16:19 PST): "HJ-16 1500m. Sorry I meant SRAT II armor." /
"a lot of the infantry models broke and don't work anymore. I see the russian one".
- ZBL-191 HJ-16 (ammo 2010339): range 750 = 1500 m displayed (the Javelin's).
- ZBL-191 armour (own row): FA Stryker SRAT II (armor 2000235): 12 HP, HEAT 700/700/130/20, KE 80/60/30/20. Price stays 105.
- FAModels 0.3.17 (models DLL, complete package only): rebuilds unloaded cached body/weapon meshes. 0.8.0-dev.15 game log
  16:12: after two matches every infantry body in the Arsenal threw Mesh.vertexCount NullReferenceException and fell back to
  the native (Russian) body.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.18'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.17.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);A,AR,UAR=t['AmmunitionsJson'],t['ArmorsJson'],t['UnitArmorsJson']
ZBL,LA,SRAT2=979,2010339,2000235
assert A[LA]['HUDName']=='HJ-16' and AR[SRAT2]['Name']=='Armor Stryker SRAT' and AR[SRAT2]['HeatArmorFront']==700
arm=[r['ArmorId'] for r in UAR.values() if r['UnitId']==ZBL];assert len(arm)==1
ARMOR=('MaxHealthPoints','HeatArmorFront','HeatArmorSides','HeatArmorRear','HeatArmorTop','KinArmorFront','KinArmorSides','KinArmorRear','KinArmorTop')
g.put('AmmunitionsJson',LA,{'GroundRange':750.0});g.put('ArmorsJson',arm[0],{k:AR[SRAT2][k] for k in ARMOR})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(A[LA]['GroundRange']==750.0 and [AR[arm[0]][k] for k in ARMOR]==[AR[SRAT2][k] for k in ARMOR],'HJ-16 1500 m, SRAT II')
for tab in t:
    for key,row in before[tab].items():
        if (tab,key) not in(('AmmunitionsJson',LA),('ArmorsJson',arm[0])):ok(t[tab].get(key)==row,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.17','base_sha256':BASE,'request':'Osama 12 Nov 16:19 PST: HJ-16 1500 m, SRAT II; infantry models broken','hj16_range_m':1500,
 'armor':{k:AR[arm[0]][k] for k in ARMOR},'famodels':'0.3.17 (cached mesh rebuild after scene unload)','checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1))
