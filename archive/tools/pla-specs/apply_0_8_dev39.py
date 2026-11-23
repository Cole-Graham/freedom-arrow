"""Freedom Arrow 0.8.0-dev.39 over exact 0.8.0-dev.38 (Osama 13 Nov 12:00-12:45 PST, thread 1569806740139282476):
"I downloaded a ton of files ... please add them to the game"; "implement all the models. I purchased the cart".
Seventeen purchased CGTrader models (Osama's cart, 13 Nov) replace stand-ins or give a model to units that had none.
Converted with work/pla-0.8/cart-20261113 (anyconv.py, runall.sh, build_cart.py, fix_glass.py): animation cleared,
ground planes and loose display parts removed, 2048 px armory / 1024 px battle textures, untextured glass made clear.
Camo: PLARF-only units (DF-15, DF-17, HQ-6A, Type 59D, ZTZ-59D1, Type 89) desert; others keep the seller's woodland/green.
Also: PHL-191 (1036) is named "PHL-191 Ballistic" (Osama 13 Nov: "cruise is the 3 box and ballistic is the 2").
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.39';PREV='0.8.0-dev.38'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units']
assert U[1036]['HUDName']=='PHL-191' and U[1036]['Name']=='PLA Catalogue PHL-191 / AR3';g.put('Units',1036,{'HUDName':'PHL-191 Ballistic'})
# unit Name -> model slug (files m_<slug>_static.fam / m_<slug>_lo_static.fam)
NEW={'PLA Catalogue AFT-09':'aft09','PLA Catalogue CSK-181':'csk181','PLA CSK-181 Transport':'csk181',
 'PLA Catalogue CTL-181 loitering munition launcher':'ctl181','PLA Catalogue DF-15':'df15','PLA Catalogue DF-17':'df17',
 'PLA Catalogue HQ-11':'hq11','PLA Catalogue HQ-6A':'hq6a','PLA Catalogue PCL-181 / SH-15':'pcl181','PLA PHL-03':'phl03',
 'PLA Catalogue PHL-16':'phl16','PLA Catalogue PHL-191 / AR3':'phl191b','PLA QN-506':'qn506c','PLA Catalogue ZBD-251':'zbd251',
 'PLA Catalogue Type 89':'zsd89d','PLA PLAN ZSD-89':'zsd89','PLA Catalogue Type 89A':'zsd89a','PLA Catalogue ZSL-92 family':'zsl92',
 'PLA ZSL-92 MG':'zsl92','PLA Catalogue Type 59D':'ztz59d','PLA ZTZ-59D1':'ztz59d'}
names={r['Name'] for r in U.values()}
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ));before={k:models.get(k) for k in NEW}
for n,s in NEW.items():
    assert n in names,n;models[n]={'file':f'm_{s}_static.fam','battle':f'm_{s}_lo_static.fam','align':False}
files=sorted(f.name for f in a.stage.iterdir())
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for n,s in NEW.items():ok(models[n]['file'] in files and models[n]['battle'] in files and f'm_{s}_static.mat.json' in files,('files',n))
for f in files:ok(f'UserData/FAModels/{f}' not in z.namelist(),('new file name, no overwrite',f))
ok(U[1036]['HUDName']=='PHL-191 Ballistic','PHL-191 Ballistic')
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov: "I downloaded a ton of files ... please add them to the game"; "implement all the models. I purchased the cart so all the models should be there"; PHL-191 two-pod = "PHL-191 Ballistic".',
 'models':{n:{'before':before[n],'after':models[n]} for n in NEW},'new_files':len(files),'renamed':{'1036 HUDName':['PHL-191','PHL-191 Ballistic']},
 'camo':{'desert (PLARF only)':['DF-15','DF-17','HQ-6A','Type 59D','ZTZ-59D1','Type 89'],'seller paint':'the rest; QN-506 seller file is flat sand, recoloured olive'},
 'tools':'work/pla-0.8/cart-20261113 (private purchased sources stay out of git)','checks':0}
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))
