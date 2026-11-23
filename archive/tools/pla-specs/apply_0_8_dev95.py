"""Freedom Arrow 0.8.0-dev.95 over exact 0.8.0-dev.94 (Osama 13 Nov 23:10 PST, thread 1571014792016171120): spec point distribution.
PLAAF: Recon 500, Air 1500. PLAGF Armored: Air 0, Combat (vehicles) 2000. PLARF Rocket: Recon 500, Support 2000.
PLAN SOF: Support 500, Air 1500, Combat 500, Helicopters 750. PLAGF Motorized: Infantry 1250, Helicopters 500, Recon 750, Air 750
(the message lists Aircraft twice, 500 then 750; the last value is used). Categories not named are unchanged.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.95';PREV='0.8.0-dev.94'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);S=t['SpecializationsJson'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
F=('ReconPoints','InfantryPoints','CombatPoints','SupportPoints','HelicoptersPoints','AirPoints')
NEW={17:{'ReconPoints':500,'AirPoints':1500},18:{'AirPoints':0,'CombatPoints':2000},19:{'ReconPoints':500,'SupportPoints':2000},
     20:{'SupportPoints':500,'AirPoints':1500,'CombatPoints':500,'HelicoptersPoints':750},21:{'InfantryPoints':1250,'HelicoptersPoints':500,'ReconPoints':750,'AirPoints':750}}
NAMES={17:'PLA PLAAF Air Force',18:'PLA PLAGF Ground Force/Armored',19:'PLA PLARF Rocket/Reservist',20:'PLA PLAN Navy/SOF',21:'PLA PLAGF Motorized'}
for sid,ch in NEW.items():
    ok(S[sid]['Name']==NAMES[sid],sid);before={f:S[sid].get(f) for f in F};g.put('SpecializationsJson',sid,ch)
    rec[S[sid]['UIName']]={'before':before,'after':{f:S[sid].get(f) for f in F},'total':[sum(before.values()),sum(S[sid].get(f) for f in F)]}
for sid in NEW:ok(all(S[sid][k]==v for k,v in NEW[sid].items()),('readback',sid))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 23:10 PST spec point distribution',checks=checks,verified='data only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
for k,v in rec.items():
    if isinstance(v,dict) and 'after' in v:print(k,v['after'],'total',v['total'])
print('checks',checks)
