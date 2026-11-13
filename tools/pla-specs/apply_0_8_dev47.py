"""Freedom Arrow 0.8.0-dev.47 over exact 0.8.0-dev.46 (Osama 13 Nov 13:52 PST, thread 1569806740139282476):
"pgz 09 guns are missing, HQ-17 radars are better but still messed up, ZTL-191 turret is floating a bit high, For ZSL-92,
can we remove the turret? and make that the MG variant (just call it ZSL-92 and the other ZSL-92 Autocannon), ZSD-89A,
ZBL-191, ZTZ-99A, ZTZ-99, ZTZ-100, ZTQ-15, we want the original artist provided woodland digital camo ... CSK 181 textures
are broken".
- Seller woodland-digital coatings (ShuyangXi packs): ZTQ-15 + ZTQ-15 Recon (Hull_Camo), ZTZ-99/99A/99A2/99G (Hull_Mix),
  ZBL-191 (Hull_Camo), ZTZ-100 (Hull_Camo). ZSD-89A already uses the seller Textures_02_main set (dev.43).
- PGZ-09: twin 35 mm guns raised 1.63 m to the turret (FBX local offset); HQ-17A: search radar 0.9 m forward and 2.0 m up,
  tracking radar 1.9 m up; ZTL-191: turret, gun and remote MG 0.18 m back and 0.27-0.47 m down to Shawn's ZTL-221-Orig.blend.
- ZSL-92 MG card (1232): named "ZSL-92", model without the turret (m_zsl92mg). 1079 stays "ZSL-92 Autocannon".
- CSK-181 and PCL-181: the 3.1M / 14M-vertex seller meshes are decimated (0.12 / 0.3); PCL-181 tyres dark as in the preview.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.47';PREV='0.8.0-dev.46'
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
assert U[1232]['Name']=='PLA ZSL-92 MG' and U[1079]['HUDName']=='ZSL-92 Autocannon',(U[1232]['HUDName'],U[1079]['HUDName'])
hud_before=U[1232]['HUDName']
if hud_before!='ZSL-92':g.put('Units',1232,{'HUDName':'ZSL-92'})
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ))
SET={**{k:'m_ztq15_camo' for k in ('PLA ZTQ-15','PLA ZTQ-15 Recon')},**{k:'m_ztz99a_mix' for k in ('PLA Catalogue ZTZ-99','PLA ZTZ-99A','PLA ZTZ-99A2','PLA ZTZ-99G')},
 **{k:'m_zbl191_camo' for k in ('PLA ZBL-191','PLA Catalogue ZBL19 — seller name')},'PLA ZTZ-100':'m_ztz100_camo','PLA ZSL-92 MG':'m_zsl92mg'}
files=sorted(x.name for x in a.stage.iterdir());before={};checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for k,stem in SET.items():
    ok(k in models,('mapped',k));before[k]=dict(models[k]);models[k]={**models[k],'file':f'{stem}_static.fam','battle':f'{stem}_lo_static.fam'}
    ok(models[k]['file'] in files and models[k]['battle'] in files,('files',k))
ok(U[1232]['HUDName']=='ZSL-92','ZSL-92 name')
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 13:52 PST: PGZ-09 guns, HQ-17 radars, ZTL-191 turret height, turretless ZSL-92 (MG card named ZSL-92), seller woodland digital for ZSD-89A/ZBL-191/ZTZ-99A/ZTZ-99/ZTZ-100/ZTQ-15, ZTZ-59D model, CSK-181 textures.',
 'mappings':{k:{'before':before[k],'after':models[k]} for k in SET},'renamed':{'1232 HUDName':[hud_before,'ZSL-92']},'files':files,'checks':0}
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files),'1232',hud_before,'->',U[1232]['HUDName'])
