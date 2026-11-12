"""Build53 over exact Build52 (Osama 12 Nov 11:01 PST): "Rename akd-10 to HJ-10".
Every PLA weapon/ammunition name and loadout label that says AKD-10 now says HJ-10.
Statistics are unchanged. AKD-9 is left as it is.
"""
import argparse,copy,hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-52.json').read_text())['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native)
changed={}
for tab,fields in [('WeaponsJson',('HUDName',)),('AmmunitionsJson',('HUDName',)),('OptionsJson',('UIName',)),('TurretsJson',('Name',))]:
    for key,row in list(t[tab].items()):
        if key in native[tab]:continue
        upd={f:row[f].replace('AKD-10','HJ-10') for f in fields if isinstance(row.get(f),str) and 'AKD-10' in row[f]}
        if upd:g.put(tab,key,upd);changed.setdefault(tab,0);changed[tab]+=1
LABEL={'Custom_Option_2xM230':'2x 30 mm gun pods','Custom_Option_38xHydra':'38x 70 mm rockets','Custom_Option_32xDAGR':'32x FS-70A','Custom_Option_8xJAGM':'8x HJ-10',
 'Custom_Option_14xHydra':'14x 70 mm rockets','Custom_Option_16xDAGR':'16x FS-70A','Custom_Option_4xStingerAA':'4x TY-90','Custom_Option_4xJAGM':'4x HJ-10'}
z20=0
for m in [m for m in t['ModificationsJson'].values() if m['UnitId'] in (914,1245) and m['Type']==3]:
    for o in [o for o in t['OptionsJson'].values() if o['ModificationId']==m['Id'] and o['UIName'] in LABEL]:g.put('OptionsJson',o['Id'],{'UIName':LABEL[o['UIName']]});z20+=1
changed['Z-20 menu labels']=z20
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for tab in ('WeaponsJson','AmmunitionsJson','OptionsJson'):
    for key,row in t[tab].items():
        ok(not any(isinstance(v,str) and 'AKD-10' in v for k,v in row.items() if k in('HUDName','UIName')),('AKD-10 left',tab,key))
        if key in before[tab]:ok({k:v for k,v in row.items() if k not in('HUDName','UIName','Name')}=={k:v for k,v in before[tab][key].items() if k not in('HUDName','UIName','Name')},('stats changed',tab,key))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
receipt={'build':53,'base_build':52,'base_sha256':BASE,'renamed_rows':changed,'checks':checks}
save('UserData/FreedomArrow/pla-build53.json',receipt);(ROOT/'tools/pla-specs/build53-checks.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=1))
