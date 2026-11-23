"""Build56 over exact Build55: restore China (Osama 12 Nov 11:19 "the pla build doesnt show china").

Game log 11:17:36: FREEDOM_ARROW_FAILED: constants not applied; original fields restored.
Field type mismatch Turret0Id. Builds 47-55 wrote empty pylon slots in new loadout options as null;
the live table uses integer 0 for an empty slot. Every null in a patched row whose vanilla field is
never null becomes that type's empty value (only OptionsJson Turret*Id rows are affected).
The generating scripts now write 0, and check_field_types.py runs on every build.
"""
import argparse,hashlib,json,sys,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
BASE=json.loads((REL/'out/PLA-TEST-Build-55.json').read_text())['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base);EMPTY={'int':0,'float':0.0,'str':'','bool':False};fixed=defaultdict(int)
for tab,fn in FIELD_TO_FILE.items():
    types=defaultdict(set)
    for r in json.loads((a.vanilla/(tab+'.json')).read_text()):
        for k,v in r.items():types[k].add(type(v).__name__)
    n='UserData/FreedomArrow/constants/'+fn;raw=z.read(n);data=json.loads(raw);changed=False
    for key,row in data.items():
        if row is None:continue
        for f,v in list(row.items()):
            if v is None and f in types and 'NoneType' not in types[f] and len(types[f])==1:
                row[f]=EMPTY[next(iter(types[f]))];fixed[f'{tab}.{f}']+=1;changed=True
    if changed:out=SRC/n;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((json.dumps(data,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
    else:(SRC/n).write_bytes(raw)
receipt={'build':56,'base_build':55,'base_sha256':BASE,'cause':'FREEDOM_ARROW_FAILED: Field type mismatch Turret0Id (null empty pylon slots since Build47)','fixed':dict(fixed),'total':sum(fixed.values())}
f=SRC/'UserData/FreedomArrow/pla-build56.json';f.write_text(json.dumps(receipt,indent=2)+'\n');(ROOT/'tools/pla-specs/build56-checks.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=1))
