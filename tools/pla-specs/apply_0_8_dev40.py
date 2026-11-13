"""Freedom Arrow 0.8.0-dev.40 over exact 0.8.0-dev.39 (Osama 13 Nov 12:58-13:02 PST, thread 1569806740139282476):
"QN-506 should have textures, let me redownload"; "do we have zbl-08 btw because the current in game model isn't good".
- QN-506: the re-download is the same seller package (its OBJ is byte-identical; the SketchUp file holds only thumbnails,
  no texture maps). The main body paint now carries PLA woodland digital camo, projected on the hull (m_qn506w).
- ZBL-08 uses Shawn's PBR ZBL-09 model (same 8x8 family, woodland), in place of the old rip with camo netting.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.40';PREV='0.8.0-dev.39'
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
NEW={'PLA QN-506':'qn506w','PLA ZBL-08':'zbl09'}
names={r['Name'] for r in U.values()}
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ));before={k:models.get(k) for k in NEW}
assert before['PLA QN-506']['file']=='m_qn506c_static.fam' and before['PLA ZBL-08']['file']=='m_zbl08_static.fam',before
for n,s in NEW.items():
    assert n in names,n;models[n]={'file':f'm_{s}_static.fam','battle':f'm_{s}_lo_static.fam','align':False}
files=sorted(f.name for f in a.stage.iterdir())
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(all(f'UserData/FAModels/m_zbl09{x}' in z.namelist() for x in ('_static.fam','_lo_static.fam')),'ZBL-09 files in package')
ok(models['PLA QN-506']['file'] in files and models['PLA QN-506']['battle'] in files,'QN-506 files')
for f in files:ok(f'UserData/FAModels/{f}' not in z.namelist(),('new file name, no overwrite',f))
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov: "QN-506 should have textures, let me redownload"; "QN-506 redownloaded please check"; "do we have zbl-08 btw because the current in game model isn\'t good".',
 'models':{n:{'before':before[n],'after':models[n]} for n in NEW},'new_files':files,
 'qn506':'re-download identical (OBJ byte-identical; SKP has 97 thumbnails, no texture maps); body material _3 gets triplanar woodland digital, tile 3200 units (~4 m)',
 'zbl08':'Shawn ZBL-09 PBR model, same Type 08 8x8 family','checks':0}
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))
