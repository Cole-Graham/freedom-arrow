"""Offline copy of the runtime 'Field type mismatch' rule: every patched field must have the JSON
type the live (vanilla) table uses for that field. null where vanilla never has null fails.
Usage: python3 check_field_types.py PACKAGE.bamod [VANILLA_DIR]"""
import json,sys,zipfile
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pla-hotfix39-worktree'))
from pipeline.tables import FIELD_TO_FILE
V=Path(sys.argv[2] if len(sys.argv)>2 else '/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla')
z=zipfile.ZipFile(sys.argv[1]);bad=[]
num={'int','float'}
for tab,fn in FIELD_TO_FILE.items():
    types=defaultdict(set)
    for r in json.loads((V/(tab+'.json')).read_text()):
        for k,v in r.items():types[k].add(type(v).__name__)
    for key,row in json.loads(z.read('UserData/FreedomArrow/constants/'+fn)).items():
        if row is None:continue
        for f,v in row.items():
            t=type(v).__name__;ok=types.get(f)
            if ok is None:continue
            if t in ok or (t in num and ok&num and 'bool' not in ok):continue
            bad.append([tab,key,f,t,sorted(ok)])
from collections import Counter
print(json.dumps({"package":sys.argv[1],"violations":len(bad),"by_field":{f"{a}.{c} {d}":n for (a,c,d),n in Counter((b[0],b[2],b[3]) for b in bad).items()},"first":bad[:8]},indent=1))
sys.exit(1 if bad else 0)
